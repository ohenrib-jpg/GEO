import requests

response = requests.post(
    "http://localhost:8080/completion",
    json={
        "prompt": """<|im_start|>system
Tu es un expert géopolitique.<|im_end|>
<|im_start|>user
Résume en 2 phrases la situation actuelle au Moyen-Orient.<|im_end|>
<|im_start|>assistant
""",
        "max_tokens": 100,
        "temperature": 0.7,
        "stop": ["<|im_end|>"]
    }
)

print("Statut:", response.status_code)
result = response.json()
print("Réponse:", result.get('content', 'ERREUR'))