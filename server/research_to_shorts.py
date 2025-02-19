import asyncio
import re
from typing import List, Dict
import os
from dotenv import load_dotenv

# Import our custom modules
from run_deepresearch import run_research
from process_video import process_video_url

# Load environment variables
load_dotenv()

def extract_youtube_links(markdown_content: str) -> List[Dict[str, str]]:
    """
    Extract YouTube links from markdown content.
    Returns a list of dicts containing the link and surrounding context.
    """
    # YouTube URL patterns
    youtube_patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([^\s&]+)',
    ]
    
    videos = []
    lines = markdown_content.split('\n')
    
    for i, line in enumerate(lines):
        for pattern in youtube_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                # Get some context (the line containing the link)
                videos.append({
                    "url": match.group(0),
                    "context": line.strip(),
                    "line_number": i + 1
                })
    
    return videos

async def research_to_shorts(query: str, prompt: str, face_tracking: bool = False) -> List[str]:
    """
    Main function to run research and process videos.
    Returns a list of output clip paths.
    """
    # Run the deep research
    print("\n1. Running deep research...")
    report = await run_research(query, prompt)
    
    # Extract YouTube links
    print("\n2. Extracting YouTube links from research...")
    videos = extract_youtube_links(report)
    
    if not videos:
        print("No YouTube links found in the research output!")
        return []
    
    # Display found videos
    print("\nFound the following YouTube videos:")
    for i, video in enumerate(videos):
        print(f"\n{i+1}. {video['url']}")
        print(f"   Context: {video['context']}")
    
    # Get user selection
    print("\nEnter the numbers of the videos you want to process (comma-separated)")
    print("Example: 1,3,4 or press Enter to process all")
    selection = input("> ").strip()
    
    # Process selection
    if selection:
        selected_indices = [int(i.strip()) - 1 for i in selection.split(",")]
        selected_videos = [videos[i] for i in selected_indices if 0 <= i < len(videos)]
    else:
        selected_videos = videos
    
    # Process each selected video
    output_clips = []
    for video in selected_videos:
        print(f"\nProcessing video: {video['url']}")
        try:
            clips = await process_video_url(video['url'], face_tracking=face_tracking)
            output_clips.extend(clips)
        except Exception as e:
            print(f"Error processing video {video['url']}: {str(e)}")
    
    return output_clips

if __name__ == "__main__":
    print("Welcome to Research to Shorts!")
    print("This tool will run deep research and create short clips from relevant YouTube videos.\n")
    
    # Get user inputs
    query = input("Enter your research query: ")
    prompt = input("Enter your report prompt: ")
    face_tracking = input("Use face tracking? (y/n): ").lower() == 'y'
    
    # Run the main process
    clips = asyncio.run(research_to_shorts(query, prompt, face_tracking))
    
    # Display results
    if clips:
        print("\nProcessing complete!")
        print("Output clips:", clips)
    else:
        print("\nNo clips were generated.") 