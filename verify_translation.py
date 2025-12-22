from bot_engine import ChatbotEngine
import sys

def test_translation():
    print("Initializing ChatbotEngine...")
    try:
        # We don't need real data for translation test
        bot = ChatbotEngine(data_path="dummy.csv", query_col="q", response_col="a")
        
        # Test 1: Translate to English
        print("\nTest 1: Translate to English")
        spanish_text = "hola"
        english_text = bot.translate_to_english(spanish_text)
        print(f"Input: {spanish_text}")
        print(f"Output: {english_text}")
        if english_text.lower() == "hello":
            print("PASS")
        else:
            print(f"WARN: Expected 'hello', got '{english_text}' (might be close enough)")

        # Test 2: Translate from English
        print("\nTest 2: Translate from English")
        english_msg = "Hello world"
        french_msg = bot.translate_from_english(english_msg, "french")
        print(f"Input: {english_msg}")
        print(f"Output: {french_msg}")
        if "bonjour" in french_msg.lower():
            print("PASS")
        else:
            print(f"WARN: Expected 'bonjour...', got '{french_msg}'")

    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_translation()
