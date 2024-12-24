import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Google Drive folder ID
FOLDER_ID = '1j83pj6sIL2mfNiWFqOYbb21vvNvlTwqd'

def upload_to_drive(filepath, title, original_filename):
    """
    Upload a file to Google Drive.

    Args:
        filepath (str): Path to the local file.
        title (str): Title provided by the client.
        original_filename (str): Original file name of the uploaded file.

    Returns:
        str: File ID of the uploaded file, or None if upload fails.
    """
    try:
        # Use relative path to load token.pickle from the current directory
        token_path = os.path.join(os.path.dirname(__file__), 'token.pickle')
        
        # Load the token credentials
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

        # Build the Google Drive API service
        drive_service = build('drive', 'v3', credentials=creds)

        # Metadata for the file
        file_metadata = {
            'name': f"{title}_{original_filename}",
            'parents': [FOLDER_ID]
        }
        media = MediaFileUpload(filepath, resumable=True)

        # Upload the file
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
      
