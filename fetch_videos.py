import os
import json
import requests
from datetime import datetime

# কনফিগারেশন
API_KEY = os.getenv("AIzaSyA0XpD13WvB9hr6OPwlrWsiurMAC8Z9sBU")
DATA_FILE = "videos.json"

# আপনি যে যে বিষয়ের ভিডিও চান (এখানে আপনার পছন্দমতো কীওয়ার্ড যোগ করতে পারেন)
SEARCH_KEYWORDS = [
    "Bangla Natok 2026", 
    "New Movie", 
    "Music Video", 
    "Bangla Waz New", 
    "Bangla Gojol", 
    "Bangla Telefilm"
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

    # আগের জমানো (Cache) ডাটা লোড করা
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                existing_videos = json.load(f)
            except json.JSONDecodeError:
                existing_videos = []
    else:
        existing_videos = []

    # নতুন ও পুরাতন ভিডিও একসাথে করা (ডুপ্লিকেট ভিডিও বাদ দিয়ে)
    video_dict = {v["id"]: v for v in existing_videos}
    for nv in all_new_videos:
        video_dict[nv["id"]] = nv

    # কোনো ফিল্টার ছাড়া সব ভিডিও সরাসরি ক্যাশে রাখা হচ্ছে (আপনার ফ্রি স্টোরেজ ফুল হবে না)
    filtered_videos = list(video_dict.values())

    # তারিখ অনুযায়ী সাজানো (সবচেয়ে নতুন ভিডিও সবার আগে থাকবে)
    filtered_videos.sort(key=lambda x: x["publishedAt"], reverse=True)

    # ফাইনাল ডাটা ফাইলে সেভ করা
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_videos, f, ensure_ascii=False, indent=4)
    print(f"Successfully updated! Total videos in cache: {len(filtered_videos)}")

if __name__ == "__main__":
    main()
