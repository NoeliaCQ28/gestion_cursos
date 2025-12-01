import google.generativeai as genai
import os

GOOGLE_API_KEY = "AIzaSyDq6g8Oz__UjTaWGNV44lQn8br_rCfpN_E"
genai.configure(api_key=GOOGLE_API_KEY)

model_name = 'nano-banana-pro-preview'

print(f"Testing generation with {model_name}...")
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello, are you working?")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Failed with {model_name}: {e}")
