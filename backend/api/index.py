"""
Vercel serverless function handler for Todo API.
Wraps the FastAPI app with Mangum for AWS Lambda/Vercel compatibility.
"""
import sys
from pathlib import Path

# Add parent directory to Python path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mangum import Mangum
from src.main import app

# Create a Lambda handler for the FastAPI app
# Mangum adapts ASGI applications to work with AWS Lambda
handler = Mangum(app, lifespan="off")

# For Vercel, we need to export the handler
lambda_handler = handler
