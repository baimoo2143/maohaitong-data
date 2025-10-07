import os, io, csv, json, requests, traceback
from datetime import datetime

# 📌 API 來源清單（目前已含 9 個縣市，之後可擴充）
sources = [
    {
        "city": "新北市",
        "url": "https://data.ntpc.gov.tw/api/datasets/71E5B4E2-28F1-4B61-8B7F-19DF64A50A6D/json",
        "format": "json"
    },
    {
        "city": "台北市",
        "url": "https://data.taipei/api/v1/dataset/6c1ffab3-5957-4f2a-9c47-6c5c4c862a9a?scope=resourceAquire",
        "format": "json"
    },
    {
        "city": "台中市",
        "url": "https://datacenter.taichung.gov.tw/swagger/OpenData/5e0579f5-08d0-4b77-9f6b-eca65aeb0541",
        "format": "json"
    },
    {
        "city": "台中市",
        "url": "https://opendata.taichung.gov.tw/api/v1/dataset/cfe37e8e-18c5-4cbf-bc38-47595038fa57?format=json",
        "format": "json",
        "is24h": True
    },
    {
        "city": "台南市",
        "url": "https://data.tainan.gov.tw/dataset/0c61b89d-46e4-43e1-8893-9478c30eeb3b/resource/61bb64f1-7d78-4c54-9275-3d76d7e45e3b/download/animal_hospital.json",
        "format": "json"
    },
    {
        "city": "高雄市",
        "url": "https://api.kcg.gov.tw/api/service/Get/6a2e5103-d634-4a5c-8a9f-d2c3b4bc6fdf",
        "format": "json"
    },
    {
        "city": "南投縣",
        "url": "https://data.nantou.gov.tw/od/data/api/CC2A9C1A-BC84-43D4-A8A2-6C1F5073BD08?$format=csv",
        "format": "csv"
    },
    {
        "city": "花蓮縣",
        "url": "https://od.hl.gov.tw/dataset/50c72fb5-8ee7-4c69-a38a-9cb6785f2d60/resource/7f8b7d46-6d4c-45b5-8f68-3a88d3bc8c1c/download/animal_hospital.json",
        "format": "json"
    },
    {
        "city": "屏東縣",
        "url": "https://data.pthg.gov.tw/api/3/action/datastore_search?resource_id=45f6f746-9cc6-4d13-b5d0-d0dc8b2c0d7a",
        "format": "json"
    }
]

# 📌 縣市名稱正規化
def normalize_city(name: str) -> str:
    return name.replace("臺", "台").strip() if name else ""

# 📌 抓取單一來源
def fetch_source(src):
    city = src["city"]
    url = src["url"]
    fmt = src.get("format", "json")
    print(f"\n🔗 {city} → {url}")

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()

        # 印前 300 字 raw data
        print(f"📥 {city} 回傳前 300 字：{resp.text[:300]}")

        records = []
        if fmt == "json":
            raw = resp.json()
            if isinstance(raw, list):
                records = raw
            elif "result" in raw and "records" in raw["result"]:
                records = raw["result"]["records"]
            elif "result" in raw and "results" in raw["result"]:
                records = raw["result"]["results"]
            elif "records" in raw:
                records = raw["records"]
        elif fmt == "csv":
            f = io.StringIO(resp.text)
            reader = csv.DictReader(f)
            records = list(reader)

        print(f"🔍 {city} API 回傳 {len(records)} 筆原始資料")

        data = []
        for item in records:
            data.append({
                "id": "",
                "name": item.get("機構名稱") or item.get("名稱") or item.get("醫院名稱") or item.get("name", ""),
                "city": normalize_city(item.get("縣市") or city),
                "address": item.get("地址") or item.get("所在地") or item.get("addr") or item.get("address", ""),
                "phone": item.get("電話") or item.get("聯絡電話") or item.get("tel") or item.get("phone", ""),
                "lat": item.get("緯度") or item.get("lat"),
                "lng": item.get("經度") or item.get("lng"),
                "category": "醫院",
                "is24h": src.get("is24h", False) or ("24" in str(item))
            })

        print(f"✅ {city} 成功轉換 {len(data)} 筆")
        return data

    except Exception as e:
        print(f"❌ {city} 抓取失敗: {e}")
        traceback.print_exc()
        return []

# 📌 載入手動補充資料
def load_manual():
    path = "manual/extra.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 手動補充讀取失敗: {e}")
    return []

# 📌 主程式
def main():
    all_places = []
    city_counts = {}
    empty_cities = []

    for src in sources:
        data = fetch_source(src)
        all_places.extend(data)
        city_counts[src["city"]] = len(data)
        if len(data) == 0:
            empty_cities.append(src["city"])

    manual = load_manual()
    if manual:
        print(f"➕ 加入手動補充 {len(manual)} 筆")
        all_places.extend(manual)

    # 加上唯一 id
    for idx, p in enumerate(all_places, 1):
        p["id"] = f"place_{idx}"

    # 輸出
    os.makedirs("data", exist_ok=True)
    with open("data/places_auto.json", "w", encoding="utf-8") as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)
    with open("places.json", "w", encoding="utf-8") as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)

    version = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(all_places),
        "city_counts": city_counts,
        "empty_cities": empty_cities,
    }
    with open("version.json", "w", encoding="utf-8") as f:
        json.dump(version, f, ensure_ascii=False, indent=2)

    # Log summary
    print("\n📊 各縣市筆數：")
    for city, count in city_counts.items():
        if count == 0:
            print(f"⚠️ {city}: {count} 筆（可能 API 無資料）")
        else:
            print(f"   {city}: {count} 筆")

    if empty_cities:
        print(f"\n⚠️ 無資料的縣市：{', '.join(empty_cities)}")
        print(f"⚠️ 共 {len(empty_cities)} 個縣市無資料")
    else:
        print("\n✅ 所有縣市都有資料")

    print(f"\n🎉 完成！共 {len(all_places)} 筆")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 主程式錯誤: {e}")
        traceback.print_exc()
