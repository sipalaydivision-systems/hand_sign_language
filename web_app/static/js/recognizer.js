/**
 * Hand Sign Recognizer — Ported from Python to JavaScript
 * Uses MediaPipe Hands landmarks to recognize ASL/FSL letters.
 */

// Landmark indices (same as MediaPipe convention)
const LM = {
    WRIST: 0,
    THUMB_CMC: 1, THUMB_MCP: 2, THUMB_IP: 3, THUMB_TIP: 4,
    INDEX_MCP: 5, INDEX_PIP: 6, INDEX_DIP: 7, INDEX_TIP: 8,
    MIDDLE_MCP: 9, MIDDLE_PIP: 10, MIDDLE_DIP: 11, MIDDLE_TIP: 12,
    RING_MCP: 13, RING_PIP: 14, RING_DIP: 15, RING_TIP: 16,
    PINKY_MCP: 17, PINKY_PIP: 18, PINKY_DIP: 19, PINKY_TIP: 20
};

// ==================== Z MOTION TRACKER ====================
class ZMotionTracker {
    constructor() {
        this.positions = [];
        this.maxPositions = 50;
        this.lastZTime = 0;
        this.zCooldown = 2.0;
        this.zDetected = false;
        this.drawingActive = false;
        this.minPointsForZ = 15;
    }

    addPosition(x, y, isPointing) {
        const now = performance.now() / 1000;

        if (isPointing) {
            this.positions.push({ x, y, t: now });
            if (this.positions.length > this.maxPositions) this.positions.shift();
            this.drawingActive = true;
        } else {
            if (this.drawingActive && this.positions.length >= this.minPointsForZ) {
                if (this._checkZPattern()) {
                    if (now - this.lastZTime > this.zCooldown) {
                        this.zDetected = true;
                        this.lastZTime = now;
                    }
                }
            }
            this.positions = [];
            this.drawingActive = false;
        }
    }

    _checkZPattern() {
        if (this.positions.length < this.minPointsForZ) return false;
        const pts = this.positions;
        const xs = pts.map(p => p.x);
        const ys = pts.map(p => p.y);
        const minX = Math.min(...xs), maxX = Math.max(...xs);
        const minY = Math.min(...ys), maxY = Math.max(...ys);
        const w = maxX - minX, h = maxY - minY;
        if (w < 0.05 || h < 0.05) return false;

        const n = pts.length;
        const seg1 = pts.slice(0, Math.floor(n / 3));
        const seg3 = pts.slice(Math.floor(2 * n / 3));

        const seg1Ys = seg1.map(p => p.y);
        const seg1Xs = seg1.map(p => p.x);
        const seg3Ys = seg3.map(p => p.y);
        const seg3Xs = seg3.map(p => p.x);

        const s1Yvar = Math.max(...seg1Ys) - Math.min(...seg1Ys);
        const s1Xrange = Math.max(...seg1Xs) - Math.min(...seg1Xs);
        const s3Yvar = Math.max(...seg3Ys) - Math.min(...seg3Ys);
        const s3Xrange = Math.max(...seg3Xs) - Math.min(...seg3Xs);

        const isSeg1H = s1Yvar < h * 0.4 && s1Xrange > w * 0.3;
        const isSeg3H = s3Yvar < h * 0.4 && s3Xrange > w * 0.3;

        const avgS1Y = seg1Ys.reduce((a, b) => a + b, 0) / seg1Ys.length;
        const avgS3Y = seg3Ys.reduce((a, b) => a + b, 0) / seg3Ys.length;

        return isSeg1H && isSeg3H && avgS1Y < avgS3Y;
    }

    getZDetected() {
        if (this.zDetected) {
            this.zDetected = false;
            return true;
        }
        return false;
    }

    getTrailPoints() {
        return [...this.positions];
    }
}

// ==================== J MOTION TRACKER ====================
class JMotionTracker {
    constructor() {
        this.positions = [];
        this.maxPositions = 50;
        this.lastJTime = 0;
        this.jCooldown = 1.0;
        this.jDetected = false;
        this.drawingActive = false;
        this.minPointsForJ = 3;
    }

    addPosition(x, y, isPinkyPointing) {
        const now = performance.now() / 1000;
        if (isPinkyPointing) {
            this.positions.push({ x, y, t: now });
            if (this.positions.length > this.maxPositions) this.positions.shift();
            this.drawingActive = true;
        } else {
            if (this.drawingActive && this.positions.length >= this.minPointsForJ) {
                if (this._checkJPattern()) {
                    if (now - this.lastJTime > this.jCooldown) {
                        this.jDetected = true;
                        this.lastJTime = now;
                    }
                }
            }
            this.positions = [];
            this.drawingActive = false;
        }
    }

    _checkJPattern() {
        if (this.positions.length < this.minPointsForJ) return false;
        const pts = this.positions;
        const ys = pts.map(p => p.y);
        const xs = pts.map(p => p.x);
        const minY = Math.min(...ys), maxY = Math.max(...ys);
        const minX = Math.min(...xs), maxX = Math.max(...xs);
        const h = maxY - minY;
        const w = maxX - minX;
        if (h < 0.015) return false; // Even smaller vertical drop

        // Must move down at least a little, then curve left or right
        const n = pts.length;
        const first = pts[0], last = pts[pts.length - 1];
        const down = last.y > first.y + 0.01;
        const curve = w > 0.01;
        return down && curve;
    }

