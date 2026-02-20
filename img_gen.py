import os
import requests
import uuid
from datetime import datetime
from PIL import Image, ImageDraw
import user_config  # Import your config

GENERATED_IMAGES_DIR = os.path.join(os.getcwd(), 'generated_images')
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)

# Read from user_config
WORKER_API_URL = user_config.WORKER_API_URL
WORKER_API_KEY = user_config.WORKER_API_KEY

class FreeImageGenerator:
    def __init__(self):
        self.api_url = WORKER_API_URL
        self.headers = {
            "Authorization": f"Bearer {WORKER_API_KEY}",
            "Content-Type": "application/json"
        }
        print(f"✅ Using Cloudflare Worker API: {self.api_url}")
        # Mask API key for security in logs
        masked_key = WORKER_API_KEY[:4] + "..." + WORKER_API_KEY[-4:] if len(WORKER_API_KEY) > 8 else "***"
        print(f"✅ API Key set: {masked_key}")

    def generate_image(self, prompt):
        """Generate image using your Cloudflare Worker."""
        try:
            print(f"🎨 Generating via Worker: {prompt[:50]}...")
            payload = {"prompt": prompt}
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                # Worker returns image binary (JPEG)
                return self._save_image_bytes(response.content, "worker")
            else:
                print(f"❌ Worker error: {response.status_code} - {response.text}")
                return self._generate_placeholder(prompt)
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return self._generate_placeholder(prompt)

    def _save_image_bytes(self, image_bytes, prefix):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(GENERATED_IMAGES_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        print(f"✅ Image saved: {filepath}")
        return filepath

    def _generate_placeholder(self, prompt):
        """Fallback placeholder (rarely used now)."""
        print("⚠️ Generating placeholder as fallback.")
        img = Image.new('RGB', (512, 512), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10, 10), f"Image for:\n{prompt[:50]}", fill=(255, 255, 255))
        d.text((10, 450), "API unavailable", fill=(255, 200, 200))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"placeholder_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(GENERATED_IMAGES_DIR, filename)
        img.save(filepath)
        return filepath

# Keep the class name for compatibility
FreeImageGenerator = FreeImageGenerator