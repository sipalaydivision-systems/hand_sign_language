/**
 * Hand Gesture Filipino Language Voice Translator — App Controller
 * Camera, MediaPipe Hands, UI, TTS. (recognizer.js handles detection)
 */

const app = {
    running: false,
    camera: null,
    hands: null,
    recognizer: new HandSignRecognizer(),
    suggester: new WordSuggester(COMMON_WORDS),
    fps: 0,
    frameCount: 0,
    fpsStartTime: performance.now(),
    settings: {
        stableThreshold: 15,
        letterCooldown: 1.0,
        speechRate: 1.0,
        speechPitch: 1.0,
        voiceEngine: 'google-ai', // 'google-ai' or 'browser'
        ttsLang: 'fil-PH', // 'fil-PH' or 'en-US'
    }
};

// ── DOM refs ──
const dom = {
    video: document.getElementById('video'),
    canvas: document.getElementById('canvas'),
    cameraPlaceholder: document.getElementById('camera-placeholder'),
    btnCamera: document.getElementById('btn-camera'),
    fpsDisplay: document.getElementById('fps-display'),
    detectedSign: document.getElementById('detected-sign'),
    handInfo: document.getElementById('hand-info'),
    confidenceInfo: document.getElementById('confidence-info'),
    progressFill: document.getElementById('progress-fill'),
    holdingSign: document.getElementById('holding-sign'),
    textContent: document.getElementById('text-content'),
    translationContent: document.getElementById('translation-content'),
    suggestionBtns: document.querySelectorAll('.suggestion-btn'),
    btnSpeak: document.getElementById('btn-speak'),
    btnSpace: document.getElementById('btn-space'),
    btnDelete: document.getElementById('btn-delete'),
    btnClear: document.getElementById('btn-clear'),
    btnCopy: document.getElementById('btn-copy'),
    btnHelp: document.getElementById('btn-help'),
    btnSettings: document.getElementById('btn-settings'),
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    helpModal: document.getElementById('help-modal'),
    settingsModal: document.getElementById('settings-modal'),
    btnSaveSettings: document.getElementById('btn-save-settings'),
    settingStability: document.getElementById('setting-stability'),
    stabilityValue: document.getElementById('stability-value'),
    settingCooldown: document.getElementById('setting-cooldown'),
    cooldownValue: document.getElementById('cooldown-value'),
    settingRate: document.getElementById('setting-rate'),
    rateValue: document.getElementById('rate-value'),
    settingPitch: document.getElementById('setting-pitch'),
    pitchValue: document.getElementById('pitch-value'),
    voiceEngineSelect: document.getElementById('voice-engine'),
    ttsLangSelect: document.getElementById('tts-lang'),
    voicePicker: document.getElementById('voice-picker'),
    voiceSelect: document.getElementById('voice-select'),
    voicesList: document.getElementById('voices-list'),
    btnTestVoice: document.getElementById('btn-test-voice'),
    voiceTip: document.getElementById('voice-tip'),
};

