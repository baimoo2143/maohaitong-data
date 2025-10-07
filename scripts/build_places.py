import requests
import csv
import io
import json
import os
from datetime import datetime

# ✅ API 來源清單（目前先放幾個示範，後續可以再加）
sources = [
    {
        "city": "新北市",
        "url": "https://data.ntpc.gov.tw/api/datasets/71E5B4E2-28F1-4B61-8B7F-19DF64A50A6D/json",
        "format": "json"
    },
    {
        "city": "台中市",
        "url": "https://datacenter.taichung.gov.tw/swagger/OpenData/5e0579f5-08d0-4b77-9f6b-eca65aeb0541",
        "format": "json"
    },
    {
        "city": "台南市",
        "url": "https://data.tainan.gov.tw/dataset/0c61b89d-46e4-43e1-8893-9478c30eeb3b/resource/61bb64f1-7d78-4c54-9275-3d76d7e45e3b/download/animal_hospital.json",
        "format": "json"
    },
    {
        "city": "南投縣",
        "url": "https://data.nantou.gov.tw/od/data/api/CC2A9C1A-BC84-43D4-A8A2-6C1F5073BD08?$format=csv",
        "format": "csv"
    },
    # 後續可繼續加台北市、高雄市、基隆市等…
]

# ✅ 縣市正規化（臺 → 台）
def normalize_city(name: str) -> str:
    if not name:
        return ""
    return name.replace("臺", "台").strip()

# ✅ 抓取單一來源
def fetch_source(src):
    print(f"📥 抓取 {src['city']} 資料中…")
    try:
        resp = requests.get(src["url"], timeout=20)
        if resp.status_code != 200:
            print(f"⚠️ {src['city']} 回應 {resp.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ {src['city']} 下載失敗: {e}")
        return []

    data = []
    try:
        if src["format"] == "json":
            raw = resp.json()
            # 嘗試不同 JSON 結構
            if isinstance(raw, list):
                records = raw
            elif "result" in raw and "records" in raw["result"]:
                records = raw["result"]["records"]
            else:
                records = raw.get("records", raw)

            for item in records:
                data.append({
                    "id": "",
                    "name": item.get("名稱") or item.get("醫院名稱") or item.get("name", ""),
                    "city": normalize_city(item.get("縣市", src["city"])),
                    "address": item.get("地址") or item.get("所在地") or "",
                    "phone": item.get("電話") or item.get("聯絡電話") or "",
                    "lat": float(item.get("緯度", 0) or 0),
                    "lng": float(item.get("經度", 0) or 0),
                    "category": "醫院",
                    "is24h": src.get("is24h", False) or ("24" in str(item.get("服務時間", "")))
                })

        elif src["format"] == "csv":
            f = io.StringIO(resp.text)
            reader = csv.DictReader(f)
            for item in reader:
                data.append({
                    "id": "",
                    "name": item.get("名稱") or item.get("醫院名稱") or "",
                    "city": normalize_city(item.get("縣市", src["city"])),
                    "address": item.get("地址") or "",
                    "phone": item.get("電話") or "",
                    "lat": float(item.get("緯度", 0) or 0),
                    "lng": float(item.get("經度", 0) or 0),
                    "category": "醫院",
                    "is24h": src.get("is24h", False) or ("24" in str(item))
                })

    except Exception as e:
        print(f"⚠️ {src['city']} 解析失敗: {e}")

    return data

# ✅ 載入手動補充檔案
def load_manual():
    manual_file = "data/places_manual.json"
    if os.path.exists(manual_file):
        try:
            with open(manual_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 手動資料讀取失敗: {e}")
            return []
    return []

# ✅ 主程式
def main():
    all_places = []

    # 抓取各來源
    for src in sources:
        try:
            data = fetch_source(src)
            all_places.extend(data)
            print(f"✅ {src['city']} 抓到 {len(data)} 筆")
        except Exception as e:
            print(f"❌ {src['city']} 抓取爆炸: {e}")

    # 加上手動補充
    manual = load_manual()
    if manual:
        print(f"➕ 加入手動補充 {len(manual)} 筆")
        all_places.extend(manual)

    # 加上 ID
    for i, item in enumerate(all_places, start=1):
        item["id"] = str(i)

    # 存成 places_auto.json
    os.makedirs("data", exist_ok=True)
    with open("data/places_auto.json", "w", encoding="utf-8") as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)

    # 存成 places.json（App 用）
    with open("places.json", "w", encoding="utf-8") as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)

    # 存版本號
    with open("version.json", "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.utcnow().isoformat()}, f)

    print(f"🎉 完成！共 {len(all_places)} 筆")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("❌ 腳本失敗:", e)
        traceback.print_exc()
