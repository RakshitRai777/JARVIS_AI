import os
import sys
import subprocess
import platform

def install_dependencies():
    """Install required Python packages"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Install Vosk model if not present
    model_dir = os.path.join("models", "vosk-model-en-us-0.22")
    if not os.path.exists(model_dir):
        print("Downloading Vosk model...")
        import urllib.request
        import zipfile
        
        model_url = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
        zip_path = "vosk-model-en-us-0.22.zip"
        
        print(f"Downloading {model_url}...")
        urllib.request.urlretrieve(model_url, zip_path)
        
        print("Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            os.makedirs("models", exist_ok=True)
            zip_ref.extractall("models")
        
        # Clean up
        os.remove(zip_path)
        print("Vosk model installed successfully.")

def setup_environment():
    """Set up the development environment"""
    print("Setting up J.A.R.V.I.S development environment...")
    
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    
    # Install dependencies
    install_dependencies()
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# J.A.R.V.I.S Configuration\n")
            f.write("GROQ_API_KEY=your_groq_api_key_here\n")
        print("\nCreated .env file. Please update it with your API keys.")
    else:
        print("\nFound existing .env file. Please ensure it contains your API keys.")
    
    print("\nSetup complete! You can now run J.A.R.V.I.S with 'python app.py'")

if __name__ == "__main__":
    setup_environment()