    get isDrawingJ() {
        if (!this.drawingActive || this.positions.length < 2) return false;
        const recent = this.positions.slice(-3);
        const xs = recent.map(p => p.x);
        const ys = recent.map(p => p.y);
        const movement = (Math.max(...xs) - Math.min(...xs)) + (Math.max(...ys) - Math.min(...ys));
        return movement > 0.008; // Show J... with very little movement
    }

    getJDetected() {
        if (this.jDetected) {
            this.jDetected = false;
            return true;
        }
        return false;
    }

    getTrailPoints() {
        return [...this.positions];
    }
}

// ==================== SIGN RECOGNIZER ====================
class HandSignRecognizer {
    constructor() {
        this.zTracker = new ZMotionTracker();
        this.jTracker = new JMotionTracker();
        this.stableFrames = 0;
        this.stableThreshold = 15;
        this.lastStableSign = '';
        this.lastAddedLetter = '';
        this.lastAddTime = 0;
        this.letterCooldown = 1.0;
        this.textBuffer = '';
        this.suggestions = [];
    }

    // Euclidean distance between two landmarks (2D)
    dist(lm, i, j) {
        const dx = lm[i].x - lm[j].x;
        const dy = lm[i].y - lm[j].y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    // Distance from landmark to wrist (2D)
    distToWrist(lm, idx) {
        const dx = lm[idx].x - lm[LM.WRIST].x;
        const dy = lm[idx].y - lm[LM.WRIST].y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    isFingerExtended(lm, tip, pip) {
        return this.distToWrist(lm, tip) > this.distToWrist(lm, pip);
    }

    isThumbExtended(lm, handedness) {
        const tipX = lm[LM.THUMB_TIP].x;
        const mcpX = lm[LM.THUMB_MCP].x;
        return handedness === 'Right' ? tipX < mcpX : tipX > mcpX;
    }

    getFingerStates(lm, handedness) {
        return {
            thumb:  this.isThumbExtended(lm, handedness),
            index:  this.isFingerExtended(lm, LM.INDEX_TIP, LM.INDEX_PIP),
            middle: this.isFingerExtended(lm, LM.MIDDLE_TIP, LM.MIDDLE_PIP),
            ring:   this.isFingerExtended(lm, LM.RING_TIP, LM.RING_PIP),
            pinky:  this.isFingerExtended(lm, LM.PINKY_TIP, LM.PINKY_PIP)
        };
    }

    recognizeSign(lm, handedness) {
        const f = this.getFingerStates(lm, handedness);
        const thumbIndexDist  = this.dist(lm, LM.THUMB_TIP, LM.INDEX_TIP);
        const thumbMiddleDist = this.dist(lm, LM.THUMB_TIP, LM.MIDDLE_TIP);
        const indexMiddleDist = this.dist(lm, LM.INDEX_TIP, LM.MIDDLE_TIP);
        const thumbRingDist   = this.dist(lm, LM.THUMB_TIP, LM.RING_TIP);
        const thumbPinkyDist  = this.dist(lm, LM.THUMB_TIP, LM.PINKY_TIP);
        const indexRingDist   = this.dist(lm, LM.INDEX_TIP, LM.RING_TIP);
        const middleRingDist  = this.dist(lm, LM.MIDDLE_TIP, LM.RING_TIP);
        const extCount = [f.thumb, f.index, f.middle, f.ring, f.pinky].filter(Boolean).length;

        // Helper: check if hand is oriented sideways (fingers pointing horizontally)
        const indexHorizontal = Math.abs(lm[LM.INDEX_TIP].y - lm[LM.INDEX_MCP].y) < 0.1;
        // Helper: check if fingers are pointing down
        const indexDown = lm[LM.INDEX_TIP].y > lm[LM.INDEX_MCP].y + 0.03;
        // Helper: thumb-index "pinch" (for O, F, D, Q)
        const thumbIndexPinch = thumbIndexDist < 0.05;
        // Helper: thumb pointing clearly UP (for thumbs up - very strict)
        const thumbUp = lm[LM.THUMB_TIP].y < lm[LM.THUMB_MCP].y - 0.08
            && Math.abs(lm[LM.THUMB_TIP].x - lm[LM.THUMB_MCP].x) < 0.06; // thumb must be vertical
        // Helper: thumb pointing to the SIDE (for A sign)
        const thumbSide = Math.abs(lm[LM.THUMB_TIP].x - lm[LM.THUMB_MCP].x) > 0.04;
        const thumbAcross = Math.abs(lm[LM.THUMB_TIP].x - lm[LM.INDEX_MCP].x) < 0.04;

        // ──── FULL FILIPINO SIGN LANGUAGE ALPHABET ────
        // Order matters: more specific patterns first, then general ones

        // ── F — Thumb+index circle/touch, middle+ring+pinky extended ──
        if (thumbIndexPinch && f.middle && f.ring && f.pinky && !f.index)
            return { sign: 'F', confidence: 0.88 };

        // ── R — Index+middle crossed (very close together, both up) ──
        if (f.index && f.middle && !f.ring && !f.pinky && indexMiddleDist < 0.025)
            return { sign: 'R', confidence: 0.82 };

        // ── U — Index+middle up together, parallel (slightly apart but close) ──
        if (f.index && f.middle && !f.ring && !f.pinky && !f.thumb
            && indexMiddleDist >= 0.025 && indexMiddleDist < 0.055)
            return { sign: 'U', confidence: 0.85 };

        // ── O — Thumb+index form circle (tips close together), others curled ──
        // Move BEFORE fist check to catch O when index is perceived as curled
        if (!f.middle && !f.ring && !f.pinky && thumbIndexDist < 0.09) {
            // Verify openness to avoid confusing with S/A (where index tip is tucked in)
            const indexTipToMcp = this.dist(lm, LM.INDEX_TIP, LM.INDEX_MCP);
            if (indexTipToMcp > 0.05) {
                return { sign: 'O', confidence: 0.88 };
            }
        }

        // ── FIST-BASED SIGNS (all four fingers curled) ──
        // Uses relative thumb proximity to distinguish T, S, M, N, A, E
        if (!f.index && !f.middle && !f.ring && !f.pinky) {
            const tIndex  = this.dist(lm, LM.THUMB_TIP, LM.INDEX_PIP);
            const tMiddle = this.dist(lm, LM.THUMB_TIP, LM.MIDDLE_PIP);
            const tRing   = this.dist(lm, LM.THUMB_TIP, LM.RING_PIP);
            const tPinky  = this.dist(lm, LM.THUMB_TIP, LM.PINKY_MCP);

            // A — fist with thumb extended (beside the fist)
            if (f.thumb)
                return { sign: 'A', confidence: 0.88 };

            // Below: thumb NOT extended (curled/tucked)

            // T — thumb tucked tightly between index and middle
            if (tIndex < 0.06 && tMiddle < 0.06 && tIndex < tRing)
                return { sign: 'T', confidence: 0.78 };

            // Determine which finger area the thumb is closest to
            const minDist = Math.min(tIndex, tMiddle, tRing);

            if (minDist < 0.11) {
                // M — thumb closest to ring/pinky side (peeks between ring & pinky)
                if (tRing <= tMiddle && tRing <= tIndex)
                    return { sign: 'M', confidence: 0.75 };

                // N — thumb closest to middle area (peeks between middle & ring)
                if (tMiddle <= tIndex)
                    return { sign: 'N', confidence: 0.73 };

                // S — thumb near index/front of fist
                return { sign: 'S', confidence: 0.72 };
            }

            // E — thumb fully hidden, no detectable position
            return { sign: 'E', confidence: 0.70 };
        }

        // ── B — All fingers up, thumb tucked ──
        if (f.index && f.middle && f.ring && f.pinky && !f.thumb)
            return { sign: 'B', confidence: 0.85 };

        // ── X — Index finger HOOKED/BENT (tip curls back toward palm) ──
        // Improve: Check if PIP is extended but TIP is bent down (below PIP/DIP)
        if (!f.middle && !f.ring && !f.pinky) {
            const indexPipUp = this.distToWrist(lm, LM.INDEX_PIP) > this.distToWrist(lm, LM.INDEX_MCP);
            const isHooked = lm[LM.INDEX_TIP].y > lm[LM.INDEX_PIP].y; // Tip is lower than middle knuckle
            if (indexPipUp && isHooked)
                return { sign: 'X', confidence: 0.82 };
        }

        // ── D — Index STRAIGHT up, thumb forms circle with middle/ring (others curled) ──
        // Index must be up, thumb can touch middle OR ring finger
        if (f.index && !f.middle && !f.ring && !f.pinky
            && (thumbMiddleDist < 0.10 || thumbRingDist < 0.10)
            && !indexHorizontal && !indexDown)
            return { sign: 'D', confidence: 0.82 };

        // ── C — Curved hand, fingers together forming arc, thumb separated ──
        if (f.thumb && f.index && f.middle && f.ring
            && thumbIndexDist > 0.06 && thumbIndexDist < 0.16
            && indexMiddleDist < 0.05 && !thumbIndexPinch)
            return { sign: 'C', confidence: 0.75 };

        // ── G — Index+thumb pointing sideways (like a gun), tips NOT touching ──
        if (f.index && f.thumb && !f.middle && !f.ring && !f.pinky && indexHorizontal && thumbIndexDist > 0.06)
            return { sign: 'G', confidence: 0.78 };

        // ── H — Index+middle pointing sideways ──
        if (f.index && f.middle && !f.ring && !f.pinky && indexHorizontal)
            return { sign: 'H', confidence: 0.78 };

        // ── Q — Thumb+index pointing downward (like G but down) ──
        // Improve: Relax thumb check, ensure index is strictly down, thumb/index close
        if (f.index && !f.middle && !f.ring && !f.pinky && indexDown) {
            const thumbDown = lm[LM.THUMB_TIP].y > lm[LM.WRIST].y; 
            // Allow thumb to be recognized even if not "extended" in standard sense, as long as it's down
            if (thumbDown || f.thumb) {
                 return { sign: 'Q', confidence: 0.78 };
            }
        }

        // ── P — Index+middle pointing down, thumb out (like K but pointing down) ──
        if (f.index && f.middle && !f.ring && !f.pinky && indexDown && f.thumb)
            return { sign: 'P', confidence: 0.75 };

        // ── I — Pinky only extended ──
        if (!f.index && !f.middle && !f.ring && f.pinky && !f.thumb)
            return { sign: 'I', confidence: 0.90 };

        // ── K — Index+middle spread (V-like) WITH thumb between them ──
        if (f.index && f.middle && !f.ring && !f.pinky && f.thumb && indexMiddleDist > 0.055)
            return { sign: 'K', confidence: 0.80 };

        // ── V — Index+middle spread (peace sign), thumb NOT involved ──
        if (f.index && f.middle && !f.ring && !f.pinky && !f.thumb && indexMiddleDist > 0.05)
            return { sign: 'V', confidence: 0.88 };

        // ── L — L shape (index up + thumb out, widely spaced, tips NOT touching) ──
        if (f.index && f.thumb && !f.middle && !f.ring && !f.pinky && thumbIndexDist > 0.08
            && !indexHorizontal && !indexDown)
            return { sign: 'L', confidence: 0.85 };

        // ── W — Index+middle+ring extended, pinky curled ──
        if (f.index && f.middle && f.ring && !f.pinky && !f.thumb)
            return { sign: 'W', confidence: 0.85 };

        // ── Y — Thumb+pinky extended, others closed (shaka) ──
        if (f.thumb && f.pinky && !f.index && !f.middle && !f.ring)
            return { sign: 'Y', confidence: 0.90 };

        // ── NG — Thumb touching ring finger, others extended (Filipino-specific) ──
        if (f.index && f.middle && !f.ring && f.pinky && thumbRingDist < 0.06)
            return { sign: 'NG', confidence: 0.75 };

        // ── 1 — Index only (no thumb) ──
        if (f.index && !f.middle && !f.ring && !f.pinky && !f.thumb)
            return { sign: '1', confidence: 0.85 };

        return { sign: '?', confidence: 0.0 };
    }

    /**
     * Process a single frame's hand results.
     * Returns { sign, confidence, hand } or null.
     */
    processResults(results) {
        if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
            this.zTracker.addPosition(0, 0, false);
            this.stableFrames = 0;
            this.lastStableSign = '';
            return null;
        }

        const lm = results.multiHandLandmarks[0];
        const handedness = results.multiHandedness?.[0]?.label || 'Right';
        // Flip display label because the camera is mirrored
        const displayHand = handedness === 'Right' ? 'Left' : 'Right';
        const f = this.getFingerStates(lm, handedness);

        // Z tracking — only activate when index is pointing AND thumb is NOT extended
        // AND thumb is not touching other fingers (to exclude D, which has thumb on middle)
        const thumbMiddleDist = this.dist(lm, LM.THUMB_TIP, LM.MIDDLE_TIP);
        const thumbTouchingFingers = thumbMiddleDist < 0.08; // D-like pose
        const isPointing = f.index && !f.middle && !f.ring && !f.pinky && !f.thumb && !thumbTouchingFingers;
        this.zTracker.addPosition(lm[LM.INDEX_TIP].x, lm[LM.INDEX_TIP].y, isPointing);

        // J tracking — pinky extended, allow thumb and partial ring curl
        // Much more lenient: pinky must be up, index+middle should be down, thumb/ring can be anything
        const isPinkyPointing = f.pinky && !f.index && !f.middle;
        this.jTracker.addPosition(lm[LM.PINKY_TIP].x, lm[LM.PINKY_TIP].y, isPinkyPointing);

        let sign, confidence;

        if (this.zTracker.drawingActive) {
            this.stableFrames = 0;
            this.lastStableSign = '';
            return { sign: 'Z...', confidence: 0, hand: displayHand, drawing: true };
        } else if (this.zTracker.getZDetected()) {
            sign = 'Z';
            confidence = 0.90;
        } else if (this.jTracker.isDrawingJ) {
            this.stableFrames = 0;
            this.lastStableSign = '';
            return { sign: 'J...', confidence: 0, hand: displayHand, drawing: true };
        } else if (this.jTracker.getJDetected()) {
            sign = 'J';
            confidence = 0.88;
        } else {
            const result = this.recognizeSign(lm, handedness);
            sign = result.sign;
            confidence = result.confidence;
        }

        return { sign, confidence, hand: displayHand, drawing: false };
    }

    /**
     * Try to add letter to text buffer with stability check.
     */
    addLetter(sign, confidence) {
        const now = performance.now() / 1000;

        if (sign === '?' || confidence < 0.7) {
            this.stableFrames = 0;
            this.lastStableSign = '';
            return false;
        }

        if (sign === this.lastStableSign) {
            this.stableFrames++;
        } else {
            this.stableFrames = 1;
            this.lastStableSign = sign;
        }

        if (this.stableFrames >= this.stableThreshold) {
            if (sign !== this.lastAddedLetter || (now - this.lastAddTime) > this.letterCooldown) {
                this.textBuffer += sign;
                this.lastAddedLetter = sign;
                this.lastAddTime = now;
                this.stableFrames = 0;
                return true;
            }
        }
        return false;
    }

    addSpace() {
        if (this.textBuffer && !this.textBuffer.endsWith(' ')) {
            this.textBuffer += ' ';
            this.lastAddedLetter = '';
        }
    }

    backspace() {
        if (this.textBuffer) {
            this.textBuffer = this.textBuffer.slice(0, -1);
        }
    }

    clear() {
        this.textBuffer = '';
        this.suggestions = [];
        this.lastAddedLetter = '';
        this.stableFrames = 0;
    }
}

// ==================== WORD SUGGESTER ====================
const COMMON_WORDS = [
    "hello","hi","hey","goodbye","bye","good","morning","afternoon","evening","night",
    "welcome","thanks","thank","please","sorry","excuse","pardon",
    "i","me","my","mine","you","your","yours","he","him","his","she","her","hers",
    "it","its","we","us","our","they","them","their","who","what","when","where","which","why","how",
    "am","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","shall","should","may","might","must","can","could",
    "go","going","gone","come","coming","came","see","look","want","need","like","love",
    "know","think","make","take","get","give","find","tell","ask","use","try","leave",
    "call","keep","let","begin","show","hear","play","run","move","live","write","read",
    "learn","change","follow","stop","create","speak","open","walk","win","teach",
    "person","people","man","woman","child","boy","girl","friend","family",
    "father","mother","brother","sister","son","daughter","husband","wife",
    "teacher","student","doctor","nurse","home","house","school","office",
    "hospital","store","restaurant","park","city","street","building",
    "phone","computer","car","book","table","chair","door","window","food","water",
    "money","time","day","week","month","year","today","tomorrow","yesterday",
    "life","love","idea","problem","question","answer","work","job","name",
    "good","bad","big","small","long","short","old","new","fast","slow",
    "hot","cold","happy","sad","easy","hard","beautiful","ugly",
    "yes","no","okay","sure","fine","great","amazing",
    // Filipino common words
    "kumusta","salamat","magandang","umaga","hapon","gabi","tanghali",
    "oo","hindi","tulong","mahal","kita","pakiusap","paumanhin","pasensya",
    "kamusta","po","opo","ate","kuya","nanay","tatay","kapatid","anak","bahay",
    "pagkain","tubig","paaralan","trabaho","kaibigan","maganda","masaya",
    "malungkot","galit","takot","gutom","uhaw","mahal","mabuti","masama",
    "malaki","maliit","bago","luma","mainit","malamig","mabilis","mabagal",
    "saan","sino","ano","kailan","bakit","paano","ilan",
    "isang","dalawa","tatlo","apat","lima","anim","pito","walo","siyam","sampu",
    "ingat","paalam","halika","tara","sige","ayos","talaga","naman"
];

class WordSuggester {
    constructor(words) {
        this.words = [...new Set(words.map(w => w.toLowerCase()))].sort();
    }

