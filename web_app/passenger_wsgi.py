import sys, os

# Add the project directory to the sys.path
# 'repositories/hand_sign_language' should be changed to the actual path where you upload the files in cPanel
# strictly speaking, Passenger usually handles the path, but explicitly adding the current dir helps
sys.path.append(os.getcwd())

from app import app as application
