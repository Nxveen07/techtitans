import requests
import json

url = "http://127.0.0.1:8001/api/v1/content/analyze"
payload = {
    "content": "The moon is made of green cheese.",
    "type": "text"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=20)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
