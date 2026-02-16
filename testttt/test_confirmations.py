#!/usr/bin/env python3
"""
Test confirmation variations (yess, nooo, yep, nah, etc.)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_engine import ChatbotEngine

def test_confirmations():
    print("=" * 60)
    print("Testing Confirmation Variations")
    print("=" * 60)
    
    bot = ChatbotEngine()
    bot.load_model()
    bot.load_data()
    
    # Test affirmative variations
    print("\n✓ Testing Affirmative Variations")
    print("-" * 60)
    
    affirmatives = ["yess", "yesss", "yep", "yeah", "yup", "sure", "ok", "okay"]
    
    for confirmation in affirmatives:
        normalized = bot.normalize_confirmation(confirmation)
        if normalized == 'yes':
            print(f"✅ '{confirmation}' → 'yes'")
        else:
            print(f"❌ '{confirmation}' → '{normalized}' (expected 'yes')")
    
    # Test negative variations
    print("\n✓ Testing Negative Variations")
    print("-" * 60)
    
    negatives = ["nooo", "noooo", "nope", "nah", "no way"]
    
    for denial in negatives:
        normalized = bot.normalize_confirmation(denial)
        if normalized == 'no':
            print(f"✅ '{denial}' → 'no'")
        else:
            print(f"❌ '{denial}' → '{normalized}' (expected 'no')")
    
    # Test enthusiastic variations
    print("\n✓ Testing Enthusiastic/Repeated Variations")
    print("-" * 60)
    
    enthusiastic = ["YES!", "yessssss", "yes yes", "YESSSS"]
    
    for response in enthusiastic:
        normalized = bot.normalize_confirmation(response)
        if normalized == 'yes':
            print(f"✅ '{response}' → 'yes'")
        else:
            print(f"❌ '{response}' → '{normalized}' (expected 'yes')")
    
    print("\n" + "=" * 60)
    print("Confirmation Tests Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_confirmations()
