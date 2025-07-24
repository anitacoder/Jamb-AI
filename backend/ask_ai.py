# test_api.py
import requests
import json
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv() 

API_BASE_URL = 'http://127.0.0.1:8000' 
ASK_ENDPOINT = f"{API_BASE_URL}/ask"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

def check_health():
    """Checks the health endpoint of the FastAPI API."""
    print(f"Checking API health at {HEALTH_ENDPOINT}...")
    try:
        response = requests.get(HEALTH_ENDPOINT)
        response.raise_for_status()
        print("API Health Check:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print(f"\nError: Could not connect to the FastAPI server at {API_BASE_URL}.")
        print("Please ensure your `app.py` is running (e.g., `uvicorn app:app --reload`).")
    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred during health check: {http_err}")
        print(f"Response content: {response.text}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during health check: {e}")

def ask_jamb_ai(question: str, custom_intro: Optional[str] = None):
    """
    Sends a question to the JAMB AI Assistant API and prints the response.
    """
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "question": question
    }
    if custom_intro:
        payload["custom_intro"] = custom_intro

    print(f"Sending question: '{question}' to {ASK_ENDPOINT}")
    try:
        response = requests.post(ASK_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status() 
        data = response.json()

        print("\n--- AI Assistant Response ---")
        print("Answer:")
        print(data.get("answer", "No answer provided."))


    except requests.exceptions.ConnectionError:
        print(f"\nError: Could not connect to the FastAPI server at {API_BASE_URL}.")
        print("Please ensure your `app.py` is running (e.g., `uvicorn app:app --reload`).")
    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
        print("This might indicate an issue with the backend API itself.")
    except json.JSONDecodeError:
        print(f"\nError: Could not decode JSON response from API.")
        print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    print("--- Starting API Tests ---")
    check_health()
    print("\n" + "="*30 + "\n")

    questions_to_ask = [
        "What are the requirements for Medicine and Surgery at University of Ibadan?",
        "Tell me about the JAMB use of English syllabus.",
        "Who was a prominent figure in Nigerian pre-colonial history?",
        "What is the maximum JAMB score?",
        "What are the available courses for candidates applying for engineering?",
        "When is the next JAMB registration closing date?",
        "Who are you?", 
        "What is the establishment date of JAMB?",
        "Who is the current registrar of JAMB?"
    ]

    for i, q in enumerate(questions_to_ask):
        print(f"\n========== QUESTION {i+1} ==========")
        ask_jamb_ai(q)
        print("\n" + "="*30 + "\n")

    ask_jamb_ai("What is the minimum age for JAMB registration?", custom_intro="Hello, my dear student. Here is the answer:")