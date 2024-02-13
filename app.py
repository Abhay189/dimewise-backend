import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from flask import Flask, request , jsonify ,send_file
from flask_cors import CORS
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import pandas as pd
import bcrypt

# ---- Flask App Initialization ----

app = Flask(__name__)
CORS(app) 


cred = credentials.Certificate('./dimewise-6477c-firebase-adminsdk-7smhu-772c7e4761.json')

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dimewise-6477c-default-rtdb.firebaseio.com/'
})

#  ---- Helper Methods ----

def datetime_data_extractor(date_str):
    # Convert the input string to a datetime object assuming ISO format
    timestamp = datetime.fromisoformat(date_str)
    
    # Extract the data from the datetime object and format it as a string
    year = timestamp.strftime('%Y')
    month = timestamp.strftime('%m')
    day = timestamp.strftime('%d')
    time = timestamp.strftime('%H:%M:%S')

    # Return a tuple containing the extracted year, month, day, and time as strings
    return (year, month, day, time)

def initialize_account_type(username,account_type,balance):
    try:
        # Check if the provided username is valid, return error message if not
        if not user_is_valid(username):
            return {'success': False ,"message": "Invalid Username"}
        
        # Check if the account type already exists for the user, return error if it does
        if not new_resource_valid(username,account_type):
            return {'success': False ,"message": "Account Type already Exists"}

        # Prepare the account data with the specified account type and balance
        accounts_data = {
            'accounts' : {
                account_type : balance
            }
        }
        user_ref = db.reference(f"/users/{username}")
        user_ref.update(accounts_data)

        return {'success': True ,"message": "Account data set successfully"}
    except Exception as e:
        print("An error occurred:", e)
        return {"success": False ,"message": "Error occured while adding Account Resource"}

def update_account_balance(username, account_type, add_amount):
    try: 
        # Check if the provided username is valid, return error if not
        if not user_is_valid(username):
            return {'success': False, "message": "Invalid Username"}
        
        # Check if the account type does not exist for the user, return error if it doesn't
        if new_resource_valid(username, account_type):
            return {'success': False, "message": "Account Type does not exist"}

        account_ref = db.reference(f"/users/{username}/accounts/{account_type}")
        curr_account_balance = account_ref.get()

        # Prepare the updated account data with the new balance after adding the specified amount
        accounts_data = {
            'accounts': {
                account_type: curr_account_balance + add_amount
            }
        }

        user_ref = db.reference(f"/users/{username}")
        user_ref.update(accounts_data)

        return {'success': True, "message": "Account balance updated successfully"}
    except Exception as e:
        print("An error occurred:", e)
        return {"success": False, "message": "Error occurred while updating Account Resource"}

def get_monthly_spending_data(username, year, start_month, end_month):
    # Check if the end month is before the start month, which is an invalid range
    if end_month < start_month:
        return None 
    
    monthly_data = [] 
    
    # Iterate over each month in the range from start_month to end_month, inclusive
    for month in range(start_month, end_month + 1):
        month_str = str(month).zfill(2)  # Convert month to a 2-digit string, adding a leading zero if needed
        
        monthly_ref = db.reference(f"/users/{username}/transactions/{year}/{month_str}/monthly_spending")
        monthly_snap = monthly_ref.get()
        
        # If spending data exists for the month, add it to the monthly_data list
        if monthly_snap:
            monthly_data.append(monthly_snap)
        else:
            # If there's no data for the month, append 0 to represent no spending
            monthly_data.append(0)
    
    return monthly_data

