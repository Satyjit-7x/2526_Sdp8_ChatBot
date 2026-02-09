import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def check_gemini_setup():
    print("🔍 Checking Gemini API Setup")
    print("=" * 40)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        print("\n📝 To set up Gemini:")
        print("1. Get API key from: https://aistudio.google.com/app/apikey")
        print("2. Add to .env file: GEMINI_API_KEY=your_key_here")
        print("3. Restart the application")
        return False
    
    print("✅ GEMINI_API_KEY found")
    
    # Test connection
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hello, can you respond with 'Gemini is working!'?")
        
        if "Gemini is working!" in response.text:
            print("✅ Gemini API connection successful!")
            return True
        else:
            print("⚠️ Gemini responded but unexpected output")
            return True
            
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False

if __name__ == "__main__":
    check_gemini_setup()
