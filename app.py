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

app = Flask(__name__)
CORS(app) 


cred = credentials.Certificate('./dimewise-6477c-firebase-adminsdk-7smhu-772c7e4761.json')

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dimewise-6477c-default-rtdb.firebaseio.com/'
})

def safe_date_converter(date_str):
    timestamp = datetime.fromisoformat(date_str)
    year = timestamp.strftime('%Y')
    month = timestamp.strftime('%m')
    day = timestamp.strftime('%d') 
    time = timestamp.strftime('%H:%M:%S')

    return (year,month,day,time)

def initialize_account_type(username,account_type,balance):
    try: 
        if not user_is_valid(username):
            return {'success': False ,"message": "Invalid Username"}
        
        if not new_resource_valid(username,account_type):
            return {'success': False ,"message": "Account Type already Exists"}

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

def update_account_balance(username,account_type, add_amount):
    try: 
        if not user_is_valid(username):
            return {'success': False ,"message": "Invalid Username"}
        
        if new_resource_valid(username,account_type):
            return {'success': False ,"message": "Account Type does not exists"}

        account_ref = db.reference(f"/users/{username}/accounts/{account_type}")
        curr_account_balance = account_ref.get()

        accounts_data = {
            'accounts' : {
                account_type : curr_account_balance + add_amount
            }
        }
        user_ref = db.reference(f"/users/{username}")
        user_ref.update(accounts_data)

        return {'success': True ,"message": "Account data set successfully"}
    except Exception as e:
        print("An error occurred:", e)
        return {"success": False ,"message": "Error occured while updating Account Resource"}

def get_monthly_spending_data(username,year,start_month,end_month):
    if end_month < start_month :
        return None
    
    monthly_data = []
    for month in range(start_month,end_month+1):
        month_str = str(month).zfill(2)  # Pad month with leading zero if necessary
        monthly_ref = db.reference(f"/users/{username}/transactions/{year}/{month_str}/monthly_spending")
        monthly_snap = monthly_ref.get()
        if monthly_snap:
            monthly_data.append(monthly_snap)
        else:
            monthly_data.append(0)
        print(f"/users/{username}/transactions/{year}/{month_str}/monthly_spending")
    
    return monthly_data

def generate_monthly_spending_graph(username, year, start_month, end_month):
    # Create a DataFrame from the data
    months = list(range(start_month, end_month+1))
    monthly_spending = get_monthly_spending_data(username, year, start_month, end_month)
    data = {'Months': months, 'Monthly Spending': monthly_spending}
    df = pd.DataFrame(data)
    
    # Create a bar plot using Seaborn
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Months', y='Monthly Spending', data=df, palette='viridis')
    plt.title('Monthly Spending')
    plt.xlabel('Month')
    plt.ylabel('Monthly Spending')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot as an image file
    plot_dir = f"{username}/"
    os.makedirs(plot_dir, exist_ok=True)  # Create the directory if it doesn't exist
    plot_path = f"{plot_dir}monthly_spending_graph.png"
    plt.savefig(plot_path)
    plt.close()  # Close the plot to free up memory
    
    return plot_path

def get_yearly_spending_data(username,start_year,end_year):
    if end_year < start_year :
        return None
    
    yearly_data = []
    for year in range(start_year,end_year+1):
        yearly_ref = db.reference(f"/users/{username}/transactions/{year}/yearly_spending")
        yearly_snap = yearly_ref.get()
        if yearly_snap:
            yearly_data.append(yearly_snap)
        else:
            yearly_data.append(0)
    
    return yearly_data

def generate_yearly_spending_graph(username, start_year, end_year):
    # Create a DataFrame from the data
    years = list(range(start_year, end_year+1))
    yearly_spending = get_yearly_spending_data(username,start_year,end_year)
    data = {'Year': years, 'Yearly Spending': yearly_spending}
    df = pd.DataFrame(data)
    
    # Create a bar plot using Seaborn
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Year', y='Yearly Spending', data=df, palette='viridis')
    plt.title('Yearly Spending')
    plt.xlabel('Year')
    plt.ylabel('Yearly Spending')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot as an image file
    plot_dir = f"{username}/"
    os.makedirs(plot_dir, exist_ok=True)  # Create the directory if it doesn't exist
    plot_path = f"{plot_dir}yearly_spending_graph.png"
    plt.savefig(plot_path)
    plt.close()  # Close the plot to free up memory
    
    return plot_path

def encode_email(email):
    return email.replace('.', ',')

def decode_email(encoded_email):
    return encoded_email.replace(',', '.')

def valid_signup(username,encoded_email):
    # Db paths for username and email 
    username_path = f"/users/{username}"
    email_path = f"/emails/{encoded_email}"

    try:
        # creating db path references 
        username_ref = db.reference(username_path)
        email_ref = db.reference(email_path)
        
        # Checking if these paths exist in the db 
        username_snap = username_ref.get()
        email_snap = email_ref.get()
        if username_snap:
            return ({"success": False ,"message": "Username already exists"})
        elif email_snap : 
            return ({"success": False ,"message": "Email already exists"})
        
    except:
        return ({"success": False ,"message": "A database error occurred, please try again later."})
    
    return ({"success": True , "message": "Valid sign-in data"})

def user_is_valid(username):
    user_ref = db.reference(f"/users/{username}")
    user_snap = user_ref.get()

    if not user_snap:
        return False
    else:
        return True

def new_resource_valid(username,account_type):
    try:
        account_path = f"/users/{username}/accounts/{account_type}"
        account_ref = db.reference(account_path)
        account_snap = account_ref.get()
        if account_snap:
            return False 
        else:
            return True 
    except Exception as e:
        print("An error occurred:", e)
        return False 

