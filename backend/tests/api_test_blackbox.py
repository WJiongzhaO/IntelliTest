"""Quick API test script to verify all blackbox endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_get_techniques():
    """Test GET /blackbox/techniques"""
    print("\n1. Testing GET /blackbox/techniques...")
    response = requests.get(f"{BASE_URL}/blackbox/techniques")
    assert response.status_code == 200
    data = response.json()
    print(f"   ✓ Found {len(data)} techniques: {', '.join(data.keys())}")
    return True

def test_generate_all():
    """Test POST /blackbox/generate/all"""
    print("\n2. Testing POST /blackbox/generate/all...")
    
    requirement = {
        "id": "TEST001",
        "raw_text": "User age must be between 18 and 120",
        "input_fields": ["age"],
        "data_ranges": ["Age between 18 and 120"],
        "conditions": ["If age >= 18"],
        "expected_actions": ["Register user"]
    }
    
    response = requests.post(
        f"{BASE_URL}/blackbox/generate/all",
        json={"requirement": requirement, "use_llm": False},
    )
    assert response.status_code == 200
    test_cases = response.json()
    print(f"   ✓ Generated {len(test_cases)} test cases")
    
    # Count by technique
    techniques = {}
    for tc in test_cases:
        tech = tc.get('technique', 'Unknown')
        techniques[tech] = techniques.get(tech, 0) + 1
    
    print(f"   ✓ Techniques used: {techniques}")
    return True

def test_generate_with_coverage():
    """Test POST /blackbox/generate/with-coverage"""
    print("\n3. Testing POST /blackbox/generate/with-coverage...")
    
    payload = {
        "requirement": {
            "id": "TEST002",
            "raw_text": "User registration with age and membership validation",
            "input_fields": ["age", "membership_type"],
            "data_ranges": ["Age between 18 and 120"],
            "conditions": ["If age >= 65", "If membership_type is premium"],
            "expected_actions": ["Create account", "Apply discount"]
        },
        "selected_techniques": ["EP", "BVA", "DT"],
        "use_llm": False,
    }
    
    response = requests.post(f"{BASE_URL}/blackbox/generate/with-coverage", json=payload)
    assert response.status_code == 200, f"Status: {response.status_code}, Body: {response.text[:200]}"
    result = response.json()
    
    print(f"   ✓ Generated {len(result['test_cases'])} test cases")
    print(f"   ✓ Identified {len(result['coverage_items'])} coverage items")
    print(f"   ✓ Coverage: {result['coverage_report']['coverage_percentage']}%")
    return True

def test_identify_coverage_items():
    """Test POST /blackbox/coverage/identify"""
    print("\n4. Testing POST /blackbox/coverage/identify...")
    
    requirement = {
        "id": "TEST003",
        "raw_text": "Test requirement",
        "input_fields": ["field1"],
        "data_ranges": ["Range 1-100"],
        "conditions": ["If condition1"],
        "expected_actions": ["Action1"]
    }
    
    response = requests.post(f"{BASE_URL}/blackbox/coverage/identify", json=requirement)
    assert response.status_code == 200
    items = response.json()
    print(f"   ✓ Identified {len(items)} coverage items")
    
    item_types = set(item['item_type'] for item in items)
    print(f"   ✓ Item types: {', '.join(item_types)}")
    return True

def main():
    """Run all API tests."""
    print("=" * 80)
    print("IntelliTest Black-Box API Test Suite")
    print("=" * 80)
    
    tests = [
        test_get_techniques,
        test_generate_all,
        test_generate_with_coverage,
        test_identify_coverage_items,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ✗ FAILED: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n✅ All API tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
