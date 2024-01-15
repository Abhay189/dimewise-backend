import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Fetch the service account key JSON file contents
cred = credentials.Certificate('./dimewise-6477c-firebase-adminsdk-7smhu-772c7e4761.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dimewise-6477c-default-rtdb.firebaseio.com/'
})