    getSuggestions(prefix, max = 5) {
        if (!prefix) return [];
        const p = prefix.toLowerCase();
        return this.words.filter(w => w.startsWith(p)).slice(0, max);
    }
}

// ==================== FILIPINO TRANSLATION ====================
const ENGLISH_TO_FILIPINO = {
    // ── Greetings & Farewells ──
    "hello": "kumusta", "hi": "kumusta", "hey": "hoy",
    "good morning": "magandang umaga", "good afternoon": "magandang hapon",
    "good evening": "magandang gabi", "good night": "magandang gabi",
    "goodbye": "paalam", "bye": "paalam", "see you": "kita tayo",
    "see you later": "kita tayo mamaya", "welcome": "mabuhay",

    // ── Courtesy & Responses ──
    "thank you": "salamat", "thanks": "salamat", "thank you very much": "maraming salamat",
    "please": "pakiusap", "sorry": "paumanhin", "excuse me": "paumanhin po",
    "you're welcome": "walang anuman", "no problem": "walang problema",
    "yes": "oo", "no": "hindi", "okay": "sige", "maybe": "siguro",
    "of course": "syempre", "sure": "sigurado", "never": "hindi kailanman",
    "always": "lagi", "sometimes": "minsan",

    // ── Common Phrases ──
    "how are you": "kumusta ka", "i am fine": "mabuti naman ako",
    "what is your name": "ano ang pangalan mo",
    "my name is": "ang pangalan ko ay",
    "i love you": "mahal kita", "help": "tulong",
    "come here": "halika dito", "let's go": "tara na",
    "take care": "ingat ka", "i'm hungry": "gutom na ako",
    "i'm thirsty": "uhaw na ako", "i need help": "kailangan ko ng tulong",
    "where are you": "nasaan ka", "i am here": "nandito ako",
    "wait": "hintay", "wait for me": "hintayin mo ako",
    "i don't know": "hindi ko alam", "i know": "alam ko",
    "i understand": "naiintindihan ko", "i don't understand": "hindi ko naiintindihan",
    "what time is it": "anong oras na", "how much": "magkano",
    "where is": "nasaan ang", "who is": "sino ang",
    "what is this": "ano ito", "what is that": "ano iyon",
    "i like": "gusto ko", "i don't like": "ayaw ko",
    "i want": "gusto ko", "i need": "kailangan ko",
    "can you help me": "pwede mo ba akong tulungan",
    "nice to meet you": "ikinagagalak kong makilala ka",
    "congratulations": "pagbati", "happy birthday": "maligayang kaarawan",
    "merry christmas": "maligayang pasko", "happy new year": "manigong bagong taon",
    "god bless you": "pagpalain ka ng diyos",
    "i miss you": "namimiss kita", "take care of yourself": "ingatan mo ang sarili mo",
    "don't worry": "huwag kang mag-alala", "it's okay": "okay lang",
    "be careful": "mag-ingat ka", "hurry up": "bilisan mo",
    "slow down": "bagalan mo", "come back": "bumalik ka",
    "let me know": "sabihin mo sa akin",

    // ── Verbs / Actions ──
    "read": "basahin", "write": "sulat", "eat": "kain",
    "drink": "inom", "sleep": "tulog", "wake up": "gising",
    "go": "punta", "come": "halika", "run": "takbo",
    "walk": "lakad", "stop": "tigil", "start": "simula",
    "open": "bukas", "close": "sara", "give": "bigay",
    "take": "kunin", "look": "tingin", "see": "kita",
    "hear": "rinig", "listen": "makinig", "speak": "magsalita",
    "talk": "usap", "say": "sabi", "ask": "tanong",
    "answer": "sagot", "think": "isip", "know": "alam",
    "learn": "aral", "study": "mag-aral", "teach": "magturo",
    "work": "trabaho", "play": "laro", "sing": "kanta",
    "dance": "sayaw", "cook": "luto", "clean": "linis",
    "wash": "hugas", "buy": "bili", "sell": "benta",
    "pay": "bayad", "send": "padala", "call": "tawag",
    "try": "subukan", "wait": "hintay", "sit": "upo",
    "stand": "tayo", "love": "mahal", "like": "gusto",
    "want": "nais", "need": "kailangan", "can": "pwede",
    "make": "gawa", "do": "gawin", "find": "hanap",
    "bring": "dalhin", "use": "gamit", "hold": "hawak",
    "put": "lagay", "leave": "alis", "stay": "manatili",
    "return": "balik", "change": "palitan", "move": "galaw",
    "turn": "liko", "push": "tulak", "pull": "hilahin",
    "carry": "buhat", "throw": "tapon", "catch": "saluhin",
    "cut": "gupit", "break": "basag", "fix": "ayos",
    "build": "gawa", "draw": "guhit", "paint": "pintura",
    "fly": "lipad", "swim": "langoy", "jump": "talon",
    "climb": "akyat", "fall": "laglag", "cry": "iyak",
    "laugh": "tawa", "smile": "ngiti", "pray": "dasal",
    "fight": "laban", "win": "panalo", "lose": "talo",
    "die": "mamatay", "live": "buhay", "born": "ipinanganak",
    "grow": "tubo", "finish": "tapos", "begin": "umpisahan",
    "forget": "kalimutan", "remember": "tandaan",
    "promise": "pangako", "believe": "maniwala",
    "hope": "pag-asa", "dream": "panaginip",
    "share": "ibahagi", "choose": "pumili",
    "enter": "pasok", "exit": "labas",

    // ── People & Family ──
    "mother": "nanay", "father": "tatay", "brother": "kapatid na lalaki",
    "sister": "kapatid na babae", "son": "anak na lalaki", "daughter": "anak na babae",
    "baby": "sanggol", "child": "bata", "children": "mga bata",
    "parent": "magulang", "parents": "mga magulang",
    "grandmother": "lola", "grandfather": "lolo",
    "uncle": "tiyo", "aunt": "tiya", "cousin": "pinsan",
    "husband": "asawa", "wife": "asawa",
    "family": "pamilya", "friend": "kaibigan", "friends": "mga kaibigan",
    "neighbor": "kapitbahay", "teacher": "guro", "student": "estudyante",
    "doctor": "doktor", "nurse": "nars", "police": "pulis",
    "driver": "tsuper", "farmer": "magsasaka", "worker": "manggagawa",
    "boss": "amo", "person": "tao", "people": "mga tao",
    "man": "lalaki", "woman": "babae", "boy": "batang lalaki", "girl": "batang babae",

    // ── Body ──
    "head": "ulo", "face": "mukha", "eye": "mata", "eyes": "mga mata",
    "ear": "tenga", "nose": "ilong", "mouth": "bibig",
    "hand": "kamay", "hands": "mga kamay", "finger": "daliri",
    "arm": "braso", "leg": "binti", "foot": "paa", "feet": "mga paa",
    "body": "katawan", "heart": "puso", "blood": "dugo",
    "hair": "buhok", "teeth": "ngipin", "tongue": "dila",
    "skin": "balat", "bone": "buto", "stomach": "tiyan",
    "back": "likod", "neck": "leeg", "shoulder": "balikat",
    "knee": "tuhod", "chest": "dibdib",

    // ── Places ──
    "home": "bahay", "house": "bahay", "school": "paaralan",
    "church": "simbahan", "hospital": "ospital", "market": "palengke",
    "store": "tindahan", "office": "opisina", "room": "kwarto",
    "kitchen": "kusina", "bathroom": "banyo", "garden": "hardin",
    "street": "kalye", "road": "daan", "city": "lungsod",
    "town": "bayan", "country": "bansa", "world": "mundo",
    "park": "parke", "beach": "dalampasigan", "mountain": "bundok",
    "river": "ilog", "sea": "dagat", "farm": "bukid",
    "library": "aklatan", "airport": "paliparan",
    "restaurant": "kainan", "bank": "bangko",

    // ── Food & Drink ──
    "water": "tubig", "food": "pagkain", "rice": "kanin",
    "bread": "tinapay", "meat": "karne", "fish": "isda",
    "chicken": "manok", "egg": "itlog", "milk": "gatas",
    "coffee": "kape", "tea": "tsaa", "juice": "juice",
    "fruit": "prutas", "vegetable": "gulay", "sugar": "asukal",
    "salt": "asin", "soup": "sabaw", "cake": "keyk",
    "candy": "kendi", "ice cream": "sorbetes",
    "breakfast": "almusal", "lunch": "tanghalian", "dinner": "hapunan",

    // ── Things & Objects ──
    "book": "aklat", "pen": "bolpen", "paper": "papel",
    "phone": "telepono", "computer": "kompyuter",
    "table": "mesa", "chair": "upuan", "door": "pinto",
    "window": "bintana", "key": "susi", "money": "pera",
    "bag": "bag", "clothes": "damit", "shoe": "sapatos",
    "car": "kotse", "bus": "bus", "clock": "orasan",
    "picture": "larawan", "letter": "liham", "gift": "regalo",
    "ball": "bola", "toy": "laruan", "light": "ilaw",
    "fire": "apoy", "umbrella": "payong", "mirror": "salamin",
    "soap": "sabon", "towel": "tuwalya", "plate": "plato",
    "glass": "baso", "spoon": "kutsara", "fork": "tinidor",
    "knife": "kutsilyo", "bed": "kama", "pillow": "unan",
    "blanket": "kumot", "television": "telebisyon", "radio": "radyo",
    "camera": "kamera", "bottle": "bote", "box": "kahon",

    // ── Nature & Weather ──
    "sun": "araw", "moon": "buwan", "star": "bituin",
    "sky": "langit", "cloud": "ulap", "rain": "ulan",
    "wind": "hangin", "storm": "bagyo", "thunder": "kulog",
    "lightning": "kidlat", "snow": "niyebe", "tree": "puno",
    "flower": "bulaklak", "grass": "damo", "leaf": "dahon",
    "stone": "bato", "sand": "buhangin", "earth": "lupa",
    "air": "hangin", "rainbow": "bahaghari",

    // ── Animals ──
    "dog": "aso", "cat": "pusa", "bird": "ibon",
    "fish": "isda", "cow": "baka", "pig": "baboy",
    "horse": "kabayo", "goat": "kambing", "snake": "ahas",
    "monkey": "unggoy", "elephant": "elepante", "lion": "leon",
    "mouse": "daga", "frog": "palaka", "butterfly": "paru-paro",
    "ant": "langgam", "bee": "bubuyog", "chicken": "manok",
    "duck": "pato", "rabbit": "kuneho", "turtle": "pagong",
    "shark": "pating", "whale": "balyena", "crab": "alimango",

    // ── Adjectives / Descriptions ──
    "beautiful": "maganda", "handsome": "gwapo",
    "happy": "masaya", "sad": "malungkot", "angry": "galit",
    "scared": "takot", "tired": "pagod", "sick": "may sakit",
    "hungry": "gutom", "thirsty": "uhaw", "full": "busog",
    "big": "malaki", "small": "maliit", "tall": "matangkad",
    "short": "mababa", "long": "mahaba", "wide": "malawak",
    "fast": "mabilis", "slow": "mabagal", "strong": "malakas",
    "weak": "mahina", "hard": "matigas", "soft": "malambot",
    "hot": "mainit", "cold": "malamig", "warm": "maligamgam",
    "new": "bago", "old": "luma", "young": "bata",
    "good": "mabuti", "bad": "masama", "nice": "maganda",
    "clean": "malinis", "dirty": "marumi", "wet": "basa",
    "dry": "tuyo", "heavy": "mabigat", "light": "magaan",
    "dark": "madilim", "bright": "maliwanag",
    "easy": "madali", "difficult": "mahirap",
    "rich": "mayaman", "poor": "mahirap",
    "safe": "ligtas", "dangerous": "delikado",
    "important": "mahalaga", "ready": "handa",
    "busy": "abala", "free": "libre", "open": "bukas", "closed": "sarado",
    "right": "tama", "wrong": "mali", "true": "totoo", "false": "hindi totoo",
    "same": "pareho", "different": "iba",
    "many": "marami", "few": "konti", "all": "lahat", "some": "ilan",
    "empty": "walang laman", "enough": "sapat",
    "special": "espesyal", "favorite": "paborito",
    "sweet": "matamis", "sour": "maasim", "salty": "maalat",
    "bitter": "mapait", "delicious": "masarap",
    "loud": "malakas", "quiet": "tahimik",
    "deep": "malalim", "shallow": "mababaw",
    "near": "malapit", "far": "malayo",
    "early": "maaga", "late": "huli",
    "alive": "buhay", "dead": "patay",
    "alone": "mag-isa", "together": "magkasama",
    "possible": "posible", "impossible": "imposible",

    // ── Time & Days ──
    "today": "ngayon", "tomorrow": "bukas", "yesterday": "kahapon",
    "now": "ngayon", "later": "mamaya", "soon": "malapit na",
    "morning": "umaga", "afternoon": "hapon", "evening": "gabi",
    "night": "gabi", "day": "araw", "week": "linggo",
    "month": "buwan", "year": "taon", "time": "oras",
    "hour": "oras", "minute": "minuto", "second": "segundo",
    "monday": "lunes", "tuesday": "martes", "wednesday": "miyerkules",
    "thursday": "huwebes", "friday": "biyernes",
    "saturday": "sabado", "sunday": "linggo",
    "january": "enero", "february": "pebrero", "march": "marso",
    "april": "abril", "may": "mayo", "june": "hunyo",
    "july": "hulyo", "august": "agosto", "september": "setyembre",
    "october": "oktubre", "november": "nobyembre", "december": "disyembre",

    // ── Numbers ──
    "one": "isa", "two": "dalawa", "three": "tatlo",
    "four": "apat", "five": "lima", "six": "anim",
    "seven": "pito", "eight": "walo", "nine": "siyam",
    "ten": "sampu", "hundred": "daan", "thousand": "libo",
    "first": "una", "second": "pangalawa", "third": "pangatlo",
    "last": "huli", "next": "susunod",

    // ── Colors ──
    "red": "pula", "blue": "asul", "green": "berde",
    "yellow": "dilaw", "white": "puti", "black": "itim",
    "orange": "kahel", "pink": "rosas", "purple": "lila",
    "brown": "kayumanggi", "gray": "kulay abo", "gold": "ginto",
    "silver": "pilak",

    // ── Emotions & States ──
    "love": "pag-ibig", "hate": "galit", "fear": "takot",
    "joy": "tuwa", "peace": "kapayapaan", "pain": "sakit",
    "anger": "galit", "surprise": "gulat", "worry": "kabalisahan",
    "proud": "proud", "shy": "mahiyain", "jealous": "seloso",
    "lonely": "malungkot", "excited": "sabik", "bored": "inip",
    "grateful": "nagpapasalamat", "confused": "naguguluhan",

    // ── Common Nouns ──
    "name": "pangalan", "age": "edad", "birthday": "kaarawan",
    "life": "buhay", "death": "kamatayan", "god": "diyos",
    "king": "hari", "queen": "reyna", "president": "pangulo",
    "game": "laro", "song": "kanta", "music": "musika",
    "story": "kwento", "news": "balita", "problem": "problema",
    "question": "tanong", "answer": "sagot", "idea": "ideya",
    "word": "salita", "language": "wika", "sign": "senyas",
    "voice": "boses", "sound": "tunog", "color": "kulay",
    "number": "numero", "price": "presyo", "size": "sukat",
    "way": "daan", "thing": "bagay", "place": "lugar",
    "power": "kapangyarihan", "truth": "katotohanan",
    "dream": "panaginip", "wish": "kahilingan",
    "reason": "dahilan", "chance": "pagkakataon",
    "future": "kinabukasan", "past": "nakaraan",
    "nothing": "wala", "everything": "lahat",
    "something": "may kung ano"
};

// ──── Local quick-translate (instant, offline fallback) ────
function translateToFilipinoLocal(text) {
    if (!text) return '—';
    const lower = text.toLowerCase().trim();

    // Try full phrase match first
    if (ENGLISH_TO_FILIPINO[lower]) return ENGLISH_TO_FILIPINO[lower];

    // Try matching from longest phrases down
    let result = lower;
    const phrases = Object.keys(ENGLISH_TO_FILIPINO).sort((a, b) => b.length - a.length);
    for (const phrase of phrases) {
        if (result.includes(phrase)) {
            result = result.replace(phrase, ENGLISH_TO_FILIPINO[phrase]);
        }
    }

    return result === lower ? null : result;
}

// ──── Google Translate API (accurate sentences) ────
let _translateCache = {};
let _translateTimer = null;
let _lastTranslateText = '';

/**
 * Main translation function. Shows local translation instantly,
 * then fetches accurate Google Translate result in background.
 */
function translateToFilipino(text) {
    if (!text) return '—';
    const trimmed = text.trim();
    if (!trimmed) return '—';

    // 1) Show cached Google result if available
    const cacheKey = trimmed.toLowerCase();
    if (_translateCache[cacheKey]) {
        return _translateCache[cacheKey];
    }

    // 2) Show local dictionary result instantly
    const local = translateToFilipinoLocal(trimmed);

    // 3) Request accurate Google translation in background
    //    Debounce to avoid flooding the server on every letter
    if (_lastTranslateText !== cacheKey) {
        _lastTranslateText = cacheKey;
        clearTimeout(_translateTimer);
        _translateTimer = setTimeout(() => {
            fetchGoogleTranslation(trimmed, cacheKey);
        }, 400); // 400ms debounce
    }

    return local || '(nagsasalin...)';  // "translating..."
}

async function fetchGoogleTranslation(text, cacheKey) {
    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, to: 'fil' })
        });

        if (!response.ok) throw new Error('Translation API error');

        const data = await response.json();
        if (data.translated) {
            _translateCache[cacheKey] = data.translated;

            // Update the translation display immediately
            const el = document.getElementById('translation-content');
            if (el) el.textContent = data.translated;
        }
    } catch (e) {
        console.warn('[Translate] Google API failed, using local:', e.message);
        // Local translation is already shown as fallback
    }
}
