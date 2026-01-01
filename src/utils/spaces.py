"""Lightweight DigitalOcean Spaces (S3-compatible) helper."""

import json
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

import config

logger = logging.getLogger(__name__)


class SpacesClient:
    """Thin wrapper around boto3 S3 client for Spaces."""

    def __init__(self):
        if not config.SPACES_ENABLED:
            raise ValueError("Spaces is not enabled; missing credentials or config")

        self.bucket = config.SPACES_BUCKET
        self.client = boto3.client(
            "s3",
            endpoint_url=config.SPACES_ENDPOINT,
            region_name=config.SPACES_REGION,
            aws_access_key_id=config.SPACES_KEY,
            aws_secret_access_key=config.SPACES_SECRET,
        )

    def download_text(self, key: str) -> Optional[str]:
        """Download an object as UTF-8 text. Returns None if not found."""
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read().decode("utf-8")
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                return None
            logger.warning(f"Spaces download failed for {key}: {e}")
            return None
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"Spaces download failed for {key}: {e}")
            return None

    def upload_text(self, key: str, text: str, content_type: str = "text/plain", public: bool = True):
        """Upload a text object."""
        params = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": text.encode("utf-8"),
            "ContentType": content_type,
        }
        if public:
            params["ACL"] = "public-read"

        self.client.put_object(**params)

    def upload_json(self, key: str, payload, public: bool = True):
        """Upload JSON payload with indentation."""
        body = json.dumps(payload, indent=2)
        self.upload_text(key, body, content_type="application/json", public=public)

    def append_text(self, key: str, text: str, content_type: str = "text/plain"):
        """Append text to existing file. Downloads current, appends, re-uploads."""
        current = self.download_text(key) or ""
        updated = current + text
        self.upload_text(key, updated, content_type=content_type, public=True)

