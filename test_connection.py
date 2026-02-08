import requests
import time

def check_backend():
    url = "http://localhost:5001/api/chat"
    payload = {"message": "hello"}
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("Backend is up and running!")
            return True
        else:
            print(f"Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Backend not reachable yet.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    for i in range(10):
        if check_backend():
            break
        time.sleep(2)
