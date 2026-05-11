import requests
import json

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"query": "hello", "top_k": 1},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
