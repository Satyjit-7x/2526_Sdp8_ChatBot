import requests
import json

def test_order_queries():
    """Test specific order number queries"""
    
    base_url = "http://localhost:5001"
    
    order_queries = [
        "ORD999",
        "what is ORD999?", 
        "tell me about ORD999",
        "show order ORD999",
        "ORD999 details",
        "status of ORD999",
        "ORD789",
        "what is ORD789?"
    ]
    
    print("🔍 Testing Order Number Queries")
    print("=" * 50)
    
    for i, query in enumerate(order_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                
                print(f"🤖 Response:")
                print(reply)
                print(f"📊 Length: {len(reply)} chars")
                
                # Check if it contains order info
                if "ORD" in reply.upper():
                    print("✅ Contains order info")
                else:
                    print("❌ No order info found")
                    
                # Check if it's unusually long
                if len(reply) > 200:
                    print("⚠️ Response seems unusually long")
                elif len(reply) < 50:
                    print("✅ Response seems appropriately short")
                
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_order_queries()
