import logging
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class TextExplainer:
    """Text explanation using T5 model for creating accessible descriptions"""
    
    def __init__(self, model_name="google/flan-t5-small"):
        """
        Initialize the T5 model for text explanation
        
        Args:
            model_name: str, the T5 model variant to use (t5-small, t5-base, etc.)
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = model_name
        logger.info(f"Using device: {self.device}")
        logger.info(f"Using T5 model: {model_name}")
        
        try:
            # Load T5 model and tokenizer
            logger.info("Loading T5 model for text explanation...")
            self.tokenizer = T5Tokenizer.from_pretrained(model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(model_name)
            
            # Move model to appropriate device
            self.model.to(self.device)
            logger.info("T5 model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading T5 model: {str(e)}")
            raise RuntimeError(f"Failed to load T5 model: {str(e)}")
    
    def explain_for_visually_impaired(self, caption):
        """
        Convert a raw caption into an accessible explanation for visually impaired users
        
        Args:
            caption: str, the raw caption from the image
            
        Returns:
            str: Accessible explanation text
        """
        # The VizWiz-tuned captioner flags unreadable photos with this phrase; give actionable advice instead
        if caption.lower().startswith("quality issues"):
            return ("I can't make out this photo clearly. Please try again: hold the camera steady, "
                    "about 30 centimetres away, with more light.")

        try:
            # Create the prompt for T5
            prompt = f"Describe this scene in one complete sentence for a blind listener: {caption}"
            
            # Tokenize the input
            inputs = self.tokenizer.encode(
                prompt,
                max_length=512,
                truncation=True,
                return_tensors="pt"
            )
            inputs = inputs.to(self.device)
            
            # Generate explanation
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=150,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode the generated explanation
            explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the explanation
            explanation = explanation.strip()
            if not explanation.endswith('.'):
                explanation += '.'
            
            # Add accessibility enhancements
            explanation = self._enhance_for_accessibility(explanation)
            
            logger.info(f"Generated accessible explanation: {explanation}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            raise RuntimeError(f"Failed to generate explanation: {str(e)}")
    
    def _enhance_for_accessibility(self, text):
        """
        Enhance the text with accessibility features
        
        Args:
            text: str, the generated explanation
            
        Returns:
            str: Enhanced text with accessibility features
        """
        try:
            # Add context if the text is too short
            if len(text.split()) < 10:
                text = f"This image shows: {text}"
            
            # Ensure the text starts with a clear introduction
            if not text.lower().startswith(('this', 'the', 'a', 'an', 'in', 'on', 'at')):
                text = f"This image contains: {text}"
            
            # Add spatial context if missing
            spatial_indicators = ['left', 'right', 'top', 'bottom', 'center', 'middle', 'front', 'back']
            if not any(indicator in text.lower() for indicator in spatial_indicators):
                # Try to add basic spatial context
                if 'person' in text.lower() or 'people' in text.lower():
                    text = text[:-1] + ' in the center of the image.'
                elif 'object' in text.lower() or 'item' in text.lower():
                    text = text[:-1] + ' prominently displayed in the image.'
            
            return text
            
        except Exception as e:
            logger.warning(f"Error enhancing accessibility: {str(e)}")
            return text
    
    def explain_with_context(self, caption, context_type="general"):
        """
        Generate explanation with specific context type
        
        Args:
            caption: str, the raw caption
            context_type: str, type of context ("meme", "infographic", "scene", "general")
            
        Returns:
            str: Contextual explanation
        """
        try:
            # Create context-specific prompts
            context_prompts = {
                "meme": f"Explain this meme for a visually impaired person, describing the humor and visual elements: {caption}",
                "infographic": f"Describe this infographic for a visually impaired person, explaining the data and visual elements: {caption}",
                "scene": f"Describe this scene for a visually impaired person, explaining what is happening: {caption}",
                "general": f"Describe this scene in one complete sentence for a blind listener: {caption}"
            }
            
            prompt = context_prompts.get(context_type, context_prompts["general"])
            
            # Tokenize the input
            inputs = self.tokenizer.encode(
                prompt,
                max_length=512,
                truncation=True,
                return_tensors="pt"
            )
            inputs = inputs.to(self.device)
            
            # Generate explanation
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=150,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode the generated explanation
            explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the explanation
            explanation = explanation.strip()
            if not explanation.endswith('.'):
                explanation += '.'
            
            # Add accessibility enhancements
            explanation = self._enhance_for_accessibility(explanation)
            
            logger.info(f"Generated {context_type} explanation: {explanation}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating contextual explanation: {str(e)}")
            raise RuntimeError(f"Failed to generate contextual explanation: {str(e)}") 