# setup.py
"""
J.A.R.V.I.S Environment Setup Script
------------------------------------
• Safe to rerun
• Windows SSL fixed
• Dependency install with recovery
• Vosk model auto-install
• .env bootstrap
"""

import os
import sys
import subprocess
import certifi
import urllib.request
import zipfile
import shutil
from pathlib import Path

# ===================== GLOBALS =====================

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
VOSK_MODEL = "vosk-model-en-us-0.22"
VOSK_URL = f"https://alphacephei.com/vosk/models/{VOSK_MODEL}.zip"

ENV_FILE = BASE_DIR / ".env"
REQUIREMENTS = BASE_DIR / "requirements.txt"

# Fix SSL issues on Windows
os.environ["SSL_CERT_FILE"] = certifi.where()

# ===================== UTIL =====================

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.check_call(cmd)


def python_version_check():
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required.")
        sys.exit(1)


# ===================== DEPENDENCIES =====================

def install_dependencies():
    if not REQUIREMENTS.exists():
        print("❌ requirements.txt not found")
        return

    print("\n📦 Installing Python dependencies...\n")

    try:
        run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    except subprocess.CalledProcessError:
        print("❌ Dependency installation failed.")
        sys.exit(1)


# ===================== VOSK MODEL =====================

def install_vosk_model():
    model_path = MODELS_DIR / VOSK_MODEL

    if model_path.exists():
        print("✅ Vosk model already installed.")
        return

    print("\n🎧 Installing Vosk speech model...\n")

    MODELS_DIR.mkdir(exist_ok=True)

    zip_path = MODELS_DIR / f"{VOSK_MODEL}.zip"

    try:
        print("⬇ Downloading Vosk model...")
        urllib.request.urlretrieve(VOSK_URL, zip_path)

        print("📂 Extracting model...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(MODELS_DIR)

        print("✅ Vosk model installed.")

    except Exception as e:
        print("❌ Failed to install Vosk model:", e)
        if zip_path.exists():
            zip_path.unlink()
        sys.exit(1)

    finally:
        if zip_path.exists():
            zip_path.unlink()


# ===================== ENV FILE =====================

def setup_env():
    if ENV_FILE.exists():
        print("✅ .env file already exists.")
        return

    print("\n📝 Creating .env file...\n")

    ENV_FILE.write_text(
        "# J.A.R.V.I.S Configuration\n"
        "# ---------------------------------\n"
        "# REQUIRED\n"
        "GROQ_API_KEY=your_groq_api_key_here\n\n"
        "# OPTIONAL\n"
        "JARVIS_ENV=production\n"
        "JARVIS_VOICE=en-GB-RyanNeural\n"
        "JARVIS_UI_WIDTH=1000\n"
        "JARVIS_UI_HEIGHT=700\n"
    )

    print("⚠️  IMPORTANT:")
    print("➡ Open .env and set your GROQ_API_KEY before running JARVIS.\n")


# ===================== MAIN =====================

def setup_environment():
    print("\n🧠 Setting up J.A.R.V.I.S environment...\n")

    python_version_check()
    install_dependencies()
    install_vosk_model()
    setup_env()

    print("\n✅ Setup complete!\n")
    print("🚀 Start JARVIS with:")
    print("👉 python jarvis_supervisor.py\n")


if __name__ == "__main__":
    setup_environment()
