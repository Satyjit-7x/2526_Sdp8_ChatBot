import requests
import json
import time

def test_crud():
    url = "http://localhost:5001/api/chat"
    
    # 1. READ
    print("\n--- TEST 1: READ ---")
    payload = {"message": "Show me all orders"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Bot: {response.json()['reply']}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. CREATE
    print("\n--- TEST 2: CREATE ---")
    payload = {"message": "Create a new order for a Laptop"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        reply = response.json()['reply']
        print(f"Bot: {reply}")
        
        if "Are you sure" in reply:
             # Confirm
             print("Confirmation required. Sending 'yes'...")
             payload = {"message": "yes"}
             response = requests.post(url, json=payload, timeout=10)
             print(f"Bot: {response.json()['reply']}")
             
    except Exception as e:
        print(f"Error: {e}")

    # 3. VERIFY CREATE
    print("\n--- TEST 3: VERIFY CREATE ---")
    payload = {"message": "Show all orders"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Bot: {response.json()['reply']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    time.sleep(5) # Wait for server start
    test_crud()
