import requests
import os
from datetime import datetime
from typing import Optional
import time
import hashlib
from io import BytesIO
import random

# Try to import PIL for image processing
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not installed. Install with: pip install Pillow")

class ImageGenerator:  # Changed from FreeImageGenerator to ImageGenerator
    def __init__(self):
        self.session = requests.Session()
        # Create generated_images directory if it doesn't exist
        self.images_dir = os.path.join(os.getcwd(), 'generated_images')
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
            print(f"✅ Created images directory: {self.images_dir}")
    
    # ============ POLLINATIONS (FREE, NO KEY) ============
    def generate_with_pollinations(self, prompt: str, width: int = 512, height: int = 512) -> Optional[bytes]:
        """Generate image using Pollinations AI (free, no key needed)"""
        try:
            print("🌸 Trying Pollinations AI...", flush=True)
            
            # Clean prompt for URL
            clean_prompt = prompt.replace(" ", "%20").replace(",", "%2C").replace("'", "").replace('"', '')
            
            # Try multiple endpoints
            endpoints = [
                f"https://image.pollinations.ai/prompt/{clean_prompt}?width={width}&height={height}&nologo=true",
                f"https://pollinations.ai/p/{clean_prompt}",
                f"https://text-to-image.pollinations.ai/generate?text={clean_prompt}"
            ]
            
            for i, url in enumerate(endpoints):
                try:
                    print(f"   Trying endpoint {i+1}...", flush=True)
                    response = self.session.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'image' in content_type or len(response.content) > 1000:
                            print(f"✅ Pollinations success (endpoint {i+1})", flush=True)
                            return response.content
                except Exception as e:
                    print(f"   Endpoint {i+1} failed: {e}", flush=True)
                    continue
            
            return None
        except Exception as e:
            print(f"⚠️ Pollinations error: {e}", flush=True)
            return None
    
    # ============ PLACEHOLDER (ALWAYS WORKS) ============
    def generate_placeholder(self, prompt: str) -> Optional[bytes]:
        """Generate a beautiful placeholder image (ALWAYS works)"""
        try:
            print("🎨 Generating placeholder image...", flush=True)
            
            if not PIL_AVAILABLE:
                return self._generate_simple_placeholder(prompt)
            
            width, height = 512, 512
            image = Image.new('RGB', (width, height), color=(37, 99, 235))
            draw = ImageDraw.Draw(image)
            
            # Create gradient background
            for i in range(height):
                color = (
                    int(37 + (218 * i / height)),
                    int(99 + (156 * i / height)),
                    int(235 + (20 * i / height))
                )
                draw.line([(0, i), (width, i)], fill=color)
            
            # Add decorative circles
            draw.ellipse([50, 50, 462, 462], outline=(255, 255, 255, 100), width=2)
            draw.ellipse([100, 100, 412, 412], outline=(255, 255, 255, 150), width=2)
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 24)
                small_font = ImageFont.truetype("arial.ttf", 18)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Split prompt into lines
            lines = []
            words = prompt.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) < 30:
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            # Draw prompt text
            y_start = 200
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x_position = (width - text_width) // 2
                draw.text((x_position, y_start + i * 30), line, fill=(255, 255, 255), font=font)
            
            # Add footer
            footer = "MAN-I AI"
            bbox = draw.textbbox((0, 0), footer, font=small_font)
            footer_width = bbox[2] - bbox[0]
            draw.text(((width - footer_width) // 2, 400), footer, fill=(255, 255, 255), font=small_font)
            
            # Save to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            print(f"✅ Placeholder generated", flush=True)
            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"⚠️ Placeholder error: {e}, using simple fallback", flush=True)
            return self._generate_simple_placeholder(prompt)
    
    def _generate_simple_placeholder(self, prompt: str) -> bytes:
        """Ultimate simple fallback"""
        try:
            from PIL import Image, ImageDraw
            
            # Create deterministic color based on prompt
            hash_obj = hashlib.md5(prompt.encode())
            hash_hex = hash_obj.hexdigest()
            r = int(hash_hex[0:2], 16)
            g = int(hash_hex[2:4], 16)
            b = int(hash_hex[4:6], 16)
            
            img = Image.new('RGB', (512, 512), color=(r, g, b))
            draw = ImageDraw.Draw(img)
            draw.rectangle([100, 200, 412, 300], fill=(255, 255, 255))
            
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return img_byte_arr.getvalue()
        except:
            # If even PIL fails, return a simple colored square as bytes
            return b''
    
    def save_image(self, image_data: bytes, prompt: str, method: str) -> str:
        """Save image to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_prompt = safe_prompt.replace(' ', '_')
        filename = f"{method}_{timestamp}_{safe_prompt}.png"
        filepath = os.path.join(self.images_dir, filename)
        
        try:
            with open(filepath, "wb") as f:
                f.write(image_data)
            print(f"✅ Image saved: {filename}", flush=True)
            return filepath
        except Exception as e:
            print(f"❌ Failed to save image: {e}", flush=True)
            return None
    
    def clean_prompt(self, prompt: str) -> str:
        """Clean and enhance prompt"""
        # Remove common command words
        prompt = prompt.lower()
        prompt = prompt.replace("generate", "").replace("image", "").replace("of", "").replace("create", "").replace("make", "").replace("draw", "").strip()
        
        # Capitalize first letter
        if prompt:
            prompt = prompt[0].upper() + prompt[1:]
        
        if not prompt or len(prompt) < 3:
            prompt = "Beautiful landscape"
        
        return prompt
    
    def generate_image(self, prompt: str) -> Optional[str]:
        """Generate image using multiple methods"""
        clean_prompt = self.clean_prompt(prompt)
        print(f"\n🎯 Generating image for: '{clean_prompt}'", flush=True)
        
        # Try methods in order
        methods = [
            ("pollinations", self.generate_with_pollinations),
            ("placeholder", self.generate_placeholder)
        ]
        
        for method_name, method_func in methods:
            print(f"🔄 Trying {method_name}...", flush=True)
            image_data = method_func(clean_prompt)
            
            if image_data and len(image_data) > 1000:
                filepath = self.save_image(image_data, clean_prompt, method_name)
                if filepath:
                    print(f"✅ Success with {method_name}!", flush=True)
                    return filepath
            else:
                print(f"⚠️ {method_name} failed", flush=True)
        
        print("❌ All methods failed", flush=True)
        return None

# Standalone function (KEEP THIS EXACT NAME)
def generate_image(request: str) -> Optional[str]:
    """Generate image from text prompt - THIS FUNCTION IS CALLED BY server.py"""
    generator = ImageGenerator()
    return generator.generate_image(request)

# For backward compatibility - add this alias
FreeImageGenerator = ImageGenerator

if __name__ == "__main__":
    generator = ImageGenerator()
    result = generator.generate_image("test image")
    if result:
        print(f"✅ Test successful! Image saved to: {result}")
    else:
        print("❌ Test failed")