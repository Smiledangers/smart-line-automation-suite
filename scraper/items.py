"""Scraped data items definition."""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScrapedItem:
    """Base scraped item."""

    url: str
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None


@dataclass
class ProductItem(ScrapedItem):
    """Product item for e-commerce scraping."""

    name: Optional[str] = None
    price: Optional[float] = None
    currency: str = "TWD"
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    category: Optional[str] = None
    sku: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArticleItem(ScrapedItem):
    """Article item for content scraping."""

    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    reading_time: int = 0  # minutes


@dataclass
class ProfileItem(ScrapedItem):
    """Profile item for social media scraping."""

    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    verified: bool = False
    location: Optional[str] = None
    website: Optional[str] = None


def item_to_dict(item: ScrapedItem) -> Dict[str, Any]:
    """Convert item to dictionary."""
    result = {
        "url": item.url,
        "scraped_at": item.scraped_at.isoformat() if item.scraped_at else None,
        "source": item.source,
    }

    # Add item-specific fields
    if isinstance(item, ProductItem):
        result.update(
            {
                "type": "product",
                "name": item.name,
                "price": item.price,
                "currency": item.currency,
                "description": item.description,
                "images": item.images,
                "category": item.category,
                "sku": item.sku,
                "availability": item.availability,
                "rating": item.rating,
                "reviews_count": item.reviews_count,
                "metadata": item.metadata,
            }
        )
    elif isinstance(item, ArticleItem):
        result.update(
            {
                "type": "article",
                "title": item.title,
                "author": item.author,
                "publish_date": item.publish_date.isoformat() if item.publish_date else None,
                "content": item.content,
                "summary": item.summary,
                "tags": item.tags,
                "images": item.images,
                "reading_time": item.reading_time,
            }
        )
    elif isinstance(item, ProfileItem):
        result.update(
            {
                "type": "profile",
                "username": item.username,
                "display_name": item.display_name,
                "bio": item.bio,
                "avatar_url": item.avatar_url,
                "followers": item.followers,
                "following": item.following,
                "posts_count": item.posts_count,
                "verified": item.verified,
                "location": item.location,
                "website": item.website,
            }
        )

    return result