// ── MediaPipe ──
function initMediaPipe() {
    const hands = new Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${file}`
    });
    hands.setOptions({
        maxNumHands: 1,
        modelComplexity: 0,
        minDetectionConfidence: 0.6,
        minTrackingConfidence: 0.5
    });
    hands.onResults(onHandResults);
    app.hands = hands;
    setStatus('Ready');
}

// ── Camera ──
function startCamera() {
    if (app.running) return;
    dom.video.style.display = 'block';
    dom.cameraPlaceholder.style.display = 'none';

    app.camera = new Camera(dom.video, {
        onFrame: async () => {
            if (app.hands) await app.hands.send({ image: dom.video });
        },
        width: 640,
        height: 480
    });

    app.camera.start();
    app.running = true;
    dom.statusDot.classList.add('active');
    if (dom.btnCamera) {
        dom.btnCamera.innerHTML = '<span class="material-symbols-rounded">stop</span><span>Stop Camera</span>';
        dom.btnCamera.classList.remove('btn-primary');
        dom.btnCamera.classList.add('btn-accent');
    }
    setStatus('Camera running...');
}

function stopCamera() {
    if (!app.running) return;
    if (app.camera) app.camera.stop();
    app.running = false;
    dom.video.style.display = 'none';
    dom.cameraPlaceholder.style.display = 'flex';
    const ctx = dom.canvas.getContext('2d');
    ctx.clearRect(0, 0, dom.canvas.width, dom.canvas.height);
    dom.statusDot.classList.remove('active');
    if (dom.btnCamera) {
        dom.btnCamera.innerHTML = '<span class="material-symbols-rounded">play_arrow</span><span>Start Camera</span>';
        dom.btnCamera.classList.remove('btn-accent');
        dom.btnCamera.classList.add('btn-primary');
    }
    setStatus('Camera stopped');
    clearDetection();
}

function toggleCamera() { app.running ? stopCamera() : startCamera(); }

// ── Hand Results ──
function onHandResults(results) {
    const canvas = dom.canvas;
    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        for (const lm of results.multiHandLandmarks) {
            drawConnectors(ctx, lm, HAND_CONNECTIONS, { color: '#FCD116', lineWidth: 3 });
            drawLandmarks(ctx, lm, { color: '#0038A8', fillColor: '#FCD116', lineWidth: 2, radius: 4 });
        }
    }
    ctx.restore();

    // Z trail
    const trail = app.recognizer.zTracker.getTrailPoints();
    if (trail.length > 1) {
        ctx.save();
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        for (let i = 1; i < trail.length; i++) {
            const a = i / trail.length;
            ctx.strokeStyle = `rgba(206, 17, 38, ${a * 0.8})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.moveTo(trail[i-1].x * canvas.width, trail[i-1].y * canvas.height);
            ctx.lineTo(trail[i].x * canvas.width, trail[i].y * canvas.height);
            ctx.stroke();
        }
        ctx.restore();
    }

    // Recognition
    const rec = app.recognizer.processResults(results);
    if (rec) {
        updateDetection(rec);
        if (rec.sign.length === 1 && /^[A-Z]$/.test(rec.sign)) {
            if (app.recognizer.addLetter(rec.sign, rec.confidence)) {
                updateTextDisplay();
                updateSuggestions();
                pulseElement(dom.btnSpace);
            }
        }
        if (app.recognizer.stableFrames > 0) {
            const p = Math.min(app.recognizer.stableFrames / app.recognizer.stableThreshold, 1.0);
            dom.progressFill.style.width = (p * 100) + '%';
            dom.holdingSign.textContent = app.recognizer.lastStableSign;
        } else {
            dom.progressFill.style.width = '0%';
            dom.holdingSign.textContent = '';
        }
    } else {
        clearDetection();
    }

    // FPS
    app.frameCount++;
    const elapsed = (performance.now() - app.fpsStartTime) / 1000;
    if (elapsed >= 1) {
        app.fps = Math.round(app.frameCount / elapsed);
        app.frameCount = 0;
        app.fpsStartTime = performance.now();
        dom.fpsDisplay.textContent = `${app.fps} FPS`;
    }
}

// ── UI Helpers ──
function updateDetection(r) {
    dom.detectedSign.textContent = r.sign;
    dom.detectedSign.style.color = r.confidence > 0.7 ? 'var(--ph-red)' : r.drawing ? 'var(--ph-gold-dark)' : 'var(--ph-blue)';
    dom.handInfo.textContent = r.hand;
    dom.confidenceInfo.textContent = `${Math.round(r.confidence * 100)}%`;
}

function clearDetection() {
    dom.detectedSign.textContent = '—';
    dom.detectedSign.style.color = 'var(--border)';
    dom.handInfo.textContent = '—';
    dom.confidenceInfo.textContent = '—';
    dom.progressFill.style.width = '0%';
    dom.holdingSign.textContent = '';
}

