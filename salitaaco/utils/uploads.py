import mimetypes
import uuid

IMAGE_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
}


def base_mime(mime):
    """'audio/webm;codecs=opus' -> 'audio/webm'"""
    return (mime or "").split(";")[0].strip().lower()


def random_upload_name(mime):
    """
    A file name for a stored upload. Uploads never keep the name the browser
    sent: the name is random and the extension follows the content type.
    """
    mime = base_mime(mime)
    extension = MIME_EXTENSIONS.get(mime) or mimetypes.guess_extension(mime) or ""
    return f"{uuid.uuid4().hex}{extension}"
