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

async def research_to_shorts(query: str, prompt: str, face_tracking: bool = False) -> str:
    """
    Function to run research and return the research report.
    Returns the research report text.
    """
    # Run the deep research
    print("\n1. Running deep research...")
    report = await run_research(query, prompt)
    
    return report

if __name__ == "__main__":
    print("Welcome to Research to Shorts!")
    print("This tool will run deep research and extract YouTube links.\n")
    
    # Get user inputs
    query = input("Enter your research query: ")
    prompt = input("Enter your report prompt: ")
    
    # Run the research process
    report = asyncio.run(research_to_shorts(query, prompt))
    
    # Extract and display links
    videos = extract_youtube_links(report)
    if videos:
        print("\nFound YouTube links:")
        for video in videos:
            print(f"- {video['url']}")
    else:
        print("\nNo YouTube links found in the research.") 