import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import mimetypes

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def upload_to_drive(file_path, title, original_filename):
    try:
        # Load credentials
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
        service = build("drive", "v3", credentials=creds)

        # Determine file MIME type
        mime_type = mimetypes.guess_type(file_path)[0]

        # Set file metadata and upload
        file_metadata = {"name": title}
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        uploaded_file = service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()

        return uploaded_file.get("id")
    except Exception as e:
        # Log the error details
        logging.error(f"Failed to upload {original_filename} to Google Drive: {e}")
        print(f"Error: {e}")  # Optional: For console output during debugging
        return None
