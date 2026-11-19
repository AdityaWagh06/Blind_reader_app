import streamlit as st
import os
import logging
from PIL import Image
import io
import base64
from utils.image_captioning import ImageCaptioner
from utils.text_explainer import TextExplainer
from utils.tts_generator import TTSGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Blind Reader Assistant",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .audio-player {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #e8f4fd;
        border-radius: 0.5rem;
    }
    .caption-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .explanation-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="📦 Loading AI models (first run downloads ~1 GB)...")
def load_models():
    """Load models once per server process, shared across sessions"""
    return ImageCaptioner(), TextExplainer(), TTSGenerator(use_bark=False)


def main():
    """Main application function"""
    
    # Header
    st.markdown('<h1 class="main-header">👁️ Blind Reader Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Upload an image and get an audio description for visually impaired users</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This app helps visually impaired users understand images by:
        1. **Captioning** the image using BLIP model
        2. **Explaining** the content in an accessible way using T5
        3. **Converting** the explanation to speech using Bark TTS
        
        All processing happens locally - no external APIs required!
        """)
        
        st.header("📋 Instructions")
        st.markdown("""
        1. Upload an image (PNG, JPG, JPEG)
        2. Wait for processing (may take 30-60 seconds)
        3. Listen to the audio description
        4. Use the re-read button if needed
        """)
        
        # Model status
        st.header("🔧 Model Status")
        if 'models_loaded' not in st.session_state:
            st.session_state.models_loaded = False
            
        if st.session_state.models_loaded:
            st.success("✅ All models loaded successfully")
        else:
            st.warning("⏳ Models loading... (first run)")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<h2 class="sub-header">📤 Upload Image</h2>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg'],
            help="Upload an image to get an audio description"
        )
        
        if uploaded_file is not None:
            # Display the uploaded image
            try:
                image = Image.open(uploaded_file)
                image.load()
            except Exception:
                st.error("❌ Could not read this file as an image.")
                return
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Process button
            if st.button("🎯 Process Image", type="primary", use_container_width=True):
                process_image(uploaded_file, image)
    
    with col2:
        st.markdown('<h2 class="sub-header">📝 Results</h2>', unsafe_allow_html=True)
        
        # Display results if available
        if 'caption' in st.session_state:
            st.markdown('<div class="caption-box">', unsafe_allow_html=True)
            st.markdown("**🔍 Raw Caption:**")
            st.write(st.session_state.caption)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if 'explanation' in st.session_state:
            st.markdown('<div class="explanation-box">', unsafe_allow_html=True)
            st.markdown("**💡 Accessible Explanation:**")
            st.write(st.session_state.explanation)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Audio player
        if 'audio_data' in st.session_state:
            st.markdown('<div class="audio-player">', unsafe_allow_html=True)
            st.markdown("**🔊 Audio Description:**")
            
            # Audio player
            st.audio(st.session_state.audio_data, format='audio/wav')
            
            # Re-read button
            if st.button("🔄 Re-read Explanation", use_container_width=True):
                st.audio(st.session_state.audio_data, format='audio/wav')
            
            st.markdown('</div>', unsafe_allow_html=True)

def process_image(uploaded_file, image):
    """Process the uploaded image through the complete pipeline"""
    
    try:
        with st.spinner("🔄 Processing image... This may take 30-60 seconds on first run"):
            
            captioner, explainer, tts_generator = load_models()
            st.session_state.models_loaded = True
            
            # Step 1: Generate caption
            with st.spinner("🔍 Generating image caption..."):
                caption = captioner.generate_caption(image)
                st.session_state.caption = caption
                logger.info(f"Generated caption: {caption}")
            
            # Step 2: Generate accessible explanation
            with st.spinner("💡 Creating accessible explanation..."):
                explanation = explainer.explain_for_visually_impaired(caption)
                st.session_state.explanation = explanation
                logger.info(f"Generated explanation: {explanation}")
            
            # Step 3: Convert to speech
            with st.spinner("🔊 Converting to speech..."):
                audio_data = tts_generator.text_to_speech(explanation)
                st.session_state.audio_data = audio_data
                logger.info("Audio generated successfully")
            
            st.success("✅ Processing complete! Audio will play automatically.")
            
            # Auto-play audio
            st.audio(audio_data, format='audio/wav', autoplay=True)
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        st.error(f"❌ Error processing image: {str(e)}")
        st.info("💡 Try uploading a different image or check the console for more details.")

if __name__ == "__main__":
    main() 