#!/usr/bin/env python
"""
Test script for the Bitcoin Indicator Dashboard API.
This script tests the connection to the backend API and verifies that it returns valid data.
"""

import sys
import requests
import json
import argparse

def test_api(port=5001):
    """Test the connection to the backend API."""
    url = f"http://localhost:{port}/api/indicators"
    
    print(f"Testing connection to {url}...")
    
    try:
        # Make the API request
        response = requests.get(url, timeout=5)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("✅ Connection successful!")
            
            # Parse the JSON response
            data = response.json()
            
            # Check if the response contains the expected data
            if 'indicators' in data and 'lastUpdate' in data:
                print("✅ Response contains expected data structure")
                
                # Check if indicators contain expected fields
                indicators = data['indicators']
                expected_indicators = ['rsi', 'stochRsi', 'mfi', 'crsi', 'williamsR', 'rvi', 'adaptiveRsi']
                missing_indicators = [ind for ind in expected_indicators if ind not in indicators]
                
                if not missing_indicators:
                    print("✅ All expected indicators are present")
                else:
                    print(f"❌ Missing indicators: {', '.join(missing_indicators)}")
                
                # Print a formatted version of the response
                print("\nResponse data:")
                print(json.dumps(data, indent=2))
                
                return True
            else:
                print("❌ Response is missing expected data structure")
                print("\nActual response:")
                print(json.dumps(data, indent=2))
                return False
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {url}")
        print("   Make sure the backend server is running.")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error: The request to {url} timed out")
        print("   The server might be overloaded or not responding.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test the Bitcoin Indicator Dashboard API')
    parser.add_argument('--port', type=int, default=5001, help='Port number of the backend server')
    args = parser.parse_args()
    
    success = test_api(args.port)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
