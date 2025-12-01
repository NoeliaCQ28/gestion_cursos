import google.generativeai as genai
import os

GOOGLE_API_KEY = "AIzaSyDq6g8Oz__UjTaWGNV44lQn8br_rCfpN_E"
genai.configure(api_key=GOOGLE_API_KEY)

model_name = 'gemini-3-pro-image-preview'
# Try with and without 'models/' prefix if needed, but usually without is fine.
# Let's try the exact name from the list first.

print(f"Testing generation with {model_name}...")
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello, are you working?")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Failed with {model_name}: {e}")
    
    # Fallback test
    print("Trying fallback models...")
    for m in ['models/gemini-3-pro-image-preview', 'gemini-2.5-computer-use-preview-10-2025']:
        try:
            print(f"Testing {m}...")
            model = genai.GenerativeModel(m)
            response = model.generate_content("Hello")
            print(f"Success with {m}!")
            break
        except Exception as inner_e:
            print(f"Failed with {m}: {inner_e}")
