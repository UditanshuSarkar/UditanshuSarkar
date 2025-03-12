import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Upload folder for storing files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'py'}

# Create an in-memory 'database' for users (to keep things simple)
users = {}

# Utility function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to register new users
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        if username in users:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        # Create a folder for the user to upload files
        user_folder = os.path.join(UPLOAD_FOLDER, username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        users[username] = {'password': password, 'files': []}
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Route to login users
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username not in users or users[username]['password'] != password:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('login'))

        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# Route to logout users
@app.route('logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Route to show the dashboard and upload files
@app.route('dashboard.html', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_folder = os.path.join(UPLOAD_FOLDER, username)

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if len(os.listdir(user_folder)) >= 10:
                flash('You can only upload up to 10 files!', 'danger')
            else:
                file.save(os.path.join(user_folder, filename))
                users[username]['files'].append(filename)
                flash('File uploaded successfully!', 'success')

    files = users[username]['files']
    return render_template('dashboard.html', files=files)

# Route to run a Python file
@app.route('/run/<filename>')
def run_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_folder = os.path.join(UPLOAD_FOLDER, username)

    if filename not in users[username]['files']:
        flash('File not found!', 'danger')
        return redirect(url_for('dashboard'))

    file_path = os.path.join(user_folder, filename)
    try:
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        output = result.stdout + "\n" + result.stderr
    except Exception as e:
        output = str(e)

    return render_template('dashboard.html', files=users[username]['files'], output=output)

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)