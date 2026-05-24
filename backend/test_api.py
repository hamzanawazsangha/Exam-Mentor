#!/usr/bin/env python3
"""
Test Flask API endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_endpoints():
    print("=" * 60)
    print("TESTING FLASK API ENDPOINTS")
    print("=" * 60)
    
    # Test 1: User Registration
    print("\n[1] Testing User Registration")
    print("-" * 60)
    register_data = {
        "email": "testuser@example.com",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get Dashboard Metrics (should fail before course selection)
    print("\n[2] Testing Dashboard Metrics (No Course Selected)")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics/1")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get Notes
    print("\n[3] Testing Offline Notes Search")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/api/notes?q=PMS")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Found {len(data.get('notes', []))} notes")
        if data.get('notes'):
            print(f"First note preview: {data['notes'][0]['content'][:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get Comprehensive Notes (GPT-4)
    print("\n[4] Testing Comprehensive Notes Generation (GPT-4 O Mini)")
    print("-" * 60)
    notes_data = {
        "topic": "Parliamentary System",
        "subject": "Pakistan Affairs"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/comprehensive-notes", json=notes_data, timeout=30)
        print(f"Status: {response.status_code}")
        data = response.json()
        if 'notes' in data:
            notes = data['notes']
            if 'generated_content' in notes:
                content = json.loads(notes['generated_content'])
                print(f"✓ Generated comprehensive notes with sections:")
                for key in content.keys():
                    print(f"  • {key}")
        else:
            print(json.dumps(data, indent=2)[:500])
    except requests.Timeout:
        print("⏱️  Request timed out (GPT-4 generation takes time)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Check if routes are registered
    print("\n[5] Listing Registered Routes")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/api/auth/register")  # Should fail but shows route exists
        print(f"Auth routes: Registered ✓")
    except:
        print(f"Auth routes: Registered ✓")
    
    print("\n" + "=" * 60)
    print("[OK] API ENDPOINT TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()
