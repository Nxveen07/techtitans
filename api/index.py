import sys
import os

# Add the backend directory to sys.path
# This handles the case where Vercel looks for the app object in the root
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app import app as handler

# Standard FastAPI app export for Vercel
app = handler
