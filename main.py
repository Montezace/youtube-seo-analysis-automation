import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import openai

# --- CONFIGURATION ---
# It is better to set these in your environment, but you can paste them here for testing
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "PASTE_YOUR_KEY_HERE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "PASTE_YOUR_KEY_HERE")

# Initialize Services
yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
openai.api_key = OPENAI_API_KEY

def get_channel_id(url_or_handle):
    """Gets Channel ID using handle or search fallback."""
    handle = url_or_handle.split("@")[-1].split("/")[0].split("?")[0]
    request = yt_service.channels().list(part="id", forHandle=f"@{handle}")
    response = request.execute()
    
    if not response.get('items'):
        request = yt_service.search().list(q=url_or_handle, type='channel', part='id')
        response = request.execute()
        return response['items'][0]['id']['channelId']
    return response['items'][0]['id']

def fetch_top_videos(channel_url, limit=10):
    """Compiles top videos and summaries into a text file."""
    try:
        channel_id = get_channel_id(channel_url)
        request = yt_service.search().list(
            channelId=channel_id,
            part='snippet,id',
            order='viewCount',
            maxResults=limit,
            type='video'
        )
        response = request.execute()
        
        report = f"TOP {limit} VIDEOS FOR {channel_url}\n" + "="*40 + "\n\n"
        for item in response['items']:
            title = item['snippet']['title']
            v_id = item['id']['videoId']
            desc = item['snippet']['description']
            report += f"TITLE: {title}\nURL: https://youtu.be/{v_id}\nSUMMARY: {desc[:200]}...\n\n"
        
        with open("top_videos_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        print("\n[SUCCESS] Report saved to top_videos_report.txt")
    except Exception as e:
        print(f"[ERROR] {e}")

def analyze_video_seo(video_url):
    """Fetches transcript and uses OpenAI to analyze SEO strategy."""
    try:
        video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
        
        # Get Transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([t['text'] for t in transcript_list])
        
        print("Analyzing SEO with AI...")
        prompt = f"Analyze the following YouTube transcript for SEO strategies, keywords used, and content structure. Provide suggestions for optimization:\n\n{full_text[:4000]}"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = response.choices[0].message.content
        with open("seo_analysis.txt", "w", encoding="utf-8") as f:
            f.write(analysis)
        print("\n[SUCCESS] SEO Analysis saved to seo_analysis.txt")
    except Exception as e:
        print(f"[ERROR] Could not analyze video: {e}")

if __name__ == "__main__":
    print("--- YouTube Automation & SEO Tool ---")
    mode = input("Choose: (1) Channel Top Videos (2) Single Video SEO Analysis: ")

    if mode == "1":
        url = input("Paste Channel Link: ")
        count = int(input("How many videos? (10/20/30): "))
        fetch_top_videos(url, count)
    elif mode == "2":
        url = input("Paste Video Link: ")
        analyze_video_seo(url)
