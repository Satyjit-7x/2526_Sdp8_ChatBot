import requests
import json

def test_order_query():
    url = "http://localhost:5001/api/chat"
    
    # Emulate the frontend sending orders context
    orders = [
      { "orderId": 'ORD001', "product": 'Mobile', "date": '2023-10-03', "status": 'Delivered' },
      { "orderId": 'ORD002', "product": 'Headphones', "date": '2023-09-15', "status": 'Shipped' },
      { "orderId": 'ORD003', "product": 'Wireless Charger', "date": '2023-08-21', "status": 'Returned' },
      { "orderId": 'ORD004', "product": 'Smartwatch', "date": '2023-07-02', "status": 'Delivered' },
    ]
    
    query = "where is my return order?"
    
    payload = {
        "message": query,
        "orders": orders
    }
    
    print(f"Query: {query}")
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"Bot Reply: {data['reply']}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_order_query()
