import google.genai as genai
from google.genai import types
import user_config

# Configure Gemini with your API key
client = genai.Client(api_key=user_config.google_api_key)

# Using the latest flash model
MODEL_NAME = "gemma-3-27b-it"  # or "gemini-1.5-flash"

def send_request(query):
    """
    Send request to Gemini AI
    query: List of message dictionaries in format [{"role": "user", "content": "message"}]
    """
    try:
        print(f"🤖 AI Request received - Using model: {MODEL_NAME}", flush=True)
        
        if not query or len(query) == 0:
            return "Please say something for me to respond to."
        
        # Get the last user message
        last_message = query[-1]["content"]
        
        # Create conversation context
        if len(query) > 1:
            conversation = ""
            for msg in query[:-1]:
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation += f"{role}: {msg['content']}\n"
            
            prompt = f"""You are MAN-I, a helpful, friendly, and concise AI voice assistant.

Previous conversation:
{conversation}
User: {last_message}
Assistant:"""
        else:
            prompt = f"""You are MAN-I, a helpful, friendly, and concise AI voice assistant.

User: {last_message}
MAN-I:"""
        
        print(f"📤 Sending to Gemini...", flush=True)
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        print(f"✅ AI Response received", flush=True)
        return response.text
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Gemini API Error: {error_str}", flush=True)
        return f"I'm having trouble processing your request. Please try again."

def simple_send_request(query):
    """Simple version without chat history"""
    try:
        last_message = query[-1]["content"] if query else "Hello"
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=last_message
        )
        return response.text
    except Exception as e:
        print(f"❌ Simple request error: {e}", flush=True)
        return "I'm having trouble connecting. Please try again."

def list_available_models():
    """Helper function to list all available models"""
    try:
        print("\n📋 Available Gemini Models:")
        for model in client.models.list():
            if model.name.startswith("models/gemini"):
                print(f"   ✅ {model.name}")
        print("")
    except Exception as e:
        print(f"❌ Could not list models: {e}")

# Run this when file is imported
try:
    list_available_models()
    print(f"✅ Using model: {MODEL_NAME}")
except:
    pass