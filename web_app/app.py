"""
Web Based Hand Gesture Filipino Sign Language Voice Translator
Flask server - serves the web application.
"""

import io
import os
import json
import re
import asyncio
from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
from deep_translator import GoogleTranslator
import edge_tts

EDGE_VOICES = {
    'female': 'fil-PH-BlessicaNeural',
    'male':   'fil-PH-AngeloNeural',
}

_tts_cache: dict = {}

async def _edge_tts_bytes(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    audio = b''
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            audio += chunk['data']
    return audio

app = Flask(__name__)

# Initialize translators (reuse for performance)
en_to_fil_translator = GoogleTranslator(source='en', target='tl')
fil_to_en_translator = GoogleTranslator(source='tl', target='en')

_translate_cache: dict = {}

# Initialize Gemini AI for word suggestions
_gemini_model = None
try:
    import google.generativeai as genai
    _config_path = os.path.join(os.path.dirname(__file__), '..', 'gemini_config.json')
    with open(_config_path) as f:
        _cfg = json.load(f)
    genai.configure(api_key=_cfg['api_key'])
    _gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    pass

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
    cache_key = f"{text}:{target}"

    if cache_key in _translate_cache:
        return jsonify(_translate_cache[cache_key])

    try:
        if target in ('fil', 'tl', 'fil-PH'):
            result = en_to_fil_translator.translate(text)
            payload = {"translated": result, "source": "en", "target": "fil"}
        else:
            result = fil_to_en_translator.translate(text)
            payload = {"translated": result, "source": "fil", "target": "en"}
        _translate_cache[cache_key] = payload
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Neural Text-to-Speech endpoint (Edge TTS → gTTS fallback).
    Accepts JSON: { "text": "...", "voice": "female" | "male" }
    Returns MP3 audio stream.
    """
    data = request.get_json(silent=True)
    if not data or not data.get('text'):
        return jsonify({"error": "No text provided"}), 400

    text = data['text'].strip()
    voice_key = data.get('voice', 'female')
    voice = EDGE_VOICES.get(voice_key, EDGE_VOICES['female'])
    cache_key = f"{voice}:{text}"

    # Return cached audio instantly
    if cache_key in _tts_cache:
        return send_file(io.BytesIO(_tts_cache[cache_key]), mimetype='audio/mpeg',
                         as_attachment=False, download_name='speech.mp3')

    # Try Microsoft Edge Neural TTS
    try:
        loop = asyncio.new_event_loop()
        audio = loop.run_until_complete(_edge_tts_bytes(text, voice))
        loop.close()
        _tts_cache[cache_key] = audio
        return send_file(io.BytesIO(audio), mimetype='audio/mpeg',
                         as_attachment=False, download_name='speech.mp3')
    except Exception:
        pass

    # Fallback to gTTS
    try:
        tts = gTTS(text=text, lang='tl', slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        audio = buf.getvalue()
        _tts_cache[cache_key] = audio
        return send_file(io.BytesIO(audio), mimetype='audio/mpeg',
                         as_attachment=False, download_name='speech.mp3')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/suggest', methods=['POST'])
def suggest_words():
    """
    Gemini AI word suggestions.
    Accepts JSON: { "prefix": "hel", "context": "full text so far" }
    Returns JSON: { "suggestions": ["hello", "help", ...] }
    """
    data = request.get_json(silent=True)
    if not data or not data.get('prefix'):
        return jsonify({"suggestions": []}), 200

    prefix = data['prefix'].strip().lower()
    context = data.get('context', '').strip()

    if not _gemini_model:
        return jsonify({"suggestions": []}), 200

    try:
        prompt = (
            f'You are helping a sign language user build words letter by letter. '
            f'Context so far: "{context}". '
            f'The user is typing the word starting with "{prefix}". '
            f'Suggest 5 likely word completions. '
            f'Return ONLY a JSON array like ["word1","word2","word3","word4","word5"]. No explanation.'
        )
        response = _gemini_model.generate_content(prompt)
        match = re.search(r'\[.*?\]', response.text, re.DOTALL)
        if match:
            suggestions = json.loads(match.group())
            return jsonify({"suggestions": [s.lower() for s in suggestions[:5]]})
    except Exception:
        pass

    return jsonify({"suggestions": []}), 200


if __name__ == '__main__':
    print("=" * 55)
    print("  Filipino Sign Language Voice Translator (Web)")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)
