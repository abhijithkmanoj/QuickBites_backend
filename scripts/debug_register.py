import sys
sys.path.append('.')
from app.main import app
from fastapi.testclient import TestClient
client=TestClient(app)
user_payload={"name":"Test User","email":"testuser@example.com","password":"Password123","phone":"1234567890"}
resp=client.post('/api/v1/auth/register', json=user_payload)
print('status',resp.status_code)
try:
    import json
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print('text',resp.text)
