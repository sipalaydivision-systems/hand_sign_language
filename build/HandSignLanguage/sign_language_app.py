"""
Hand Sign Language Recognition System - Full Application Design
A modern desktop application with professional UI using tkinter/customtkinter.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from collections import deque
import time
import urllib.request
import os
import sys
import threading
import pyttsx3
import json
from PIL import Image, ImageTk

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI not installed. Run: pip install google-generativeai")

# Try to import customtkinter for modern UI, fallback to tkinter
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    USING_CTK = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    USING_CTK = False


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# Extended English vocabulary for suggestions
COMMON_WORDS = [
    # Greetings & Basic
    "hello", "hi", "hey", "goodbye", "bye", "good", "morning", "afternoon", "evening", "night",
    "welcome", "thanks", "thank", "please", "sorry", "excuse", "pardon",
    
    # Pronouns
    "i", "me", "my", "mine", "myself", "you", "your", "yours", "yourself",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves", "who", "whom", "whose",
    
    # Common Verbs
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "done",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "go", "going", "gone", "went", "come", "coming", "came",
    "see", "seeing", "saw", "seen", "look", "looking", "looked",
    "want", "wanted", "need", "needed", "like", "liked", "love", "loved",
    "know", "knowing", "knew", "known", "think", "thinking", "thought",
    "make", "making", "made", "take", "taking", "took", "taken",
    "get", "getting", "got", "give", "giving", "gave", "given",
    "find", "finding", "found", "tell", "telling", "told",
    "ask", "asking", "asked", "use", "using", "used",
    "try", "trying", "tried", "leave", "leaving", "left",
    "call", "calling", "called", "keep", "keeping", "kept",
    "let", "begin", "beginning", "began", "begun",
    "show", "showing", "showed", "shown", "hear", "hearing", "heard",
    "play", "playing", "played", "run", "running", "ran",
    "move", "moving", "moved", "live", "living", "lived",
    "believe", "bring", "brought", "happen", "happened",
    "write", "writing", "wrote", "written", "read", "reading",
    "learn", "learning", "learned", "change", "changing", "changed",
    "follow", "following", "followed", "stop", "stopping", "stopped",
    "create", "creating", "created", "speak", "speaking", "spoke", "spoken",
    "allow", "allowed", "add", "added", "spend", "spent",
    "grow", "growing", "grew", "grown", "open", "opening", "opened",
    "walk", "walking", "walked", "win", "winning", "won",
    "teach", "teaching", "taught", "offer", "offered",
    "remember", "remembered", "consider", "considered",
    "appear", "appeared", "buy", "buying", "bought",
    "wait", "waiting", "waited", "serve", "serving", "served",
    "die", "died", "send", "sending", "sent",
    "expect", "expected", "build", "building", "built",
    "stay", "staying", "stayed", "fall", "falling", "fell", "fallen",
    "cut", "cutting", "reach", "reaching", "reached",
    "kill", "killed", "remain", "remained",
    "suggest", "suggested", "raise", "raised",
    "pass", "passing", "passed", "sell", "selling", "sold",
    "require", "required", "report", "reported",
    "decide", "decided", "pull", "pulled",
    
    # Question Words
    "what", "when", "where", "which", "why", "how",
    
    # Common Nouns - People
    "person", "people", "man", "men", "woman", "women", "child", "children",
    "boy", "girl", "baby", "adult", "friend", "family",
    "father", "mother", "dad", "mom", "parent", "parents",
    "brother", "sister", "son", "daughter", "husband", "wife",
    "uncle", "aunt", "cousin", "grandma", "grandpa", "grandmother", "grandfather",
    "teacher", "student", "doctor", "nurse", "police", "officer",
    "manager", "worker", "employee", "boss", "customer", "client",
    "neighbor", "stranger", "guest", "host",
    
    # Common Nouns - Places
    "home", "house", "apartment", "room", "kitchen", "bathroom", "bedroom",
    "school", "university", "college", "class", "classroom",
    "office", "work", "workplace", "company", "business",
    "hospital", "clinic", "pharmacy", "bank", "store", "shop",
    "restaurant", "cafe", "hotel", "airport", "station",
    "park", "garden", "beach", "mountain", "forest", "lake", "river", "ocean",
    "city", "town", "village", "country", "state", "street", "road",
    "building", "church", "library", "museum", "theater", "cinema",
    "market", "mall", "supermarket", "gym", "pool",
    
    # Common Nouns - Things
    "thing", "stuff", "object", "item", "product",
    "phone", "computer", "laptop", "tablet", "television", "tv", "radio",
    "car", "bus", "train", "plane", "bike", "bicycle", "motorcycle",
    "book", "newspaper", "magazine", "letter", "email", "message",
    "table", "chair", "desk", "bed", "sofa", "couch",
    "door", "window", "wall", "floor", "ceiling", "roof",
    "food", "water", "coffee", "tea", "juice", "milk", "beer", "wine",
    "breakfast", "lunch", "dinner", "meal", "snack",
    "bread", "rice", "meat", "chicken", "fish", "egg", "cheese",
    "fruit", "apple", "banana", "orange", "vegetable", "salad",
    "cake", "cookie", "chocolate", "candy", "ice cream",
    "money", "cash", "card", "credit", "dollar", "price", "cost",
    "clothes", "shirt", "pants", "dress", "shoes", "hat", "jacket", "coat",
    "bag", "purse", "wallet", "key", "keys", "watch", "glasses",
    "paper", "pen", "pencil", "notebook",
    
    # Common Nouns - Abstract
    "time", "day", "week", "month", "year", "today", "tomorrow", "yesterday",
    "hour", "minute", "second", "moment", "period",
    "morning", "afternoon", "evening", "night", "midnight", "noon",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "life", "death", "birth", "age", "health", "disease", "illness",
    "love", "hate", "fear", "hope", "dream", "wish",
    "idea", "thought", "opinion", "belief", "knowledge", "education",
    "problem", "solution", "question", "answer", "reason", "result",
    "way", "method", "process", "system", "plan", "project",
    "work", "job", "career", "profession", "experience", "skill",
    "news", "information", "data", "fact", "truth", "lie",
    "story", "history", "future", "past", "present",
    "art", "music", "song", "movie", "film", "game", "sport",
    "party", "meeting", "event", "ceremony", "wedding", "funeral",
    "war", "peace", "fight", "battle", "victory", "defeat",
    "law", "rule", "right", "freedom", "justice", "power",
    "nature", "environment", "weather", "rain", "snow", "sun", "wind",
    "science", "technology", "internet", "website", "software", "application", "app",
    
    # Adjectives
    "good", "bad", "great", "best", "worst", "better", "worse",
    "big", "small", "large", "little", "huge", "tiny",
    "long", "short", "tall", "high", "low", "deep", "wide", "narrow",
    "old", "new", "young", "ancient", "modern", "recent",
    "fast", "slow", "quick", "rapid",
    "hot", "cold", "warm", "cool", "frozen",
    "hard", "soft", "easy", "difficult", "simple", "complex",
    "happy", "sad", "angry", "upset", "excited", "bored", "tired", "sick",
    "hungry", "thirsty", "full", "empty",
    "beautiful", "ugly", "pretty", "handsome", "cute",
    "rich", "poor", "cheap", "expensive", "free",
    "clean", "dirty", "neat", "messy",
    "safe", "dangerous", "careful", "careless",
    "true", "false", "real", "fake", "honest", "correct", "wrong",
    "open", "closed", "busy", "available",
    "important", "special", "normal", "usual", "strange", "weird",
    "different", "same", "similar", "equal",
    "possible", "impossible", "necessary", "optional",
    "positive", "negative", "certain", "uncertain", "sure", "unsure",
    "public", "private", "personal", "professional",
    "local", "national", "international", "global",
    "physical", "mental", "emotional", "social",
    "whole", "complete", "perfect", "broken",
    "ready", "prepared", "finished", "done",
    "alive", "dead", "awake", "asleep",
    "alone", "together", "single", "married",
    "early", "late", "on time",
    "near", "far", "close", "distant",
    "left", "right", "front", "back", "top", "bottom", "middle", "center",
    "inside", "outside", "above", "below", "between", "among",
    
    # Adverbs
    "very", "really", "quite", "pretty", "too", "so", "much", "more", "most",
    "always", "never", "sometimes", "usually", "often", "rarely", "seldom",
    "now", "then", "soon", "later", "already", "still", "yet", "just",
    "here", "there", "everywhere", "somewhere", "nowhere", "anywhere",
    "well", "badly", "quickly", "slowly", "carefully", "easily",
    "probably", "possibly", "certainly", "definitely", "maybe", "perhaps",
    "also", "too", "either", "neither", "only", "even", "especially",
    "almost", "nearly", "about", "approximately", "exactly", "precisely",
    "together", "alone", "apart",
    "forward", "backward", "upward", "downward",
    "again", "once", "twice",
    
    # Prepositions & Conjunctions
    "in", "on", "at", "to", "from", "with", "without", "for", "of", "by",
    "about", "after", "before", "during", "since", "until", "through",
    "into", "onto", "upon", "within", "throughout",
    "and", "or", "but", "so", "because", "if", "when", "while", "although",
    "however", "therefore", "otherwise", "instead", "besides",
    
    # Numbers as words
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
    "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million",
    "first", "second", "third", "fourth", "fifth", "last",
    
    # Common Expressions
    "yes", "no", "okay", "ok", "alright", "sure", "fine", "great", "wonderful", "awesome", "amazing",
    "wow", "oh", "ah", "oops", "uh", "um", "hmm",
    "congratulations", "welcome", "goodbye", "farewell",
    "happy birthday", "merry christmas", "happy new year",
    
    # Technology & Modern Terms
    "internet", "wifi", "password", "username", "login", "logout", "account",
    "download", "upload", "install", "update", "delete", "save", "copy", "paste",
    "search", "google", "youtube", "facebook", "instagram", "twitter", "tiktok",
    "video", "photo", "picture", "image", "camera", "selfie",
    "text", "chat", "post", "share", "like", "comment", "follow", "subscribe",
    "online", "offline", "virtual", "digital",
    
    # Emotions & Feelings
    "feeling", "emotion", "mood", "stress", "anxiety", "depression",
    "joy", "happiness", "sadness", "anger", "fear", "surprise", "disgust",
    "confidence", "doubt", "confusion", "curiosity", "interest",
    "pride", "shame", "guilt", "jealousy", "envy",
    "gratitude", "appreciation", "respect", "admiration",
    "sympathy", "empathy", "compassion", "kindness",
    "patience", "frustration", "disappointment", "satisfaction",
    
    # Health & Body
    "head", "face", "eye", "eyes", "ear", "ears", "nose", "mouth", "teeth", "tongue",
    "hair", "neck", "shoulder", "arm", "arms", "hand", "hands", "finger", "fingers",
    "chest", "stomach", "back", "leg", "legs", "foot", "feet", "toe", "toes",
    "heart", "brain", "blood", "bone", "skin", "muscle",
    "pain", "ache", "headache", "fever", "cough", "cold", "flu",
    "medicine", "pill", "drug", "treatment", "surgery", "therapy",
    "exercise", "diet", "sleep", "rest", "relax",
    
    # Education & Work
    "education", "study", "studying", "homework", "assignment", "exam", "test", "quiz",
    "grade", "score", "pass", "fail", "graduate", "graduation", "degree", "diploma",
    "subject", "math", "mathematics", "science", "english", "history", "geography",
    "physics", "chemistry", "biology", "literature", "art", "music", "sports",
    "meeting", "presentation", "report", "deadline", "project", "task",
    "salary", "wage", "income", "bonus", "promotion", "interview", "resume",
    "contract", "agreement", "document", "file", "folder",
    
    # Travel & Transportation
    "travel", "trip", "journey", "vacation", "holiday", "tour", "adventure",
    "ticket", "passport", "visa", "luggage", "baggage", "suitcase",
    "flight", "departure", "arrival", "delay", "cancel",
    "reservation", "booking", "check in", "check out",
    "tourist", "guide", "map", "direction", "destination",
    
    # Shopping & Money
    "shopping", "buy", "sell", "pay", "payment", "purchase",
    "price", "cost", "discount", "sale", "offer", "deal",
    "receipt", "bill", "invoice", "tax", "tip",
    "cash", "credit", "debit", "bank", "atm", "loan", "debt",
    "budget", "savings", "investment", "profit", "loss"
]


class TextToSpeech:
    """Thread-safe text-to-speech handler."""
    def __init__(self):
        self.speaking = False
        self.speech_rate = 150
        self.volume = 0.9
    
    def speak(self, text):
        """Speak text in a separate thread."""
        if text and not self.speaking:
            thread = threading.Thread(target=self._speak_thread, args=(text,))
            thread.daemon = True
            thread.start()
    
    def _speak_thread(self, text):
        """Internal method to speak in a thread."""
        try:
            self.speaking = True
            engine = pyttsx3.init()
            engine.setProperty('rate', self.speech_rate)
            engine.setProperty('volume', self.volume)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            self.speaking = False


class WordSuggester:
    """Suggests words based on typed letters."""
    def __init__(self, word_list):
        self.word_list = sorted(set(w.lower() for w in word_list))
    
    def get_suggestions(self, prefix, max_suggestions=5):
        """Get word suggestions based on prefix."""
        if not prefix:
            return []
        prefix = prefix.lower()
        suggestions = [w for w in self.word_list if w.startswith(prefix)]
        return suggestions[:max_suggestions]


class GeminiWordSuggester:
    """AI-powered word suggestions using Google Gemini."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        self.enabled = False
        self.fallback_suggester = WordSuggester(COMMON_WORDS)
        self.cache = {}  # Cache for suggestions
        self.last_query_time = 0
        self.query_cooldown = 0.5  # Minimum seconds between API calls
        self.config_file = "gemini_config.json"
        
        # Load saved API key
        self._load_config()
        
        if self.api_key:
            self._initialize_model()
    
    def _load_config(self):
        """Load API key from config file."""
        try:
            config_path = get_resource_path(self.config_file)
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key', '')
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save API key to config file."""
        try:
            config_path = get_resource_path(self.config_file)
            with open(config_path, 'w') as f:
                json.dump({'api_key': self.api_key}, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _initialize_model(self):
        """Initialize the Gemini model."""
        if not GEMINI_AVAILABLE:
            print("Gemini not available. Using fallback suggestions.")
            return False
        
        try:
            genai.configure(api_key=self.api_key)
            # Use gemini-2.0-flash or fallback to gemini-pro
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash')
            except:
                self.model = genai.GenerativeModel('gemini-pro')
            self.enabled = True
            print("Gemini AI initialized successfully!")
            return True
        except Exception as e:
            print(f"Failed to initialize Gemini: {e}")
            self.enabled = False
            return False
    
    def set_api_key(self, api_key):
        """Set and save a new API key."""
        self.api_key = api_key
        self._save_config()
        return self._initialize_model()
    
    def get_suggestions(self, text, max_suggestions=5):
        """Get AI-powered word suggestions."""
        if not text:
            return []
        
        # Get the current word being typed
        words = text.split()
        current_word = words[-1].lower() if words else text.lower()
        
        # Check cache first
        cache_key = text.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key][:max_suggestions]
        
        # If AI not enabled, use fallback
        if not self.enabled or not self.model:
            return self.fallback_suggester.get_suggestions(current_word, max_suggestions)
        
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_query_time < self.query_cooldown:
            return self.fallback_suggester.get_suggestions(current_word, max_suggestions)
        
        # Try AI suggestions in a thread to avoid blocking
        try:
            self.last_query_time = current_time
            suggestions = self._get_ai_suggestions(text, current_word, max_suggestions)
            if suggestions:
                self.cache[cache_key] = suggestions
                return suggestions[:max_suggestions]
        except Exception as e:
            print(f"AI suggestion error: {e}")
        
        # Fallback to word list
        return self.fallback_suggester.get_suggestions(current_word, max_suggestions)
    
    def _get_ai_suggestions(self, full_text, current_word, max_suggestions):
        """Get suggestions from Gemini AI."""
        prompt = f"""You are a word prediction assistant for a sign language app. 