function updateTextDisplay() {
    const t = app.recognizer.textBuffer;
    if (t) {
        dom.textContent.textContent = t;
    } else {
        dom.textContent.innerHTML = ''; // Clear and let placeholder show
    }
    getAccurateTranslation(t);
}

function updateSuggestions() {
    const text = app.recognizer.textBuffer;
    const words = text.split(' ');
    const cur = words[words.length - 1]?.toLowerCase() || '';
    const sug = app.suggester.getSuggestions(cur);
    app.recognizer.suggestions = sug;
    dom.suggestionBtns.forEach((btn, i) => {
        const sugText = btn.querySelector('.sug-text');
        if (!sugText) return;
        if (i < sug.length) {
            sugText.textContent = sug[i];
            btn.classList.add('active');
        } else {
            sugText.textContent = '—';
            btn.classList.remove('active');
        }
    });
}

function selectSuggestion(idx) {
    const sug = app.recognizer.suggestions;
    if (idx < 0 || idx >= sug.length) return;
    const words = app.recognizer.textBuffer.split(' ');
    words[words.length - 1] = sug[idx].toUpperCase();
    app.recognizer.textBuffer = words.join(' ') + ' ';
    app.recognizer.suggestions = [];
    app.recognizer.lastAddedLetter = '';
    updateTextDisplay();
    updateSuggestions();
}

function pulseElement(el) {
    el.classList.remove('pulse');
    void el.offsetWidth;
    el.classList.add('pulse');
}

function setStatus(text) { dom.statusText.textContent = text; }

// ── TTS ──
let cachedVoices = [];
function loadVoices() { cachedVoices = speechSynthesis.getVoices(); populateVoiceDropdown(); }
speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

function populateVoiceDropdown() {
    const voices = cachedVoices.length ? cachedVoices : speechSynthesis.getVoices();
    if (!dom.voiceSelect) return;
    const lang = app.settings.ttsLang;
    const accept = lang === 'fil-PH' ? ['fil-ph','fil','tl-ph','tl'] : ['en-us','en-gb','en-au','en'];
    const match = voices.filter(v => { const vl = v.lang.toLowerCase(); return accept.some(a => vl === a || vl.startsWith(a+'-')); });
    const prev = dom.voiceSelect.value;
    dom.voiceSelect.innerHTML = '<option value="auto">Auto (Best)</option>';
    match.forEach((v, i) => {
        const o = document.createElement('option');
        o.value = i.toString(); o.dataset.voiceName = v.name;
        o.textContent = `${v.name} ${voiceLabel(v)}`;
        dom.voiceSelect.appendChild(o);
    });
    if (prev !== 'auto') { const e = [...dom.voiceSelect.options].find(o => o.value === prev); if (e) dom.voiceSelect.value = prev; }
    dom.voiceSelect._voices = match;
    updateVoicesInfo(match);
    if (dom.voiceTip) {
        const hasNeural = match.some(v => { const n = v.name.toLowerCase(); return n.includes('neural') || n.includes('natural') || (n.includes('google') && !n.includes('espeak')); });
        dom.voiceTip.style.display = hasNeural ? 'none' : 'block';
    }
}

function voiceLabel(v) {
    const n = v.name.toLowerCase();
    if (n.includes('neural') || n.includes('natural')) return '⭐';
    if (n.includes('online') || (n.includes('google') && !n.includes('espeak'))) return '☁️';
    if (!v.localService) return '☁️';
    return '💻';
}

function updateVoicesInfo(voices) {
    if (!voices.length) { dom.voicesList.innerHTML = '<em>No matching voices found for this language.</em>'; return; }
    dom.voicesList.innerHTML = voices.map(v => {
        const n = v.name.toLowerCase();
        let c = 'local';
        if (n.includes('neural') || n.includes('natural')) c = 'neural';
        else if (n.includes('online') || n.includes('google') || !v.localService) c = 'online';
        return `<div class="voice-item">${v.name} <span class="voice-quality ${c}">${voiceLabel(v)} ${c}</span></div>`;
    }).join('');
}

