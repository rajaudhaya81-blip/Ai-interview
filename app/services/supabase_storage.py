import os
import requests
import mimetypes
from flask import current_app

class SupabaseStorageService:
    @staticmethod
    def _get_credentials():
        url = current_app.config.get('SUPABASE_URL')
        key = current_app.config.get('SUPABASE_KEY')
        return url, key

    @classmethod
    def ensure_bucket_exists(cls, bucket_name):
        url, key = cls._get_credentials()
        if not url or not key:
            return False
        
        # Strip trailing slash from URL if present
        url = url.rstrip('/')
        create_url = f"{url}/storage/v1/bucket"
        headers = {
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json"
        }
        payload = {
            "id": bucket_name,
            "name": bucket_name,
            "public": True,
            "file_size_limit": 10485760,  # 10MB
            "allowed_mime_types": None
        }
        
        try:
            # Check if bucket exists
            list_url = f"{url}/storage/v1/bucket/{bucket_name}"
            get_res = requests.get(list_url, headers=headers)
            if get_res.status_code == 200:
                return True
            
            # Create bucket
            res = requests.post(create_url, headers=headers, json=payload)
            return res.status_code == 200
        except Exception as e:
            print(f"Error ensuring bucket {bucket_name} exists: {e}")
            return False

    @classmethod
    def upload_file(cls, bucket, file_bytes, filepath, content_type=None):
        """
        Uploads a file to Supabase Storage, falling back to local file storage if Supabase is unavailable.
        Returns the public URL of the uploaded file.
        """
        url, key = cls._get_credentials()
        
        # Deduce content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filepath)
            if not content_type:
                content_type = "application/octet-stream"

        if url and key:
            # Clean URL
            url = url.rstrip('/')
            
            # Make sure bucket exists first
            cls.ensure_bucket_exists(bucket)
            
            upload_url = f"{url}/storage/v1/object/{bucket}/{filepath}"
            headers = {
                "Authorization": f"Bearer {key}",
                "apikey": key,
                "x-upsert": "true",
                "Content-Type": content_type
            }
            
            try:
                res = requests.post(upload_url, headers=headers, data=file_bytes)
                if res.status_code in [200, 201]:
                    # Return the public URL
                    return f"{url}/storage/v1/object/public/{bucket}/{filepath}"
                else:
                    print(f"Supabase upload failed: {res.status_code} - {res.text}. Falling back to local storage.")
            except Exception as e:
                print(f"Supabase upload error: {e}. Falling back to local storage.")
        
        # Local Fallback
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], bucket)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Replace subdirectories in filepath if any to avoid file path errors
        local_filename = filepath.replace('/', '_')
        local_path = os.path.join(upload_dir, local_filename)
        
        try:
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            # Return relative local path accessible via Flask static routes
            return f"/static/uploads/{bucket}/{local_filename}"
        except Exception as e:
            print(f"Failed to write file locally: {e}")
            return None
