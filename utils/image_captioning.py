import logging
import torch
from PIL import Image
import requests
from transformers import BlipProcessor, BlipForConditionalGeneration
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class ImageCaptioner:
    """Image captioning using BLIP model from Salesforce"""
    
    def __init__(self):
        """Initialize the BLIP model for image captioning"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        try:
            # Load BLIP model and processor
            logger.info("Loading BLIP model for image captioning...")
            self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            
            # Move model to appropriate device
            self.model.to(self.device)
            logger.info("BLIP model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading BLIP model: {str(e)}")
            raise RuntimeError(f"Failed to load BLIP model: {str(e)}")
    
    def preprocess_image(self, image):
        """Preprocess the image for BLIP model"""
        try:
            # Convert PIL image to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize image if it's too large (BLIP works well with standard sizes)
            max_size = 512
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise RuntimeError(f"Failed to preprocess image: {str(e)}")
    
    def generate_caption(self, image):
        """
        Generate a caption for the given image
        
        Args:
            image: PIL Image object
            
        Returns:
            str: Generated caption
        """
        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image)
            
            # Prepare inputs for the model
            inputs = self.processor(processed_image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=50,
                    num_beams=5,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode the generated caption
            caption = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the caption
            caption = caption.strip()
            if not caption.endswith('.'):
                caption += '.'
            
            logger.info(f"Generated caption: {caption}")
            return caption
            
        except Exception as e:
            logger.error(f"Error generating caption: {str(e)}")
            raise RuntimeError(f"Failed to generate caption: {str(e)}")
    
    def generate_caption_with_prompt(self, image, prompt):
        """
        Generate a caption with a specific prompt
        
        Args:
            image: PIL Image object
            prompt: str, the prompt to guide caption generation
            
        Returns:
            str: Generated caption
        """
        try:
            # Preprocess the image
            processed_image = self.preprocess_image(image)
            
            # Prepare inputs with prompt
            inputs = self.processor(processed_image, text=prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=50,
                    num_beams=5,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode the generated caption
            caption = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the caption
            caption = caption.strip()
            if not caption.endswith('.'):
                caption += '.'
            
            logger.info(f"Generated caption with prompt '{prompt}': {caption}")
            return caption
            
        except Exception as e:
            logger.error(f"Error generating caption with prompt: {str(e)}")
            raise RuntimeError(f"Failed to generate caption with prompt: {str(e)}") 