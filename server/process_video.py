import os
from dotenv import load_dotenv
import uuid
import tempfile
import yt_dlp
from create_video import create_video
from snippets import generate_snippets
import json
from fireworks.client.audio import AudioInference
import asyncio

# Load environment variables
load_dotenv()

def download(url, output_path):
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'nocheckcertificate': True,
        'no_cache_dir': True,
        'no_mtime': True,
        'noprogress': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("downloading video")
            info = ydl.extract_info(url, download=True)
            return {
                "message": "Video downloaded successfully",
                "title": info['title'],
            }
    except Exception as e:
        print(f"YouTube DL Error: {str(e)}")
        return {"message": f"Error downloading video: {str(e)}"}

async def transcribe(video_path):
    client = AudioInference(
        model="whisper-v3-turbo",
        base_url="https://audio-turbo.us-virginia-1.direct.fireworks.ai",
    )

    print("transcribing audio")
    result = await client.transcribe_async(
        audio=video_path,
        language="en",
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )
    return result.model_dump()

async def process_video_url(url, face_tracking=False, bottom_video_url=None):
    # Create output directory if it doesn't exist
    os.makedirs("video_inputs", exist_ok=True)
    os.makedirs("video_outputs", exist_ok=True)
    
    # Generate a random video ID
    video_id = str(uuid.uuid4())
    input_path = f"video_inputs/{video_id}"
    
    # Download the video
    print("Downloading video...")
    download_result = download(url, input_path)
    
    # Transcribe the video
    print("Transcribing video...")
    transcript = await transcribe(input_path)
    
    # Generate snippets
    print("Generating snippets...")
    snippets_result = generate_snippets({
        "transcript": transcript["text"]
    })
    
    # Download bottom video if provided
    bottom_video_path = None
    if bottom_video_url:
        bottom_video_path = f"video_inputs/bottom_{video_id}"
        download(bottom_video_url, bottom_video_path)
    
    # Create clips for each snippet
    output_clips = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, snippet in enumerate(snippets_result["clips"]):
            print(f"\nProcessing clip {i+1}...")
            output_path = f"video_outputs/clip_{video_id}_{i}.mp4"
            
            create_video(
                input_path,
                output_path,
                transcript,
                snippet["text"],
                face_tracking=face_tracking,
                bottom_video_path=bottom_video_path
            )
            
            output_clips.append(output_path)
            print(f"Clip {i+1} saved to: {output_path}")
    
    return output_clips

if __name__ == "__main__":
    # Example usage
    url = input("Enter top video URL: ")
    bottom_url = input("Enter bottom video URL (or press Enter to skip): ")
    use_face_tracking = input("Use face tracking? (y/n): ").lower() == 'y'
    
    bottom_video_url = bottom_url if bottom_url.strip() else None
    clips = asyncio.run(process_video_url(url, face_tracking=use_face_tracking, bottom_video_url=bottom_video_url))
    print("\nProcessing complete!")
    print("Output clips:", clips)