function getBestVoice(langCode) {
    const voices = cachedVoices.length ? cachedVoices : speechSynthesis.getVoices();
    if (!voices.length) return null;
    const accept = langCode === 'fil-PH' ? ['fil-ph','fil','tl-ph','tl'] : ['en-us','en-gb','en-au','en'];
    const match = voices.filter(v => { const vl = v.lang.toLowerCase(); return accept.some(a => vl === a || vl.startsWith(a+'-')); });
    if (!match.length) { const p = langCode.split('-')[0].toLowerCase(); return voices.find(v => v.lang.toLowerCase().startsWith(p)) || null; }
    function score(v) {
        const n = v.name.toLowerCase(); let s = 0;
        if (n.includes('google') && !n.includes('espeak')) s += 100;
        if (n.includes('microsoft') && (n.includes('online') || n.includes('neural'))) s += 90;
        if (n.includes('microsoft')) s += 50;
        if (n.includes('online')) s += 40; if (n.includes('natural')) s += 40; if (n.includes('neural')) s += 40;
        if (!v.localService) s += 30;
        return s;
    }
    match.sort((a, b) => score(b) - score(a));
    return match[0];
}

function speakText() {
    const raw = app.recognizer.textBuffer.trim();
    if (!raw) return;
    // Convert to lowercase so TTS reads words, not individual letters
    const text = raw.toLowerCase();
    const lang = app.settings.ttsLang;
    const engine = app.settings.voiceEngine;

    if (lang === 'fil-PH' && engine === 'google-ai') {
        // Use the already translated text if available
        const translatedText = dom.translationContent.textContent;
        speakWithGoogleAI(translatedText && translatedText !== '—' ? translatedText : text, lang);
    } else if (lang === 'fil-PH' && engine === 'browser') {
        const translatedText = dom.translationContent.textContent;
        speakWithBrowser(translatedText && translatedText !== '—' ? translatedText : text, lang);
    }
    else { // English
        engine === 'google-ai' ? speakWithGoogleAI(text, lang) : speakWithBrowser(text, lang);
    }
}

async function getAccurateTranslation(text) {
    if (!text) {
        dom.translationContent.textContent = '';
        return;
    }
    try {
        const r = await fetch('/api/translate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({text, to:'fil'}) });
        if (r.ok) {
            const d = await r.json();
            if (d.translated) {
                dom.translationContent.textContent = d.translated;
                return d.translated;
            }
        }
    } catch (e) { console.warn('[Translate] API failed:', e.message); }
    // Fallback to local if API fails
    const local = translateToFilipinoLocal(text);
    dom.translationContent.textContent = local || '';
    return local || text;
}

let currentAudio = null;
async function speakWithGoogleAI(text, lang) {
    stopAudio(); speechSynthesis.cancel();
    setStatus(`Speaking (${lang === 'fil-PH' ? 'Filipino' : 'English'})...`);
    try {
        const r = await fetch('/api/tts', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({text, lang}) });
        if (!r.ok) throw new Error((await r.json()).error || 'TTS failed');
        const blob = await r.blob(); const url = URL.createObjectURL(blob);
        currentAudio = new Audio(url);
        currentAudio.playbackRate = app.settings.speechRate;
        currentAudio.onended = () => { URL.revokeObjectURL(url); currentAudio = null; setStatus('Ready'); };
        currentAudio.onerror = () => { URL.revokeObjectURL(url); currentAudio = null; setStatus('Audio error'); speakWithBrowser(text, lang); };
        await currentAudio.play();
    } catch (e) { console.error('[TTS]', e); setStatus('Google AI unavailable, using browser'); speakWithBrowser(text, lang); }
}

