"""
Schema.org Product model based on https://schema.org/Product

This model represents the standard schema.org Product type that most
e-commerce sites use in their JSON-LD structured data.
"""

from datetime import date
from typing import List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class Organization(BaseModel):
    """Schema.org Organization"""
    type: str = Field(alias="@type", default="Organization")
    name: Optional[str] = None
    url: Optional[Union[HttpUrl, str]] = None  # Allow both full URLs and relative URLs


class Brand(BaseModel):
    """Schema.org Brand"""
    type: str = Field(alias="@type", default="Brand")
    name: Optional[str] = None
    url: Optional[Union[HttpUrl, str]] = None  # Allow both full URLs and relative URLs


class Offer(BaseModel):
    """Schema.org Offer"""
    type: str = Field(alias="@type", default="Offer")
    price: Optional[Union[str, float]] = None
    price_currency: Optional[str] = Field(alias="priceCurrency", default="USD")
    availability: Optional[str] = None
    url: Optional[Union[HttpUrl, str]] = None  # Allow both full URLs and relative URLs
    seller: Optional[Union[Organization, str]] = None
    valid_from: Optional[date] = Field(alias="validFrom", default=None)
    valid_through: Optional[date] = Field(alias="validThrough", default=None)


class AggregateRating(BaseModel):
    """Schema.org AggregateRating"""
    type: str = Field(alias="@type", default="AggregateRating")
    rating_value: Optional[Union[str, float]] = Field(alias="ratingValue", default=None)
    rating_count: Optional[int] = Field(alias="ratingCount", default=None)
    review_count: Optional[int] = Field(alias="reviewCount", default=None)
    best_rating: Optional[Union[str, float]] = Field(alias="bestRating", default=None)
    worst_rating: Optional[Union[str, float]] = Field(alias="worstRating", default=None)


class ImageObject(BaseModel):
    """Schema.org ImageObject"""
    type: str = Field(alias="@type", default="ImageObject")
    url: Optional[Union[HttpUrl, str]] = None  # Allow both full URLs and relative URLs
    width: Optional[int] = None
    height: Optional[int] = None


class Review(BaseModel):
    """Schema.org Review"""
    type: str = Field(alias="@type", default="Review")
    author: Optional[Union[str, dict]] = None
    date_published: Optional[date] = Field(alias="datePublished", default=None)
    review_body: Optional[str] = Field(alias="reviewBody", default=None)
    review_rating: Optional[dict] = Field(alias="reviewRating", default=None)


class SchemaOrgProduct(BaseModel):
    """
    Schema.org Product model
    
    Based on https://schema.org/Product specification.
    Includes the most commonly used properties from e-commerce sites.
    """
    
    # Required schema.org fields
    context: str = Field(alias="@context", default="https://schema.org")
    type: str = Field(alias="@type", default="Product")
    
    # Core product information
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[Union[HttpUrl, str]] = None  # Allow both full URLs and relative URLs
    image: Optional[Union[HttpUrl, List[HttpUrl], str, List[str], ImageObject, List[ImageObject], dict, List[dict]]] = None
    
    # Identifiers
    sku: Optional[str] = None
    mpn: Optional[str] = Field(alias="mpn", default=None)  # Manufacturer Part Number
    gtin: Optional[str] = None  # Global Trade Item Number
    gtin8: Optional[str] = None
    gtin12: Optional[str] = None
    gtin13: Optional[str] = None
    gtin14: Optional[str] = None
    product_id: Optional[str] = Field(alias="productID", default=None)
    
    # Brand and manufacturer
    brand: Optional[Union[Brand, Organization, str]] = None
    manufacturer: Optional[Union[Organization, str]] = None
    
    # Pricing and offers
    offers: Optional[Union[Offer, List[Offer]]] = None
    
    # Physical properties
    color: Optional[str] = None
    size: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    width: Optional[str] = None
    depth: Optional[str] = None
    material: Optional[str] = None
    pattern: Optional[str] = None
    
    # Categories and classification
    category: Optional[Union[str, List[str]]] = None
    keywords: Optional[Union[str, List[str]]] = None
    
    # Ratings and reviews
    aggregate_rating: Optional[AggregateRating] = Field(alias="aggregateRating", default=None)
    review: Optional[Union[Review, List[Review]]] = None
    
    # Availability and condition
    item_condition: Optional[str] = Field(alias="itemCondition", default=None)
    availability: Optional[str] = None
    
    # Dates
    release_date: Optional[date] = Field(alias="releaseDate", default=None)
    production_date: Optional[date] = Field(alias="productionDate", default=None)
    
    # Additional properties
    model: Optional[str] = None
    logo: Optional[str] = None  # Allow any string for logo URLs
    slogan: Optional[str] = None
    award: Optional[Union[str, List[str]]] = None
    
    # Relationships
    is_variant_of: Optional[str] = Field(alias="isVariantOf", default=None)
    is_similar_to: Optional[Union[str, List[str]]] = Field(alias="isSimilarTo", default=None)
    is_related_to: Optional[Union[str, List[str]]] = Field(alias="isRelatedTo", default=None)
    
    model_config = ConfigDict(
        populate_by_name=True
    )
    
    def get_price(self) -> Optional[float]:
        """Extract the first available price as a float"""
        if not self.offers:
            return None
        
        offers_list = self.offers if isinstance(self.offers, list) else [self.offers]
        
        for offer in offers_list:
            if offer.price:
                try:
                    # Handle string prices like "$99.99"
                    if isinstance(offer.price, str):
                        # Remove currency symbols and convert to float
                        price_str = offer.price.replace('$', '').replace(',', '').strip()
                        return float(price_str)
                    else:
                        return float(offer.price)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def get_currency(self) -> str:
        """Extract the currency from offers, default to USD"""
        if not self.offers:
            return "USD"
        
        offers_list = self.offers if isinstance(self.offers, list) else [self.offers]
        
        for offer in offers_list:
            if offer.price_currency:
                return offer.price_currency
        
        return "USD"
    
    def get_brand_name(self) -> Optional[str]:
        """Extract brand name from brand field"""
        if not self.brand:
            return None
        
        if isinstance(self.brand, str):
            return self.brand
        elif hasattr(self.brand, 'name'):
            return self.brand.name
        
        return None
    
    def get_image_url(self) -> Optional[str]:
        """Get the first image URL"""
        if not self.image:
            return None
        
        if isinstance(self.image, str):
            return self.image
        elif isinstance(self.image, dict):
            # Handle ImageObject dict
            return self.image.get('url')
        elif isinstance(self.image, ImageObject):
            return str(self.image.url) if self.image.url else None
        elif isinstance(self.image, list) and self.image:
            first_image = self.image[0]
            if isinstance(first_image, str):
                return first_image
            elif isinstance(first_image, dict):
                return first_image.get('url')
            elif isinstance(first_image, ImageObject):
                return str(first_image.url) if first_image.url else None
            else:
                return str(first_image)
        
        return None
    
    def to_simple_dict(self) -> dict:
        """Convert to a simple dictionary with key product info"""
        return {
            "name": self.name,
            "price": self.get_price(),
            "currency": self.get_currency(),
            "brand": self.get_brand_name(),
            "url": str(self.url) if self.url else None,
            "image": self.get_image_url(),
            "sku": self.sku,
            "description": self.description,
            "color": self.color,
            "size": self.size,
            "category": self.category if isinstance(self.category, str) else (
                self.category[0] if isinstance(self.category, list) and self.category else None
            )
        }
