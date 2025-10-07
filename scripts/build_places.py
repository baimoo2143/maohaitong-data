import os, io, csv, json, requests, traceback
from datetime import datetime

# 資料來源清單（目前先示範幾個，實際你可以補全 22 縣市）
sources = [
    {
        "city": "台北市",
        "url": "https://data.taipei/api/getDatasetInfo/downloadResource?id=xxxx&rid=xxxx"
    },
    {
        "city": "新北市",
        "url": "https://data.ntpc.gov.tw/api/datasets/xxxx/csv/file"
    },
    # 👉 其他縣市照樣補
]

def fetch_source(source):
    url = source["url"]
    city = source["city"]
    print(f"\n🔗 {city} → {url}")

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()

        # 印前 300 字 raw data
        print(f"📥 {city} 回傳前 300 字： {resp.text[:300]}")

        # 嘗試轉 JSON
        records = []
        try:
            data = resp.json()
            if isinstance(data, list):
                records = data
            elif "data" in data and isinstance(data["data"], list):
                records = data["data"]
            elif "result" in data and "records" in data["result"]:
                records = data["result"]["records"]
        except Exception:
            # 可能是 CSV
            try:
                csvfile = io.StringIO(resp.text)
                reader = csv.DictReader(csvfile)
                records = list(reader)
            except Exception as e:
                print(f"⚠️ {city} 無法解析成 JSON 或 CSV: {e}")

        print(f"✅ {city} 解析出 {len(records)} 筆")
        return [
            {
                "name": r.get("機構名稱") or r.get("醫院名稱") or r.get("name"),
                "address": r.get("地址") or r.get("address"),
                "phone": r.get("電話") or r.get("phone"),
                "city": city,
                "is24h": "24" in (r.get("服務時間") or "").lower()
            }
            for r in records
        ]

    except Exception as e:
        print(f"❌ {city} 抓取失敗: {e}")
        traceback.print_exc()
        return []

def load_manual():
    path = "manual/extra.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

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

    # 加上手動補充
    manual = load_manual()
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
