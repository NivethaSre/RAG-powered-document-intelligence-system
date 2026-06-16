from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Get API key
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

# Initialize Groq client
client = Groq(api_key=api_key)

messages = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant."
    }
]

print("Chatbot started! Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=1024
    )

    assistant_reply = response.choices[0].message.content

    print(f"\nBot: {assistant_reply}\n")

    messages.append({
        "role": "assistant",
        "content": assistant_reply
    })