"""Image processing utilities for album artwork."""

from io import BytesIO
from typing import Optional

from PIL import Image


def resize_artwork(image_data: bytes, target_size: int = 500) -> bytes:
    """
    Resize artwork to target size while maintaining aspect ratio.

    Args:
        image_data: Original image bytes
        target_size: Target dimension (will create square image)

    Returns:
        Resized image as JPEG bytes
    """
    img = Image.open(BytesIO(image_data))

    # Convert to RGB if necessary (for PNG with alpha, etc.)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create white background for transparency
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Get current dimensions
    width, height = img.size

    # Calculate new dimensions
    if width > height:
        new_width = target_size
        new_height = int(height * (target_size / width))
    else:
        new_height = target_size
        new_width = int(width * (target_size / height))

    # Resize with high quality
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # If not square, pad to square
    if new_width != new_height:
        # Create square canvas
        square_img = Image.new('RGB', (target_size, target_size), (255, 255, 255))

        # Center the image
        x = (target_size - new_width) // 2
        y = (target_size - new_height) // 2
        square_img.paste(img, (x, y))
        img = square_img

    # Save to bytes
    output = BytesIO()
    img.save(output, format='JPEG', quality=90, optimize=True)
    return output.getvalue()


def convert_to_jpeg(image_data: bytes, quality: int = 90) -> bytes:
    """
    Convert image to JPEG format.

    Args:
        image_data: Original image bytes
        quality: JPEG quality (1-100)

    Returns:
        Image as JPEG bytes
    """
    img = Image.open(BytesIO(image_data))

    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    return output.getvalue()


def get_image_dimensions(image_data: bytes) -> tuple[int, int]:
    """
    Get dimensions of an image.

    Args:
        image_data: Image bytes

    Returns:
        Tuple of (width, height)
    """
    img = Image.open(BytesIO(image_data))
    return img.size


def is_valid_image(image_data: bytes) -> bool:
    """
    Check if image data is valid.

    Args:
        image_data: Image bytes

    Returns:
        True if valid image, False otherwise
    """
    try:
        img = Image.open(BytesIO(image_data))
        img.verify()  # Verify it's a valid image
        return True
    except Exception:
        return False


def create_thumbnail(image_data: bytes, size: int = 100) -> bytes:
    """
    Create a thumbnail for preview.

    Args:
        image_data: Original image bytes
        size: Thumbnail size

    Returns:
        Thumbnail as JPEG bytes
    """
    img = Image.open(BytesIO(image_data))

    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Create thumbnail (maintains aspect ratio)
    img.thumbnail((size, size), Image.Resampling.LANCZOS)

    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    return output.getvalue()


def crop_to_square(image_data: bytes) -> bytes:
    """
    Crop image to square (center crop).

    Args:
        image_data: Original image bytes

    Returns:
        Cropped image as JPEG bytes
    """
    img = Image.open(BytesIO(image_data))

    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')

    width, height = img.size

    # Determine crop box
    if width > height:
        # Landscape - crop sides
        left = (width - height) // 2
        top = 0
        right = left + height
        bottom = height
    else:
        # Portrait - crop top/bottom
        left = 0
        top = (height - width) // 2
        right = width
        bottom = top + width

    img = img.crop((left, top, right, bottom))

    output = BytesIO()
    img.save(output, format='JPEG', quality=90, optimize=True)
    return output.getvalue()
