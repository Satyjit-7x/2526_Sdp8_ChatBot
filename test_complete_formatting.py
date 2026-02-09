import requests
import json
import time
import re

def test_complete_formatting():
    """Test all formatting scenarios with live API"""
    
    base_url = "http://localhost:5001"
    
    test_scenarios = [
        {
            "name": "Show Full Order List",
            "message": "show my full order list",
            "expected_type": "order_list"
        },
        {
            "name": "Show Orders",
            "message": "show my orders", 
            "expected_type": "order_list"
        },
        {
            "name": "Create Mobile Order",
            "message": "i want to order mobile",
            "expected_type": "order_creation"
        },
        {
            "name": "Create Smartphone Order",
            "message": "create order for smartphone",
            "expected_type": "order_creation"
        },
        {
            "name": "Single Order Status",
            "message": "what is the status of my order ORD999?",
            "expected_type": "single_order"
        },
        {
            "name": "Delete Pending Order",
            "message": "delete pending order",
            "expected_type": "clarification"
        }
    ]
    
    print("🌐 Testing Complete Smart Formatting")
    print("=" * 60)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 Test {i}: {scenario['name']}")
        print(f"💬 Message: {scenario['message']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": scenario['message']},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                formatted_reply = data.get("reply", "")
                
                print(f"🤖 Response:")
                print(formatted_reply)
                
                # Analyze response format
                lines = formatted_reply.split('\n')
                print(f"📊 Format Analysis:")
                print(f"   • Lines: {len(lines)}")
                print(f"   • Has bullets: {'•' in formatted_reply}")
                print(f"   • Has orders: {len(re.findall(r'ORD\d+', formatted_reply))} orders found")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to server")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
        time.sleep(1)  # Small delay between requests

if __name__ == "__main__":
    test_complete_formatting()
