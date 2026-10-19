import os
import json
import requests
from datetime import datetime, timedelta

# কনফিগারেশন
API_KEY = os.getenv("AIzaSyCQf9y6FyB1lrxFGNU8cdwBhyuww5bzkiI")
DATA_FILE = "videos.json"

# আপনি যে যে বিষয়ের ভিডিও চান
SEARCH_KEYWORDS = [
    "Bangla Natok 2026", 
    "New Movie", 
    "New Music Video", 
    "Bangla Waz New", 
    "Bangla Gojol", 
    "Bangla Telefilm"
]
MAX_RESULTS_PER_KEYWORD = 10 

def fetch_youtube_videos_by_keyword(keyword):
    # ইউআরএলটি একদম পরিষ্কার করে রি-ফরম্যাট করা হলো যাতে কোনো ক্যারেক্টার জটলা না পাকায়
    url = "https://googleapis.com"
    params = {
        "key": API_KEY,
        "q": keyword,
        "part": "snippet,id",
        "order": "date",
        "maxResults": MAX_RESULTS_PER_KEYWORD,
        "type": "video",
        "videoEmbeddable": "true"
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching data for keyword: {keyword}. Status Code: {response.status_code}")
        return []
    
    data = response.json()
    videos = []
    for item in data.get("items", []):
        video_id = item["id"].get("videoId")
        if not video_id:
            continue
        title = item["snippet"]["title"]
        description = item["snippet"]["description"]
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        published_at = item["snippet"]["publishedAt"]
        
        videos.append({
            "id": video_id,
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "publishedAt": published_at,
            "category": keyword 
        })
    return videos

def main():
    all_new_videos = []
    
    for kw in SEARCH_KEYWORDS:
        print(f"Searching for: {kw}")
        videos = fetch_youtube_videos_by_keyword(kw)
        all_new_videos.extend(videos)
        
    if not all_new_videos:
        print("No videos fetched. Please check if your YOUTUBE_API_KEY is correct in Repository Secrets.")
        return

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                existing_videos = json.load(f)
            except json.JSONDecodeError:
                existing_videos = []
    else:
        existing_videos = []

    video_dict = {v["id"]: v for v in existing_videos}
    for nv in all_new_videos:
        video_dict[nv["id"]] = nv

    fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
    filtered_videos = []
    
    for v_id, video in video_dict.items():
        pub_time = datetime.strptime(video["publishedAt"][:19], "%Y-%m-%dT%H:%M:%S")
        if pub_time > fifteen_days_ago:
            filtered_videos.append(video)

    filtered_videos.sort(key=lambda x: x["publishedAt"], reverse=True)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_videos, f, ensure_ascii=False, indent=4)
    print(f"Successfully updated! Total videos in cache: {len(filtered_videos)}")

if __name__ == "__main__":
    main()
