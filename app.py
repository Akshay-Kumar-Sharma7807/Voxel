#!/usr/bin/env python3
"""
Voxel Web Interface - Flask application for browser-based ambient art generation.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
import json
import threading
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from voxel.audio.capture import AudioCapture
from voxel.speech.processor import SpeechProcessor
from voxel.analysis.analyzer import TextAnalyzer
from voxel.generation.crafter import PromptCrafter
from voxel.generation.generator import ImageGenerator
from voxel.config import SystemConfig, GenerationConfig
from voxel.models import TranscriptionResult

app = Flask(__name__)
app.config['SECRET_KEY'] = 'voxel-ambient-art-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global components
audio_capture = None
speech_processor = None
text_analyzer = None
prompt_crafter = None
image_generator = None
processing_active = False

def initialize_components():
    """Initialize all Voxel components."""
    global audio_capture, speech_processor, text_analyzer, prompt_crafter, image_generator
    
    try:
        audio_capture = AudioCapture()
        speech_processor = SpeechProcessor()
        text_analyzer = TextAnalyzer()
        prompt_crafter = PromptCrafter()
        
        # Initialize image generator based on provider
        if GenerationConfig.PROVIDER == "openai" and SystemConfig.OPENAI_API_KEY:
            image_generator = ImageGenerator(provider="openai")
        elif GenerationConfig.PROVIDER == "google_cloud" and GenerationConfig.GCP_PROJECT_ID:
            image_generator = ImageGenerator(provider="google_cloud")
        elif GenerationConfig.PROVIDER == "freepik" and SystemConfig.FREEPIK_API_KEY:
            image_generator = ImageGenerator(provider="freepik")
        elif SystemConfig.OPENAI_API_KEY:  # Fallback to OpenAI
            image_generator = ImageGenerator(provider="openai")
        
        return True
    except Exception as e:
        print(f"Error initializing components: {e}")
        return False

@app.route('/')
def index():
    """Main web interface."""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """Get system status."""
    provider = GenerationConfig.PROVIDER
    provider_configured = False
    
    if provider == "openai":
        provider_configured = SystemConfig.OPENAI_API_KEY is not None
    elif provider == "google_cloud":
        provider_configured = GenerationConfig.GCP_PROJECT_ID is not None
    elif provider == "freepik":
        provider_configured = SystemConfig.FREEPIK_API_KEY is not None
    
    return jsonify({
        'audio_available': audio_capture is not None,
        'speech_available': speech_processor is not None,
        'image_provider': provider,
        'provider_configured': provider_configured,
        'openai_configured': SystemConfig.OPENAI_API_KEY is not None,
        'google_cloud_configured': GenerationConfig.GCP_PROJECT_ID is not None,
        'freepik_configured': SystemConfig.FREEPIK_API_KEY is not None,
        'processing_active': processing_active
    })

@app.route('/api/start', methods=['POST'])
def start_processing():
    """Start ambient art generation."""
    global processing_active
    
    # Check if any image provider is configured
    provider = GenerationConfig.PROVIDER
    if provider == "openai" and not SystemConfig.OPENAI_API_KEY:
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    elif provider == "google_cloud" and not GenerationConfig.GCP_PROJECT_ID:
        return jsonify({'error': 'Google Cloud project not configured'}), 400
    elif provider == "freepik" and not SystemConfig.FREEPIK_API_KEY:
        return jsonify({'error': 'Freepik API key not configured'}), 400
    
    processing_active = True
    
    # Start processing in background thread
    thread = threading.Thread(target=processing_loop)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_processing():
    """Stop ambient art generation."""
    global processing_active
    processing_active = False
    return jsonify({'status': 'stopped'})

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve generated images."""
    return send_from_directory('generated_images', filename)

def processing_loop():
    """Main processing loop for ambient art generation."""
    global processing_active
    
    while processing_active:
        try:
            # Emit status update
            socketio.emit('status_update', {'message': 'Listening for audio...'})
            
            # Capture audio (simulated for web demo)
            socketio.emit('status_update', {'message': 'Processing audio...'})
            time.sleep(2)  # Simulate processing time
            
            # For demo purposes, use sample text
            sample_texts = [
                "peaceful sunset over calm waters",
                "energetic city lights at night",
                "serene forest with morning mist",
                "vibrant abstract patterns dancing",
                "cozy fireplace on winter evening"
            ]
            
            import random
            demo_text = random.choice(sample_texts)
            
            socketio.emit('transcription', {'text': demo_text})
            
            # Analyze text
            if text_analyzer:
                socketio.emit('status_update', {'message': 'Analyzing speech...'})
                
                # Create proper TranscriptionResult object
                transcription = TranscriptionResult(
                    text=demo_text,
                    confidence=0.85,  # Demo confidence
                    timestamp=datetime.now(),
                    is_valid=True
                )
                
                analysis = text_analyzer.analyze_text(transcription)
                
                socketio.emit('analysis', {
                    'keywords': analysis.keywords,
                    'sentiment': analysis.sentiment,
                    'themes': analysis.themes,
                    'confidence': analysis.confidence
                })
                
                # Generate prompt
                if prompt_crafter:
                    socketio.emit('status_update', {'message': 'Crafting image prompt...'})
                    prompt = prompt_crafter.craft_prompt(analysis)
                    
                    socketio.emit('prompt', {
                        'text': prompt.prompt_text,
                        'style_modifiers': prompt.style_modifiers
                    })
                    
                    # Generate image (if configured)
                    if image_generator:
                        socketio.emit('status_update', {'message': 'Generating artwork...'})
                        
                        try:
                            result = image_generator.generate_image(prompt)
                            
                            socketio.emit('image_generated', {
                                'url': result.url,
                                'local_path': result.local_path,
                                'filename': Path(result.local_path).name if result.local_path else None
                            })
                            
                        except Exception as e:
                            socketio.emit('error', {'message': f'Image generation failed: {str(e)}'})
            
            # Wait before next cycle
            socketio.emit('status_update', {'message': f'Waiting {SystemConfig.CYCLE_COOLDOWN} seconds...'})
            time.sleep(SystemConfig.CYCLE_COOLDOWN)
            
        except Exception as e:
            socketio.emit('error', {'message': f'Processing error: {str(e)}'})
            time.sleep(5)  # Wait before retrying

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'message': 'Connected to Voxel server'})

if __name__ == '__main__':
    print("🎨 Starting Voxel Web Interface...")
    
    # Initialize components
    if initialize_components():
        print("✅ Components initialized successfully")
    else:
        print("⚠️  Some components failed to initialize")
    
    # Create necessary directories
    Path('generated_images').mkdir(exist_ok=True)
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    
    print("🌐 Starting web server at http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)