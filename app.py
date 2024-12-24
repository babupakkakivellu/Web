from flask import Flask, request, jsonify, render_template
import os
import logging
from drive_uploader import upload_to_drive  # Ensure this function is implemented correctly

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.ppt'}

def allowed_file(filename):
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload_form.html')
    elif request.method == 'POST':
        # Validate file and title
        if 'file' not in request.files or 'title' not in request.form:
            return jsonify({'error': 'Invalid request'}), 400
        
        file = request.files['file']
        title = request.form['title']
        
        if file and allowed_file(file.filename):
            # Preserve file extension
            _, file_extension = os.path.splitext(file.filename)
            updated_filename = f"{title}{file_extension}"

            # Save the file temporarily
            temp_path = os.path.join('uploads', updated_filename)
            os.makedirs('uploads', exist_ok=True)
            try:
                file.save(temp_path)
                logging.info(f"File saved temporarily: {temp_path}")
                
                # Upload to Google Drive
                drive_file_id = upload_to_drive(temp_path, updated_filename, updated_filename)
                
                # Clean up temporary file
                os.remove(temp_path)
                logging.info(f"Temporary file removed: {temp_path}")

                if drive_file_id:
                    return jsonify({'message': 'Upload successful', 'title': updated_filename, 'drive_file_id': drive_file_id})
                else:
                    return jsonify({'error': 'Failed to upload to Google Drive'}), 500
            except Exception as e:
                logging.error(f"Error during file processing: {e}")
                return jsonify({'error': 'An error occurred during upload'}), 500
        else:
            return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
