# 👁️ Blind Reader Assistant

A fully offline Python application that helps visually impaired users understand images by providing audio descriptions. The app uses open-source AI models to caption images, create accessible explanations, and convert them to speech.

## 🚀 Features

- **🖼️ Image Upload**: Support for PNG, JPG, JPEG formats
- **🔍 BLIP Captioning**: Uses Salesforce's BLIP model for accurate image descriptions
- **💡 T5 Explanation**: Converts raw captions into accessible explanations using T5
- **🔊 Text-to-Speech**: High-quality speech synthesis using Bark (with Coqui TTS fallback)
- **🎨 Beautiful UI**: Modern Streamlit interface with custom styling
- **🔄 Re-read Function**: Button to replay audio descriptions
- **⚡ Offline Operation**: No external APIs required - everything runs locally

## 🏗️ Architecture

The application follows a modular pipeline:

1. **Image Captioning** (`utils/image_captioning.py`): BLIP model generates raw captions
2. **Text Explanation** (`utils/text_explainer.py`): T5 model creates accessible descriptions
3. **Speech Synthesis** (`utils/tts_generator.py`): Bark/Coqui TTS converts text to audio
4. **Web Interface** (`main.py`): Streamlit app orchestrates the entire process

## 📋 Requirements

- Python 3.8+
- 8GB+ RAM (recommended)
- GPU support (optional, for faster processing)
- Internet connection (only for initial model download)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd blind_reader_app
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run main.py
```

The app will be available at `http://localhost:8501`

## 🎯 Usage

1. **Upload Image**: Click "Browse files" and select an image (PNG, JPG, JPEG)
2. **Process**: Click "Process Image" button
3. **Wait**: The first run may take 30-60 seconds as models download
4. **Listen**: Audio description will play automatically
5. **Re-read**: Use the "Re-read Explanation" button to replay audio

## 🔧 Configuration

### Model Selection
- **BLIP Model**: `Salesforce/blip-image-captioning-base`
- **T5 Model**: `t5-small` (can be changed to `t5-base` for better quality)
- **TTS Engine**: Bark (primary) with Coqui TTS fallback

### Performance Optimization
- **GPU**: Automatically detected and used if available
- **CPU Fallback**: Works on CPU-only systems (slower but functional)
- **Model Caching**: Models are cached after first download

## 🐛 Troubleshooting

### Common Issues

1. **Out of Memory Error**
   - Reduce image size before uploading
   - Close other applications
   - Use CPU-only mode if GPU memory is insufficient

2. **Model Download Issues**
   - Check internet connection
   - Clear HuggingFace cache: `rm -rf ~/.cache/huggingface/`

3. **Audio Not Playing**
   - Check browser audio settings
   - Try different browser
   - Verify system audio is working

4. **Slow Processing**
   - First run downloads models (30-60 seconds)
   - Subsequent runs are faster
   - GPU acceleration recommended for better performance

### Error Messages

- **"Failed to load BLIP model"**: Check internet connection and try again
- **"Failed to load T5 model"**: Verify transformers installation
- **"TTS failed"**: Bark will automatically fallback to Coqui TTS

## 📁 Project Structure

```
blind_reader_app/
├── main.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── image_captioning.py    # BLIP image captioning
│   ├── text_explainer.py      # T5 text explanation
│   └── tts_generator.py       # Bark/Coqui TTS
└── assets/                # Static assets
    └── sample.png          # Sample image for testing
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Salesforce** for the BLIP model
- **Google** for the T5 model
- **Suno AI** for Bark TTS
- **Coqui AI** for Coqui TTS
- **Streamlit** for the web framework

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information

## 🔮 Future Enhancements

- [ ] Support for video files
- [ ] Multiple language support
- [ ] Custom voice selection
- [ ] Batch processing
- [ ] Mobile app version
- [ ] Integration with screen readers
- [ ] Real-time processing
- [ ] Advanced accessibility features

---

**Made with ❤️ for the visually impaired community** 