function stopAudio() { if (currentAudio) { currentAudio.pause(); currentAudio.currentTime = 0; currentAudio = null; } }

function speakWithBrowser(text, lang) {
    stopAudio();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang; u.rate = app.settings.speechRate; u.pitch = app.settings.speechPitch;
    const v = getSelectedVoice(lang);
    if (v) { u.voice = v; u.lang = v.lang; }
    speechSynthesis.cancel(); speechSynthesis.speak(u);
    setStatus(`Speaking (${v ? v.name.split(' ')[0] : 'default'})...`);
    u.onend = () => setStatus('Ready');
}

function getSelectedVoice(lc) {
    if (dom.voiceSelect && dom.voiceSelect.value !== 'auto') {
        const vs = dom.voiceSelect._voices; const i = parseInt(dom.voiceSelect.value);
        if (vs && vs[i]) return vs[i];
    }
    return getBestVoice(lc);
}

function testVoice() {
    const lang = app.settings.ttsLang;
    const engine = app.settings.voiceEngine;
    const sample = lang === 'fil-PH' ? 'Kumusta! Magandang araw!' : 'Hello! Nice to meet you!';
    if (engine === 'google-ai') { speakWithGoogleAI(sample, lang); return; }
    stopAudio();
    const u = new SpeechSynthesisUtterance(sample);
    u.lang = lang; u.rate = app.settings.speechRate; u.pitch = app.settings.speechPitch;
    const v = getSelectedVoice(lang);
    if (v) { u.voice = v; u.lang = v.lang; }
    speechSynthesis.cancel(); speechSynthesis.speak(u);
    setStatus(`Testing: ${v ? v.name.split(' ')[0] : 'default'}...`);
    u.onend = () => setStatus('Ready');
}

function updateEngineUI() {
    const engine = app.settings.voiceEngine;
    dom.voicePicker.style.display = engine === 'browser' ? 'block' : 'none';
    dom.voiceTip.textContent = engine === 'google-ai'
        ? 'Google AI — fluent in Filipino & English.'
        : 'For best quality, use Microsoft Edge browser.';
}

// ── Actions ──
function addSpace() { app.recognizer.addSpace(); updateTextDisplay(); updateSuggestions(); pulseElement(dom.btnSpace); }
function doBackspace() { app.recognizer.backspace(); updateTextDisplay(); updateSuggestions(); pulseElement(dom.btnDelete); }
function clearAll() { app.recognizer.clear(); updateTextDisplay(); updateSuggestions(); pulseElement(dom.btnClear); }
function copyText() {
    const t = app.recognizer.textBuffer.trim();
    if (!t) return;
    navigator.clipboard.writeText(t).then(() => {
        setStatus('Copied!');
        pulseElement(dom.btnCopy);
        setTimeout(() => setStatus('Ready'), 1500);
    });
}

// ── Modals ──
function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

function saveSettings() {
    app.settings.stableThreshold = parseInt(dom.settingStability.value);
    app.settings.letterCooldown = parseFloat(dom.settingCooldown.value);
    app.settings.speechRate = parseFloat(dom.settingRate.value);
    app.settings.speechPitch = parseFloat(dom.settingPitch.value);
    app.settings.voiceEngine = dom.voiceEngineSelect.value;
    app.settings.ttsLang = dom.ttsLangSelect.value;

    app.recognizer.stableThreshold = app.settings.stableThreshold;
    app.recognizer.letterCooldown = app.settings.letterCooldown;

    populateVoiceDropdown();
    updateEngineUI();
    closeModal('settings-modal');
    setStatus('Settings saved');
}

