"""
Configuration file for Blind Reader Assistant
Modify these settings to customize the application behavior.
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for Blind Reader Assistant"""
    
    # Application settings
    APP_NAME = "Blind Reader Assistant"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "An AI-powered assistant for visually impaired users"
    
    # Model configurations
    BLIP_MODEL = "adityawagh07/blip-vizwiz"  # BLIP fine-tuned on VizWiz; base: "Salesforce/blip-image-captioning-base"
    T5_MODEL = "google/flan-t5-small"  # Options: google/flan-t5-small, google/flan-t5-base
    TTS_ENGINE = "bark"  # Options: bark, coqui
    
    # TTS settings
    BARK_VOICE_PRESET = "v2/en_speaker_6"  # Default voice
    COQUI_MODEL = "tts_models/en/ljspeech/tacotron2-DDC"
    
    # Processing settings
    MAX_IMAGE_SIZE = 512  # Maximum image dimension for processing
    CAPTION_MAX_LENGTH = 50  # Maximum caption length
    EXPLANATION_MAX_LENGTH = 150  # Maximum explanation length
    
    # UI settings
    STREAMLIT_THEME = {
        "primaryColor": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6",
        "textColor": "#262730"
    }
    
    # Performance settings
    USE_GPU = True  # Automatically detect and use GPU if available
    ENABLE_CACHING = True  # Cache models for faster subsequent runs
    
    # File settings
    SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg']
    MAX_FILE_SIZE_MB = 10  # Maximum file size in MB
    
    # Logging settings
    LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Accessibility settings
    AUTO_PLAY_AUDIO = True  # Automatically play audio when generated
    ENABLE_RE_READ = True  # Show re-read button
    ACCESSIBILITY_ENHANCEMENTS = True  # Add spatial context to descriptions
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """Get model configuration"""
        return {
            "blip_model": cls.BLIP_MODEL,
            "t5_model": cls.T5_MODEL,
            "tts_engine": cls.TTS_ENGINE,
            "bark_voice": cls.BARK_VOICE_PRESET,
            "coqui_model": cls.COQUI_MODEL
        }
    
    @classmethod
    def get_processing_config(cls) -> Dict[str, Any]:
        """Get processing configuration"""
        return {
            "max_image_size": cls.MAX_IMAGE_SIZE,
            "caption_max_length": cls.CAPTION_MAX_LENGTH,
            "explanation_max_length": cls.EXPLANATION_MAX_LENGTH,
            "use_gpu": cls.USE_GPU,
            "enable_caching": cls.ENABLE_CACHING
        }
    
    @classmethod
    def get_ui_config(cls) -> Dict[str, Any]:
        """Get UI configuration"""
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "theme": cls.STREAMLIT_THEME,
            "auto_play_audio": cls.AUTO_PLAY_AUDIO,
            "enable_re_read": cls.ENABLE_RE_READ,
            "accessibility_enhancements": cls.ACCESSIBILITY_ENHANCEMENTS
        }
    
    @classmethod
    def get_file_config(cls) -> Dict[str, Any]:
        """Get file configuration"""
        return {
            "supported_formats": cls.SUPPORTED_IMAGE_FORMATS,
            "max_file_size_mb": cls.MAX_FILE_SIZE_MB
        }
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": cls.LOG_LEVEL,
            "format": cls.LOG_FORMAT
        }
    
    @classmethod
    def update_config(cls, **kwargs):
        """Update configuration with new values"""
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Check model names
        if not cls.BLIP_MODEL:
            errors.append("BLIP_MODEL cannot be empty")
        
        if not cls.T5_MODEL:
            errors.append("T5_MODEL cannot be empty")
        
        # Check TTS engine
        if cls.TTS_ENGINE not in ["bark", "coqui"]:
            errors.append("TTS_ENGINE must be 'bark' or 'coqui'")
        
        # Check file size
        if cls.MAX_FILE_SIZE_MB <= 0:
            errors.append("MAX_FILE_SIZE_MB must be positive")
        
        # Check image size
        if cls.MAX_IMAGE_SIZE <= 0:
            errors.append("MAX_IMAGE_SIZE must be positive")
        
        if errors:
            for error in errors:
                print(f"Configuration error: {error}")
            return False
        
        return True

# Environment-specific overrides
if os.getenv("BLIND_READER_DEBUG"):
    Config.LOG_LEVEL = "DEBUG"

if os.getenv("BLIND_READER_TTS_ENGINE"):
    Config.TTS_ENGINE = os.getenv("BLIND_READER_TTS_ENGINE")

if os.getenv("BLIND_READER_BLIP_MODEL"):
    Config.BLIP_MODEL = os.getenv("BLIND_READER_BLIP_MODEL")

if os.getenv("BLIND_READER_T5_MODEL"):
    Config.T5_MODEL = os.getenv("BLIND_READER_T5_MODEL")

# Validate configuration on import
if not Config.validate_config():
    raise ValueError("Invalid configuration detected") 