The user is typing: "{full_text}"
The current incomplete word is: "{current_word}"

Provide exactly {max_suggestions} word suggestions that:
1. Complete the current word "{current_word}" if it's incomplete
2. Or suggest the next likely word based on context

Rules:
- Return ONLY the words, one per line
- No explanations, no numbering, no punctuation
- Words should be common, practical English words
- Consider the sentence context for better predictions

Example output format:
hello
help
happy"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=50,
                    temperature=0.3
                )
            )
            
            if response and response.text:
                # Parse the response
                suggestions = []
                for line in response.text.strip().split('\n'):
                    word = line.strip().lower()
                    # Remove any numbering or punctuation
                    word = ''.join(c for c in word if c.isalpha())
                    if word and len(word) > 0:
                        suggestions.append(word)
                return suggestions[:max_suggestions]
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        return []
    
    def get_next_word_suggestions(self, sentence, max_suggestions=5):
        """Get suggestions for the next word after a complete sentence."""
        if not self.enabled or not self.model:
            return []
        
        prompt = f"""Complete this sentence with the most likely next word.
Sentence: "{sentence}"

Provide {max_suggestions} possible next words, one per line.
No explanations, just words."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=30,
                    temperature=0.5
                )
            )
            
            if response and response.text:
                suggestions = []
                for line in response.text.strip().split('\n'):
                    word = line.strip().lower()
                    word = ''.join(c for c in word if c.isalpha())
                    if word:
                        suggestions.append(word)
                return suggestions[:max_suggestions]
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        return []


class ZMotionTracker:
    """Tracks finger motion to detect Z pattern for letter Z."""
    
    def __init__(self):
        self.positions = deque(maxlen=50)  # Track last 50 positions
        self.last_z_time = 0
        self.z_cooldown = 2.0  # Seconds before detecting another Z
        self.z_detected = False
        self.drawing_active = False
        self.min_points_for_z = 15
    
    def add_position(self, x, y, is_pointing):
        """Add a new fingertip position."""
        current_time = time.time()
        
        # Only track when index finger is pointing (extended)
        if is_pointing:
            self.positions.append((x, y, current_time))
            self.drawing_active = True
        else:
            # Check for Z when finger stops pointing
            if self.drawing_active and len(self.positions) >= self.min_points_for_z:
                if self._check_z_pattern():
                    if current_time - self.last_z_time > self.z_cooldown:
                        self.z_detected = True
                        self.last_z_time = current_time
            self.positions.clear()
            self.drawing_active = False
    
    def _check_z_pattern(self):
        """Check if the tracked positions form a Z pattern."""
        if len(self.positions) < self.min_points_for_z:
            return False
        
        points = list(self.positions)
        
        # Get bounding box
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Z should have reasonable size
        if width < 0.05 or height < 0.05:
            return False
        
        # Divide into 3 segments
        n = len(points)
        seg1 = points[:n//3]  # Top horizontal (right to left or left to right)
        seg2 = points[n//3:2*n//3]  # Diagonal
        seg3 = points[2*n//3:]  # Bottom horizontal
        
        # Check segment 1: mostly horizontal at top
        seg1_ys = [p[1] for p in seg1]
        seg1_xs = [p[0] for p in seg1]
        seg1_y_var = max(seg1_ys) - min(seg1_ys) if seg1_ys else 1
        seg1_x_range = max(seg1_xs) - min(seg1_xs) if seg1_xs else 0
        
        # Check segment 3: mostly horizontal at bottom
        seg3_ys = [p[1] for p in seg3]
        seg3_xs = [p[0] for p in seg3]
        seg3_y_var = max(seg3_ys) - min(seg3_ys) if seg3_ys else 1
        seg3_x_range = max(seg3_xs) - min(seg3_xs) if seg3_xs else 0
        
        # Segment 1 should be more horizontal (low y variance, high x range)
        # Segment 3 should be more horizontal too
        # Middle segment should be diagonal
        
        is_seg1_horizontal = seg1_y_var < height * 0.4 and seg1_x_range > width * 0.3
        is_seg3_horizontal = seg3_y_var < height * 0.4 and seg3_x_range > width * 0.3
        
        # Check that top segment is above bottom segment
        avg_seg1_y = sum(seg1_ys) / len(seg1_ys) if seg1_ys else 0
        avg_seg3_y = sum(seg3_ys) / len(seg3_ys) if seg3_ys else 0
        
        # In screen coordinates, top has smaller y
        top_bottom_order = avg_seg1_y < avg_seg3_y
        
        return is_seg1_horizontal and is_seg3_horizontal and top_bottom_order
    
    def get_z_detected(self):
        """Check and reset Z detection flag."""
        if self.z_detected:
            self.z_detected = False
            return True
        return False
    
    def get_trail_points(self):
        """Get recent positions for drawing trail."""
        return list(self.positions)


class HandSignRecognizer:
    """Hand sign recognition engine using MediaPipe."""
    
    def __init__(self):
        model_path = self._ensure_model()
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.hand_landmarker = vision.HandLandmarker.create_from_options(options)
        
        self.prediction_buffer = deque(maxlen=10)
        self.current_letter = ""
        self.confidence = 0.0
        
        self.text_buffer = ""
        self.last_added_letter = ""
        self.last_add_time = 0
        self.letter_cooldown = 1.0
        self.stable_frames = 0
        self.stable_threshold = 15
        self.last_stable_sign = ""
        
        self.word_suggester = GeminiWordSuggester()
        self.suggestions = []
        self.tts = TextToSpeech()
        
        # Z motion tracker for drawing Z in the air
        self.z_tracker = ZMotionTracker()
        
        # Landmark indices
        self.WRIST = 0
        self.THUMB_CMC, self.THUMB_MCP, self.THUMB_IP, self.THUMB_TIP = 1, 2, 3, 4
        self.INDEX_MCP, self.INDEX_PIP, self.INDEX_DIP, self.INDEX_TIP = 5, 6, 7, 8
        self.MIDDLE_MCP, self.MIDDLE_PIP, self.MIDDLE_DIP, self.MIDDLE_TIP = 9, 10, 11, 12
        self.RING_MCP, self.RING_PIP, self.RING_DIP, self.RING_TIP = 13, 14, 15, 16
        self.PINKY_MCP, self.PINKY_PIP, self.PINKY_DIP, self.PINKY_TIP = 17, 18, 19, 20

    def _ensure_model(self):
        """Download the hand landmarker model if not present."""
        if hasattr(sys, '_MEIPASS'):
            model_path = get_resource_path("hand_landmarker.task")
            if os.path.exists(model_path):
                return model_path
        
        model_path = "hand_landmarker.task"
        if not os.path.exists(model_path):
            print("Downloading hand landmarker model...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            urllib.request.urlretrieve(url, model_path)
            print("Model downloaded successfully!")
        return model_path

    def get_landmark_positions(self, hand_landmarks):
        landmarks = []
        for lm in hand_landmarks:
            landmarks.append([lm.x, lm.y, lm.z])
        return np.array(landmarks)

    def is_finger_extended(self, landmarks, finger_tip, finger_pip, finger_mcp):
        tip = landmarks[finger_tip]
        pip = landmarks[finger_pip]
        tip_to_wrist = np.linalg.norm(tip[:2] - landmarks[self.WRIST][:2])
        pip_to_wrist = np.linalg.norm(pip[:2] - landmarks[self.WRIST][:2])
        return tip_to_wrist > pip_to_wrist

    def is_thumb_extended(self, landmarks, handedness):
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        if handedness == "Right":
            return thumb_tip[0] < thumb_mcp[0]
        else:
            return thumb_tip[0] > thumb_mcp[0]

    def get_finger_states(self, landmarks, handedness):
        return {
            'thumb': self.is_thumb_extended(landmarks, handedness),
            'index': self.is_finger_extended(landmarks, self.INDEX_TIP, self.INDEX_PIP, self.INDEX_MCP),
            'middle': self.is_finger_extended(landmarks, self.MIDDLE_TIP, self.MIDDLE_PIP, self.MIDDLE_MCP),
            'ring': self.is_finger_extended(landmarks, self.RING_TIP, self.RING_PIP, self.RING_MCP),
            'pinky': self.is_finger_extended(landmarks, self.PINKY_TIP, self.PINKY_PIP, self.PINKY_MCP)
        }

    def distance(self, landmarks, idx1, idx2):
        return np.linalg.norm(landmarks[idx1] - landmarks[idx2])

    def recognize_sign(self, landmarks, handedness):
        """Recognize ASL letter from hand landmarks."""
        fingers = self.get_finger_states(landmarks, handedness)
        
        thumb_index_dist = self.distance(landmarks, self.THUMB_TIP, self.INDEX_TIP)
        thumb_middle_dist = self.distance(landmarks, self.THUMB_TIP, self.MIDDLE_TIP)
        index_middle_dist = self.distance(landmarks, self.INDEX_TIP, self.MIDDLE_TIP)
        
        extended_count = sum(fingers.values())
        
        # A - Fist with thumb beside index finger
        if not fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            if fingers['thumb']:
                return 'A', 0.85
        
        # B - All fingers extended, thumb tucked
        if fingers['index'] and fingers['middle'] and fingers['ring'] and fingers['pinky'] and not fingers['thumb']:
            return 'B', 0.85
        
        # C - Curved hand
        if extended_count >= 3:
            if 0.05 < thumb_index_dist < 0.15:
                return 'C', 0.75
        
        # D - Index up, others touching thumb
        if fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            if thumb_middle_dist < 0.08:
                return 'D', 0.80
        
        # E - All fingers curled
        if not fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky'] and not fingers['thumb']:
            return 'E', 0.75
        
        # F - Index and thumb touch, others extended
        if thumb_index_dist < 0.05 and fingers['middle'] and fingers['ring'] and fingers['pinky']:
            return 'F', 0.85
        
        # G - Index pointing sideways
        if fingers['index'] and fingers['thumb'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            index_tip = landmarks[self.INDEX_TIP]
            index_mcp = landmarks[self.INDEX_MCP]
            if abs(index_tip[1] - index_mcp[1]) < 0.1:
                return 'G', 0.75
        
        # H - Index and middle pointing sideways
        if fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            index_tip = landmarks[self.INDEX_TIP]
            index_mcp = landmarks[self.INDEX_MCP]
            if abs(index_tip[1] - index_mcp[1]) < 0.1:
                return 'H', 0.75
        
        # I - Pinky up only
        if not fingers['index'] and not fingers['middle'] and not fingers['ring'] and fingers['pinky']:
            return 'I', 0.90
        
        # K - Index and middle up in V, thumb between
        if fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            if index_middle_dist > 0.06:
                return 'K', 0.80
        
        # L - L shape
        if fingers['index'] and fingers['thumb'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            if thumb_index_dist > 0.1:
                return 'L', 0.85
        
        # O - Fingers curved to form O
        if 0.03 < thumb_index_dist < 0.08 and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            return 'O', 0.75
        
        # R - Index and middle crossed
        if fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            if index_middle_dist < 0.03:
                return 'R', 0.80
        
        # U - Index and middle up together
        if fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky'] and not fingers['thumb']:
            if index_middle_dist < 0.05:
                return 'U', 0.85
        
        # V - Peace sign
        if fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            if index_middle_dist > 0.05:
                return 'V', 0.90
        
        # W - Index, middle, ring extended
        if fingers['index'] and fingers['middle'] and fingers['ring'] and not fingers['pinky']:
            return 'W', 0.85
        
        # Y - Thumb and pinky extended
        if fingers['thumb'] and fingers['pinky'] and not fingers['index'] and not fingers['middle'] and not fingers['ring']:
            return 'Y', 0.90
        
        # 5 - All fingers extended
        if all(fingers.values()):
            return '5', 0.90
        
        # 1 - Index only
        if fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky'] and not fingers['thumb']:
            return '1', 0.85
        
        # Thumbs up
        if fingers['thumb'] and not fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']:
            thumb_tip = landmarks[self.THUMB_TIP]
            thumb_mcp = landmarks[self.THUMB_MCP]
            if thumb_tip[1] < thumb_mcp[1]:
                return 'THUMBS_UP', 0.90
        
        return '?', 0.0

    def draw_landmarks(self, frame, hand_landmarks, width, height):
        """Draw hand landmarks with modern styling."""
        HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17)
        ]
        
        # Draw connections with gradient effect
        for connection in HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start = hand_landmarks[start_idx]
            end = hand_landmarks[end_idx]
            start_point = (int(start.x * width), int(start.y * height))
            end_point = (int(end.x * width), int(end.y * height))
            cv2.line(frame, start_point, end_point, (0, 255, 180), 3)
            cv2.line(frame, start_point, end_point, (0, 200, 150), 2)
        
        # Draw landmarks with glow effect
        for idx, lm in enumerate(hand_landmarks):
            x, y = int(lm.x * width), int(lm.y * height)
            if idx in [4, 8, 12, 16, 20]:
                cv2.circle(frame, (x, y), 12, (0, 100, 255), -1)
                cv2.circle(frame, (x, y), 8, (0, 150, 255), -1)
                cv2.circle(frame, (x, y), 5, (50, 200, 255), -1)
            elif idx == 0:
                cv2.circle(frame, (x, y), 12, (255, 100, 0), -1)
                cv2.circle(frame, (x, y), 8, (255, 150, 50), -1)
            else:
                cv2.circle(frame, (x, y), 7, (0, 200, 150), -1)
                cv2.circle(frame, (x, y), 4, (100, 255, 200), -1)
        
        return frame

    def process_frame(self, frame):
        """Process a single frame and return recognition results."""
        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.hand_landmarker.detect(mp_image)
        
        recognized_signs = []
        
        if results.hand_landmarks:
            for idx, hand_landmarks in enumerate(results.hand_landmarks):
                self.draw_landmarks(frame, hand_landmarks, width, height)
                
                hand_label = "Right"
                if results.handedness and idx < len(results.handedness):
                    hand_label = results.handedness[idx][0].category_name
                
                landmarks = self.get_landmark_positions(hand_landmarks)
                
                # Track index fingertip for Z motion detection
                index_tip = landmarks[self.INDEX_TIP]
                fingers = self.get_finger_states(landmarks, hand_label)
                
                # Check if only index finger is pointing (for Z drawing)
                is_pointing = (fingers['index'] and not fingers['middle'] and 
                              not fingers['ring'] and not fingers['pinky'])
                
                self.z_tracker.add_position(index_tip[0], index_tip[1], is_pointing)
                
                # Draw motion trail for Z
                trail = self.z_tracker.get_trail_points()
                if len(trail) > 1:
                    for i in range(1, len(trail)):
                        pt1 = (int(trail[i-1][0] * width), int(trail[i-1][1] * height))
                        pt2 = (int(trail[i][0] * width), int(trail[i][1] * height))
                        # Fade color based on age
                        alpha = i / len(trail)
                        color = (int(255 * alpha), int(100 * alpha), int(255))
                        cv2.line(frame, pt1, pt2, color, 3)
                
                # When drawing Z, pause stability detection
                if self.z_tracker.drawing_active:
                    # Reset stability to pause "hold sign steady"
                    self.stable_frames = 0
                    self.last_stable_sign = ""
                    # Show drawing indicator
                    cv2.putText(frame, "Drawing Z...", (width//2 - 80, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 200, 0), 2)
                    sign, confidence = 'Z?', 0.0  # Temporary sign while drawing
                # Check for Z detection
                elif self.z_tracker.get_z_detected():
                    sign, confidence = 'Z', 0.90
                    # Show Z detected message
                    cv2.putText(frame, "Z DETECTED!", (width//2 - 100, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                else:
                    sign, confidence = self.recognize_sign(landmarks, hand_label)
                
                recognized_signs.append({
                    'hand': hand_label,
                    'sign': sign,
                    'confidence': confidence,
                    'landmarks': hand_landmarks
                })
        else:
            # No hand detected - check if we just finished drawing Z
            self.z_tracker.add_position(0, 0, False)
        
        return frame, recognized_signs

    def add_letter(self, letter, confidence):
        """Add a letter to the text buffer with stability check."""
        current_time = time.time()
        
        if letter == '?' or confidence < 0.7:
            self.stable_frames = 0
            self.last_stable_sign = ""
            return False
        
        if letter == self.last_stable_sign:
            self.stable_frames += 1
        else:
            self.stable_frames = 1
            self.last_stable_sign = letter
        
        if self.stable_frames >= self.stable_threshold:
            if letter != self.last_added_letter or (current_time - self.last_add_time) > self.letter_cooldown:
                self.text_buffer += letter
                self.last_added_letter = letter
                self.last_add_time = current_time
                self.stable_frames = 0
                self.update_suggestions()
                return True
        
        return False
    
    def update_suggestions(self):
        # Use full text for AI context, or just current word for fallback
        if self.text_buffer:
            self.suggestions = self.word_suggester.get_suggestions(self.text_buffer)
        else:
            self.suggestions = []
    
    def select_suggestion(self, index):
        if 0 <= index < len(self.suggestions):
            words = self.text_buffer.split()
            if words:
                words[-1] = self.suggestions[index].upper()
                self.text_buffer = ' '.join(words) + ' '
            else:
                self.text_buffer = self.suggestions[index].upper() + ' '
            self.suggestions = []
            self.last_added_letter = ""
            return True
        return False
    
    def add_space(self):
        if self.text_buffer and not self.text_buffer.endswith(' '):
            self.text_buffer += ' '
            self.suggestions = []
            self.last_added_letter = ""
    
    def backspace(self):
        if self.text_buffer:
            self.text_buffer = self.text_buffer[:-1]
            self.update_suggestions()
    
    def clear_text(self):
        self.text_buffer = ""
        self.suggestions = []
        self.last_added_letter = ""
        self.stable_frames = 0
    
    def speak_text(self):
        if self.text_buffer.strip():
            self.tts.speak(self.text_buffer.strip())
    
    def release(self):
        self.hand_landmarker.close()


# ============== ACCESSIBLE GUI APPLICATION FOR PWD ==============

class SignLanguageApp:
    """
    Accessible Application Window designed for PWD (Persons with Disabilities).
    Features: Large buttons, high contrast, simple navigation, clear feedback.
    """
    
    # Modern "Interesting" Light Theme
    COLORS = {
        'bg_main': '#E5E5E5',       # Light Gray background
        'bg_panel': '#FFFFFF',      # Pure white cards
        'bg_header': '#FFFFFF',     # Header background
        'bg_button': '#F0F2F5',     # Subtle button background
        'primary': '#0969da',       # Vibrant Blue
        'secondary': '#FF6584',     # Soft Red/Pink
        'success': '#00B894',       # Mint Green
        'header_text': '#2D3436',   # Dark Slate
        'accent_green': '#00B894',  # Mapped for compatibility
        'accent_blue': '#0969da',   
        'accent_red': '#FF3B30',    
        'accent_yellow': '#FFCC00', 
        'accent_purple': '#AF52DE', 
        'text_white': '#2D3436',    # Dark text for light mode (name kept for compat)
        'text_dark': '#2D3436',     # New clean name
        'text_gray': '#636E72',     # Secondary text
        'text_light': '#636E72',    # Alias
        'border': '#DFE6E9',        
        'highlight': '#0969da',     
    }
    
    def __init__(self):
        self.recognizer = None
        self.cap = None
        self.running = False
        self.fps = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # Create main window - Fullscreen for accessibility
        if USING_CTK:
            self.root = ctk.CTk()
            ctk.set_appearance_mode("light")  # Set to Light Mode
        else:
            self.root = tk.Tk()
            self.root.configure(bg=self.COLORS['bg_main'])
        
        self.root.title("✋Hand Sign Language")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Start in TRUE fullscreen (covers taskbar)
        self.root.attributes('-fullscreen', True)
        self.is_fullscreen = True
        
        self._setup_accessible_ui()
        self._bind_shortcuts()
        
        # Initialize recognizer
        self.status_label.configure(text="🔄 Starting up... Please wait")
        self.root.after(100, self._initialize_recognizer)
    
    def _setup_accessible_ui(self):
        """Setup accessible UI with MODERN DASHBOARD layout."""
        if not USING_CTK:
            self._setup_accessible_ui_tk()
            return
        
        # Configure root
        self.root.configure(fg_color=self.COLORS['bg_main'])
        
        # ========== HEADER + TEXT DISPLAY (Top Section) ==========
        top_section = ctk.CTkFrame(self.root, fg_color=self.COLORS['bg_header'], corner_radius=0)
        top_section.pack(fill="x", padx=0, pady=0)
        
        # Header Row
        header_row = ctk.CTkFrame(top_section, height=60, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=10)
        
        # Title
        ctk.CTkLabel(
            header_row,
            text="Hand Sign Language ",
            font=("Segoe UI", 26, "bold"),
            text_color=self.COLORS['text_dark']
        ).pack(side="left", padx=10)
        
        # Right Side Header Buttons
        self.exit_btn = ctk.CTkButton(header_row, text="✕", width=50, height=40,
                                      fg_color=self.COLORS['accent_red'], text_color="#FFF",
                                      font=("Segoe UI", 20, "bold"), corner_radius=10, command=self._on_closing)
        self.exit_btn.pack(side="right", padx=5)
        
        self.fullscreen_btn = ctk.CTkButton(header_row, text="⛶", width=50, height=40,
                                            fg_color=self.COLORS['bg_button'], text_color=self.COLORS['text_dark'],
                                            font=("Segoe UI", 20), corner_radius=10, command=self._toggle_fullscreen)
        self.fullscreen_btn.pack(side="right", padx=5)
        
        self.settings_btn = ctk.CTkButton(header_row, text="⚙", width=50, height=40, 
                                          fg_color=self.COLORS['bg_button'], text_color=self.COLORS['text_dark'],
                                          font=("Segoe UI", 20), corner_radius=10, command=self._show_settings)
        self.settings_btn.pack(side="right", padx=5)
        
        self.help_btn = ctk.CTkButton(header_row, text="❓", width=50, height=40,
                                      fg_color=self.COLORS['bg_button'], text_color=self.COLORS['text_dark'],
                                      font=("Segoe UI", 20), corner_radius=10, command=self._show_help)
        self.help_btn.pack(side="right", padx=5)

        # Text Display (Prominent Bar) - Looks like a document
        text_bar = ctk.CTkFrame(top_section, fg_color=self.COLORS['bg_main'], corner_radius=15)
        text_bar.pack(fill="x", padx=30, pady=(0, 20))
        
        self.text_display = ctk.CTkTextbox(
            text_bar,
            height=80,
            font=("Consolas", 32), # Huge font for visibility
            fg_color="transparent",
            text_color=self.COLORS['primary'],
            state="disabled",
            activate_scrollbars=False
        )
        self.text_display.pack(fill="both", padx=20, pady=10)
        
        # ========== MAIN CONTENT (Split Layout) ==========
        main_content = ctk.CTkFrame(self.root, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- LEFT: CAMERA (65%) ---
        left_col = ctk.CTkFrame(main_content, fg_color=self.COLORS['bg_panel'], corner_radius=20)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Camera Header
        cam_head = ctk.CTkFrame(left_col, height=40, fg_color="transparent")
        cam_head.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(cam_head, text="📷 Live Camera", font=("Segoe UI", 18, "bold"), text_color=self.COLORS['text_light']).pack(side="left")
        self.fps_label = ctk.CTkLabel(cam_head, text="FPS: 0", font=("Segoe UI", 14), text_color=self.COLORS['text_light'])
        self.fps_label.pack(side="right")
        
        # Camera Feed
        self.camera_label = ctk.CTkLabel(
            left_col,
            text="Press START to detect signs",
            font=("Segoe UI", 24),
            text_color=self.COLORS['text_light'],
            fg_color=self.COLORS['bg_main'],
            corner_radius=15
        )
        self.camera_label.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Stability Bar & Feedback
        stability_frame = ctk.CTkFrame(left_col, fg_color="transparent", height=40)
        stability_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(stability_frame, text="Hold Steady:", font=("Segoe UI", 14, "bold"), text_color=self.COLORS['text_light']).pack(side="left")
        self.progress_bar = ctk.CTkProgressBar(stability_frame, height=12, progress_color=self.COLORS['success'], fg_color=self.COLORS['bg_main'])
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=15)
        self.progress_bar.set(0)
        
        self.holding_sign_label = ctk.CTkLabel(stability_frame, text="", font=("Segoe UI", 20, "bold"), text_color=self.COLORS['secondary'])
        self.holding_sign_label.pack(side="right", padx=10)
        
        # --- RIGHT: TOOLS & CONTROLS (35%) ---
        right_col = ctk.CTkFrame(main_content, fg_color="transparent")
        right_col.pack(side="right", fill="y", padx=0)
        right_col.pack_propagate(False)
        right_col.configure(width=350)
        
        # 1. Current Detection Card - Colorful & Big
        det_card = ctk.CTkFrame(right_col, fg_color=self.COLORS['bg_panel'], corner_radius=20, height=170)
        det_card.pack(fill="x", pady=(0, 10))
        det_card.pack_propagate(False)
        
        ctk.CTkLabel(det_card, text="DETECTED SIGN", font=("Segoe UI", 12, "bold"), text_color=self.COLORS['text_light']).pack(pady=(12, 0))
        self.current_sign_label = ctk.CTkLabel(det_card, text="—", font=("Segoe UI", 90, "bold"), text_color=self.COLORS['primary'])
        self.current_sign_label.pack(expand=True)
        
        # Stats row
        info_row = ctk.CTkFrame(det_card, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 10), padx=20)
        self.hand_label = ctk.CTkLabel(info_row, text="Hand: -", font=("Segoe UI", 12), text_color=self.COLORS['text_light'])
        self.hand_label.pack(side="left")
        self.confidence_label = ctk.CTkLabel(info_row, text="Conf: -%", font=("Segoe UI", 12), text_color=self.COLORS['text_light'])
        self.confidence_label.pack(side="right")
        
        # 2. Suggestions - Modern Tags
        sugg_card = ctk.CTkFrame(right_col, fg_color=self.COLORS['bg_panel'], corner_radius=20)
        sugg_card.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(sugg_card, text="SUGGESTIONS", font=("Segoe UI", 12, "bold"), text_color=self.COLORS['text_light']).pack(pady=(10, 3))
        self.suggestion_buttons = []
        for i in range(5):
            btn = ctk.CTkButton(sugg_card, text=f"{i+1}. —", height=30, 
                               fg_color=self.COLORS['bg_main'], text_color=self.COLORS['text_dark'],
                               hover_color=self.COLORS['highlight'], corner_radius=8,
                               anchor="w", font=("Segoe UI", 13),
                               command=lambda idx=i: self._select_suggestion(idx))
            btn.pack(fill="x", padx=12, pady=2)
            self.suggestion_buttons.append(btn)
        ctk.CTkLabel(sugg_card, text="", height=5).pack() # Spacer
        
        # 3. Controls - Refined Panel
        ctrl_card = ctk.CTkFrame(right_col, fg_color=self.COLORS['bg_panel'], corner_radius=20)
        ctrl_card.pack(fill="both", expand=True, pady=(0, 0))
        
        # Header
        ctk.CTkLabel(ctrl_card, text="ACTIONS", font=("Segoe UI", 12, "bold"), text_color=self.COLORS['text_light']).pack(pady=(10, 5))

        # Content container
        ctrl_content = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_content.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Start/Stop (Big)
        self.start_btn = ctk.CTkButton(ctrl_content, text="▶ START CAMERA", height=45, font=("Segoe UI", 15, "bold"),
                                      fg_color=self.COLORS['success'], hover_color="#00a884", corner_radius=12,
                                      command=self._toggle_camera)
        self.start_btn.pack(fill="x", pady=(0, 8))
        
        # Row 1: Space & Backspace
        row1 = ctk.CTkFrame(ctrl_content, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))
        
        self.space_btn = ctk.CTkButton(row1, text="␣ SPACE", height=40, fg_color="#F0F2F5", 
                                       text_color=self.COLORS['text_dark'], hover_color="#DCDFEE", corner_radius=10,
                                       font=("Segoe UI", 13, "bold"), command=self._add_space)
        self.space_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        self.backspace_btn = ctk.CTkButton(row1, text="⌫ DEL", height=40, fg_color=self.COLORS['accent_yellow'],
                                           text_color="#FFF", hover_color="#e0b020", corner_radius=10,
                                           font=("Segoe UI", 13, "bold"), command=self._backspace)
        self.backspace_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
        
        # Row 2: Speak & Clear
        row2 = ctk.CTkFrame(ctrl_content, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 6))

        self.speak_btn = ctk.CTkButton(row2, text="🔊 SPEAK", height=40, fg_color=self.COLORS['accent_purple'],
                                       text_color="#FFF", hover_color="#9050e0", corner_radius=10,
                                       font=("Segoe UI", 13, "bold"), command=self._speak_text)
        self.speak_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        self.clear_btn = ctk.CTkButton(row2, text="🗑 CLEAR", height=40, fg_color=self.COLORS['accent_red'],
                                       text_color="#FFF", hover_color="#d03030", corner_radius=10,
                                       font=("Segoe UI", 13, "bold"), command=self._clear_text)
        self.clear_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
        
        # Copy Button
        self.copy_btn = ctk.CTkButton(ctrl_content, text="📋 COPY TEXT", height=40, fg_color="#F0F2F5",
                                       text_color=self.COLORS['text_dark'], hover_color="#DCDFEE", corner_radius=10,
                                       font=("Segoe UI", 13, "bold"), command=self._copy_text)
        self.copy_btn.pack(fill="x", pady=(0, 0))

        # Status Bar
        self.status_label = ctk.CTkLabel(self.root, text="Ready", text_color=self.COLORS['text_light'], font=("Segoe UI", 12))
        self.status_label.pack(side="bottom", pady=5)

    
    def _setup_accessible_ui_tk(self):
        """Fallback accessible UI with standard tkinter."""
        # Basic tk implementation for systems without customtkinter
        self.root.configure(bg=self.COLORS['bg_main'])
        
        # Title
        title = tk.Label(self.root, text="✋ Sign Language Recognition",
                        font=("Segoe UI", 28, "bold"), bg=self.COLORS['bg_panel'],
                        fg=self.COLORS['text_white'])
        title.pack(fill="x", pady=20)
        
        # Main frame
        main = tk.Frame(self.root, bg=self.COLORS['bg_main'])
        main.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left - Camera
        left = tk.Frame(main, bg=self.COLORS['bg_panel'])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.current_sign_label = tk.Label(left, text="—", font=("Segoe UI", 64, "bold"),
                                           bg=self.COLORS['bg_panel'], fg=self.COLORS['accent_green'])
        self.current_sign_label.pack(pady=20)
        
        self.camera_label = tk.Label(left, text="Press START to begin",
                                     font=("Segoe UI", 20), bg=self.COLORS['bg_button'],
                                     fg=self.COLORS['text_gray'])
        self.camera_label.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.hand_label = tk.Label(left, text="Hand: —", font=("Segoe UI", 16),
                                   bg=self.COLORS['bg_panel'], fg=self.COLORS['text_gray'])
        self.hand_label.pack()
        
        self.confidence_label = tk.Label(left, text="Confidence: —%", font=("Segoe UI", 16),
                                         bg=self.COLORS['bg_panel'], fg=self.COLORS['text_gray'])
        self.confidence_label.pack()
        
        self.fps_label = tk.Label(left, text="FPS: 0", font=("Segoe UI", 14),
                                  bg=self.COLORS['bg_panel'], fg=self.COLORS['text_gray'])
        self.fps_label.pack()
        
        self.progress_bar = None
        self.stability_label = None
        self.holding_sign_label = None
        
        # Right - Controls
        right = tk.Frame(main, width=350, bg=self.COLORS['bg_panel'])
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)
        
        self.text_display = tk.Text(right, height=4, font=("Consolas", 18),
                                    bg=self.COLORS['bg_button'], fg=self.COLORS['text_white'])
        self.text_display.pack(fill="x", padx=15, pady=20)
        
        self.suggestion_buttons = []
        for i in range(5):
            btn = tk.Button(right, text=f"{i+1}. —", font=("Segoe UI", 14),
                           bg=self.COLORS['bg_button'], fg=self.COLORS['text_white'],
                           relief="flat", command=lambda idx=i: self._select_suggestion(idx))
            btn.pack(fill="x", padx=15, pady=3)
            self.suggestion_buttons.append(btn)
        
        self.start_btn = tk.Button(right, text="▶ START CAMERA", font=("Segoe UI", 18, "bold"),
                                   bg=self.COLORS['accent_green'], fg="white",
                                   relief="flat", height=2, command=self._toggle_camera)
        self.start_btn.pack(fill="x", padx=15, pady=15)
        
        self.space_btn = tk.Button(right, text="SPACE", font=("Segoe UI", 14, "bold"),
                                   bg=self.COLORS['accent_blue'], fg="white",
                                   relief="flat", command=self._add_space)
        self.space_btn.pack(fill="x", padx=15, pady=3)
        
        self.backspace_btn = tk.Button(right, text="DELETE", font=("Segoe UI", 14, "bold"),
                                       bg=self.COLORS['accent_yellow'], fg="black",
                                       relief="flat", command=self._backspace)
        self.backspace_btn.pack(fill="x", padx=15, pady=3)
        
        self.speak_btn = tk.Button(right, text="🔊 SPEAK", font=("Segoe UI", 14, "bold"),
                                   bg=self.COLORS['accent_purple'], fg="white",
                                   relief="flat", command=self._speak_text)
        self.speak_btn.pack(fill="x", padx=15, pady=3)
        
        self.copy_btn = tk.Button(right, text="COPY", font=("Segoe UI", 14, "bold"),
                                  bg=self.COLORS['bg_button'], fg="white",
                                  relief="flat", command=self._copy_text)
        self.copy_btn.pack(fill="x", padx=15, pady=3)
        
        self.clear_btn = tk.Button(right, text="CLEAR ALL", font=("Segoe UI", 14, "bold"),
                                   bg=self.COLORS['accent_red'], fg="white",
                                   relief="flat", command=self._clear_text)
        self.clear_btn.pack(fill="x", padx=15, pady=10)
        
        # Status
        self.status_label = tk.Label(self.root, text="Ready", font=("Segoe UI", 16),
                                     bg=self.COLORS['bg_panel'], fg=self.COLORS['text_white'])
        self.status_label.pack(fill="x", pady=10)
        
        self.settings_btn = None
        self.help_btn = None
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<space>', lambda e: self._add_space())
        self.root.bind('<BackSpace>', lambda e: self._backspace())
        self.root.bind('<Return>', lambda e: self._speak_text())
        self.root.bind('<r>', lambda e: self._clear_text())
        self.root.bind('<R>', lambda e: self._clear_text())
        self.root.bind('<Escape>', lambda e: self._toggle_fullscreen())
        self.root.bind('<F11>', lambda e: self._toggle_fullscreen())
        self.root.bind('<1>', lambda e: self._select_suggestion(0))
        self.root.bind('<2>', lambda e: self._select_suggestion(1))
        self.root.bind('<3>', lambda e: self._select_suggestion(2))
        self.root.bind('<4>', lambda e: self._select_suggestion(3))
        self.root.bind('<5>', lambda e: self._select_suggestion(4))
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        if not self.is_fullscreen:
            self.root.state('zoomed')
    
    def _initialize_recognizer(self):
        """Initialize the hand sign recognizer."""
        try:
            self.recognizer = HandSignRecognizer()
            self.status_label.configure(text="Recognition engine ready. Click 'Start Camera' to begin.")
        except Exception as e:
            self.status_label.configure(text=f"Error initializing: {str(e)}")
    
    def _toggle_camera(self):
        """Toggle camera on/off."""
        if not self.running:
            self._start_camera()
        else:
            self._stop_camera()
    
    def _start_camera(self):
        """Start the camera feed."""
        if self.recognizer is None:
            self.status_label.configure(text="Please wait for initialization...")
            return
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_label.configure(text="Error: Could not open camera!")
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.running = True
        if USING_CTK:
            self.start_btn.configure(text="⏹  STOP CAMERA", fg_color=self.COLORS['accent_red'])
        else:
            self.start_btn.configure(text="⏹  STOP CAMERA", bg=self.COLORS['accent_red'])
        
        self.status_label.configure(text="Camera running - Show hand signs to recognize")
        self._update_frame()
    
    def _stop_camera(self):
        """Stop the camera feed."""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if USING_CTK:
            self.start_btn.configure(text="▶  START CAMERA", fg_color=self.COLORS['accent_green'])
            self.camera_label.configure(image=None, text="📹  CAMERA\n\nPress the green START button to begin")
        else:
            self.start_btn.configure(text="▶  START CAMERA", bg=self.COLORS['accent_green'])
        
        self.status_label.configure(text="Camera stopped")
    
    def _update_frame(self):
        """Update the camera frame."""
        if not self.running or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.configure(text="Error reading camera frame")
            self._stop_camera()
            return
        
        # Flip and process frame
        frame = cv2.flip(frame, 1)
        frame, recognized_signs = self.recognizer.process_frame(frame)
        
        # Update FPS
        self.fps_counter += 1
        if time.time() - self.fps_start_time >= 1:
            self.fps = self.fps_counter / (time.time() - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = time.time()
            if USING_CTK:
                self.fps_label.configure(text=f"FPS: {self.fps:.1f}")
            else:
                self.fps_label.configure(text=f"FPS: {self.fps:.1f}")
        
        # Process recognized signs
        if recognized_signs:
            sign = recognized_signs[0]['sign']
            confidence = recognized_signs[0]['confidence']
            hand = recognized_signs[0]['hand']
            
            # Update UI
            if USING_CTK:
                color = self.COLORS['accent_green'] if confidence > 0.7 else self.COLORS['accent_yellow']
                self.current_sign_label.configure(text=sign, text_color=color)
                self.hand_label.configure(text=f"Hand: {hand}")
                self.confidence_label.configure(text=f"Confidence: {confidence*100:.0f}%")
            else:
                self.current_sign_label.configure(text=sign)
                self.hand_label.configure(text=f"Hand: {hand}")
                self.confidence_label.configure(text=f"Confidence: {confidence*100:.0f}%")
            
            # Try to add letter
            if len(sign) == 1 and sign.isalpha():
                if self.recognizer.add_letter(sign, confidence):
                    self._update_text_display()
            
            # Update progress bar
            if self.progress_bar and self.recognizer.stable_frames > 0:
                progress = min(self.recognizer.stable_frames / self.recognizer.stable_threshold, 1.0)
                if USING_CTK:
                    self.progress_bar.set(progress)
                    self.holding_sign_label.configure(text=self.recognizer.last_stable_sign)
        else:
            self.recognizer.stable_frames = 0
            self.recognizer.last_stable_sign = ""
            if USING_CTK:
                self.current_sign_label.configure(text="—", text_color=self.COLORS['text_gray'])
                self.hand_label.configure(text="Hand: -")
                self.confidence_label.configure(text="Confidence: -%")
                self.progress_bar.set(0)
                self.holding_sign_label.configure(text="")
            else:
                self.current_sign_label.configure(text="-")
                self.hand_label.configure(text="Hand: -")
                self.confidence_label.configure(text="Confidence: -%")
        
        # Update suggestions
        self._update_suggestions()
        
        # Convert frame for display — dynamically size to camera widget
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cam_w = self.camera_label.winfo_width()
        cam_h = self.camera_label.winfo_height()
        if cam_w > 10 and cam_h > 10:
            # Maintain aspect ratio within the available space
            src_h, src_w = frame.shape[:2]
            scale = min(cam_w / src_w, cam_h / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            frame = cv2.resize(frame, (new_w, new_h))
        else:
            frame = cv2.resize(frame, (800, 500))
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        if USING_CTK:
            self.camera_label.configure(image=imgtk, text="")
        else:
            self.camera_label.configure(image=imgtk)
        self.camera_label.imgtk = imgtk
        
        # Schedule next update
        self.root.after(10, self._update_frame)
    
    def _update_text_display(self):
        """Update the text display."""
        if USING_CTK:
            self.text_display.configure(state="normal")  # Enable temporarily to update
            self.text_display.delete("0.0", "end")
            self.text_display.insert("0.0", self.recognizer.text_buffer + "▌")
            self.text_display.configure(state="disabled")  # Disable again
        else:
            self.text_display.configure(state="normal")
            self.text_display.delete("1.0", "end")
            self.text_display.insert("1.0", self.recognizer.text_buffer + "▌")
            self.text_display.configure(state="disabled")
    
    def _update_suggestions(self):
        """Update word suggestion buttons."""
        suggestions = self.recognizer.suggestions if self.recognizer else []
        for i, btn in enumerate(self.suggestion_buttons):
            if i < len(suggestions):
                if USING_CTK:
                    btn.configure(text=f"{i+1}.  {suggestions[i]}", fg_color=self.COLORS['accent_blue'])
                else:
                    btn.configure(text=f"{i+1}.  {suggestions[i]}", bg=self.COLORS['accent_blue'])
            else:
                if USING_CTK:
                    btn.configure(text=f"{i+1}.  —", fg_color=self.COLORS['bg_button'])
                else:
                    btn.configure(text=f"{i+1}.  —", bg=self.COLORS['bg_button'])
    
    def _add_space(self):
        """Add space to text."""
        if self.recognizer:
            self.recognizer.add_space()
            self._update_text_display()
    
    def _backspace(self):
        """Delete last character."""
        if self.recognizer:
            self.recognizer.backspace()
            self._update_text_display()
    
    def _clear_text(self):
        """Clear all text."""
        if self.recognizer:
            self.recognizer.clear_text()
            self._update_text_display()
    
    def _speak_text(self):
        """Speak the current text."""
        if self.recognizer:
            self.recognizer.speak_text()
            self.status_label.configure(text="Speaking...")
            self.root.after(2000, lambda: self.status_label.configure(text="Ready"))
    
    def _copy_text(self):
        """Copy text to clipboard."""
        if self.recognizer and self.recognizer.text_buffer:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.recognizer.text_buffer)
            self.status_label.configure(text="Text copied to clipboard!")
            self.root.after(2000, lambda: self.status_label.configure(text="Ready"))
    
    def _select_suggestion(self, index):
        """Select a word suggestion."""
        if self.recognizer and self.recognizer.select_suggestion(index):
            self._update_text_display()
    
    def _show_settings(self):
        """Show accessible settings dialog."""
        if USING_CTK:
            settings_window = ctk.CTkToplevel(self.root)
            settings_window.title("⚙ Settings")
            settings_window.geometry("500x500")
            settings_window.transient(self.root)
            settings_window.grab_set()  # Modal
            settings_window.configure(fg_color=self.COLORS['bg_main'])
            
            # Header
            ctk.CTkLabel(settings_window, text="⚙  SETTINGS", 
                        font=("Segoe UI", 28, "bold"),
                        text_color=self.COLORS['text_white']).pack(pady=25)
            
            # Main content frame
            content = ctk.CTkFrame(settings_window, fg_color=self.COLORS['bg_panel'], corner_radius=15)
            content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            # === Recognition Settings ===
            settings_frame = ctk.CTkFrame(content, fg_color="transparent")
            settings_frame.pack(fill="x", padx=25, pady=20)
            
            ctk.CTkLabel(settings_frame, text="🎯  RECOGNITION SETTINGS", 
                        font=("Segoe UI", 20, "bold"),
                        text_color=self.COLORS['text_white']).pack(anchor="w", pady=(0, 15))
            
            # Stability threshold
            ctk.CTkLabel(settings_frame, text="Sign Hold Time:", 
                        font=("Segoe UI", 16),
                        text_color=self.COLORS['text_white']).pack(anchor="w")
            stability_slider = ctk.CTkSlider(settings_frame, from_=5, to=30, number_of_steps=25,
                                             height=25, progress_color=self.COLORS['accent_green'])
            stability_slider.set(self.recognizer.stable_threshold if self.recognizer else 15)
            stability_slider.pack(fill="x", pady=(5, 15))
            
            # Letter cooldown
            ctk.CTkLabel(settings_frame, text="Letter Cooldown:", 
                        font=("Segoe UI", 16),
                        text_color=self.COLORS['text_white']).pack(anchor="w")
            cooldown_slider = ctk.CTkSlider(settings_frame, from_=0.5, to=3.0, number_of_steps=25,
                                            height=25, progress_color=self.COLORS['accent_green'])
            cooldown_slider.set(self.recognizer.letter_cooldown if self.recognizer else 1.0)
            cooldown_slider.pack(fill="x", pady=(5, 15))
            
            # TTS Speed
            ctk.CTkLabel(settings_frame, text="Speech Speed:", 
                        font=("Segoe UI", 16),
                        text_color=self.COLORS['text_white']).pack(anchor="w")
            rate_slider = ctk.CTkSlider(settings_frame, from_=100, to=200, number_of_steps=20,
                                        height=25, progress_color=self.COLORS['accent_green'])
            rate_slider.set(self.recognizer.tts.speech_rate if self.recognizer else 150)
            rate_slider.pack(fill="x", pady=(5, 15))
            
            def apply_settings():
                if self.recognizer:
                    self.recognizer.stable_threshold = int(stability_slider.get())
                    self.recognizer.letter_cooldown = cooldown_slider.get()
                    self.recognizer.tts.speech_rate = int(rate_slider.get())
                self.status_label.configure(text="✅ Settings saved!")
                settings_window.destroy()
            
            # Apply button - Large
            ctk.CTkButton(content, text="✅  SAVE & CLOSE", 
                         font=("Segoe UI", 20, "bold"), height=60,
                         fg_color=self.COLORS['accent_green'],
                         hover_color="#3fb950",
                         command=apply_settings).pack(fill="x", padx=25, pady=20)
    
    def _show_help(self):
        """Show accessible help dialog."""
        if USING_CTK:
            help_window = ctk.CTkToplevel(self.root)
            help_window.title("❓ Help")
            help_window.geometry("600x750")
            help_window.transient(self.root)
            help_window.grab_set()  # Modal
            help_window.configure(fg_color=self.COLORS['bg_main'])
            
            # Header
            ctk.CTkLabel(help_window, text="❓  HOW TO USE", 
                        font=("Segoe UI", 28, "bold"),
                        text_color=self.COLORS['text_white']).pack(pady=25)
            
            # Scrollable content
            scroll_frame = ctk.CTkScrollableFrame(help_window, fg_color=self.COLORS['bg_panel'], corner_radius=15)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            # Quick Start
            ctk.CTkLabel(scroll_frame, text="🚀  QUICK START", 
                        font=("Segoe UI", 22, "bold"),
                        text_color=self.COLORS['accent_green']).pack(anchor="w", padx=20, pady=(20, 10))
            
            steps = [
                "1️⃣  Press the green START button",
                "2️⃣  Show your hand to the camera",
                "3️⃣  Make ASL sign letters",
                "4️⃣  Hold steady until recognized",
                "5️⃣  Letter appears in your text!"
            ]
            for step in steps:
                ctk.CTkLabel(scroll_frame, text=step, 
                            font=("Segoe UI", 18),
                            text_color=self.COLORS['text_white']).pack(anchor="w", padx=25, pady=3)
            
            # Supported Signs
            ctk.CTkLabel(scroll_frame, text="✋  SUPPORTED SIGNS", 
                        font=("Segoe UI", 22, "bold"),
                        text_color=self.COLORS['accent_blue']).pack(anchor="w", padx=20, pady=(25, 10))
            
            signs_text = """Letters:  A  B  C  D  E  F  G  H  I  K  L  O  R  U  V  W  Y

