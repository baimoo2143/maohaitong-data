import requests
import csv
import io
import json
from datetime import datetime

# ✅ 來源清單（先整理幾個有完整 API 的縣市）
sources = [
    {
        "city": "新北市",
        "url": "https://data.ntpc.gov.tw/api/datasets/de4cfd62-e977-4c4f-822f-7d2aa65f6e4a/json",
        "format": "json"
    },
    {
        "city": "台中市",
        "url": "https://opendata.taichung.gov.tw/api/v1/dataset/8e1bdc1c-a41a-4645-9bcb-0ec40c6ccf89?format=json",
        "format": "json"
    },
    {
        "city": "台中市",
        "url": "https://opendata.taichung.gov.tw/api/v1/dataset/cfe37e8e-18c5-4cbf-bc38-47595038fa57?format=json",
        "format": "json",  # 夜間急診 / 24H
        "is24h": True
    },
    {
        "city": "台南市",
        "url": "https://data.tainan.gov.tw/api/3/action/datastore_search?resource_id=8f329f1e-f2c9-46f2-87df-37a9f0f9e05a",
        "format": "json"
    },
    {
        "city": "南投縣",
        "url": "https://data.nantou.gov.tw/od/data/api/CC2A9C1A-BC84-43D4-A8A2-6C1F5073BD08?$format=csv",
        "format": "csv"
    },
    # 後續可以再加其他縣市
]

def normalize_city(name: str) -> str:
    """把 臺 → 台，保持一致"""
    return name.replace("臺", "台")

def fetch_source(src):
    print(f"📥 抓取 {src['city']} 資料中…")
    resp = requests.get(src["url"])
    resp.raise_for_status()

    data = []
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
    return data

def load_manual():
    try:
        with open("data/places_manual.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def main():
    all_places = []

    # 抓取各來源
    for src in sources:
        try:
            data = fetch_source(src)
            all_places.extend(data)
            print(f"✅ {src['city']} 抓到 {len(data)} 筆")
        except Exception as e:
            print(f"⚠️ {src['city']} 抓取失敗: {e}")

    # 存成 places_auto.json
    with open("data/places_auto.json", "w", encoding="utf-8") as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)

    # 合併手動資料
    manual = load_manual()
    final = all_places + manual

    # 加上 ID
    for idx, item in enumerate(final, start=1):
        item["id"] = f"{normalize_city(item['city'])}_{idx:04d}"

    # 輸出 places.json
    with open("places.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    # 更新版本號
    version = {"last_updated": datetime.utcnow().isoformat()}
    with open("version.json", "w", encoding="utf-8") as f:
        json.dump(version, f, ensure_ascii=False, indent=2)

    print(f"🎉 完成！共 {len(final)} 筆資料")

if __name__ == "__main__":
    main()
