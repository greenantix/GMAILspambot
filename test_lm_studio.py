#!/usr/bin/env python3
"""Test LM Studio connectivity and performance"""

import requests
import time

def test_lm_studio():
    print("🧪 Testing LM Studio connectivity...")
    
    # Test 1: Check if API is responding
    try:
        response = requests.get('http://localhost:1234/v1/models', timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ API responding - {len(models.get('data', []))} models available")
            for model in models.get('data', []):
                print(f"   📱 {model.get('id')}")
        else:
            print(f"❌ API error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LM Studio API on localhost:1234")
        print("💡 Make sure LM Studio is running and a model is loaded")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Simple inference test
    print("🧪 Testing inference performance...")
    try:
        test_payload = {
            "messages": [{"role": "user", "content": "Reply with just 'OK'"}],
            "temperature": 0.1,
            "max_tokens": 5
        }
        
        start_time = time.time()
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            json=test_payload,
            timeout=10
        )
        end_time = time.time()
        
        if response.status_code == 200:
            duration = end_time - start_time
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Inference working - Response time: {duration:.2f}s")
            print(f"   🤖 Response: '{content.strip()}'")
            
            if duration > 5:
                print("⚠️  Response time is slow - consider using a smaller model")
            
            return True
        else:
            print(f"❌ Inference failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Inference timed out - model may be too large or system overloaded")
        return False
    except Exception as e:
        print(f"❌ Inference error: {e}")
        return False

if __name__ == "__main__":
    if test_lm_studio():
        print("\n🎉 LM Studio is ready for email processing!")
        print("✅ You can now restart bulk processing safely")
    else:
        print("\n❌ LM Studio is not ready")
        print("🔧 Please check LM Studio and load a model")