Special:  Z (draw in air with index finger!)
                     
Numbers:  1  5

Gestures:  👍 Thumbs Up"""
            
            ctk.CTkLabel(scroll_frame, text=signs_text, 
                        font=("Consolas", 16),
                        text_color=self.COLORS['text_white'],
                        justify="left").pack(anchor="w", padx=25, pady=5)
            
            # Tips
            ctk.CTkLabel(scroll_frame, text="💡  TIPS FOR BETTER RECOGNITION", 
                        font=("Segoe UI", 22, "bold"),
                        text_color=self.COLORS['accent_yellow']).pack(anchor="w", padx=20, pady=(25, 10))
            
            tips = [
                "✓  Use good lighting",
                "✓  Keep hand clearly visible",
                "✓  Hold signs steady",
                "✓  Use plain background",
                "✓  Face palm toward camera"
            ]
            for tip in tips:
                ctk.CTkLabel(scroll_frame, text=tip, 
                            font=("Segoe UI", 18),
                            text_color=self.COLORS['text_white']).pack(anchor="w", padx=25, pady=3)
            
            # Keyboard Shortcuts
            ctk.CTkLabel(scroll_frame, text="⌨  KEYBOARD SHORTCUTS", 
                        font=("Segoe UI", 22, "bold"),
                        text_color=self.COLORS['accent_purple']).pack(anchor="w", padx=20, pady=(25, 10))
            
            shortcuts = [
                "SPACE     →  Add space",
                "BACKSPACE →  Delete character",
                "ENTER     →  Speak text aloud",
                "R         →  Clear all text",
                "1-5       →  Pick word suggestion",
                "ESC       →  Exit application"
            ]
            for shortcut in shortcuts:
                ctk.CTkLabel(scroll_frame, text=shortcut, 
                            font=("Consolas", 16),
                            text_color=self.COLORS['text_white']).pack(anchor="w", padx=25, pady=3)
            
            # Close button - Large
            ctk.CTkButton(help_window, text="✅  GOT IT!", 
                         font=("Segoe UI", 20, "bold"), height=60,
                         fg_color=self.COLORS['accent_green'],
                         hover_color="#3fb950",
                         command=help_window.destroy).pack(fill="x", padx=20, pady=15)
    
    def _on_closing(self):
        """Handle window closing."""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.recognizer:
            self.recognizer.release()
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    print("=" * 50)
    print("Hand Sign Language Recognition System v2.0")
    print("=" * 50)
    
    app = SignLanguageApp()
    app.run()


if __name__ == "__main__":
    main()
