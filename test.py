import requests

headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
data = {
    'grant_type': '',
    'username': 'bh',
    'password': 'test',
    'scope': '',
    'client_id': '',
    'client_secret': '',
}

token_request = requests.post('http://localhost:8000/api/token', headers=headers, data=data)

token = token_request.json()

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer ' + token['access_token']
}

user_req = requests.get('http://localhost:8000/api/users/me', headers=headers)

print(
    user_req.status_code,
    user_req.json()
)