import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def call_ollama(model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    
    response = requests.post(OLLAMA_URL, json=payload, verify=False)
    if response.status_code == 200:
        return response.json().get("response", "")
    
    return f"Error: {response.status_code} - {response.text}"


if __name__ == "__main__":
    result = call_ollama("gemma2:2b", "Hello, how are you?")
    print(result)
