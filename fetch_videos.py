import os
import json
import requests
from datetime import datetime, timedelta

# কনফিগারেশন
API_KEY = os.getenv("YOUTUBE_API_KEY")
# এখানে আপনার ইউটিউব চ্যানেলের ID বসাবেন (অথবা প্লেলিস্ট ID)
CHANNEL_ID = "UCxxxxxxxxxxxxxxxxxxxxxx" 
MAX_RESULTS = 50
DATA_FILE = "videos.json"

def fetch_youtube_videos():
    url = f"https://googleapis.com{API_KEY}&channelId={CHANNEL_ID}&part=snippet,id&order=date&maxResults={MAX_RESULTS}&type=video"
    response = requests.get(url)
    if response.status_code != 200:
        print("Error fetching data from YouTube API")
        return []
    
    data = response.json()
    videos = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        description = item["snippet"]["description"]
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        published_at = item["snippet"]["publishedAt"]
        
        videos.append({
            "id": video_id,
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "publishedAt": published_at
        })
    return videos

def main():
    # নতুন ভিডিও নিয়ে আসা
    new_videos = fetch_youtube_videos()
    if not new_videos:
        print("No new videos fetched. Exiting.")
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
    for nv in new_videos:
        video_dict[nv["id"]] = nv

    # ১৫ দিনের ফিল্টার বা অটো-ডিলিট লজিক
    fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
    filtered_videos = []
    
    for v_id, video in video_dict.items():
        # ইউটিউবের টাইমস্ট্যাম্প ফরম্যাট: 2026-10-19T12:00:00Z
        pub_time = datetime.strptime(video["publishedAt"][:19], "%Y-%m-%dT%H:%M:%S")
        if pub_time > fifteen_days_ago:
            filtered_videos.append(video)

    # তারিখ অনুযায়ী সাজানো (সবচেয়ে নতুন ভিডিও সবার আগে)
    filtered_videos.sort(key=lambda x: x["publishedAt"], reverse=True)

    # ফাইনাল ডাটা ফাইলে সেভ করা
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_videos, f, ensure_ascii=False, indent=4)
    print(f"Successfully updated. Total videos in cache: {len(filtered_videos)}")

if __name__ == "__main__":
    main()
