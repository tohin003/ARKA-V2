from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Error: OPENAI_API_KEY not found.")
    exit(1)

client = OpenAI(api_key=api_key)

try:
    print("Fetching available models...")
    models = client.models.list()
    
    gpt_models = [m.id for m in models.data if "gpt" in m.id]
    gpt_models.sort()
    
    print("\n--- Available GPT Models ---")
    for model in gpt_models:
        print(model)
        
    print("\n--- Check for 5.2 ---")
    five_point_two = [m.id for m in models.data if "5.2" in m.id or "5-2" in m.id]
    if five_point_two:
        print("FOUND:", five_point_two)
    else:
        print("No models with '5.2' or '5-2' found.")

except Exception as e:
    print(f"Error fetching models: {e}")
