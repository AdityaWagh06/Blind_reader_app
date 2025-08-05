#!/usr/bin/env python3
"""
Launcher script for Blind Reader Assistant
This script provides a user-friendly way to start the application.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        logger.error(f"Current version: {sys.version}")
        return False
    logger.info(f"✅ Python version: {sys.version}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'torch',
        'transformers',
        'pillow',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is not installed")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("💡 Run: pip install -r requirements.txt")
        return False
    
    return True

def run_streamlit():
    """Run the Streamlit application"""
    try:
        # Get the directory of this script
        script_dir = Path(__file__).parent
        main_file = script_dir / "main.py"
        
        if not main_file.exists():
            logger.error(f"❌ main.py not found at {main_file}")
            return False
        
        logger.info("🚀 Starting Blind Reader Assistant...")
        logger.info("📱 The app will open in your default web browser")
        logger.info("🌐 URL: http://localhost:8501")
        logger.info("⏹️  Press Ctrl+C to stop the application")
        logger.info("-" * 50)
        
        # Change to the script directory and run streamlit
        os.chdir(script_dir)
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py"])
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n👋 Application stopped by user")
        return True
    except Exception as e:
        logger.error(f"❌ Error running Streamlit: {e}")
        return False

def main():
    """Main launcher function"""
    logger.info("👁️ Blind Reader Assistant Launcher")
    logger.info("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check dependencies
    if not check_dependencies():
        logger.info("\n💡 To install dependencies:")
        logger.info("1. Create a virtual environment: python -m venv venv")
        logger.info("2. Activate it: source venv/bin/activate (or venv\\Scripts\\activate on Windows)")
        logger.info("3. Install requirements: pip install -r requirements.txt")
        return False
    
    # Run the application
    return run_streamlit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 