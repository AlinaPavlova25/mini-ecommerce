import os
import io
import time
from werkzeug.utils import secure_filename
from PIL import Image
try:
    import pillow_avif
except ImportError:
    pass

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'avif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
MAX_IMAGE_SIZE = (1920, 1920)
MAX_BANNER_SIZE = (3840, 3840)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file, upload_folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time() * 1000))
        name, ext = os.path.splitext(filename)

        file.stream.seek(0)
        raw = file.stream.read()

        try:
            image = Image.open(io.BytesIO(raw))
            image.load()
        except Exception:
            return None

        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        filename = f"{name}_{timestamp}.jpg"
        filepath = os.path.join(upload_folder, filename)

        image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        image.save(filepath, 'JPEG', optimize=True, quality=95)

        return filename
    return None

def delete_product_image(filename, upload_folder):
    if filename:
        filepath = os.path.join(upload_folder, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

def save_banner_image(file, upload_folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time() * 1000))
        name, ext = os.path.splitext(filename)

        file.stream.seek(0)
        raw = file.stream.read()

        try:
            image = Image.open(io.BytesIO(raw))
            image.load()
        except Exception:
            return None

        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        filename = f"{name}_{timestamp}.jpg"
        filepath = os.path.join(upload_folder, filename)

        image.thumbnail(MAX_BANNER_SIZE, Image.Resampling.LANCZOS)
        image.save(filepath, 'JPEG', optimize=True, quality=100, subsampling=0)

        return filename
    return None

def save_product_video(file, upload_folder):
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            return None
        name = secure_filename(file.filename.rsplit('.', 1)[0])
        timestamp = str(int(time.time() * 1000))
        filename = f"{name}_{timestamp}.{ext}"
        filepath = os.path.join(upload_folder, filename)
        file.stream.seek(0)
        file.save(filepath)
        return filename
    return None
