import os
import json
import requests
from datetime import datetime

# কনফিগারেশন
API_KEY = os.getenv("AIzaSyA0XpD13WvB9hr6OPwlrWsiurMAC8Z9sBU")
DATA_FILE = "videos.json"

# সহজে পাওয়ার জন্য সিম্পল কিওয়ার্ড দেওয়া হলো
SEARCH_KEYWORDS = [
    "Bangla Natok", 
    "Song", 
    "Bangla Waz"
]
MAX_RESULTS_PER_KEYWORD = 10 

def fetch_youtube_videos_by_keyword(keyword):
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
    print(f"Keyword: {keyword} -> Status Code: {response.status_code}")
    
    # গুগলের সার্ভার কোনো এরর দিলে তা এখানে প্রিন্ট হবে
    if response.status_code != 200:
        print(f"Google API Error Response: {response.text}")
        return []
    
    data = response.json()
    items = data.get("items", [])
    print(f"Found {len(items)} videos for keyword: {keyword}")
    
    videos = []
    for item in items:
        video_id = item["id"].get("videoId")
        if not video_id:
            continue
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        published_at = item["snippet"]["publishedAt"]
        
        videos.append({
            "id": video_id,
            "title": title,
            "description": item["snippet"]["description"],
            "thumbnail": thumbnail,
            "publishedAt": published_at,
            "category": keyword 
        })
    return videos

def main():
    if not API_KEY:
        print("CRITICAL ERROR: YOUTUBE_API_KEY is missing or empty in Repository Secrets!")
        return
        
    all_new_videos = []
    for kw in SEARCH_KEYWORDS:
        videos = fetch_youtube_videos_by_keyword(kw)
        all_new_videos.extend(videos)
        
    if not all_new_videos:
        print("No videos fetched at all.")
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

    filtered_videos = list(video_dict.values())
    filtered_videos.sort(key=lambda x: x["publishedAt"], reverse=True)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_videos, f, ensure_ascii=False, indent=4)
    print(f"Successfully updated! Cache size: {len(filtered_videos)}")

if __name__ == "__main__":
    main()
