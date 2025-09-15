from pydantic import BaseModel, Field
from typing import Literal, Optional, Union, BinaryIO, List
from enum import Enum
import base64
import mimetypes
from pathlib import Path
from loguru import logger

# =============================================================================
# CONTENT ENUMS
# =============================================================================

class ContentType(str, Enum):
    """Content types for multimodal messages"""
    TEXT = "text"
    IMAGE_URL = "image_url"
    VIDEO_URL = "video_url"
    FILE_URL = "file_url"

# =============================================================================
# CONTENT MODELS
# =============================================================================

class TextContent(BaseModel):
    """Text content item"""
    type: Literal[ContentType.TEXT] = ContentType.TEXT
    text: str = Field(..., description="Text content")

class ImageUrlObject(BaseModel):
    """Image URL object"""
    url: str = Field(..., description="Image URL or Base64 encoding. Image size limit is under 5M per image, with pixels not exceeding 6000*6000. Supports jpg, png, jpeg formats.")

class ImageContent(BaseModel):
    """Image content item"""
    type: Literal[ContentType.IMAGE_URL] = ContentType.IMAGE_URL
    image_url: ImageUrlObject = Field(..., description="Image information")
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "ImageContent":
        """Create ImageContent from a file path"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        # Read file and encode as base64
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type or not mime_type.startswith('image/'):
            # Default to common image types based on extension
            ext = file_path.suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif ext == '.png':
                mime_type = 'image/png'
            elif ext == '.gif':
                mime_type = 'image/gif'
            elif ext == '.webp':
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'  # Default fallback
        
        # Create data URL
        base64_data = base64.b64encode(file_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        return cls(image_url=ImageUrlObject(url=data_url))
    
    @classmethod
    def from_file_object(cls, file_obj: BinaryIO, filename: Optional[str] = None) -> "ImageContent":
        """Create ImageContent from a file object"""
        file_data = file_obj.read()
        
        # Try to determine MIME type from filename if provided
        mime_type = 'image/jpeg'  # Default
        if filename:
            detected_mime, _ = mimetypes.guess_type(filename)
            if detected_mime and detected_mime.startswith('image/'):
                mime_type = detected_mime
        
        # Create data URL
        base64_data = base64.b64encode(file_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        return cls(image_url=ImageUrlObject(url=data_url))
    
    @classmethod
    def from_url(cls, url: str) -> "ImageContent":
        """Create ImageContent from a URL"""
        return cls(image_url=ImageUrlObject(url=url))
    
    
    @classmethod
    def from_product_image(cls, product_data: dict) -> Optional["ImageContent"]:
        """Create ImageContent from product data using HTTP URLs directly
        
        Args:
            product_data: Dictionary containing product information with 'image_url' key
        """
        image_url = product_data.get('image_url')
        if not image_url or image_url == 'N/A':
            return None
        
        try:
            return cls.from_url(image_url)
        except Exception as e:
            logger.warning(f"Failed to create ImageContent from product image: {e}")
            return None

class VideoUrlObject(BaseModel):
    """Video URL object"""
    url: str = Field(..., description="Video URL address. The video size is limited to within 200 MB, and the format must be MP4.")

class VideoContent(BaseModel):
    """Video content item"""
    type: Literal[ContentType.VIDEO_URL] = ContentType.VIDEO_URL
    video_url: VideoUrlObject = Field(..., description="Video information")
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "VideoContent":
        """Create VideoContent from a file path"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        # Check file size (200MB limit as per API spec)
        file_size = file_path.stat().st_size
        max_size = 200 * 1024 * 1024  # 200MB in bytes
        if file_size > max_size:
            raise ValueError(f"Video file too large: {file_size / (1024*1024):.1f}MB. Maximum allowed: 200MB")
        
        # Read file and encode as base64
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Get MIME type - default to MP4 as per API spec
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type or not mime_type.startswith('video/'):
            mime_type = 'video/mp4'  # Default as per API spec
        
        # Create data URL
        base64_data = base64.b64encode(file_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        return cls(video_url=VideoUrlObject(url=data_url))
    
    @classmethod
    def from_file_object(cls, file_obj: BinaryIO, filename: Optional[str] = None) -> "VideoContent":
        """Create VideoContent from a file object"""
        file_data = file_obj.read()
        
        # Check file size (200MB limit)
        file_size = len(file_data)
        max_size = 200 * 1024 * 1024  # 200MB in bytes
        if file_size > max_size:
            raise ValueError(f"Video file too large: {file_size / (1024*1024):.1f}MB. Maximum allowed: 200MB")
        
        # Try to determine MIME type from filename if provided
        mime_type = 'video/mp4'  # Default
        if filename:
            detected_mime, _ = mimetypes.guess_type(filename)
            if detected_mime and detected_mime.startswith('video/'):
                mime_type = detected_mime
        
        # Create data URL
        base64_data = base64.b64encode(file_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        return cls(video_url=VideoUrlObject(url=data_url))
    
    @classmethod
    def from_url(cls, url: str) -> "VideoContent":
        """Create VideoContent from a URL"""
        return cls(video_url=VideoUrlObject(url=url))

class FileUrlObject(BaseModel):
    """File URL object"""
    url: str = Field(..., description="File URL address. Only GLM-4.5V supported. Supports formats such as PDF and Word, with a maximum of 50.")

class FileContent(BaseModel):
    """File content item"""
    type: Literal[ContentType.FILE_URL] = ContentType.FILE_URL
    file_url: FileUrlObject = Field(..., description="File information")
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "FileContent":
        """Create FileContent from a file path"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file and encode as base64
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            # Default based on extension
            ext = file_path.suffix.lower()
            if ext == '.pdf':
                mime_type = 'application/pdf'
            elif ext in ['.doc', '.docx']:
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif ext == '.txt':
                mime_type = 'text/plain'
            else:
                mime_type = 'application/octet-stream'  # Generic binary
        
        # Create data URL
        base64_data = base64.b64encode(file_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        return cls(file_url=FileUrlObject(url=data_url))
    
    @classmethod
    def from_file_object(cls, file_obj: BinaryIO, filename: Optional[str] = None) -> "FileContent":
        """Create FileContent from a file object"""
        file_data = file_obj.read()
        
        # Try to determine MIME type from filename if provided
        mime_type = 'application/octet-stream'  # Default
        if filename:
            detected_mime, _ = mimetypes.guess_type(filename)
            if detected_mime:
                mime_type = detected_mime
        
        # Create data URL
        base64_data = base64.b64encode(file_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        return cls(file_url=FileUrlObject(url=data_url))
    
    @classmethod
    def from_url(cls, url: str) -> "FileContent":
        """Create FileContent from a URL"""
        return cls(file_url=FileUrlObject(url=url))

# Union type for all multimodal content
VisionMultimodalContentItem = Union[TextContent, ImageContent, VideoContent, FileContent]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_multimodal_product_content(products: List[dict], collection_info: dict = None) -> List[VisionMultimodalContentItem]:
    """
    Create multimodal content from product data including text and images
    
    Args:
        products: List of product dictionaries
        collection_info: Optional collection metadata
        
    Returns:
        List of multimodal content items (text and images)
    """
    content_items = []
    
    # Add collection header if provided
    if collection_info:
        header_text = f"**{collection_info.get('site_name', 'Products')}** - {len(products)} products found\n\n"
        content_items.append(TextContent(text=header_text))
    
    # Add each product with text and image
    for product in products:
        # Add product text info
        product_text = f"**{product.get('product_name', 'Unknown Product')}**\n"
        product_text += f"Store: {product.get('store', 'Unknown')}\n"
        product_text += f"Price: {product.get('price', 'N/A')}\n"
        if product.get('product_url'):
            product_text += f"[View Product]({product['product_url']})\n"
        product_text += "\n"
        
        content_items.append(TextContent(text=product_text))
        
        # Add product image if available
        image_content = ImageContent.from_product_image(product)
        if image_content:
            content_items.append(image_content)
    
    return content_items
