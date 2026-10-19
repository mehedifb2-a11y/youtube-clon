import os
import json
import requests
from datetime import datetime, timedelta

# কনফিগারেশন
API_KEY = os.getenv("YOUTUBE_API_KEY")
DATA_FILE = "videos.json"

# আপনি যে যে বিষয়ের ভিডিও আপনার ওয়েবসাইটে চান, সেই কিওয়ার্ডগুলো এখানে লিখুন
SEARCH_KEYWORDS = [
    "Bangla Natok", 
    "New Movie", 
    "Movie",
    "Music Video", 
    "Bangla Waz", 
    "Bangla Gojol", 
    "Bangla Telefilm"
]
MAX_RESULTS_PER_KEYWORD = 10 # প্রতি ৩০ মিনিটে প্রতি ক্যাটাগরি থেকে কয়টি করে ভিডিও আনবে

def fetch_youtube_videos_by_keyword(keyword):
    url = f"https://googleapis.com{API_KEY}&q={keyword}&part=snippet,id&order=date&maxResults={MAX_RESULTS_PER_KEYWORD}&type=video&videoEmbeddable=true"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching data for keyword: {keyword}")
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
            "category": keyword # কোন ক্যাটাগরির ভিডিও তা ট্র্যাক রাখার জন্য
        })
    return videos

def main():
    all_new_videos = []
    
    # সব কিওয়ার্ড দিয়ে একে একে ইউটিউবে সার্চ করা
    for kw in SEARCH_KEYWORDS:
        print(f"Searching for: {kw}")
        videos = fetch_youtube_videos_by_keyword(kw)
        all_new_videos.extend(videos)
    if not all_new_videos:
        print("No videos fetched at all. Exiting.")
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

    # নতুন ও পুরাতন ভিডিও একসাথে করা (ডুপ্লিকেট বাদ দিয়ে)
    video_dict = {v["id"]: v for v in existing_videos}
    for nv in all_new_videos:
        video_dict[nv["id"]] = nv

    # আপনার চমৎকার আইডিয়া: ১৫ দিনের ফিল্টার বা অটো-ডিলিট লজিক
    fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
    filtered_videos = []
    
    for v_id, video in video_dict.items():
        pub_time = datetime.strptime(video["publishedAt"][:19], "%Y-%m-%dT%H:%M:%S")
        if pub_time > fifteen_days_ago:
            filtered_videos.append(video)

    # তারিখ অনুযায়ী সাজানো (সবচেয়ে নতুন ভিডিও সবার আগে থাকবে)
    filtered_videos.sort(key=lambda x: x["publishedAt"], reverse=True)

    # ফাইনাল ডাটা ফাইলে সেভ করা
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_videos, f, ensure_ascii=False, indent=4)
    print(f"Successfully updated. Total videos in cache: {len(filtered_videos)}")

if __name__ == "__main__":
    main()
