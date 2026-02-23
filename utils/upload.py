import os
import time
from werkzeug.utils import secure_filename
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = (800, 800)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file, upload_folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        timestamp = str(int(time.time() * 1000))
        name, ext = os.path.splitext(filename)
        
        image = Image.open(file)
        
        # RGBA (PNG with transparency) -> RGB (JPEG compatible)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Her zaman JPEG olarak kaydet
        filename = f"{name}_{timestamp}.jpg"
        filepath = os.path.join(upload_folder, filename)
        
        image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        image.save(filepath, 'JPEG', optimize=True, quality=85)
        
        return filename
    return None

def delete_product_image(filename, upload_folder):
    if filename:
        filepath = os.path.join(upload_folder, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
