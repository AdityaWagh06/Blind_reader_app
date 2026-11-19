import logging
import io
import numpy as np
import torch
import warnings
from typing import Optional, Union

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class TTSGenerator:
    """Text-to-Speech generator using Bark with Coqui TTS fallback"""
    
    def __init__(self, use_bark=True):
        """
        Initialize the TTS generator
        
        Args:
            use_bark: bool, whether to use Bark (True) or Coqui TTS (False)
        """
        self.use_bark = use_bark
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        try:
            if use_bark:
                self._init_bark()
            else:
                self._init_coqui_tts()
                
        except Exception as e:
            logger.error(f"Error initializing TTS: {str(e)}")
            # Fallback to Coqui TTS if Bark fails
            if use_bark:
                logger.info("Falling back to Coqui TTS...")
                self.use_bark = False
                self._init_coqui_tts()
            else:
                raise RuntimeError(f"Failed to initialize TTS: {str(e)}")
    
    def _init_bark(self):
        """Initialize Bark TTS"""
        try:
            logger.info("Loading Bark TTS model...")
            from bark import SAMPLE_RATE, generate_audio, preload_models
            
            # Preload models for faster inference
            preload_models()
            
            self.bark_generate_audio = generate_audio
            self.bark_sample_rate = SAMPLE_RATE
            logger.info("Bark TTS model loaded successfully")
            
        except ImportError:
            logger.error("Bark not available, falling back to Coqui TTS")
            raise ImportError("Bark not available")
        except Exception as e:
            logger.error(f"Error loading Bark: {str(e)}")
            raise RuntimeError(f"Failed to load Bark: {str(e)}")
    
    def _init_coqui_tts(self):
        """Initialize Coqui TTS"""
        try:
            logger.info("Loading Coqui TTS model...")
            from TTS.api import TTS
            
            # Use a fast and good quality model
            self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
            logger.info("Coqui TTS model loaded successfully")
            
        except ImportError:
            logger.error("Coqui TTS not available")
            raise ImportError("Coqui TTS not available")
        except Exception as e:
            logger.error(f"Error loading Coqui TTS: {str(e)}")
            raise RuntimeError(f"Failed to load Coqui TTS: {str(e)}")
    
    def text_to_speech(self, text: str, voice_preset: str = "v2/en_speaker_6") -> bytes:
        """
        Convert text to speech
        
        Args:
            text: str, the text to convert to speech
            voice_preset: str, voice preset for Bark (only used if use_bark=True)
            
        Returns:
            bytes: Audio data in WAV format
        """
        try:
            if self.use_bark:
                return self._bark_tts(text, voice_preset)
            else:
                return self._coqui_tts(text)
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            raise RuntimeError(f"Failed to convert text to speech: {str(e)}")
    
    def _bark_tts(self, text: str, voice_preset: str) -> bytes:
        """Convert text to speech using Bark"""
        try:
            # Generate audio using Bark
            audio_array = self.bark_generate_audio(text, history_prompt=voice_preset)
            
            # Convert to WAV format
            audio_bytes = self._numpy_to_wav(audio_array, self.bark_sample_rate)
            
            logger.info(f"Generated Bark audio for text: {text[:50]}...")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error in Bark TTS: {str(e)}")
            raise RuntimeError(f"Bark TTS failed: {str(e)}")
    
    def _coqui_tts(self, text: str) -> bytes:
        """Convert text to speech using Coqui TTS"""
        try:
            # Generate audio using Coqui TTS
            audio_array = self.tts.tts(text)
            
            # Convert to WAV format
            audio_bytes = self._numpy_to_wav(audio_array, 22050)  # Coqui TTS sample rate
            
            logger.info(f"Generated Coqui TTS audio for text: {text[:50]}...")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error in Coqui TTS: {str(e)}")
            raise RuntimeError(f"Coqui TTS failed: {str(e)}")
    
    def _pyttsx3_tts(self, text: str) -> bytes:
        """Convert text to speech using the OS voices via pyttsx3 (offline)"""
        import os
        import tempfile
        import pyttsx3

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            # New engine per call: pyttsx3 engines are tied to the thread that created them
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.save_to_file(text, path)
            engine.runAndWait()
            with open(path, "rb") as f:
                return f.read()
        finally:
            os.remove(path)

    def _numpy_to_wav(self, audio_array: np.ndarray, sample_rate: int) -> bytes:
        """
        Convert numpy array to WAV format bytes
        
        Args:
            audio_array: np.ndarray, the audio data
            sample_rate: int, the sample rate
            
        Returns:
            bytes: WAV format audio data
        """
        try:
            import wave
            import struct
            
            # Normalize audio to 16-bit range
            audio_normalized = np.int16(np.clip(np.asarray(audio_array), -1, 1) * 32767)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_normalized.tobytes())
            
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting to WAV: {str(e)}")
            raise RuntimeError(f"Failed to convert audio to WAV: {str(e)}")
    
    def get_available_voices(self) -> list:
        """Get list of available voice presets (Bark only)"""
        if not self.use_bark:
            return ["default"]
        
        try:
            # Common Bark voice presets
            voices = [
                "v2/en_speaker_0", "v2/en_speaker_1", "v2/en_speaker_2", "v2/en_speaker_3",
                "v2/en_speaker_4", "v2/en_speaker_5", "v2/en_speaker_6", "v2/en_speaker_7",
                "v2/en_speaker_8", "v2/en_speaker_9"
            ]
            return voices
        except Exception as e:
            logger.warning(f"Could not get available voices: {str(e)}")
            return ["v2/en_speaker_6"]  # Default fallback
    
    def change_voice(self, voice_preset: str):
        """
        Change the voice preset (Bark only)
        
        Args:
            voice_preset: str, the new voice preset
        """
        if self.use_bark:
            logger.info(f"Voice preset changed to: {voice_preset}")
            self.current_voice = voice_preset
        else:
            logger.warning("Voice changing not supported in Coqui TTS mode")
    
    def get_audio_info(self) -> dict:
        """Get information about the current TTS setup"""
        info = {
            "tts_engine": "Bark" if self.use_bark else "Coqui TTS",
            "device": self.device,
            "sample_rate": self.bark_sample_rate if self.use_bark else 22050
        }
        
        if self.use_bark:
            info["available_voices"] = self.get_available_voices()
        
        return info 