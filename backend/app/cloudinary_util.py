import os
import uuid
import logging
from typing import Optional
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
from app.config import settings

logger = logging.getLogger("khetsaathi.cloudinary")

# Configure cloudinary if credentials are provided
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

def upload_image(file: UploadFile, folder: str = "khetsaathi_equipment") -> Optional[str]:
    """
    Uploads an image to Cloudinary (if configured) or stores locally in backend/uploads/.
    Returns the accessible URL for the image.
    """
    if not file or not file.filename:
        return None

    # Check if Cloudinary is configured
    if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
        try:
            logger.info("Uploading image to Cloudinary...")
            result = cloudinary.uploader.upload(
                file.file,
                folder=folder,
                resource_type="image"
            )
            return result.get("secure_url")
        except Exception as e:
            logger.warning(f"Cloudinary upload failed: {e}. Falling back to local upload.")

    # Local storage fallback
    try:
        ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Ensure uploads folder exists
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        dest_path = os.path.join(uploads_dir, unique_filename)
        file.file.seek(0)
        with open(dest_path, "wb") as buffer:
            buffer.write(file.file.read())
            
        return f"/uploads/{unique_filename}"
    except Exception as e:
        logger.error(f"Failed to save image locally: {e}")
        return None
