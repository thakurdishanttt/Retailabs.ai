from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uvicorn
import os

from src.api.router import router
from src.config.settings import PROJECT_NAME, API_PREFIX
from src.utils.logging_config import setup_logging

# Setup logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP and request details
    client_host = request.client.host if request.client else "unknown"
    request_path = request.url.path
    request_method = request.method
    
    logger.info(f"Request: {request_method} {request_path} from {client_host}")
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response details
        logger.info(
            f"Response: {request_method} {request_path} - Status: {response.status_code} - "
            f"Processed in {process_time:.4f}s"
        )
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {request_method} {request_path} - Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Include API router
app.include_router(router, prefix=API_PREFIX)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": PROJECT_NAME,
        "message": "Welcome to the Retailabs AI Agents API",
        "docs": f"{API_PREFIX}/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting {PROJECT_NAME} on port {port}...")
    
    # Run the server with hot reload for development
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )
