import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from flask import Flask, request , jsonify ,send_file
from flask_cors import CORS
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)
CORS(app) 

# Fetch the service account key JSON file contents
cred = credentials.Certificate('./dimewise-6477c-firebase-adminsdk-7smhu-772c7e4761.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dimewise-6477c-default-rtdb.firebaseio.com/'
})

def safe_date_converter(date_str):
    timestamp = datetime.fromisoformat(date_str)
    return timestamp.strftime('%Y%m%dT%H%M%S%f')

def add_account_type(username,account_type,curr_acc_balance):
    accounts_path = '/users/'+username+'/accounts'
    
    user_ref = db.reference(accounts_path)

    data = {
        account_type : curr_acc_balance
    }

    user_ref.update(data)

def add_account_balance(username,account_type, add_amount):
    accounts_path = '/users/'+username+'/accounts'
    
    user_ref = db.reference(accounts_path)

    curr_balance = user_ref.child(account_type).get()

    data = {
        account_type : add_amount + curr_balance
    }

    user_ref.update(data)

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


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        print(request.json)
        userdata = request.json
        email = userdata.get('email')
        first_name = userdata.get('first_name')
        last_name = userdata.get('last_name')
        password = userdata.get('password')
        username = userdata.get('username')

        all_users_ref = db.reference('/users')
        all_users_data = all_users_ref.get()

        for user_dat in all_users_data.values():
            if user_dat.get('email') == email:
                return jsonify({"message": "Email already exists"}), 400


        user_check_ref = db.reference('/users/'+username)
        user_check = user_check_ref.get()

        if user_check:
            return jsonify({"message": "Username already exists"}), 400
        

        userref = db.reference('/users')

        data = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'password': password
        }
        userref.child(username).set(data)

        return jsonify({"message": "User created successfully"}), 201
    
    else:
        return jsonify({"message": "Invalid request method"}), 400
    
@app.route('/login', methods=['POST'])
def login():

    print(request.json)
    username = request.json.get('username')
    password = request.json.get('password')

    user_path = '/users/'+username
    
    user_ref = db.reference(user_path)
    user_data = user_ref.get()
    if user_data and user_data['password'] == password:
        return jsonify({'success': True ,"message": "Successfully logged in"}), 201
    else: 
        return jsonify({'success': False ,"message": "Invalid username or password"}), 404
        

@app.route('/accounts/add', methods=['POST'])
def addAccount():
    if request.method == 'POST':
        print(request.json)
        username = request.json.get('username')
        account_type = request.json.get('account_type')
        balance = request.json.get('balance')

        check_user = '/users/'+username
        check_ref = db.reference(check_user)
        check_snapshot = check_ref.get()

        print(check_snapshot)

        if not check_snapshot:
            return jsonify({"message": "Invalid Username"}), 400

        user_path = '/users/'+username
        
        user_ref = db.reference(user_path)

        data = {
            'accounts' : {
                account_type : balance
            }
        }

        user_ref.update(data)

        return jsonify({"message": "Accounts data set successfully"}), 201
    
    else:
        return jsonify({"message": "Invalid request method"}), 400


@app.route('/transaction/add', methods=['POST'])
def addTransaction():
    if request.method == 'POST':
        print(request.json)
        username = request.json.get('username')
        account_type = request.json.get('account_type')
        amount = request.json.get('amount')
        timestamp = request.json.get('timestamp')
        description = request.json.get('description')

        safe_datetime_str = safe_date_converter(timestamp)

        account_type_path = '/users/'+username + '/accounts/' + account_type
        account_type_ref = db.reference(account_type_path)
        account_type_check = account_type_ref.get()

        if account_type_check:
            add_account_balance(username,account_type,amount)
        else:
            add_account_type(username,account_type,amount)

        data = {
            'account_type' : account_type,
            'amount' : amount,
            'description' : description
        }

        #update yearly_spending , monthly_spending and daily spending. 
        yearly_ref = db.reference(f"/users/{username}/transactions/{safe_datetime_str[:4]}")
        curr_yearly_val = yearly_ref.child('yearly_spending').get()

        # Yearly 
        if curr_yearly_val is None:
            curr_yearly_val = amount
        else:
            curr_yearly_val += amount

        yearly_ref.update({'yearly_spending': curr_yearly_val})

        # Monthly : 
        monthly_ref = db.reference(f"/users/{username}/transactions/{safe_datetime_str[:4]}/{safe_datetime_str[4:6]}")
        curr_montly_val = monthly_ref.child('monthly_spending').get()

        # Yearly 
        if curr_montly_val is None:
            curr_montly_val = amount
        else:
            curr_montly_val += amount

        monthly_ref.update({'monthly_spending': curr_montly_val})

        transaction_path = f"/users/{username}/transactions/{safe_datetime_str[:4]}/{safe_datetime_str[4:6]}/{safe_datetime_str[6:8]}"
        transaction_ref = db.reference(transaction_path)

        transaction_ref.child(safe_datetime_str[8:]).update(data)

        return jsonify({"message": "Transaction successfully added"}), 201
    
    else:
        return jsonify({"message": "Invalid request method"}), 400

@app.route('/transaction/delete', methods=['DELETE'])
def deleteTransaction():
    if request.method == 'DELETE':
        print(request.json)
        username = request.json.get('username')
        timestamp = request.json.get('timestamp')

        safe_datetime_str = safe_date_converter(timestamp)

        transactions_path = '/users/'+username+ '/transactions'
        transactions_ref = db.reference(transactions_path)
        transactions_snap = transactions_ref.child(safe_datetime_str).get()

        if transactions_snap:  
            print("data to be deleted : ",transactions_ref.child(safe_datetime_str).get())
            transactions_ref.child(safe_datetime_str).delete()
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
        
        # Return the file path in the response
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
        
        # Return the file path in the response
        return send_file(plot_path, mimetype='image/png'), 201
    else:
        return jsonify({"message": "Invalid request method"}), 400


if __name__ == '__main__':
    app.run(debug=True)