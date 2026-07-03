import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import Settings, get_settings

IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
    "image/gif": (b"GIF87a", ".gif"),
    "image/webp": (b"RIFF", ".webp"),
}


@dataclass(frozen=True)
class StoredFile:
    original_filename: str
    storage_path: str
    content_type: str
    file_size: int
    checksum_sha256: str


@dataclass(frozen=True)
class ValidatedUpload:
    original_filename: str
    content: bytes
    content_type: str
    file_size: int
    checksum_sha256: str
    extension: str


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root

    def save_listing_image(self, listing_id: int, filename: str, content: bytes) -> Path:
        listing_dir = self.root / str(listing_id)
        listing_dir.mkdir(parents=True, exist_ok=True)
        target = listing_dir / filename
        target.write_bytes(content)
        return target


def get_storage(settings: Settings | None = None) -> LocalStorage:
    settings = settings or get_settings()
    if settings.storage_backend != "local":
        raise RuntimeError(f"Unsupported storage backend: {settings.storage_backend}")
    return LocalStorage(settings.upload_path)


async def validate_and_store_image(
    file: UploadFile,
    listing_id: int,
    settings: Settings | None = None,
) -> StoredFile:
    validated = await read_validated_image(file, settings)
    target = store_validated_image(validated, listing_id, settings)
    return StoredFile(
        original_filename=validated.original_filename,
        storage_path=str(target),
        content_type=validated.content_type,
        file_size=validated.file_size,
        checksum_sha256=validated.checksum_sha256,
    )


async def read_validated_image(
    file: UploadFile,
    settings: Settings | None = None,
) -> ValidatedUpload:
    settings = settings or get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded image is empty")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Image exceeds {settings.max_upload_size_mb} MB limit")

    detected_type, extension = detect_image_type(content)
    if detected_type not in settings.allowed_image_type_set:
        raise HTTPException(status_code=415, detail=f"Unsupported image type: {detected_type}")

    declared_type = (file.content_type or "").lower()
    if declared_type and declared_type not in settings.allowed_image_type_set:
        raise HTTPException(status_code=415, detail=f"Unsupported image type: {declared_type}")

    original = safe_filename(file.filename or f"upload{extension}")
    checksum = hashlib.sha256(content).hexdigest()

    return ValidatedUpload(
        original_filename=original,
        content=content,
        content_type=detected_type,
        file_size=len(content),
        checksum_sha256=checksum,
        extension=extension,
    )


def store_validated_image(
    upload: ValidatedUpload,
    listing_id: int,
    settings: Settings | None = None,
) -> Path:
    stem = Path(upload.original_filename).stem or "image"
    stored_name = f"{stem}-{uuid.uuid4().hex}{upload.extension}"
    return get_storage(settings).save_listing_image(listing_id, stored_name, upload.content)


def detect_image_type(content: bytes) -> tuple[str, str]:
    if content.startswith(IMAGE_SIGNATURES["image/jpeg"][0]):
        return "image/jpeg", ".jpg"
    if content.startswith(IMAGE_SIGNATURES["image/png"][0]):
        return "image/png", ".png"
    if content.startswith(IMAGE_SIGNATURES["image/gif"][0]):
        return "image/gif", ".gif"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp", ".webp"
    raise HTTPException(status_code=415, detail="Unsupported image type")


def safe_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return name[:180] or "upload"
