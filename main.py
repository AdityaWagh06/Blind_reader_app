import streamlit as st
import streamlit.components.v1  # noqa: F401  (used as st.components.v1.html)
import logging
import html
import time
from PIL import Image
import base64
from config import Config
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
    initial_sidebar_state="collapsed",
)

# Only sizes and spacing here: colours come from the theme so light and dark mode both stay readable
st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 1200px; }
    .hero h1 { font-size: 2.6rem; margin-bottom: 0.2rem; }
    .hero p { font-size: 1.15rem; opacity: 0.8; margin-top: 0; }
    .badges span {
        display: inline-block; padding: 0.15rem 0.7rem; margin: 0 0.4rem 0.4rem 0;
        border: 1px solid rgba(128,128,128,0.4); border-radius: 999px; font-size: 0.85rem;
    }
    .stMarkdown p.description { font-size: 1.6rem; line-height: 1.45; font-weight: 600; margin: 0.2rem 0 0.8rem; }
    .stButton button { font-size: 1.1rem; padding: 0.6rem 1rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="📦 Loading AI models (first run downloads ~1 GB)...")
def load_models():
    """Load models once per server process, shared across sessions"""
    return (
        ImageCaptioner(Config.BLIP_MODEL),
        TextExplainer(Config.T5_MODEL),
        TTSGenerator(use_bark=False),
    )


def play_audio(audio_bytes):
    """Speak the audio now. st.audio(autoplay=True) skips media it has already played, so re-reads stayed silent."""
    st.session_state.play_count = st.session_state.get('play_count', 0) + 1
    b64 = base64.b64encode(audio_bytes).decode()
    # The counter makes each call new HTML so the iframe remounts and plays again
    st.components.v1.html(
        f'<audio autoplay src="data:audio/wav;base64,{b64}" data-n="{st.session_state.play_count}"></audio>',
        height=0,
    )


def render_sidebar():
    with st.sidebar:
        st.header("How it works")
        st.markdown(f"""
1. **See**: `{Config.BLIP_MODEL}` describes the photo.
2. **Explain**: `{Config.T5_MODEL}` turns it into a clear sentence.
3. **Speak**: your computer's built-in voice reads it aloud.
""")
        st.header("Privacy")
        st.markdown("Everything runs on this computer. Photos are never uploaded to any server or API.")
        st.header("Tips")
        st.markdown("- Hold the camera steady, about 30 cm away.\n- Good light helps a lot.\n- Press **Read aloud again** to replay.")
        st.caption(f"{Config.APP_NAME} v{Config.APP_VERSION}")


def main():
    """Main application function"""
    render_sidebar()

    st.markdown("""
<div class="hero">
  <h1>👁️ Blind Reader Assistant</h1>
  <p>Take or upload a photo and hear what is in it.</p>
  <div class="badges"><span>🔒 Runs offline</span><span>🆓 Free, open models</span><span>🔊 Speaks automatically</span></div>
</div>
""", unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("1. Choose a photo")
        upload_tab, camera_tab = st.tabs(["📁 Upload", "📷 Camera"])
        with upload_tab:
            uploaded = st.file_uploader(
                "Upload an image (PNG or JPG)",
                type=[f.lstrip('.') for f in Config.SUPPORTED_IMAGE_FORMATS],
            )
        with camera_tab:
            snapped = st.camera_input("Take a photo")

        source = snapped or uploaded
        image = None
        if source is not None:
            if source.size > Config.MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"❌ This file is larger than {Config.MAX_FILE_SIZE_MB} MB. Please choose a smaller image.")
                source = None
            else:
                try:
                    image = Image.open(source)
                    image.load()
                except Exception:
                    st.error("❌ Could not read this file as an image.")
                    source = None
        if image is not None:
            st.image(image, caption="Your photo", use_container_width=True)

    with right:
        st.subheader("2. Hear the description")
        # Describe each new photo automatically: one less button to find with a screen reader
        if source is not None and st.session_state.get('image_key') != source.file_id:
            st.session_state.image_key = source.file_id
            process_image(image)

        if 'explanation' not in st.session_state:
            st.info("Your description will appear here and be read aloud as soon as you choose a photo.")
            return

        with st.container(border=True):
            st.markdown(f'<p class="description" role="status">{html.escape(st.session_state.explanation)}</p>',
                        unsafe_allow_html=True)
            if st.button("🔊 Read aloud again", type="primary", use_container_width=True):
                play_audio(st.session_state.audio_data)
            st.audio(st.session_state.audio_data, format='audio/wav')

        with st.expander("Details"):
            st.markdown(f"**Raw caption:** {st.session_state.caption}")
            st.markdown(f"**Processing time:** {st.session_state.elapsed:.1f} s")


def process_image(image):
    """Run caption -> explanation -> speech and store results in session_state"""
    try:
        captioner, explainer, tts_generator = load_models()
        start = time.time()
        with st.status("Describing your photo...", expanded=True) as status:
            st.write("🔍 Looking at the image...")
            caption = captioner.generate_caption(image)
            st.write("💡 Writing a clear description...")
            explanation = explainer.explain_for_visually_impaired(caption)
            st.write("🔊 Preparing speech...")
            audio_data = tts_generator.text_to_speech(explanation)
            status.update(label="Done", state="complete", expanded=False)
        logger.info(f"Caption: {caption} | Explanation: {explanation}")

        st.session_state.update(caption=caption, explanation=explanation,
                                audio_data=audio_data, elapsed=time.time() - start)
        play_audio(audio_data)

    except Exception as e:
        logger.exception("Error processing image")
        st.error(f"❌ Something went wrong while describing this photo: {e}")
        for key in ('image_key', 'explanation'):  # allow a retry and don't show the previous photo's result
            st.session_state.pop(key, None)


if __name__ == "__main__":
    main()
