from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import time
import sys

app = Flask(__name__)
CORS(app)

assistant_process = None

@app.route('/start', methods=['POST'])
def start_assistant():
    global assistant_process
    
    print("=== START REQUEST RECEIVED ===", flush=True)
    
    if assistant_process and assistant_process.poll() is None:
        print("MAN-I is already running", flush=True)
        return jsonify({"status": "error", "message": "MAN-I is already running"})
    
    try:
        print("Starting MAN-I.py...", flush=True)
        
        # Start MAN-I.py with proper Python executable
        python_executable = sys.executable  # Use the same Python as the server
        
        assistant_process = subprocess.Popen(
            [python_executable, 'MAN-I.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            cwd=os.getcwd()  # Ensure correct working directory
        )
        
        # Wait a bit to see if it starts successfully
        time.sleep(2)
        
        # Check if process is still running
        if assistant_process.poll() is not None:
            # Process ended immediately - there was an error
            stdout, stderr = assistant_process.communicate()
            print(f"MAN-I failed to start.", flush=True)
            print(f"STDOUT: {stdout}", flush=True)
            print(f"STDERR: {stderr}", flush=True)
            return jsonify({"status": "error", "message": f"MAN-I failed to start: {stderr}"})
        
        print("MAN-I started successfully!", flush=True)
        return jsonify({"status": "success", "message": "MAN-I started"})
        
    except Exception as e:
        print(f"Error starting MAN-I: {e}", flush=True)
        return jsonify({"status": "error", "message": str(e)})

@app.route('/stop', methods=['POST'])
def stop_assistant():
    global assistant_process
    
    print("=== STOP REQUEST RECEIVED ===", flush=True)
    
    if assistant_process and assistant_process.poll() is None:
        print("Stopping MAN-I...", flush=True)
        
        # Try graceful termination first
        assistant_process.terminate()
        
        try:
            assistant_process.wait(timeout=5)
            print("MAN-I stopped successfully", flush=True)
        except subprocess.TimeoutExpired:
            print("MAN-I not responding, forcing kill...", flush=True)
            assistant_process.kill()
            assistant_process.wait()
        
        assistant_process = None
        return jsonify({"status": "success", "message": "MAN-I stopped"})
    else:
        print("MAN-I is not running", flush=True)
        return jsonify({"status": "error", "message": "MAN-I is not running"})

@app.route('/status', methods=['GET'])
def get_status():
    global assistant_process
    status = "stopped"
    if assistant_process and assistant_process.poll() is None:
        status = "running"
    
    print(f"Status check: {status}", flush=True)
    return jsonify({"status": status})

if __name__ == '__main__':
    print("=" * 50, flush=True)
    print("MAN-I Server running on http://localhost:5001", flush=True)
    print("=" * 50, flush=True)
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)  