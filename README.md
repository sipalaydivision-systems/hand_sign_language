# ✋ Hand Gesture Filipino Language Voice Translator

A powerful, accessible application that recognizes hand gestures for Filipino Sign Language and converts it to text with real-time translation and text-to-speech capabilities.

## Features

- 🎥 **Real-time Hand Sign Recognition** - Uses MediaPipe for accurate hand pose detection
- 📝 **ASL Letter Recognition** - Recognizes ASL letters A-Z with confidence scoring
- 🤖 **AI-Powered Word Suggestions** - Google Generative AI provides smart word completions
- 🌐 **Multi-language Translation** - English ↔ Filipino translation powered by Google Translate
- 🔊 **Text-to-Speech** - gTTS generates natural-sounding speech in multiple languages
- ♿ **Accessibility First** - Designed for persons with disabilities (PWD)
  - Large buttons and text
  - High contrast UI
  - Keyboard shortcuts
  - Clear visual feedback

## System Components

### 1. Desktop Application (GUI)
- **Location:** `build/HandSignLanguage/sign_language_app.py`
- **Framework:** tkinter + CustomTkinter
- **Features:**
  - Full-screen camera interface
  - Real-time sign detection
  - Live text generation
  - Settings and help dialogs

### 2. Web Application (Flask)
- **Location:** `web_app/`
- **API Endpoints:**
  - `/` - Main interface
  - `/api/translate` - Translation service
  - `/api/tts` - Text-to-speech service
- **Deployment:** Railway, Heroku, or any WSGI-compatible platform

## Installation

### Requirements
- Python 3.10+
- Webcam for hand detection
- Internet connection (for AI features)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/wesleyhansplatil123/hand_sign_language.git
cd hand_sign_language
```

2. **Create virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Usage

### Desktop App
```bash
cd build/HandSignLanguage
python sign_language_app.py
```

### Web App (Local)
```bash
cd web_app
python app.py
# Open http://localhost:5000
```

## Supported Sign Language

- **Letters:** A B C D E F G H I K L O R U V W Y
- **Numbers:** 1 5
- **Special Signs:** Z (draw in air) • Thumbs Up
- **Total:** 25+ hand signs

## How to Use

1. **Start the application** and click the green **START CAMERA** button
2. **Show your hand** to the camera with good lighting
3. **Make ASL signs** - hold steady until recognized
4. The recognized letter appears in the text display
5. Use suggestions (1-5 keys) to auto-complete words
6. Press **SPACE** to add word breaks
7. Press **SPEAK** (Enter) to hear the text aloud
8. Press **CLEAR** (R) to erase all text

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `SPACE` | Add space |
| `BACKSPACE` | Delete character |
| `ENTER` | Speak text |
| `R` | Clear all |
| `1-5` | Select suggestion |
| `ESC` | Toggle fullscreen |

## Technologies Used

### Core
- **MediaPipe** - Hand pose detection
- **OpenCV** - Video processing
- **TensorFlow** - Neural networks

### AI/ML
- **Google Generative AI** - Word suggestions
- **Google Translate API** - Language translation
- **gTTS** - Text-to-speech

### Web
- **Flask** - Web framework
- **CustomTkinter** - Modern GUI
- **Bootstrap/CSS** - Responsive design

## Deployment

### Railway (Recommended for Web App)
1. Push to GitHub
2. Connect repository on [Railway.app](https://railway.app)
3. Set environment variables if needed
4. Deploy with one click

### Local Deployment
```bash
pip install -r requirements.txt
python web_app/app.py
```

## API Documentation

### Translate Endpoint
```bash
POST /api/translate
Content-Type: application/json

{
  "text": "Hello world",
  "to": "fil"  # or "en"
}

Response:
{
  "translated": "Kamustahan sa mundo",
  "source": "en",
  "target": "fil"
}
```

### Text-to-Speech Endpoint
```bash
POST /api/tts
Content-Type: application/json

{
  "text": "Hello",
  "lang": "en"  # "en" or "fil"
}

Response: Audio stream (MP3)
```

## Configuration

### Recognition Settings
- **Sign Hold Time:** 5-30 frames (default: 15)
- **Letter Cooldown:** 0.5-3.0 seconds (default: 1.0)
- **Detection Confidence:** Min 50%

Adjust these in the app's Settings dialog (⚙ icon).

## Known Limitations

- Requires good lighting for accurate recognition
- Works best with clear hand visibility
- Single-hand detection optimal (supports up to 2 hands)
- Needs stable internet for AI features

## Future Enhancements

- [ ] Support for sign sentences (not just letters)
- [ ] Filipino Sign Language (FSL) recognition
- [ ] Offline mode for core recognition
- [ ] Mobile app version
- [ ] Cloud-based model serving
- [ ] Real-time video streaming

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

Having issues? Check:
- Lighting and hand visibility
- Camera permissions
- Internet connection
- Python version (3.10+)

## License

MIT License - Feel free to use for personal and commercial projects

## Author

**Wesley Hans Platil**
- GitHub: [@wesleyhansplatil123](https://github.com/wesleyhansplatil123)
- Email: wesleyhansplatil@gmail.com

## Acknowledgments

- MediaPipe team for hand detection models
- Google for Generative AI and Translation APIs
- Open-source community for incredible libraries

---

**Built with ❤️ for accessibility and inclusion**
