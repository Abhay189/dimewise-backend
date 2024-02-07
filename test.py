import requests
from datetime import datetime

# timestamp = datetime.now().isoformat()

# def reverse_to_isoformat(custom_format_str):
#     # Parse the custom format string back to a datetime object
#     datetime_obj = datetime.strptime(custom_format_str, '%Y%m%dT%H%M%S%f')
    
#     # Convert the datetime object back to an ISO format string
#     iso_format_str = datetime_obj.isoformat()
    
#     return iso_format_str

# # timestamp1 = reverse_to_isoformat('20240207T000832677124')

data = {
    'username' : 'brendawood',
    'account_type' : 'savings',
    'amount' : 150,
    # 'timestamp' : timestamp,
    'description' : 'Food and grocery',
    'year':2002,
    'start_month': 1,
    'end_month' : 12,
}

response = requests.get('http://127.0.0.1:5000/transaction/get/graph/monthly', json=data)
# Check if the request was successful
if response.status_code == 201:
    # Save the image file received in response
    with open('monthly_spending_graph_client.png', 'wb') as f:
        f.write(response.content)
    print("Image saved successfully")
else:
    print("Error:", response.json())

# print(response.status_code)


# import requests
# import random
# import string
# from datetime import datetime

# # Function to generate random transaction data
# def generate_random_transaction():
#     username = "brendawood"  # Replace with the actual username
#     account_type = random.choice(["savings", "checking" , "debit"])  # Choose randomly between savings and checking
#     amount = round(random.uniform(10, 1000), 2)  # Random amount between 10 and 1000
#     month = str(random.randint(1, 12)).zfill(2)  # Random month, padded with zero if necessary
#     day = str(random.randint(1, 28)).zfill(2)  # Random day, padded with zero if necessary
#     year = str(random.randint(1989, 2028)).zfill(2)  # Random day, padded with zero if necessary
#     hour = str(random.randint(0, 23)).zfill(2)  # Random hour, padded with zero if necessary
#     minute = str(random.randint(0, 59)).zfill(2)  # Random minute, padded with zero if necessary
#     second = str(random.randint(0, 59)).zfill(2)  # Random second, padded with zero if necessary
#     timestamp = f"{year}-{month}-{day}T{hour}:{minute}:{second}"  # Random timestamp within the year 2024
#     description = ''.join(random.choices(string.ascii_letters, k=10))  # Random description

#     return {
#         "username": username,
#         "account_type": account_type,
#         "amount": amount,
#         "timestamp": timestamp,
#         "description": description
#     }

# # Function to add a transaction using the provided endpoint
# def add_transaction(transaction_data):
#     url = "http://127.0.0.1:5000/transaction/add"  # Replace with your actual API endpoint
#     response = requests.post(url, json=transaction_data)
#     return response.json()

# # Add 100 transactions
# for _ in range(10):
#     transaction_data = generate_random_transaction()
#     response = add_transaction(transaction_data)
#     print(response)  # Print response from the server