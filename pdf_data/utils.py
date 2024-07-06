# utils.py
import fitz  # PyMuPDF
from PIL import Image
import io

from django.core.mail import  EmailMultiAlternatives
from django.template.loader import render_to_string
import mimetypes
from django.conf import settings


def generate_pdf_thumbnail(pdf_path, target_size=824 * 580):
    try:
        document = fitz.open(pdf_path)
        page = document.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
        
        img = Image.open(io.BytesIO(pix.tobytes("png"))) 
        img_data = compress_image(img, target_size)
        
        return img_data
    except Exception as e:
        return None

def compress_image(image, target_size):
    """Compress the image to be less than the target size."""
    img_byte_arr = io.BytesIO()
    quality = 95
    image.save(img_byte_arr, format='PNG', quality=quality)
    
    while img_byte_arr.tell() > target_size and quality > 10:
        img_byte_arr = io.BytesIO() 
        quality -= 5 
        image.save(img_byte_arr, format='PNG', quality=quality)
        
    return img_byte_arr.getvalue()


def send_custom_email(to_email, subject, mail, files=None):
    """
    Sends a custom email with multiple attachments.

    :param to_email: Recipient's email address
    :param subject: Subject of the email
    :param mail: Body of the email
    :param files: List of file data (bytes) to be attached (optional)
    """
    
    try:
        # Create an EmailMultiAlternatives object
        email = EmailMultiAlternatives(
            subject=subject,
            body=mail,
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
        )

        # Attach the files if provided
        if files:
            for idx, file_data in enumerate(files, start=1):
                filename = f"attachment_{idx}.dat"  # Generating a generic filename
                mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                email.attach(filename, file_data, mimetype)

        # Send the email
        email.send()
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False