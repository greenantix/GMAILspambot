#!/usr/bin/env python3
"""
Test script to verify Gemini API integration
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini():
    print("🤖 Gemini API Test")
    print("=" * 50)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return
    
    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Test with a simple prompt
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        test_prompt = """Respond with exactly this JSON format, no extra text:
{"test": "success", "timestamp": "2024-06-10", "model": "gemini"}"""
        
        print("📤 Sending test prompt to Gemini...")
        response = model.generate_content(test_prompt)
        
        print("📥 Raw Gemini response:")
        print("-" * 30)
        print(response.text)
        print("-" * 30)
        
        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response.text.strip())
            print("✅ JSON parsing successful!")
            print(f"📊 Parsed response: {parsed}")
            
            # Check if it looks like a real response
            if parsed.get('test') == 'success':
                print("✅ Gemini is responding correctly - NOT mocked")
            else:
                print("⚠️ Unexpected response format")
                
        except json.JSONDecodeError:
            print("❌ Response is not valid JSON")
            print("💡 Gemini might be adding extra text or formatting")
            
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        if "API_KEY" in str(e):
            print("💡 Check if your API key is valid and has Gemini access")
        elif "quota" in str(e).lower():
            print("💡 API quota exceeded - wait or check billing")

if __name__ == "__main__":
    test_gemini()