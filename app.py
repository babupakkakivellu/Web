from flask import Flask, request, jsonify, render_template
import os
from drive_uploader import upload_to_drive

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'title' not in request.form:
        return jsonify({'error': 'Invalid request'}), 400

    file = request.files['file']
    title = request.form['title']

    if file and allowed_file(file.filename):
        _, file_extension = os.path.splitext(file.filename)
        updated_filename = f"{title}{file_extension}"

        temp_path = os.path.join('uploads', updated_filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(temp_path)

        drive_file_id = upload_to_drive(temp_path, updated_filename, updated_filename)
        os.remove(temp_path)

        if drive_file_id:
            return jsonify({'message': 'Upload successful', 'title': updated_filename})
        else:
            return jsonify({'error': 'Failed to upload to Google Drive'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Only PDF, DOCX, and PPT are allowed.'}), 400



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
