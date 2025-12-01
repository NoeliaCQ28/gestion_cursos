import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load secrets from .streamlit/secrets.toml manually since we are running a script
# Or just use the key directly for this test script since I know it from previous turns
# But better to read it if possible. I'll just hardcode it for this quick check since I saw it in the user prompt history
# User provided: AIzaSyDq6g8Oz__UjTaWGNV44lQn8br_rCfpN_E

GOOGLE_API_KEY = "AIzaSyDq6g8Oz__UjTaWGNV44lQn8br_rCfpN_E"
genai.configure(api_key=GOOGLE_API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
