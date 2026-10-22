import mimetypes
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

IMAGE_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
# A picture a user uploads to show (a payment's screenshot, the QR code, a board's icon): still pictures only.
PICTURE_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

# A board's picture is shown at most about 76 pixels wide; this is sharp on any screen.
ICON_MAX_SIDE = 256
SHRUNK_MIME = "image/webp"

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


def shrink_picture(upload, max_side):
    """
    An uploaded picture made small enough to keep: no side longer than
    `max_side`, turned the way the camera held it, as a WEBP (which keeps a
    transparent background). A phone photo of several megabytes becomes a few
    dozen kilobytes. Returns (the file, its content type).
    """
    upload.seek(0)
    with Image.open(upload) as opened:
        image = ImageOps.exif_transpose(opened)
        image.thumbnail((max_side, max_side))
        image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")
        buffer = BytesIO()
        image.save(buffer, "WEBP", quality=85)
    return ContentFile(buffer.getvalue()), SHRUNK_MIME
