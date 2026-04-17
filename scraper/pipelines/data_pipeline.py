"""Data cleaning pipeline."""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataCleaningPipeline:
    """Pipeline for cleaning and validating scraped data."""

    def __init__(self):
        self.items_cleaned = 0
        self.items_dropped = 0

    def open_spider(self, spider):
        """Called when spider opens."""
        logger.info("DataCleaningPipeline opened")
        self.items_cleaned = 0
        self.items_dropped = 0

    def close_spider(self, spider):
        """Called when spider closes."""
        logger.info(
            f"DataCleaningPipeline closed: {self.items_cleaned} cleaned, {self.items_dropped} dropped"
        )

    def process_item(self, item: Dict[str, Any], spider) -> Optional[Dict[str, Any]]:
        """Clean and validate item."""
        try:
            # Clean text fields
            cleaned = self._clean_text_fields(item)

            # Validate required fields
            if not self._validate_required_fields(cleaned):
                self.items_dropped += 1
                return None

            # Normalize data
            normalized = self._normalize_data(cleaned)

            self.items_cleaned += 1
            return normalized

        except Exception as e:
            logger.error(f"Error cleaning item: {e}")
            self.items_dropped += 1
            return None

    def _clean_text_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean text fields."""
        cleaned = item.copy()
        for key, value in cleaned.items():
            if isinstance(value, str):
                # Remove extra whitespace
                cleaned[key] = " ".join(value.split())
                # Remove null bytes
                cleaned[key] = cleaned[key].replace("\x00", "")
        return cleaned

    def _validate_required_fields(self, item: Dict[str, Any]) -> bool:
        """Validate required fields are present and non-empty."""
        required_fields = item.get("_required_fields", [])
        for field in required_fields:
            if not item.get(field):
                return False
        return True

    def _normalize_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data formats."""
        normalized = item.copy()

        # Normalize URLs
        if "url" in normalized:
            normalized["url"] = self._normalize_url(normalized["url"])

        # Normalize dates
        if "date" in normalized:
            normalized["date"] = self._normalize_date(normalized["date"])

        # Normalize numbers
        if "price" in normalized:
            normalized["price"] = self._normalize_number(normalized["price"])

        return normalized

    def _normalize_url(self, url: str) -> str:
        """Normalize URL."""
        if not url:
            return ""
        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string."""
        # Add your date normalization logic here
        return date_str

    def _normalize_number(self, value: str) -> Optional[float]:
        """Normalize number string."""
        try:
            # Remove currency symbols and commas
            cleaned = "".join(c for c in str(value) if c.isdigit() or c == ".")
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None


class StoragePipeline:
    """Pipeline for storing cleaned data."""

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.items_stored = 0
        self.items_failed = 0

    def open_spider(self, spider):
        """Called when spider opens."""
        logger.info("StoragePipeline opened")
        self.items_stored = 0
        self.items_failed = 0

    def close_spider(self, spider):
        """Called when spider closes."""
        logger.info(
            f"StoragePipeline closed: {self.items_stored} stored, {self.items_failed} failed"
        )

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Store item in database or file."""
        try:
            if self.db_session:
                self._store_in_db(item)
            else:
                self._store_in_file(item)

            self.items_stored += 1
            return item

        except Exception as e:
            logger.error(f"Error storing item: {e}")
            self.items_failed += 1
            return item

    def _store_in_db(self, item: Dict[str, Any]):
        """Store item in database."""
        # Implementation depends on your models
        pass

    def _store_in_file(self, item: Dict[str, Any]):
        """Store item in JSON file."""
        import json
        from datetime import datetime

        filename = f"scraped_data_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")