"""S3-compatible object storage with a local filesystem fallback."""

from __future__ import annotations

from io import BytesIO

from loguru import logger

from backend.config.settings import settings


class ObjectStorageService:
    """Persist raw files to MinIO when enabled, otherwise to local storage."""

    def __init__(self) -> None:
        self.local_root = settings.document_storage_dir
        self.local_root.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._storage_errors: tuple[type[Exception], ...] = (OSError,)
        if settings.MINIO_ENABLED:
            try:
                import boto3
                from botocore.exceptions import BotoCoreError, ClientError
            except ImportError:
                logger.warning("boto3 is not installed; falling back to local object storage.")
                return

            scheme = "https" if settings.MINIO_SECURE else "http"
            self._client = boto3.client(
                "s3",
                endpoint_url=f"{scheme}://{settings.MINIO_ENDPOINT}",
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
            )
            self._storage_errors = (OSError, BotoCoreError, ClientError)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def ensure_bucket(self) -> None:
        """Create the configured bucket if MinIO is enabled and it is missing."""

        if not self.enabled:
            return
        try:
            buckets = self._client.list_buckets().get("Buckets", [])
            if any(bucket["Name"] == settings.MINIO_BUCKET for bucket in buckets):
                return
            self._client.create_bucket(Bucket=settings.MINIO_BUCKET)
        except self._storage_errors as exc:
            logger.warning("Failed to ensure MinIO bucket {}: {}", settings.MINIO_BUCKET, exc)

    def save_bytes(self, object_key: str, content: bytes) -> str:
        """Persist bytes and return the stable object key."""

        if self.enabled:
            self._client.upload_fileobj(BytesIO(content), settings.MINIO_BUCKET, object_key)
            return object_key

        target_path = self.local_root / object_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return object_key

    def read_text(self, object_key: str) -> str | None:
        """Read an object back as UTF-8 text."""

        try:
            if self.enabled:
                payload = self._client.get_object(Bucket=settings.MINIO_BUCKET, Key=object_key)
                return payload["Body"].read().decode("utf-8", errors="ignore")
            target_path = self.local_root / object_key
            if not target_path.exists():
                return None
            return target_path.read_text(encoding="utf-8")
        except self._storage_errors as exc:
            logger.warning("Failed to read object {}: {}", object_key, exc)
            return None

    def delete(self, object_key: str) -> None:
        """Delete an object if it exists."""

        try:
            if self.enabled:
                self._client.delete_object(Bucket=settings.MINIO_BUCKET, Key=object_key)
                return
            target_path = self.local_root / object_key
            if target_path.exists():
                target_path.unlink()
        except self._storage_errors as exc:
            logger.warning("Failed to delete object {}: {}", object_key, exc)
