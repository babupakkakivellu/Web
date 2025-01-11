from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Upload, Admin
from drive_uploader import upload_to_drive
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.ppt', '.pptx'}

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin/mark-completed/<int:upload_id>', methods=['POST'])
@login_required
def mark_completed(upload_id):
    try:
        upload = Upload.query.get_or_404(upload_id)
        upload.status = 'completed'
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload_form.html')

    if request.method == 'POST':
        if 'file' not in request.files or 'title' not in request.form:
            return jsonify({'error': 'Invalid request'}), 400

        file = request.files['file']
        title = request.form['title']

        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Upload to Google Drive
            drive_file_id = upload_to_drive(file_path, title, filename)

            if drive_file_id:
                # Save to database
                upload = Upload(
                    title=title,
                    drive_file_id=drive_file_id,
                    original_filename=filename,
                    file_size=os.path.getsize(file_path),
                    mime_type=file.content_type
                )
                db.session.add(upload)
                db.session.commit()

                # Clean up local file
                os.remove(file_path)

                return jsonify({
                    'message': 'Upload successful',
                    'title': title,
                    'drive_file_id': drive_file_id
                })
            else:
                return jsonify({'error': 'Failed to upload to Google Drive'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid username or password.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    uploads = Upload.query.order_by(Upload.upload_date.desc()).paginate(page=page, per_page=per_page)
    return render_template('admin_dashboard.html', uploads=uploads)

@app.route('/admin/update_prints/<int:upload_id>', methods=['POST'])
@login_required
def update_prints(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    prints = request.form.get('prints', type=int)

    if prints is not None and prints >= 0:
        upload.prints_required = prints
        upload.status = 'processing' if prints > 0 else 'pending'
        db.session.commit()
        flash('Print count updated successfully.', 'success')
    else:
        flash('Invalid print count.', 'error')

    return redirect(url_for('admin_dashboard'))

def create_admin_user():
    with app.app_context():
        admin = Admin.query.filter_by(username=os.getenv('ADMIN_USERNAME')).first()
        if not admin:
            admin = Admin(
                username=os.getenv('ADMIN_USERNAME'),
                password=generate_password_hash(os.getenv('ADMIN_PASSWORD'))
            )
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(debug=True)