function loadSettings() {
    dom.settingStability.value = app.settings.stableThreshold;
    dom.stabilityValue.textContent = app.settings.stableThreshold;
    dom.settingCooldown.value = app.settings.letterCooldown;
    dom.cooldownValue.textContent = app.settings.letterCooldown.toFixed(1);
    dom.settingRate.value = app.settings.speechRate;
    dom.rateValue.textContent = app.settings.speechRate.toFixed(1);
    dom.settingPitch.value = app.settings.speechPitch;
    dom.pitchValue.textContent = app.settings.speechPitch.toFixed(1);
    dom.voiceEngineSelect.value = app.settings.voiceEngine;
    dom.ttsLangSelect.value = app.settings.ttsLang;
    updateEngineUI();
    populateVoiceDropdown();
}

// ── Events ──
function bindEvents() {
    dom.cameraPlaceholder.addEventListener('click', startCamera);
    if (dom.btnCamera) dom.btnCamera.addEventListener('click', toggleCamera);
    dom.btnSpace.addEventListener('click', addSpace);
    dom.btnDelete.addEventListener('click', doBackspace);
    dom.btnSpeak.addEventListener('click', speakText);
    dom.btnClear.addEventListener('click', clearAll);
    dom.btnCopy.addEventListener('click', copyText);
    dom.btnTestVoice.addEventListener('click', testVoice);
    dom.voiceEngineSelect.addEventListener('change', () => {
        app.settings.voiceEngine = dom.voiceEngineSelect.value;
        updateEngineUI();
    });
    dom.ttsLangSelect.addEventListener('change', () => {
        app.settings.ttsLang = dom.ttsLangSelect.value;
        populateVoiceDropdown();
    });

    dom.suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.classList.contains('active')) {
                selectSuggestion(parseInt(btn.dataset.index));
            }
        });
    });

    dom.btnHelp.addEventListener('click', () => openModal('help-modal'));
    dom.btnSettings.addEventListener('click', () => {
        loadSettings();
        openModal('settings-modal');
    });
    dom.btnSaveSettings.addEventListener('click', saveSettings);

    document.querySelectorAll('[data-close]').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.dataset.close));
    });
    document.querySelectorAll('.modal-backdrop').forEach(bd => {
        bd.addEventListener('click', () => bd.closest('.modal').classList.add('hidden'));
    });

    dom.settingStability.addEventListener('input', () => { dom.stabilityValue.textContent = dom.settingStability.value; });
    dom.settingCooldown.addEventListener('input', () => { dom.cooldownValue.textContent = parseFloat(dom.settingCooldown.value).toFixed(1); });
    dom.settingRate.addEventListener('input', () => { dom.rateValue.textContent = parseFloat(dom.settingRate.value).toFixed(1); });
    dom.settingPitch.addEventListener('input', () => { dom.pitchValue.textContent = parseFloat(dom.settingPitch.value).toFixed(1); });

    document.addEventListener('keydown', (e) => {
        if (['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
        if (document.querySelector('.modal:not(.hidden)')) return; // Don't trigger on open modal

        switch (e.key) {
            case ' ': e.preventDefault(); addSpace(); break;
            case 'Backspace': e.preventDefault(); doBackspace(); break;
            case 'Enter': e.preventDefault(); speakText(); break;
            case 'c': case 'C': if(e.ctrlKey) { e.preventDefault(); copyText(); } break;
            case 'r': case 'R': e.preventDefault(); clearAll(); break;
            case 's': case 'S': e.preventDefault(); startCamera(); break;
            case 'x': case 'X': e.preventDefault(); stopCamera(); break;
            case '1': case '2': case '3': case '4':
                const btn = document.querySelector(`.suggestion-btn[data-index="${parseInt(e.key)-1}"]`);
                if (btn && btn.classList.contains('active')) {
                    e.preventDefault();
                    selectSuggestion(parseInt(e.key) - 1);
                }
                break;
        }
    });
}

// ── Init ──
function init() {
    bindEvents();
    initMediaPipe();
    setStatus('Ready');
    loadVoices();
    setTimeout(loadVoices, 500);
    setTimeout(loadVoices, 2000);
    updateEngineUI();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
