"""
Test script for the signup endpoint.
Run this locally to test the signup functionality.
"""
import requests
import json

# Test configuration
API_URL = "http://localhost:8000/api/auth/signup"

# Test data
test_user = {
    "email": "test12345@example.com",
    "password": "testpass123",
    "name": "Test User"
}

def test_signup():
    """Test the signup endpoint."""
    print("Testing signup endpoint...")
    print(f"URL: {API_URL}")
    print(f"Request body: {json.dumps(test_user, indent=2)}")
    print("-" * 60)

    try:
        response = requests.post(
            API_URL,
            json=test_user,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 201:
            print("\n✅ SUCCESS: User created successfully!")
            data = response.json()
            print(f"Token (first 50 chars): {data['token'][:50]}...")
            print(f"User ID: {data['user']['id']}")
            print(f"User Email: {data['user']['email']}")
        else:
            print(f"\n❌ FAILED: Status code {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to the API.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_signup()
