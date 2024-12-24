from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

def upload_to_drive(file_path, title, original_filename):
    try:
        # Load credentials
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
        service = build("drive", "v3", credentials=creds)

        # File metadata without Google Workspace conversion
        file_metadata = {
            "name": title,
        }

        # Detect MIME type of the file
        mime_type = MediaFileUpload(file_path).mimetype

        # Upload file
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        uploaded_file = service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()

        return uploaded_file.get("id")
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        return None