def generate_monthly_spending_graph(username, year, start_month, end_month):
    # Create a DataFrame from the monthly spending data for the given range
    months = list(range(start_month, end_month + 1)) 
    monthly_spending = get_monthly_spending_data(username, year, start_month, end_month) 
    data = {'Months': months, 'Monthly Spending': monthly_spending} 
    df = pd.DataFrame(data) 
    
    # Set up the visual appearance of the plot
    plt.figure(figsize=(10, 6)) 
    sns.barplot(x='Months', y='Monthly Spending', data=df, palette='viridis')  
    plt.title('Monthly Spending')  
    plt.xlabel('Month') 
    plt.ylabel('Monthly Spending')  
    plt.xticks(rotation=45)  
    plt.tight_layout()  
    
    # Define the directory and path where the plot image will be saved
    plot_dir = f"{username}/"
    os.makedirs(plot_dir, exist_ok=True)  
    plot_path = f"{plot_dir}monthly_spending_graph.png" 
    plt.savefig(plot_path) 
    plt.close() 
    
    # Return the path where the plot image was saved
    return plot_path 

def get_yearly_spending_data(username, start_year, end_year):
    # Check if the end year is before the start year, which is an invalid range
    if end_year < start_year:
        return None 
    
    yearly_data = [] 
    
    # Iterate over each year in the inclusive range from start_year to end_year
    for year in range(start_year, end_year + 1):
        yearly_ref = db.reference(f"/users/{username}/transactions/{year}/yearly_spending")
        yearly_snap = yearly_ref.get()

        # If spending data exists for the year, add it to the yearly_data list
        if yearly_snap:
            yearly_data.append(yearly_snap)
        else:
            # If there's no data for the year, append 0 to represent no spending
            yearly_data.append(0)
    
    return yearly_data

def generate_yearly_spending_graph(username, start_year, end_year):
    # Create a DataFrame from the yearly spending data for the given range
    years = list(range(start_year, end_year + 1))  
    yearly_spending = get_yearly_spending_data(username, start_year, end_year)  
    data = {'Year': years, 'Yearly Spending': yearly_spending} 
    df = pd.DataFrame(data) 

    # Set up the visual appearance of the plot
    plt.figure(figsize=(10, 6)) 
    sns.barplot(x='Year', y='Yearly Spending', data=df, palette='viridis')  
    plt.title('Yearly Spending')  
    plt.xlabel('Year')  
    plt.ylabel('Yearly Spending')  
    plt.xticks(rotation=45)  
    plt.tight_layout()  

    # Define the directory and path where the plot image will be saved
    plot_dir = f"{username}/" 
    os.makedirs(plot_dir, exist_ok=True)  
    plot_path = f"{plot_dir}yearly_spending_graph.png"  
    plt.savefig(plot_path) 
    plt.close() 

    # Return the path where the plot image was saved
    return plot_path 

def encode_email(email):
    # Converts '.' to ',' in an email string to circumvent database key restrictions
    return email.replace('.', ',')

def decode_email(encoded_email):
    # Reverts ',' back to '.' in an encoded email string to get the original email.
    return encoded_email.replace(',', '.')

def valid_signup(username, encoded_email):
    try:
        username_path = f"/users/{username}"
        email_path = f"/emails/{encoded_email}"

        username_ref = db.reference(username_path)
        email_ref = db.reference(email_path)
        
        username_snap = username_ref.get()
        email_snap = email_ref.get()

        # If a snapshot exists for the username, indicate the username is already taken
        if username_snap:
            return {"success": False, "message": "Username already exists"}
        
        # If a snapshot exists for the email, indicate the email is already in use
        elif email_snap:
            return {"success": False, "message": "Email already exists"}
        
        # If no issues are found with the username and email, return a success message
        return {"success": True, "message": "Valid sign-in data"}
        
    except Exception as e:
        print("An error occurred:", e)
        return {"success": False, "message": "A database error occurred, please try again later."}
    
def user_is_valid(username):
    user_ref = db.reference(f"/users/{username}")
    user_snap = user_ref.get()

    # Return False if no data is found (user does not exist), otherwise True
    if not user_snap:
        return False
    else:
        return True

def new_resource_valid(username,account_type):
    # Verifies if a specific account type for a given user doesn't exist in the database.
    try:
        account_path = f"/users/{username}/accounts/{account_type}"
        account_ref = db.reference(account_path)
        account_snap = account_ref.get()

        # If data is retrieved, the account type exists, return False
        if account_snap:
            return False 
        # If no data is retrieved, the account type does not exist, return True
        else:
            return True 
    except Exception as e:
        print("An error occurred:", e)
        return False 

