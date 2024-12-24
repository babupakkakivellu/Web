from flask import Flask, request, jsonify, render_template
import os
from drive_uploader import upload_to_drive

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('upload_form.html')

    if 'file' not in request.files or 'title' not in request.form:
        return jsonify({'error': 'Invalid request'}), 400

    file = request.files['file']
    title = request.form['title']

    if file:
        temp_path = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(temp_path)

        drive_file_id = upload_to_drive(temp_path, title, file.filename)
        os.remove(temp_path)

        if drive_file_id:
            return jsonify({'message': 'Upload successful', 'title': title})
        else:
            return jsonify({'error': 'Failed to upload to Google Drive'}), 500
    else:
        return jsonify({'error': 'No file uploaded'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
