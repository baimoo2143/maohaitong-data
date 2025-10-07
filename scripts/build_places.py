# scripts/build_places.py
import json, hashlib, os, re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
AUTO_PATH   = os.path.join(ROOT, "data", "places_auto.json")
MANUAL_PATH = os.path.join(ROOT, "data", "places_manual.json")
OUT_PATH    = os.path.join(ROOT, "places.json")
VER_PATH    = os.path.join(ROOT, "version.json")

def load_list(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # 相容陣列或 { "places": [...] }
        if isinstance(data, list): return data
        return data.get("places", [])

def norm_city(s: str) -> str:
    return (s or "").replace("臺", "台").strip()

def to_bool_24h(val):
    if isinstance(val, bool): return val
    if not val: return False
    s = str(val).lower()
    return any(k in s for k in ["24h", "24小時", "24-hr", "24 hr", "24hours", "全天"])

def to_float(v, default=None):
    try: return float(v)
    except: return default

def clean_phone(p):
    if not p: return ""
    return re.sub(r"[^0-9#\-\+\(\)\/ ]", "", str(p)).strip()

def build_id(city, name, address):
    base = f"{city}|{name}|{address}"
    h = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return f"mh_{h}"

def normalize_item(item):
    m = dict(item)  # copy
    m["city"]     = norm_city(str(m.get("city","")))
    m["name"]     = str(m.get("name","")).strip()
    m["address"]  = str(m.get("address","")).strip()
    m["phone"]    = clean_phone(m.get("phone",""))
    m["lat"]      = to_float(m.get("lat"), None)
    m["lng"]      = to_float(m.get("lng"), None)

    # 24H 判斷與類別歸一
    is24 = to_bool_24h(m.get("is24h")) or to_bool_24h(m.get("category"))
    m["is24h"] = bool(is24)
    cat = str(m.get("category","")).strip()
    if m["is24h"]:
        m["category"] = "24H醫院" if cat in ["", "醫院", "24H", "24h", "24H醫院"] else cat
    else:
        m["category"] = "醫院" if cat in ["", "醫院", "24H", "24h"] else cat

    # 生成穩定 id（若 manual 先給 id，會保留）
    if not m.get("id"):
        m["id"] = build_id(m["city"], m["name"], m["address"])

    return m

def key_for_merge(m):
    # 用 name+address 做去重 key（大小寫不敏感）
    return (m.get("name","").lower(), m.get("address","").lower())

def main():
    auto  = [normalize_item(x) for x in load_list(AUTO_PATH)]
    manual= [normalize_item(x) for x in load_list(MANUAL_PATH)]

    merged = {}
    # 先放自動資料
    for it in auto:
        merged[key_for_merge(it)] = it
    # 再用手動覆蓋（優先權給 manual）
    for it in manual:
        merged[key_for_merge(it)] = it

    out_list = list(merged.values())
    # 排序：city > category > name
    out_list.sort(key=lambda x: (x.get("city",""), x.get("category",""), x.get("name","")))

    # 輸出最終 places.json（用陣列，與你現有 App 相容）
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out_list, f, ensure_ascii=False, indent=2)

    # 版本資訊（可選）
    with open(VER_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "count": len(out_list)
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ build done: {len(out_list)} items")

if __name__ == "__main__":
    main()