def update_yearly_monthly_spending(username,year,month,amount):
    yearly_ref = db.reference(f"/users/{username}/transactions/{year}")
    curr_yearly_val = yearly_ref.child('yearly_spending').get()

    monthly_ref = db.reference(f"/users/{username}/transactions/{year}/{month}")
    curr_monthly_val = monthly_ref.child('monthly_spending').get()

    # Update yearly spending value with the new amount
    if not curr_yearly_val:
        curr_yearly_val = amount
    else:
        curr_yearly_val += amount

    # Update monthly spending value with the new amount
    if curr_monthly_val is None:
        curr_monthly_val = amount
    else:
        curr_monthly_val += amount

    # Update the database with the new yearly and monthly spending value
    yearly_ref.update({'yearly_spending': curr_yearly_val})
    monthly_ref.update({'monthly_spending': curr_monthly_val})

def update_account_post_transaction(username,account_type,amount):
    account_type_path = f'/users/{username}/accounts/{account_type}'
    account_type_ref = db.reference(account_type_path)
    account_type_check = account_type_ref.get()

    # If the account exists, update its balance with the new amount
    if account_type_check:
        update_account_balance(username, account_type, amount)
    # If the account does not exist, initialize it with the specified amount
    else:
        initialize_account_type(username, account_type, amount)


#  ---- Flask Application Endpoints ----

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        try:
            # Extract essential information
            userdata = request.json
            email = userdata.get('email')
            username = userdata.get('username')
            userdata.pop('username')  # Remove username for separate handling
            
            # Secure password handling
            userdata['password'] = bcrypt.hashpw(userdata.get('password').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Prepare data for database insertion
            encoded_email = encode_email(email)  # Encode email for key compatibility
            userdata['email'] = encoded_email

            # Validate signup details
            signup_validation = valid_signup(username, encoded_email)
            if not signup_validation['success']:
                return jsonify(signup_validation), 400 

            # Database updates for user and email
            user_ref = db.reference('/users')
            user_ref.child(username).set(userdata)
            email_ref = db.reference(f"/emails")
            email_ref.update({encoded_email: username})

            return jsonify({"success": True, "message": "User created successfully"}), 201
        except Exception as e:
            # Handle unexpected errors during signup
            print("An error occurred:", e)
            return jsonify({"success": False, "message": "Error occurred while signing up"}), 400
    else:
        # Respond to incorrect request methods
        return jsonify({"success": False, "message": "Invalid request method"}), 400
    
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            # Retrieve login credentials from request
            username = request.json.get('username')
            password = request.json.get('password')
            
            # Access user data from database
            user_path = f"/users/{username}"
            user_ref = db.reference(user_path)
            user_data = user_ref.get()

            # Validate credentials and return success message if valid
            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data.get('password').encode('utf-8')):
                return jsonify({'success': True, "message": "Successfully logged in"}), 201
            else:
                # Handle invalid login credentials
                return jsonify({'success': False, "message": "Invalid username or password"}), 404
        except Exception as e:
            # Handle unexpected errors during login process
            print("An error occurred:", e)
            return jsonify({"success": False, "message": "Error occurred while logging in"}), 400
        
    else:
        # Respond to non-POST requests to this endpoint
        return jsonify({"success": False, "message": "Invalid request method"}), 400

    
@app.route('/accounts/add', methods=['POST'])
def addAccountResource():
    # Handle POST requests for adding account resources
    if request.method == 'POST':
        # Extract account details from the request
        username = request.json.get('username')
        account_type = request.json.get('account_type')
        balance = request.json.get('balance', 0)  # Default balance to 0 if not provided

        # Attempt to initialize the account with the provided details
        return_val = initialize_account_type(username, account_type, balance)

        # Return response based on the success of the account initialization
        if return_val['success']:
            # Account successfully added
            return jsonify(return_val), 201
        else:
            # Account addition failed
            return jsonify(return_val), 400
    else:
        # Handle incorrect request methods with an error message
        return jsonify({'success': False, "message": "Invalid request method"}), 400


