from langfuse import Langfuse
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = Langfuse()
    print("Attributes:", dir(client))
    if hasattr(client, 'trace'):
        print("Trace method exists.")
    else:
        print("Trace method MISSING.")
except Exception as e:
    print(f"Init Error: {e}")
