from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import time
import sys
from datetime import datetime
import base64
from io import BytesIO
import threading
import traceback

# ===== FORCE RELOAD of gemini_ai.py =====
if 'gemini_ai' in sys.modules:
    del sys.modules['gemini_ai']

# Now import fresh
import gemini_ai
import img_gen

print("=" * 60)
print("🚀 MAN-I Server Starting...")
print("=" * 60)
print(f"✅ GEMINI MODEL: {gemini_ai.MODEL_NAME}")
print("=" * 60)

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:5000", "http://localhost:3000"])

assistant_process = None
active_sessions = {}
image_storage = {}
session_lock = threading.Lock()

# Create generated_images directory if it doesn't exist
GENERATED_IMAGES_DIR = os.path.join(os.getcwd(), 'generated_images')
if not os.path.exists(GENERATED_IMAGES_DIR):
    os.makedirs(GENERATED_IMAGES_DIR)
    print(f"✅ Created images directory: {GENERATED_IMAGES_DIR}")

# ============ MAN-I PROCESS MANAGEMENT ============
@app.route('/start', methods=['POST'])
def start_assistant():
    global assistant_process
    
    if assistant_process and assistant_process.poll() is None:
        return jsonify({"status": "already_running", "message": "MAN-I is already running"})
    
    try:
        python_executable = sys.executable
        assistant_process = subprocess.Popen(
            [python_executable, 'MAN-I.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=os.getcwd()
        )
        
        time.sleep(2)
        
        if assistant_process.poll() is not None:
            stdout, stderr = assistant_process.communicate()
            return jsonify({"status": "error", "message": f"MAN-I failed to start: {stderr}"})
        
        return jsonify({"status": "success", "message": "MAN-I started"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/stop', methods=['POST'])
def stop_assistant():
    global assistant_process
    
    if assistant_process and assistant_process.poll() is None:
        assistant_process.terminate()
        try:
            assistant_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            assistant_process.kill()
            assistant_process.wait()
        assistant_process = None
        return jsonify({"status": "success", "message": "MAN-I stopped"})
    else:
        return jsonify({"status": "stopped", "message": "MAN-I is not running"})

@app.route('/status', methods=['GET'])
def get_status():
    """Get MAN-I status"""
    global assistant_process
    if assistant_process and assistant_process.poll() is None:
        return jsonify({"status": "active"})
    else:
        return jsonify({"status": "inactive"})

# ============ CHAT ENDPOINT ============
@app.route('/api/chat/text', methods=['POST'])
def chat_text():
    """Handle text chat requests with Gemini only"""
    try:
        data = request.json
        user_id = data.get('userId', 'anonymous')
        message = data.get('message', '')
        session_id = data.get('sessionId', user_id)
        
        if not message:
            return jsonify({"success": False, "error": "No message provided"})
        
        print(f"\n📝 Chat request: '{message[:50]}...'", flush=True)
        print(f"   Session: {session_id}", flush=True)
        
        # Prepare chat history
        with session_lock:
            if session_id not in active_sessions:
                active_sessions[session_id] = []
            chat_history = active_sessions[session_id]
            chat_history.append({"role": "user", "content": message})
        
        # Call Gemini
        try:
            response_text = gemini_ai.send_request(chat_history)
            
            # Save to history
            with session_lock:
                if session_id in active_sessions:
                    active_sessions[session_id].append({"role": "assistant", "content": response_text})
            
            return jsonify({
                "success": True,
                "response": response_text,
                "citations": [],
                "source": "gemini",
                "sessionId": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            error_str = str(e)
            print(f"⚠️ Gemini failed: {error_str[:100]}", flush=True)
            
            return jsonify({
                "success": True,
                "response": "I'm having trouble processing your request. Please try again.",
                "citations": [],
                "source": "error",
                "sessionId": session_id,
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        print(f"❌ Chat error: {e}", flush=True)
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "response": "An error occurred. Please try again.",
            "citations": [],
            "source": "error"
        })

# ============ IMAGE GENERATION ENDPOINT ============
@app.route('/api/generate-image', methods=['POST'])
def generate_image_api():
    """Generate image using img_gen.py"""
    try:
        data = request.json
        user_id = data.get('userId', 'anonymous')
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({"success": False, "error": "No prompt provided"})
        
        print(f"\n🎨 Generating image: '{prompt[:50]}...'", flush=True)
        
        # Generate image using your img_gen.py
        try:
            generator = img_gen.FreeImageGenerator()
            image_path = generator.generate_image(prompt)
        except Exception as img_error:
            print(f"⚠️ Image generation error: {img_error}", flush=True)
            image_path = None
        
        if not image_path or not os.path.exists(image_path):
            return jsonify({"success": False, "error": "Image generation failed"})
        
        # Read image file and convert to base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:image/png;base64,{image_base64}"
        
        # Generate unique ID
        image_id = f"img_{int(time.time())}_{user_id}"
        
        # Get just the filename for URL
        filename = os.path.basename(image_path)
        
        # Store image info
        with session_lock:
            if user_id not in image_storage:
                image_storage[user_id] = []
            
            image_info = {
                "id": image_id,
                "prompt": prompt,
                "path": image_path,
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "dataUrl": data_url
            }
            image_storage[user_id].append(image_info)
            
            # Keep only last 50 images per user
            if len(image_storage[user_id]) > 50:
                # Delete old files
                for old_img in image_storage[user_id][:-50]:
                    if os.path.exists(old_img['path']):
                        try:
                            os.remove(old_img['path'])
                        except:
                            pass
                image_storage[user_id] = image_storage[user_id][-50:]
        
        # Create URL for the image
        image_url = f"http://localhost:5001/api/images/{filename}"
        
        print(f"✅ Image saved: {image_path}", flush=True)
        print(f"✅ Image URL: {image_url}", flush=True)
        
        return jsonify({
            "success": True,
            "imageId": image_id,
            "imageUrl": image_url,
            "dataUrl": data_url,
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "filename": filename
        })
        
    except Exception as e:
        print(f"❌ Image generation error: {e}", flush=True)
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

# ============ SERVE IMAGES ============
@app.route('/api/images/<filename>', methods=['GET'])
def serve_image(filename):
    """Serve generated images"""
    try:
        # Security: prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"success": False, "error": "Invalid filename"}), 400
        
        file_path = os.path.join(GENERATED_IMAGES_DIR, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ Image not found: {file_path}", flush=True)
            return jsonify({"success": False, "error": "Image not found"}), 404
        
        return send_file(file_path, mimetype='image/png')
        
    except Exception as e:
        print(f"❌ Serve image error: {e}", flush=True)
        return jsonify({"success": False, "error": str(e)}), 500

# ============ GET USER IMAGES ============
@app.route('/api/get-user-images/<user_id>', methods=['GET'])
def get_user_images(user_id):
    """Get all images generated by a user"""
    try:
        with session_lock:
            if user_id in image_storage:
                images = image_storage[user_id]
                image_list = []
                for img in reversed(images):  # Show newest first
                    image_list.append({
                        "id": img['id'],
                        "prompt": img['prompt'],
                        "timestamp": img['timestamp'],
                        "imageUrl": f"http://localhost:5001/api/images/{img['filename']}",
                        "dataUrl": img.get('dataUrl'),
                        "filename": img['filename']
                    })
                return jsonify({
                    "success": True,
                    "images": image_list,
                    "count": len(images)
                })
            else:
                return jsonify({"success": True, "images": [], "count": 0})
    except Exception as e:
        print(f"❌ Get user images error: {e}", flush=True)
        return jsonify({"success": False, "error": str(e)})

# ============ DELETE IMAGE ============
@app.route('/api/delete-image/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete an image"""
    try:
        data = request.json
        user_id = data.get('userId', 'anonymous')
        
        with session_lock:
            if user_id in image_storage:
                for i, img in enumerate(image_storage[user_id]):
                    if img['id'] == image_id:
                        # Delete file if exists
                        if os.path.exists(img['path']):
                            try:
                                os.remove(img['path'])
                                print(f"✅ Deleted file: {img['path']}", flush=True)
                            except Exception as e:
                                print(f"⚠️ Could not delete file: {e}", flush=True)
                        # Remove from storage
                        del image_storage[user_id][i]
                        return jsonify({"success": True, "message": "Image deleted"})
        
        return jsonify({"success": False, "error": "Image not found"}), 404
    except Exception as e:
        print(f"❌ Delete image error: {e}", flush=True)
        return jsonify({"success": False, "error": str(e)}), 500

# ============ CLEAR CHAT ============
@app.route('/api/clear-chat/<session_id>', methods=['POST'])
def clear_chat(session_id):
    with session_lock:
        if session_id in active_sessions:
            active_sessions[session_id] = []
    return jsonify({"success": True, "message": "Chat cleared"})

# ============ GET CHAT HISTORY ============
@app.route('/api/get-chat-history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    try:
        with session_lock:
            if session_id in active_sessions:
                history = active_sessions[session_id][-50:]
                return jsonify({"success": True, "history": history, "count": len(history)})
            else:
                return jsonify({"success": True, "history": [], "count": 0})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============ HEALTH CHECK ============
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "MAN-I AI Server",
        "gemini_model": gemini_ai.MODEL_NAME,
        "active_sessions": len(active_sessions),
        "total_images": sum(len(imgs) for imgs in image_storage.values()),
        "images_directory": GENERATED_IMAGES_DIR,
        "timestamp": datetime.now().isoformat()
    })

# ============ ROOT ENDPOINT ============
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "name": "MAN-I AI Server",
        "version": "1.0.0",
        "gemini_model": gemini_ai.MODEL_NAME,
        "status": "running",
        "images_url": "http://localhost:5001/api/images/<filename>",
        "endpoints": [
            "/status - Get MAN-I status",
            "/start - Start MAN-I",
            "/stop - Stop MAN-I",
            "/api/chat/text - Chat endpoint",
            "/api/generate-image - Generate image",
            "/api/images/<filename> - Get image file",
            "/api/get-user-images/<user_id> - Get user images",
            "/api/delete-image/<image_id> - Delete image",
            "/health - Health check"
        ]
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MAN-I Server running on http://localhost:5001")
    print("=" * 60)
    print(f"✅ Gemini Model: {gemini_ai.MODEL_NAME}")
    print(f"✅ Images will be served from: http://localhost:5001/api/images/<filename>")
    print(f"✅ Images directory: {GENERATED_IMAGES_DIR}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)