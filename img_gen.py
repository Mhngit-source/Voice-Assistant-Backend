import requests
import base64
import json
import os
from datetime import datetime
from typing import Optional

class FreeImageGenerator:
    def __init__(self):
        self.session = requests.Session()
        
    def generate_with_huggingface(self, prompt: str, model: str = "stabilityai/stable-diffusion-xl-base-1.0") -> Optional[bytes]:
        """
        Generate image using Hugging Face Inference API (completely free)
        No signup required, but has rate limits
        """
        models_to_try = [
            "runwayml/stable-diffusion-v1-5",
            "CompVis/stable-diffusion-v1-4", 
            "stabilityai/stable-diffusion-xl-base-1.0",
            "prompthero/openjourney-v4"
        ]
        
        # If a specific model was requested, try it first
        if model not in models_to_try:
            models_to_try.insert(0, model)
        
        for current_model in models_to_try:
            print(f"🎨 Trying Hugging Face model: {current_model}")
            
            api_url = f"https://api-inference.huggingface.co/models/{current_model}"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5,
                    "width": 512,
                    "height": 512
                }
            }
            
            try:
                response = self.session.post(api_url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    return response.content
                elif response.status_code == 503:
                    print("⏳ Model is loading, please wait...")
                    continue  # Try next model
                elif response.status_code == 401:
                    print(f"🔒 Model {current_model} requires authentication, trying next...")
                    continue  # Try next model
                elif response.status_code == 429:
                    print("⏰ Rate limit reached, trying next model...")
                    continue  # Try next model
                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
                    continue  # Try next model
                    
            except Exception as e:
                print(f"❌ Request failed for {current_model}: {e}")
                continue  # Try next model
        
        print("❌ All Hugging Face models failed or require authentication")
        return None
    
    def generate_with_pollinations(self, prompt: str, width: int = 512, height: int = 512) -> Optional[bytes]:
        """
        Generate image using Pollinations AI (completely free)
        No signup required, no rate limits
        """
        print("🌸 Generating with Pollinations AI")
        
        # Clean prompt for URL
        clean_prompt = prompt.replace(" ", "%20").replace(",", "%2C")
        
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width={width}&height={height}&nologo=true"
        
        try:
            response = self.session.get(url, timeout=60)
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"❌ Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def generate_with_local_diffusers(self, prompt: str) -> Optional[bytes]:
        """
        Generate image using local diffusers library
        Requires: pip install diffusers torch transformers accelerate
        """
        try:
            try:
                from diffusers import StableDiffusionPipeline
                import torch
                from io import BytesIO
            except ImportError as e:
                print(f"❌ Missing required packages: {e}")
                print("💡 Install with: pip install diffusers torch transformers accelerate")
                return None
            
            print("🏠 Generating with local Stable Diffusion")
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if device == "cuda" else torch.float32
            
            print(f"🔧 Loading model on {device}...")
            
            # Load pipeline (downloads model on first run)
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch_dtype,
                safety_checker=None,  # Disable safety checker to avoid potential issues
                requires_safety_checker=False
            )
            
            # Use GPU if available
            pipe = pipe.to(device)
            
            if device == "cuda":
                print("🚀 Using GPU acceleration")
            else:
                print("💻 Using CPU (slower)")
            
            print("🎨 Generating image...")
            with torch.no_grad():  # Added no_grad for memory efficiency
                result = pipe(
                    prompt, 
                    num_inference_steps=20, 
                    guidance_scale=7.5,
                    height=512,
                    width=512
                )
                image = result.images[0]
            
            # Convert to bytes
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)  # Reset buffer position
            return buffer.getvalue()
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("💡 Install required packages: pip install diffusers torch transformers accelerate")
            return None
        except RuntimeError as e:
            if "CUDA" in str(e):
                print(f"❌ CUDA error: {e}")
                print("💡 Try running on CPU or check CUDA installation")
            else:
                print(f"❌ Runtime error: {e}")
            return None
        except Exception as e:
            print(f"❌ Local generation failed: {e}")
            print(f"💡 Error type: {type(e).__name__}")
            return None
    
    def save_image(self, image_data: bytes, prompt: str, method: str) -> str:
        """Save image data to file"""
        if not os.path.exists("generated_images"):
            os.makedirs("generated_images")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"generated_images/{method}_{timestamp}_{safe_prompt}.png"
        
        with open(filename, "wb") as f:
            f.write(image_data)
        
        return filename
    
    def enhance_prompt(self, prompt: str) -> str:
        """
        Enhance vague prompts to get better AI-generated images
        """
        enhancements = {
            # Future/futuristic concepts
            "future": "futuristic, sci-fi, advanced technology, cyberpunk, neon lights, flying cars, holographic displays",
            "modern": "contemporary, sleek design, minimalist, glass and steel architecture",
            
            # Country/location enhancements
            "india": "Indian culture, diverse people, vibrant colors, traditional and modern blend",
            "future india": "futuristic India, advanced Indian cities, sci-fi Mumbai skyline, high-tech Delhi, flying vehicles over Indian architecture, holographic Bollywood, cyber-punk Indian street markets, advanced technology with Indian cultural elements",
            
            # Common vague terms
            "beautiful": "stunning, breathtaking, highly detailed, photorealistic, award-winning photography",
            "nice": "elegant, sophisticated, well-designed, aesthetically pleasing",
            "cool": "impressive, striking, dynamic, eye-catching"
        }
        
        original_prompt = prompt.lower().strip()
        
        # Check for exact matches first
        for key, enhancement in enhancements.items():
            if original_prompt == key:
                enhanced = f"{enhancement}, high quality, detailed, 4k resolution"
                print(f"💡 Enhanced prompt: '{prompt}' → '{enhanced}'")
                return enhanced
        
        # Check for partial matches
        for key, enhancement in enhancements.items():
            if key in original_prompt:
                enhanced = f"{prompt}, {enhancement}, high quality, detailed"
                print(f"💡 Enhanced prompt: '{prompt}' → '{enhanced}'")
                return enhanced
        
        # Add general quality improvements
        if len(prompt.split()) < 5:  # Short prompts need more detail
            enhanced = f"{prompt}, highly detailed, professional quality, vibrant colors, sharp focus"
            print(f"💡 Enhanced prompt: '{prompt}' → '{enhanced}'")
            return enhanced
        
        return prompt
    
    def suggest_better_prompts(self, original_prompt: str):
        """Suggest better alternatives for common problematic prompts"""
        suggestions = {
            "future india": [
                "Futuristic Indian cityscape with flying cars and holographic billboards, cyberpunk Mumbai 2050",
                "Advanced technology integrated with traditional Indian architecture, sci-fi Delhi with floating temples",
                "Indian street market in 2080 with robots and holograms, neon-lit cyber bazaar",
                "Futuristic Indian woman in high-tech sari with glowing patterns, sci-fi Bollywood"
            ],
            "future": [
                "Cyberpunk cityscape with neon lights and flying vehicles, blade runner style",
                "Advanced space station with Earth in background, sci-fi architecture",
                "Futuristic laboratory with holographic displays and robots, high-tech interior",
                "Flying cars in a futuristic city, aerial view of tomorrow's metropolis"
            ],
            "india": [
                "Vibrant Indian festival with colorful decorations and happy people dancing",
                "Modern Indian tech hub with glass buildings and traditional elements",
                "Indian street food vendor with aromatic spices and busy market scene",
                "Beautiful Indian palace garden with fountains and peacocks"
            ]
        }
        
        original_lower = original_prompt.lower().strip()
        
        if original_lower in suggestions:
            print(f"\n💡 Better prompt suggestions for '{original_prompt}':")
            for i, suggestion in enumerate(suggestions[original_lower], 1):
                print(f"   {i}. {suggestion}")
            
            choice = input("\nUse a suggested prompt? Enter number (1-4) or press Enter to continue: ").strip()
            try:
                if choice and 1 <= int(choice) <= len(suggestions[original_lower]):
                    return suggestions[original_lower][int(choice) - 1]
            except ValueError:
                pass
        
        return original_prompt
    
    def generate_image(self, prompt: str, method: str = "auto") -> Optional[str]:
        """
        Generate image using specified method
        Methods: 'huggingface', 'pollinations', 'local', 'auto'
        """
        # First, suggest better prompts if available
        improved_prompt = self.suggest_better_prompts(prompt)
        
        # Then enhance the prompt for better results
        enhanced_prompt = self.enhance_prompt(improved_prompt)
        
        print(f"\n🎯 Prompt: {enhanced_prompt}")
        
        if method == "auto":
            methods = ["pollinations", "huggingface", "local"]
        else:
            methods = [method]
        
        for current_method in methods:
            print(f"\n🔄 Trying method: {current_method}")
            
            image_data = None
            
            if current_method == "huggingface":
                image_data = self.generate_with_huggingface(enhanced_prompt)
            elif current_method == "pollinations":
                image_data = self.generate_with_pollinations(enhanced_prompt)
            elif current_method == "local":
                image_data = self.generate_with_local_diffusers(enhanced_prompt)
            
            if image_data:
                filename = self.save_image(image_data, enhanced_prompt, current_method)
                print(f"✅ Image saved: {filename}")
                return filename
            
            if method != "auto":
                break
        
        print("❌ All methods failed")
        print("💡 Try using 'pollinations' method specifically, or install local diffusers")
        return None

