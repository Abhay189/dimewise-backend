# import requests
# from datetime import datetime 

# data = {
#     'username': 'secure_pass',
#     'email': 'secure_pass@.gmail.com',
#     'first_name': 'Abhay',
#     'last_name': 'Sharma',
#     'password': '123123',
#     'account_type': 'card',
#     'balance' : 223

# }

# response = requests.post('http://127.0.0.1:5000/accounts/add', json=data)
# if response.status_code == 201:
#     rr = response.json()
#     print(rr['message'])
# else:
#     print("Error:", response.json().get('message'))


import requests
import json
from datetime import datetime

# Replace this URL with the actual URL where your Flask app is running.
# If you're running locally on the default port: http://localhost:5000
url = 'http://localhost:5000/transaction/delete'

# Sample data for the transaction
data = {
    'username': 'secure_pass',
    'email': 'secure_pass@.gmail.com',
    'first_name': 'Abhay',
    'last_name': 'Sharma',
    'account_type': 'checking',
    'amount': 100.00,
    'timestamp': "2024-01-22T12:39:09",
    'description': 'Grocery shopping'
}

# Convert the Python dictionary to a JSON string
data_json = json.dumps(data)

# Set the appropriate headers. 'Content-Type' is often necessary to ensure
# the server interprets the incoming data as JSON.
headers = {
    'Content-Type': 'application/json'
}

# Send the POST request with the JSON data
response = requests.delete(url, data=data_json, headers=headers)

# Print the response from the server
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.json()}")