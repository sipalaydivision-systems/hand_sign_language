"""
Web Based Hand Gesture Filipino Sign Language Voice Translator
Flask server - serves the web application.
"""

import io
from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
from deep_translator import GoogleTranslator

app = Flask(__name__)

# Initialize translators (reuse for performance)
en_to_fil_translator = GoogleTranslator(source='en', target='tl')
fil_to_en_translator = GoogleTranslator(source='tl', target='en')

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('translator.html')


@app.route('/api/translate', methods=['POST'])
def translate():
    """
    Google Translate endpoint for accurate sentence translation.
    Accepts JSON: { "text": "...", "to": "fil" or "en" }
    Returns JSON: { "translated": "...", "source": "en", "target": "fil" }
    """
    data = request.get_json(silent=True)
    if not data or not data.get('text'):
        return jsonify({"error": "No text provided"}), 400

    text = data['text'].strip()
    target = data.get('to', 'fil')

    try:
        if target in ('fil', 'tl', 'fil-PH'):
            result = en_to_fil_translator.translate(text)
            return jsonify({
                "translated": result,
                "source": "en",
                "target": "fil"
            })
        else:
            result = fil_to_en_translator.translate(text)
            return jsonify({
                "translated": result,
                "source": "fil",
                "target": "en"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Google AI Text-to-Speech endpoint.
    Accepts JSON: { "text": "...", "lang": "fil" or "en" }
    Returns MP3 audio stream.
    """
    data = request.get_json(silent=True)
    if not data or not data.get('text'):
        return jsonify({"error": "No text provided"}), 400

    text = data['text'].strip()
    lang = data.get('lang', 'fil')  # 'fil' for Filipino, 'en' for English

    # Map frontend language codes to gTTS codes
    lang_map = {
        'fil-PH': 'tl',   # gTTS uses 'tl' for Tagalog/Filipino
        'fil': 'tl',
        'tl': 'tl',
        'en-US': 'en',
        'en': 'en'
    }
    tts_lang = lang_map.get(lang, 'tl')

    try:
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='speech.mp3'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 55)
    print("  Filipino Sign Language Voice Translator (Web)")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)