# Add this function at the module level for backward compatibility
def generate_image(request: str) -> Optional[str]:
    """
    Standalone function for compatibility with existing code
    """
    generator = FreeImageGenerator()
    return generator.generate_image(request)

def main():
    """Main function with example usage"""
    generator = FreeImageGenerator()
    
    prompts = [
        "Futuristic Indian cityscape with flying cars and holographic billboards, cyberpunk Mumbai 2050, neon lights",
        "Advanced space station orbiting Earth, sci-fi architecture with glass domes, detailed digital art",
        "Cyberpunk street market with neon signs and robots, blade runner style, atmospheric lighting",
        "Floating city in the clouds with advanced architecture, fantasy sci-fi, highly detailed"
    ]
    
    print("🚀 Free Image Generator with Smart Prompting")
    print("=" * 50)
    print("💡 Tip: Be specific! Instead of 'future india', try 'futuristic Indian cityscape with flying cars'")
    
    # Interactive mode
    while True:
        print("\nOptions:")
        print("1. Enter custom prompt")
        print("2. Use example prompts")
        print("3. Quit")
        
        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == "1":
            prompt = input("Enter your prompt: ").strip()
            if prompt:
                method = input("Method (huggingface/pollinations/local/auto): ").strip() or "auto"
                generator.generate_image(prompt, method)
        
        elif choice == "2":
            print("\nExample prompts:")
            for i, prompt in enumerate(prompts, 1):
                print(f"{i}. {prompt}")
            
            try:
                idx = int(input("Choose prompt (1-4): ")) - 1
                if 0 <= idx < len(prompts):
                    generator.generate_image(prompts[idx])
            except ValueError:
                print("Invalid selection")
        
        elif choice == "3":
            break
        
        else:
            print("Invalid option")
    
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()