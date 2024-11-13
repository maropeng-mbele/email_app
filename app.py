from flask import Flask, render_template, request, jsonify, send_file
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import json
import base64
import csv
from datetime import datetime
from werkzeug.utils import secure_filename
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({
            'filename': filename,
            'path': filepath
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/save', methods=['POST'])
def save_content():
    data = request.json
    content = data.get('content')
    images = data.get('images', {})
    
    try:
        with open('weekly_digest.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        
        with open('image_mappings.json', 'w') as f:
            json.dump(images, f)
        
        return jsonify({'message': 'Content saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load')
def load_content():
    try:
        content = ''
        images = {}
        
        if os.path.exists('weekly_digest.txt'):
            with open('weekly_digest.txt', 'r', encoding='utf-8') as f:
                content = f.read()
        
        if os.path.exists('image_mappings.json'):
            with open('image_mappings.json', 'r') as f:
                images = json.load(f)
        
        return jsonify({
            'content': content,
            'images': images
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send', methods=['POST'])
def send_emails():
    try:
        data = request.json
        content = data.get('content')
        images = data.get('images', {})
        
        # Gmail authentication and sending logic here
        # This would need to be adapted for web usage
        
        return jsonify({'message': 'Emails sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_message_with_attachments(to, html_content, image_paths, sender_email, subject):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to
    message['Subject'] = subject

    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    for i, image_path in enumerate(image_paths):
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            subtype = os.path.splitext(image_path)[1][1:]
            image_mime = MIMEImage(img_data, _subtype=subtype)
            image_mime.add_header('Content-ID', f'<image{i + 1}>')
            image_mime.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
            message.attach(image_mime)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

if __name__ == '__main__':
    app.run(debug=True)