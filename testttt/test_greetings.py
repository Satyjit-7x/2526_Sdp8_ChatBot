#!/usr/bin/env python3
"""
Test greeting detection and responses
"""
import requests
import time

def test_greetings():
    print("=" * 60)
    print("Testing Greeting Detection")
    print("=" * 60)
    
    API_URL = "http://localhost:5001/api/chat"
    
    # Wait a moment to ensure server is ready
    print("\nWaiting for server to be ready...")
    time.sleep(2)
    
    greetings = [
        "hi",
        "hello",
        "hey",
        "hey there",
        "hi there",
        "good morning",
        "good afternoon",
        "good evening",
        "sup",
        "what's up",
        "howdy",
        "hello!",  # With punctuation
        "Hi!",     # Capitalized
    ]
    
    print("\n✓ Testing Various Greeting Patterns")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for greeting in greetings:
        try:
            response = requests.post(API_URL, json={"message": greeting}, timeout=5)
            if response.status_code == 200:
                reply = response.json().get("reply", "")
                # Check if it's a greeting response (not "I don't understand")
                if any(word in reply.lower() for word in ["hi", "hello", "hey", "morning", "afternoon", "evening", "help", "assist"]):
                    print(f"✅ '{greeting}' → {reply[:50]}...")
                    passed += 1
                else:
                    print(f"❌ '{greeting}' → {reply[:50]}... (not a greeting response)")
                    failed += 1
            else:
                print(f"❌ '{greeting}' → HTTP {response.status_code}")
                failed += 1
        except Exception as e:
            print(f"❌ '{greeting}' → Error: {str(e)[:50]}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Greeting Tests Complete: {passed} passed, {failed} failed")
    print("=" * 60)

if __name__ == "__main__":
    test_greetings()
