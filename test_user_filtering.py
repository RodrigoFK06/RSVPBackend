#!/usr/bin/env python3
"""
Test script to verify user filtering functionality in the RSVP backend.
This script will:
1. Register two different users
2. Create RSVP sessions for each user
3. Verify that each user only sees their own sessions
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def register_user(email, password, full_name):
    """Register a new user"""
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })
    return response

def login_user(email, password):
    """Login and get access token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def create_rsvp(token, topic):
    """Create an RSVP session"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/rsvp", 
                           headers=headers,
                           json={"topic": topic})
    return response

def list_rsvp_sessions(token):
    """List user's RSVP sessions"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/rsvp", headers=headers)
    return response

def main():
    print("🔧 Testing User Filtering in RSVP Backend")
    print("=" * 50)
    
    # Test users
    user1_email = "testuser1@example.com"
    user2_email = "testuser2@example.com"
    password = "testpass123"
    
    try:
        # Test server connectivity first
        print("0. Testing server connectivity...")
        try:
            response = requests.get(f"{BASE_URL}/docs", timeout=5)
            print(f"   Server status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Server not reachable: {e}")
            return
        
        # Register users
        print("1. Registering users...")
        reg1 = register_user(user1_email, password, "Test User 1")
        reg2 = register_user(user2_email, password, "Test User 2")
        
        print(f"   User 1 registration: {reg1.status_code}")
        if reg1.status_code != 201:
            print(f"      Response: {reg1.text}")
            
        print(f"   User 2 registration: {reg2.status_code}")
        if reg2.status_code != 201:
            print(f"      Response: {reg2.text}")
        
        # Login users
        print("\n2. Logging in users...")
        token1 = login_user(user1_email, password)
        token2 = login_user(user2_email, password)
        
        print(f"   User 1 token: {'✅ SUCCESS' if token1 else '❌ FAILED'}")
        print(f"   User 2 token: {'✅ SUCCESS' if token2 else '❌ FAILED'}")
        
        if not token1 or not token2:
            print("❌ Failed to get tokens, aborting test")
            return
        
        # Create RSVP sessions for each user
        print("\n3. Creating RSVP sessions...")
        rsvp1 = create_rsvp(token1, "Mathematics basics")
        rsvp2 = create_rsvp(token2, "Science fundamentals")
        
        print(f"   User 1 RSVP creation: {rsvp1.status_code}")
        if rsvp1.status_code != 201:
            print(f"      Response: {rsvp1.text}")
            
        print(f"   User 2 RSVP creation: {rsvp2.status_code}")
        if rsvp2.status_code != 201:
            print(f"      Response: {rsvp2.text}")
        
        if rsvp1.status_code == 201:
            rsvp1_data = rsvp1.json()
            print(f"   User 1 RSVP ID: {rsvp1_data.get('id', 'N/A')}")
        
        if rsvp2.status_code == 201:
            rsvp2_data = rsvp2.json()
            print(f"   User 2 RSVP ID: {rsvp2_data.get('id', 'N/A')}")
        
        # Test user filtering
        print("\n4. Testing user filtering...")
        
        # User 1 should only see their sessions
        sessions1 = list_rsvp_sessions(token1)
        print(f"   User 1 sessions list: {sessions1.status_code}")
        if sessions1.status_code != 200:
            print(f"      Response: {sessions1.text}")
        
        if sessions1.status_code == 200:
            sessions1_data = sessions1.json()
            print(f"   User 1 session count: {len(sessions1_data)}")
            for session in sessions1_data:
                print(f"     - {session.get('topic', 'N/A')} (ID: {session.get('id', 'N/A')})")
        
        # User 2 should only see their sessions
        sessions2 = list_rsvp_sessions(token2)
        print(f"   User 2 sessions list: {sessions2.status_code}")
        if sessions2.status_code != 200:
            print(f"      Response: {sessions2.text}")
        
        if sessions2.status_code == 200:
            sessions2_data = sessions2.json()
            print(f"   User 2 session count: {len(sessions2_data)}")
            for session in sessions2_data:
                print(f"     - {session.get('topic', 'N/A')} (ID: {session.get('id', 'N/A')})")
        
        # Verify isolation
        print("\n5. Verification Results:")
        if sessions1.status_code == 200 and sessions2.status_code == 200:
            sessions1_data = sessions1.json()
            sessions2_data = sessions2.json()
            
            # Check if sessions are properly isolated
            user1_topics = [s.get('topic') for s in sessions1_data]
            user2_topics = [s.get('topic') for s in sessions2_data]
            
            print(f"   ✅ User isolation: {'PASS' if 'Mathematics basics' in user1_topics and 'Science fundamentals' in user2_topics else 'FAIL'}")
            print(f"   ✅ No cross-contamination: {'PASS' if 'Science fundamentals' not in user1_topics and 'Mathematics basics' not in user2_topics else 'FAIL'}")
        
        print("\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
