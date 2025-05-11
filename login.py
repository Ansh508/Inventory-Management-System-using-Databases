from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib

app = Flask(__name__) # initialize the flask
app.secret_key = 'inventory'  # Change this to a random secret key

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row  # This allows us to use column names
    return conn

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        batch_number = request.form['batch_number']
        password = request.form['password']
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        officer = conn  .execute('SELECT * FROM inventory_officers WHERE batch_number = ? AND password = ?',(batch_number, hashed_password)).fetchone()
        conn.close()

        if officer:
            session['batch_number'] = officer['batch_number']
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid login. Please try again.'
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'batch_number' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', batch_number=session['batch_number'])

# Logout route
@app.route('/logout')
def logout():
    session.pop('batch_number', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)