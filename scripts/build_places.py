import os, io, csv, json, requests, traceback
from datetime import datetime

# 📌 全台 22 縣市 API 清單（我已查到能用的 dataset，少數若有變動要再更新）
sources = [
    # 六都
    { "city": "台北市", "url": "https://data.taipei/api/v1/dataset/6c1ffab3-5957-4f2a-9c47-6c5c4c862a9a?scope=resourceAquire", "format": "json" },
    { "city": "新北市", "url": "https://data.ntpc.gov.tw/api/datasets/71E5B4E2-28F1-4B61-8B7F-19DF64A50A6D/json", "format": "json" },
    { "city": "桃園市", "url": "https://data.tycg.gov.tw/opendata/datalist/datasetMeta/download?id=2bcf24d6-fec1-4a3e-8ed1-c6cb921bd3a2&rid=8f3a5c33-6c2d-4a72-872d-ec5d4c77985d", "format": "json" },
    { "city": "台中市", "url": "https://datacenter.taichung.gov.tw/swagger/OpenData/5e0579f5-08d0-4b77-9f6b-eca65aeb0541", "format": "json" },
    { "city": "台南市", "url": "https://data.tainan.gov.tw/dataset/0c61b89d-46e4-43e1-8893-9478c30eeb3b/resource/61bb64f1-7d78-4c54-9275-3d76d7e45e3b/download/animal_hospital.json", "format": "json" },
    { "city": "高雄市", "url": "https://api.kcg.gov.tw/api/service/Get/6a2e5103-d634-4a5c-8a9f-d2c3b4bc6fdf", "format": "json" },

    # 直轄市 / 市
    { "city": "基隆市", "url": "https://data.klcg.gov.tw/api/3/action/datastore_search?resource_id=4f2c3dcf-3ed4-4cf8-91ff-1f3aa7e8f6d3", "format": "json" },
    { "city": "新竹市", "url": "https://opendata.hccg.gov.tw/api/3/action/datastore_search?resource_id=4dce8394-5809-49d7-a9c3-523fe5e82c48", "format": "json" },
    { "city": "嘉義市", "url": "https://data.chiayi.gov.tw/dataset/60739c0f-66db-49d7-b726-7cebf7850f22/resource/12a622a7-55a5-474a-b11b-8a64042fbaa2/download/animalhospital.json", "format": "json" },

    # 縣
    { "city": "新竹縣", "url": "https://opendata.hsinchu.gov.tw/api/3/action/datastore_search?resource_id=bd6c69a2-0f3c-40dd-b37a-9f0df2d7c05f", "format": "json" },
    { "city": "苗栗縣", "url": "https://opendata.miaoli.gov.tw/api/3/action/datastore_search?resource_id=4e7aa3c0-33d4-4db7-92f3-807401e33adf", "format": "json" },
    { "city": "彰化縣", "url": "https://opendata.chcg.gov.tw/api/3/action/datastore_search?resource_id=5a3db25f-1de0-41a0-9354-987e23af37f3", "format": "json" },
    { "city": "南投縣", "url": "https://data.nantou.gov.tw/od/data/api/CC2A9C1A-BC84-43D4-A8A2-6C1F5073BD08?$format=csv", "format": "csv" },
    { "city": "雲林縣", "url": "https://data.yunlin.gov.tw/dataset/14b6b653-dcfd-43d7-a3fd-7b54a93b24bd/resource/aa5c6d39-3f5a-4a35-99d5-f6d8a0f6eb3e/download/animalhospital.json", "format": "json" },
    { "city": "嘉義縣", "url": "https://data.cyhg.gov.tw/dataset/5c52e70d-2ff2-4e9a-b871-fbe75e5d0c09/resource/92f4858d-25e0-4999-bc7f-1b1f25df88f5/download/animalhospital.json", "format": "json" },
    { "city": "屏東縣", "url": "https://data.pthg.gov.tw/api/3/action/datastore_search?resource_id=45f6f746-9cc6-4d13-b5d0-d0dc8b2c0d7a", "format": "json" },
    { "city": "宜蘭縣", "url": "https://opendata.e-land.gov.tw/api/3/action/datastore_search?resource_id=3c3a9c91-aaa6-4c4f-8a65-089c2e03d0d2", "format": "json" },
    { "city": "花蓮縣", "url": "https://od.hl.gov.tw/dataset/50c72fb5-8ee7-4c69-a38a-9cb6785f2d60/resource/7f8b7d46-6d4c-45b5-8f68-3a88d3bc8c1c/download/animal_hospital.json", "format": "json" },
    { "city": "台東縣", "url": "https://opendata.taitung.gov.tw/dataset/9c6d0876-3c7e-4e6c-a802-1f63d9a3c0b7/resource/07c2f2d6-f7a4-4a6f-8c8f-6e85d2bb5c39/download/animalhospital.json", "format": "json" },
    { "city": "澎湖縣", "url": "https://data.phc.edu.tw/dataset/02a07dd0-7819-4c4e-b2c9-97fbb0a63df4/resource/22211889-285e-43e5-8e93-4785905a9b7d/download/animalhospital.json", "format": "json" },
    { "city": "金門縣", "url": "https://opendata.kinmen.gov.tw/dataset/55f0f171-2ab9-40d3-b62e-95d2d76f6f22/resource/2d9c6268-6e7a-4db1-9ee6-6f3a58f9fca9/download/animalhospital.json", "format": "json" },
    { "city": "連江縣", "url": "https://opendata.matsu.gov.tw/dataset/30a60ad8-1a71-4a77-bc02-9bca8d52d4d1/resource/2f3d69b7-2fa5-40d7-8444-8cb0e8f6a109/download/animalhospital.json", "format": "json" }
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
        print(f"📥 {city} 回傳前 300 字：{resp.text[:300]}")

        records = []
        if fmt == "json":
            raw = resp.json()
            if isinstance(raw, list):
                records = raw
            elif "result" in raw and "records" in raw["result"]:
                records = raw["result"]["records"]
            elif "records" in raw:
                records = raw["records"]
        elif fmt == "csv":
            f = io.StringIO(resp.text)
            reader = csv.DictReader(f)
            records = list(reader)

        print(f"🔍 {city} API 回傳 {len(records)} 筆")

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
                "is24h": "24" in str(item)
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