@app.route('/transaction/add', methods=['POST'])
def addTransaction():
    # Handle POST requests for adding transactions
    if request.method == 'POST':
        # Extract transaction details from the request
        username = request.json.get('username')
        account_type = request.json.get('account_type')
        amount = request.json.get('amount')
        timestamp = request.json.get('timestamp')
        description = request.json.get('description')

        # Extract the date and time components from the timestamp
        year, month, day, time = datetime_data_extractor(timestamp)

        # Update the account balance and spending records
        update_account_post_transaction(username, account_type, amount)
        update_yearly_monthly_spending(username, year, month, amount)

        # Prepare transaction data for storage
        transaction_data = {
            'account_type': account_type,
            'amount': amount,
            'description': description
        }

        # Construct the database path for storing the transaction
        transaction_path = f"/users/{username}/transactions/{year}/{month}/{day}"
        transaction_ref = db.reference(transaction_path)
        # Store the transaction data at the specified path and time
        transaction_ref.child(time).update(transaction_data)

        # Return a success message for the added transaction
        return jsonify({"message": "Transaction successfully added"}), 201
    else:
        # Handle incorrect request methods with an error message
        return jsonify({"message": "Invalid request method"}), 400

@app.route('/transaction/delete', methods=['DELETE'])
def deleteTransaction():
    # Handle DELETE requests to remove a specific transaction
    if request.method == 'DELETE':
        # Extract required identifiers from the request
        username = request.json.get('username')
        timestamp = request.json.get('timestamp')

        # Break down the timestamp into its components
        year, month, day, time = datetime_data_extractor(timestamp)

        # Construct the path to the specific transaction in the database
        transaction_path = f"/users/{username}/transactions/{year}/{month}/{day}"
        transaction_ref = db.reference(transaction_path)
        # Check if the transaction exists
        transactions_snap = transaction_ref.child(time).get()

        if transactions_snap:
            # Delete the transaction if it exists
            transaction_ref.child(time).delete()
            return jsonify({"message": "Transaction successfully deleted"}), 200
        else:
            # Inform the client if the transaction does not exist
            return jsonify({"message": "Transaction does not exist"}), 404
        
    else:
        # Respond to incorrect request methods
        return jsonify({"message": "Invalid request method"}), 400


@app.route('/transaction/get/graph/yearly', methods=['GET'])
def getTransactionYearlyGraph():
    # Handle GET requests to retrieve a graph of yearly transactions
    if request.method == 'GET':
        # Extract user and year range from the request
        username = request.json.get('username')
        start_year = request.json.get('start_year')
        end_year = request.json.get('end_year')

        # Generate the path to the yearly spending graph
        plot_path = generate_yearly_spending_graph(username, start_year, end_year)
        
        # Serve the generated graph as an image
        return send_file(plot_path, mimetype='image/png'), 201
    else:
        # Handle requests with invalid methods
        return jsonify({"message": "Invalid request method"}), 400

    
@app.route('/transaction/get/graph/monthly', methods=['GET'])
def getTransactionMonthlyGraph():
    # Handle GET requests to retrieve a graph of monthly transactions
    if request.method == 'GET':
        # Extract user details and the specific month range from the request
        username = request.json.get('username')
        year = request.json.get('year')
        start_month = request.json.get('start_month')
        end_month = request.json.get('end_month')

        # Generate the path to the monthly spending graph
        plot_path = generate_monthly_spending_graph(username, year, start_month, end_month)
        
        # Serve the generated graph as an image
        return send_file(plot_path, mimetype='image/png'), 201
    else:
        # Respond to non-GET requests with an error message
        return jsonify({"message": "Invalid request method"}), 400



if __name__ == '__main__':
    app.run(debug=True)