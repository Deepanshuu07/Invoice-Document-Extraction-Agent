import os
from dotenv import load_dotenv
from google import genai

# Load the API key from .env into the environment
load_dotenv()

# Create a client using the key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Send a simple prompt
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="In one sentence, what is an invoice?"
)

print(response.text)