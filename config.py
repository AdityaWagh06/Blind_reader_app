"""
Configuration for Blind Reader Assistant.
Every value can be overridden with an environment variable of the same name prefixed BLIND_READER_,
for example:  $env:BLIND_READER_BLIP_MODEL = "Salesforce/blip-image-captioning-base"
"""

import os


class Config:
    APP_NAME = "Blind Reader Assistant"
    APP_VERSION = "2.0.0"

    # Short summary + "is the photo readable?" check: BLIP fine-tuned on VizWiz (photos taken by blind people)
    BLIP_MODEL = "adityawagh07/blip-vizwiz"
    # Detailed scene description and text reading
    FLORENCE_MODEL = "florence-community/Florence-2-base"

    # Flag a photo as too blurry/dark when the fine-tuned model is at least this sure (0-1).
    # Chosen on held-out VizWiz photos by training/evaluate.py (see eval/results.json "calibration")
    UNREADABLE_THRESHOLD = 0.5

    MAX_FILE_SIZE_MB = 10
    HOST = "127.0.0.1"
    PORT = 8000


for _key in ("BLIP_MODEL", "FLORENCE_MODEL", "UNREADABLE_THRESHOLD", "MAX_FILE_SIZE_MB", "HOST", "PORT"):
    _value = os.getenv(f"BLIND_READER_{_key}")
    if _value:
        setattr(Config, _key, type(getattr(Config, _key))(_value))
