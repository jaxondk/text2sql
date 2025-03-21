import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv
import asyncio
import logging

from app.api.router import api_router
from app.web.router import web_router
from app.db.manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "Text2SQL"),
    description="Convert natural language to SQL",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(web_router)


# Initialize default database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Initializing application...")

    try:
        # Initialize default database connection
        db_manager = DatabaseManager()
        await db_manager.initialize_default_database()
        logger.info("Application initialized successfully")
    except Exception as e:
        # Log the error but let the application start anyway
        logger.error(f"Error during application initialization: {str(e)}")
        logger.info(
            "Application will continue to start but some features may be limited"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_ENV") == "development",
    )
