import os

from django.core.exceptions import ValidationError


MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/webm",
    "audio/mp4",
    "audio/x-m4a",
}


ALLOWED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".webm",
    ".m4a",
}


def validate_voice_file(file):
    """
    Validate uploaded voice file.
    """

    if not file:
        raise ValidationError("Voice file is required.")

    extension = os.path.splitext(file.name)[1].lower()

    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValidationError(
            "Unsupported audio format."
        )

    content_type = getattr(file, "content_type", "")

    if content_type and content_type not in ALLOWED_AUDIO_TYPES:
        raise ValidationError(
            "Invalid audio content type."
        )

    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            "Maximum audio size is 20 MB."
        )

    return file