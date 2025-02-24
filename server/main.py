from flask import Flask, request, render_template, make_response, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import yt_dlp
import tempfile
import json
import uuid
import asyncio
import logging
import os
from create_video import create_video
from snippets import generate_snippets
from title import generate_title
from query_refiner import refine_query
from video_metadata import get_videos_metadata
from research_to_shorts import extract_youtube_links, research_to_shorts
from process_video import process_video_url
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS with credentials support
CORS(app, 
     resources={r"/api/*": {
         "origins": ["http://localhost:3000"],
         "supports_credentials": True,
         "allow_headers": ["Content-Type", "Authorization"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
     }})

@app.route('/api/refine-query', methods=['POST', 'OPTIONS'])
async def refine_query_endpoint():
    """
    Endpoint to refine user's query using OpenAI.
    """
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    data = request.json
    user_input = data.get('query')
    
    if not user_input:
        logger.warning("No query provided in request")
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        logger.info(f"Processing refine-query request: {user_input[:100]}...")
        refinement_result = await refine_query(user_input)
        logger.info("Successfully processed refine-query request")
        return jsonify(refinement_result)
    except Exception as e:
        logger.error(f"Error in refine-query endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-research', methods=['POST', 'OPTIONS'])
async def start_research():
    """
    Endpoint to start the deep research process and return video metadata.
    """
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    data = request.json
    query = data.get('query')
    prompt = data.get('prompt')
    
    if not query or not prompt:
        logger.warning("Missing query or prompt in request")
        return jsonify({'error': 'Query and prompt are required'}), 400
    
    try:
        logger.info(f"Starting research for query: {query[:100]}...")
        
        # Run research and extract links
        report = await research_to_shorts(query, prompt, face_tracking=False)
        logger.debug(f"Research report generated: {report[:200]}...")
        
        videos = extract_youtube_links(report)
        logger.info(f"Extracted {len(videos)} video links")
        
        # Get metadata for videos
        metadata = get_videos_metadata([v['url'] for v in videos])
        logger.info(f"Retrieved metadata for {len(metadata)} videos")
        
        return jsonify({
            'videos': metadata
        })
    except Exception as e:
        logger.error(f"Error in start-research endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-videos', methods=['POST'])
async def process_videos():
    """
    Endpoint to process selected videos into shorts.
    """
    data = request.json
    query = data.get('query')
    prompt = data.get('prompt')
    selected_videos = data.get('selected_videos', [])
    face_tracking = data.get('face_tracking', False)
    
    if not selected_videos:
        logger.warning("No videos provided in request")
        return jsonify({'error': 'No videos provided'}), 400
    
    try:
        logger.info(f"Processing {len(selected_videos)} videos with face_tracking={face_tracking}")
        all_clips = []
        for video_url in selected_videos:
            logger.info(f"Processing video: {video_url}")
            clips = await process_video_url(video_url, face_tracking=face_tracking)
            all_clips.extend(clips)
            logger.info(f"Generated {len(clips)} clips for video")
        
        logger.info(f"Successfully processed all videos. Total clips: {len(all_clips)}")
        return jsonify({
            'clips': all_clips
        })
    except Exception as e:
        logger.error(f"Error in process-videos endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def cleanup_video_files(video_id: str):
    """
    Clean up video files associated with a video ID.
    """
    try:
        # Clean up input video if it exists
        input_path = f"video_inputs/{video_id}"
        if os.path.exists(input_path):
            os.remove(input_path)
            logger.info(f"Cleaned up input video: {input_path}")
        
        # Clean up bottom video if it exists
        bottom_video_path = f"video_inputs/bottom_{video_id}"
        if os.path.exists(bottom_video_path):
            os.remove(bottom_video_path)
            logger.info(f"Cleaned up bottom video: {bottom_video_path}")
            
    except Exception as e:
        logger.error(f"Error cleaning up video files: {str(e)}")

@app.route('/download/<path:filename>')
def download_file(filename):
    """
    Endpoint to download processed video clips and clean up after download.
    """
    try:
        logger.info(f"Processing download request for: {filename}")
        # Remove video_outputs/ prefix if it exists
        clean_filename = filename.replace('video_outputs/', '')
        file_path = os.path.join('video_outputs', clean_filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404
        
        # Send the file
        response = send_from_directory('video_outputs', clean_filename, as_attachment=True)
        
        # Extract video ID from filename (assuming format: clip_<uuid>_<index>.mp4)
        parts = clean_filename.split('_')
        if len(parts) >= 2:
            video_id = parts[1]  # This should be the UUID part
            
            # Schedule cleanup after response is sent
            @response.call_on_close
            def cleanup():
                try:
                    # Remove the output clip
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Cleaned up output clip: {file_path}")
                    
                    # Clean up associated input files
                    cleanup_video_files(video_id)
                except Exception as e:
                    logger.error(f"Error in cleanup: {str(e)}")
        
        return response
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, port=8000)