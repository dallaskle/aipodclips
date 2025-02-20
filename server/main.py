from flask import Flask, request, render_template, make_response, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import yt_dlp
import tempfile
import json
import uuid
import asyncio
from create_video import create_video
from snippets import generate_snippets
from title import generate_title
from query_refiner import refine_query
from video_metadata import get_videos_metadata
from research_to_shorts import extract_youtube_links, research_to_shorts

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Ensure CORS headers are added to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/refine-query', methods=['POST', 'OPTIONS'])
async def refine_query_endpoint():
    """
    Endpoint to refine user's query using OpenAI.
    """
    # Handle preflight request
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    data = request.json
    user_input = data.get('query')
    
    if not user_input:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        refinement_result = await refine_query(user_input)
        return jsonify(refinement_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-research', methods=['POST'])
async def start_research():
    """
    Endpoint to start the deep research process.
    """
    data = request.json
    query = data.get('query')
    prompt = data.get('prompt')
    
    if not query or not prompt:
        return jsonify({'error': 'Query and prompt are required'}), 400
    
    try:
        # Run research and extract links
        report = await research_to_shorts(query, prompt, face_tracking=False)
        videos = extract_youtube_links(report)
        
        # Get metadata for videos
        metadata = get_videos_metadata([v['url'] for v in videos])
        
        return jsonify({
            'videos': metadata
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-videos', methods=['POST'])
async def process_videos():
    """
    Endpoint to process selected videos into shorts.
    """
    data = request.json
    videos = data.get('videos', [])
    face_tracking = data.get('face_tracking', False)
    
    if not videos:
        return jsonify({'error': 'No videos provided'}), 400
    
    try:
        all_clips = []
        for video in videos:
            clips = await process_video_url(video['url'], face_tracking=face_tracking)
            all_clips.extend(clips)
        
        return jsonify({
            'clips': all_clips
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    """
    Endpoint to download processed video clips.
    """
    try:
        return send_from_directory('video_outputs', filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, port=8000)