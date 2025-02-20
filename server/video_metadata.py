import yt_dlp
from typing import List, Dict

def get_videos_metadata(urls: List[str]) -> List[Dict]:
    """
    Retrieve metadata for a list of YouTube videos.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
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
                print(f"Error getting metadata for {url}: {str(e)}")
                results.append({
                    'url': url,
                    'error': str(e)
                })
    
    return results 