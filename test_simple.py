import re

def test_re_access():
    print("Testing re module access...")
    
    # Test 1: Basic re usage
    try:
        pattern = r'ord\d+'
        test_string = "ORD123"
        match = re.search(pattern, test_string)
        print(f"✅ Basic re.search: {match.group(0) if match else 'No match'}")
    except Exception as e:
        print(f"❌ Basic re.error: {e}")
    
    # Test 2: Simulate the problematic scenario
    try:
        def problematic_function():
            import re  # This should use global re
            pattern = r'ord\d+'
            test_string = "ORD123"
            return re.search(pattern, test_string)
        
        result = problematic_function()
        print(f"✅ Function with local import: {result.group(0) if result else 'No match'}")
    except Exception as e:
        print(f"❌ Function with local import error: {e}")

if __name__ == "__main__":
    test_re_access()
