import yt_dlp
from typing import List, Dict
import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_video_id_from_url(url: str) -> str:
    """Extract video ID from YouTube URL."""
    if 'youtu.be' in url:
        return url.split('/')[-1]
    if 'youtube.com' in url:
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
    return url

def get_videos_metadata_api(urls: List[str]) -> List[Dict]:
    """
    Retrieve metadata using YouTube Data API.
    """
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YouTube API key not found in environment variables")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    results = []
    
    for url in urls:
        try:
            video_id = get_video_id_from_url(url)
            request = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                video = response['items'][0]
                results.append({
                    'url': url,
                    'title': video['snippet']['title'],
                    'duration': video['contentDetails']['duration'],
                    'view_count': int(video['statistics'].get('viewCount', 0)),
                    'thumbnail': video['snippet']['thumbnails']['high']['url'],
                    'channel': video['snippet']['channelTitle'],
                    'description': video['snippet']['description'],
                })
            else:
                results.append({
                    'url': url,
                    'error': 'Video not found'
                })
        except Exception as e:
            print(f"Error getting metadata for {url}: {str(e)}")
            results.append({
                'url': url,
                'error': str(e)
            })
    
    return results

def get_videos_metadata(urls: List[str]) -> List[Dict]:
    """
    Retrieve metadata for a list of YouTube videos.
    First tries using yt-dlp with cookies file, falls back to YouTube Data API.
    """
    cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', 'cookies/cookies.txt')
    
    # If cookies file exists, try using yt-dlp first
    if os.path.exists(cookies_file):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'cookiefile': cookies_file,
            }
            
            results = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    try:
                        info = ydl.extract_info(url, download=False)
                        results.append({
                            'url': url,
                            'title': info.get('title'),
                            'duration': info.get('duration'),
                            'view_count': info.get('view_count'),
                            'thumbnail': info.get('thumbnail'),
                            'channel': info.get('channel'),
                            'description': info.get('description'),
                        })
                    except Exception as e:
                        print(f"Error getting metadata with yt-dlp for {url}: {str(e)}")
                        results.append({
                            'url': url,
                            'error': str(e)
                        })
            return results
        except Exception as e:
            print(f"Error using yt-dlp with cookies: {str(e)}")
            # Fall back to YouTube Data API
            pass
    
    # Fall back to YouTube Data API
    return get_videos_metadata_api(urls) 