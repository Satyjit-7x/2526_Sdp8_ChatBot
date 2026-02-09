import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def list_available_models():
    print("🔍 Listing Available Gemini Models")
    print("=" * 40)
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        
        print("✅ Available models:")
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_available_models()