def update_yearly_monthly_spending(username,year,month,amount):
    yearly_ref = db.reference(f"/users/{username}/transactions/{year}")
    curr_yearly_val = yearly_ref.child('yearly_spending').get()

    monthly_ref = db.reference(f"/users/{username}/transactions/{year}/{month}")
    curr_montly_val = monthly_ref.child('monthly_spending').get()

    if not curr_yearly_val:
        curr_yearly_val = amount
    else:
        curr_yearly_val += amount

    if curr_montly_val is None:
        curr_montly_val = amount
    else:
        curr_montly_val += amount

    yearly_ref.update({'yearly_spending': curr_yearly_val})
    monthly_ref.update({'monthly_spending': curr_montly_val})

def update_account_post_transaction(username,account_type,amount):
    account_type_path = '/users/'+username + '/accounts/' + account_type
    account_type_ref = db.reference(account_type_path)
    account_type_check = account_type_ref.get()

    if account_type_check:
        update_account_balance(username,account_type,amount)
    else:
        initialize_account_type(username,account_type,amount)


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        try:
            userdata = request.json
            email = userdata.get('email')
            username = userdata.get('username')
            userdata.pop('username')
            userdata['password'] = bcrypt.hashpw(userdata.get('password').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            encoded_email = encode_email(email)
            userdata['email'] = encoded_email

            signup_validation = valid_signup(username,encoded_email)
            if not signup_validation['success']:
                return jsonify(signup_validation), 400 

            user_ref = db.reference('/users')
            user_ref.child(username).set(userdata)

            email_ref = db.reference(f"/emails")
            email_ref.update({encoded_email:username})

            return jsonify({"success": True ,"message": "User created successfully"}), 201
        except Exception as e:
            print("An error occurred:", e)
            return jsonify({"success": False ,"message": "Error occured while signing up"}), 400
    
    else:
        return jsonify({"success": False ,"message": "Invalid request method"}), 400
    
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try: 
            username = request.json.get('username')
            password = request.json.get('password')
            
            user_path =  f"/users/{username}"
            user_ref = db.reference(user_path)
            user_data = user_ref.get()

            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data.get('password').encode('utf-8')):
                return jsonify({'success': True ,"message": "Successfully logged in"}), 201
            else: 
                return jsonify({'success': False ,"message": "Invalid username or password"}), 404
        except Exception as e:
            print("An error occurred:", e)
            return jsonify({"success": False ,"message": "Error occured while loging in"}), 400
        
    else:
        return jsonify({"success": False ,"message": "Invalid request method"}), 400
    
@app.route('/accounts/add', methods=['POST'])
def addAccountResource():
    if request.method == 'POST':
        username = request.json.get('username')
        account_type = request.json.get('account_type')
        balance = request.json.get('balance',0)

        return_val = initialize_account_type(username,account_type,balance)

        if return_val['success']:
            return jsonify(return_val), 201
        else:
            return jsonify(return_val) , 400
    
    else:
        return jsonify({'success': False ,"message": "Invalid request method"}), 400

@app.route('/transaction/add', methods=['POST'])
def addTransaction():
    if request.method == 'POST':
        username = request.json.get('username')
        account_type = request.json.get('account_type')
        amount = request.json.get('amount')
        timestamp = request.json.get('timestamp')
        description = request.json.get('description')

        year,month,day,time= safe_date_converter(timestamp)

        update_account_post_transaction(username,account_type,amount)
        update_yearly_monthly_spending(username,year,month,amount)

        transaction_data = {
            'account_type' : account_type,
            'amount' : amount,
            'description' : description
        }

        transaction_path = f"/users/{username}/transactions/{year}/{month}/{day}"
        transaction_ref = db.reference(transaction_path)
        transaction_ref.child(time).update(transaction_data)

        return jsonify({"message": "Transaction successfully added"}), 201
    
    else:
        return jsonify({"message": "Invalid request method"}), 400

@app.route('/transaction/delete', methods=['DELETE'])
def deleteTransaction():
    if request.method == 'DELETE':
        username = request.json.get('username')
        timestamp = request.json.get('timestamp')

        year,month,day,time = safe_date_converter(timestamp)

        transaction_path = f"/users/{username}/transactions/{year}/{month}/{day}"
        transaction_ref = db.reference(transaction_path)
        transactions_snap = transaction_ref.child(time).get()

        if transactions_snap:  
            transaction_ref.child(time).delete()
            return jsonify({"message": "Transaction successfully deleted"}), 200
        else:
            return jsonify({"message": "Transaction does not exist"}), 404
        
    else:
        return jsonify({"message": "Invalid request method"}), 400


@app.route('/transaction/get/graph/yearly', methods=['GET'])
def getTransactionYearlyGraph():
    if request.method == 'GET':
        username = request.json.get('username')
        start_year = request.json.get('start_year')
        end_year = request.json.get('end_year')

        plot_path = generate_yearly_spending_graph(username,start_year,end_year)
        
        return send_file(plot_path, mimetype='image/png'), 201
    else:
        return jsonify({"message": "Invalid request method"}), 400
    
@app.route('/transaction/get/graph/monthly', methods=['GET'])
def getTransactionMonthlyGraph():
    if request.method == 'GET':
        username = request.json.get('username')
        year = request.json.get('year')
        start_month = request.json.get('start_month')
        end_month = request.json.get('end_month')

        plot_path = generate_monthly_spending_graph(username,year, start_month,end_month)
        
        return send_file(plot_path, mimetype='image/png'), 201
    else:
        return jsonify({"message": "Invalid request method"}), 400


if __name__ == '__main__':
    app.run(debug=True)