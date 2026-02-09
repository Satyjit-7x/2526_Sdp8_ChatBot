import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class ResponseFormatter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("⚠️ Gemini API key not found. Response formatting disabled.")
    
    def format_response(self, user_question, bot_response):
        """Format bot response to be more user-friendly using Gemini"""
        
        if not self.model:
            # Fallback: return original response if Gemini not available
            return bot_response
        
        try:
            formatting_prompt = f"""
            Format the following bot response to be concise and structured. 
            
            User Question: "{user_question}"
            Bot Response: "{bot_response}"
            
            Instructions:
            1. Make it SHORT and DIRECT - only essential information
            2. Use line-by-line format, not paragraphs
            3. For orders: use bullet points or numbered lists
            4. Remove unnecessary descriptions and fluff
            5. Keep only what was asked for
            6. Use minimal emojis (1-2 max if needed)
            7. Format: clear, scannable, quick to read
            
            Example:
            Question: "show my orders"
            Response: "• ORD123: Laptop - Delivered
                      • ORD456: Phone - Pending"
            
            Format now:
            """
            
            response = self.model.generate_content(formatting_prompt)
            formatted_response = response.text.strip()
            
            return formatted_response
            
        except Exception as e:
            print(f"Error formatting response: {e}")
            # Fallback to original response if formatting fails
            return bot_response
    
    def is_available(self):
        """Check if Gemini formatting is available"""
        return self.model is not None
