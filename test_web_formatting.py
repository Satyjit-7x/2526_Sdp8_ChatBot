import requests
import json

def test_web_formatting():
    """Test the web API with Gemini formatting"""
    
    base_url = "http://localhost:5001"
    
    test_questions = [
        "show my orders",
        "what is the status of my order ORD999?",
        "create order for smartphone",
        "delete pending order"
    ]
    
    print("🌐 Testing Web API with Gemini Formatting")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": question},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                formatted_reply = data.get("reply", "")
                
                print(f"🤖 Formatted Response:")
                print(formatted_reply)
                print()
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to server. Make sure app.py is running on localhost:5001")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_web_formatting()
