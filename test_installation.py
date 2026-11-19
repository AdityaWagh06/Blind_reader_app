#!/usr/bin/env python3
"""
Test script to verify Blind Reader Assistant installation
Run this script to check if all dependencies and models are working correctly.
"""

import sys
import logging
import traceback
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required packages can be imported"""
    logger.info("Testing package imports...")
    
    try:
        import streamlit
        logger.info("✅ Streamlit imported successfully")
    except ImportError as e:
        logger.error(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import torch
        logger.info(f"✅ PyTorch imported successfully (version: {torch.__version__})")
        logger.info(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"   CUDA device: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        logger.error(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        import transformers
        logger.info(f"✅ Transformers imported successfully (version: {transformers.__version__})")
    except ImportError as e:
        logger.error(f"❌ Transformers import failed: {e}")
        return False
    
    try:
        import numpy
        logger.info(f"✅ NumPy imported successfully (version: {numpy.__version__})")
    except ImportError as e:
        logger.error(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        from PIL import Image
        logger.info("✅ Pillow imported successfully")
    except ImportError as e:
        logger.error(f"❌ Pillow import failed: {e}")
        return False
    
    return True

def test_bark_tts():
    """Test Bark TTS installation"""
    logger.info("Testing Bark TTS...")
    
    try:
        from bark import SAMPLE_RATE, generate_audio, preload_models
        logger.info("✅ Bark TTS imported successfully")
        
        # Test basic functionality
        test_text = "Hello, this is a test."
        audio = generate_audio(test_text)
        logger.info(f"✅ Bark TTS test successful (audio length: {len(audio)} samples)")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Bark TTS import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Bark TTS test failed: {e}")
        return False

def test_coqui_tts():
    """Test Coqui TTS installation"""
    logger.info("Testing Coqui TTS...")
    
    try:
        from TTS.api import TTS
        logger.info("✅ Coqui TTS imported successfully")
        
        # Test basic functionality
        tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
        logger.info("✅ Coqui TTS model loaded successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Coqui TTS import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Coqui TTS test failed: {e}")
        return False

def test_tts():
    """Test the default speech pipeline (Coqui if installed, otherwise pyttsx3)"""
    logger.info("Testing text-to-speech...")

    try:
        from utils.tts_generator import TTSGenerator

        tts = TTSGenerator(use_bark=False)
        audio = tts.text_to_speech("Installation test.")
        assert audio[:4] == b"RIFF", "output is not WAV audio"

        logger.info(f"✅ {tts.engine} produced {len(audio)} bytes of WAV audio")
        return True

    except Exception as e:
        logger.error(f"❌ Text-to-speech test failed: {e}")
        return False

def test_blip_model():
    """Test BLIP model loading"""
    logger.info("Testing BLIP model...")
    
    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration
        
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
        logger.info("✅ BLIP model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ BLIP model test failed: {e}")
        return False

def test_t5_model():
    """Test T5 model loading"""
    logger.info("Testing T5 model...")
    
    try:
        from transformers import T5Tokenizer, T5ForConditionalGeneration
        
        tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
        model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
        
        logger.info("✅ T5 model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ T5 model test failed: {e}")
        return False

def test_utils_modules():
    """Test our utility modules"""
    logger.info("Testing utility modules...")
    
    try:
        from utils.image_captioning import ImageCaptioner
        logger.info("✅ ImageCaptioner imported successfully")
    except Exception as e:
        logger.error(f"❌ ImageCaptioner import failed: {e}")
        return False
    
    try:
        from utils.text_explainer import TextExplainer
        logger.info("✅ TextExplainer imported successfully")
    except Exception as e:
        logger.error(f"❌ TextExplainer import failed: {e}")
        return False
    
    try:
        from utils.tts_generator import TTSGenerator
        logger.info("✅ TTSGenerator imported successfully")
    except Exception as e:
        logger.error(f"❌ TTSGenerator import failed: {e}")
        return False
    
    return True

def create_test_image():
    """Create a simple test image"""
    try:
        # Create a simple test image
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        logger.info("✅ Test image created successfully")
        return img
    except Exception as e:
        logger.error(f"❌ Test image creation failed: {e}")
        return None

def main():
    """Run all tests"""
    logger.info("🚀 Starting Blind Reader Assistant installation test...")
    logger.info("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Text-to-Speech", test_tts),
        ("BLIP Model", test_blip_model),
        ("T5 Model", test_t5_model),
        ("Utility Modules", test_utils_modules),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                logger.info(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} test FAILED with exception: {e}")
            logger.error(traceback.format_exc())
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Installation is successful.")
        logger.info("You can now run: streamlit run main.py")
    else:
        logger.error("❌ Some tests failed. Please check the error messages above.")
        logger.info("💡 Try reinstalling dependencies: pip install -r requirements.txt")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 