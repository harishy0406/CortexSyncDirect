"""
FastAPI Backend for Autonomous Provider Directory Management System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import os
from orchestrator import create_workflow_graph, AgentState


app = FastAPI(
    title="Provider Directory Management API",
    description="Autonomous AI-powered provider data validation system",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workflow graph will be initialized lazily on first use
workflow_graph = None

def get_workflow_graph():
    """Lazy initialization of workflow graph"""
    global workflow_graph
    if workflow_graph is None:
        workflow_graph = create_workflow_graph()
    return workflow_graph


# ============================================================================
# Request/Response Models
# ============================================================================

class ProviderRequest(BaseModel):
    provider_id: int


class Discrepancy(BaseModel):
    field: str
    db_value: str
    scraped_value: str


class WorkflowResponse(BaseModel):
    success: bool
    provider_id: int
    status: str
    confidence_score: int
    current_db_data: Dict[str, Any]
    scraped_data: Dict[str, Any]
    discrepancies: List[Discrepancy]
    workflow_steps: List[str]
    message: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the landing page"""
    with open("landing.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/validate", response_class=HTMLResponse)
async def validate_page():
    """Serve the validation page"""
    with open("validate.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/validate", response_model=WorkflowResponse)
async def validate_provider(request: ProviderRequest):
    """
    Run the validation workflow for a provider.
    """
    if request.provider_id <= 0:
        raise HTTPException(status_code=400, detail="Provider ID must be a positive integer")
    
    try:
        # Initialize state
        initial_state: AgentState = {
            "provider_id": request.provider_id,
            "current_db_data": {},
            "scraped_data": {},
            "discrepancies": [],
            "confidence_score": 0,
            "status": "pending"
        }
        
        # Track workflow steps
        workflow_steps = []
        
        # Run the workflow with step-by-step tracking
        # Note: LangGraph doesn't have built-in step tracking, so we'll capture the final state
        graph = get_workflow_graph()
        final_state = graph.invoke(initial_state)
        
        # Determine workflow path taken
        if final_state["confidence_score"] > 80:
            workflow_steps = ["fetch_provider", "scrape_web", "quality_assurance", "update_db"]
        else:
            workflow_steps = ["fetch_provider", "scrape_web", "quality_assurance", "flag_review"]
        
        # Format discrepancies - ensure values are strings
        discrepancies = [
            Discrepancy(
                field=disc.get("field", ""),
                db_value=str(disc.get("db_value", "")),
                scraped_value=str(disc.get("scraped_value", ""))
            ) for disc in final_state.get("discrepancies", [])
        ]
        
        # Determine message
        if final_state["status"] == "verified":
            message = f"Provider {request.provider_id} has been verified and updated in the database."
        else:
            message = f"Provider {request.provider_id} has been flagged for human review due to data discrepancies."
        
        return WorkflowResponse(
            success=True,
            provider_id=final_state["provider_id"],
            status=final_state["status"],
            confidence_score=final_state["confidence_score"],
            current_db_data=final_state["current_db_data"],
            scraped_data=final_state["scraped_data"],
            discrepancies=discrepancies,
            workflow_steps=workflow_steps,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Provider Directory Management API"}


@app.get("/tab.png")
async def favicon_png():
    """Serve the favicon as PNG"""
    if os.path.exists("tab.png"):
        return FileResponse("tab.png", media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/favicon.ico")
async def favicon_ico():
    """Serve the favicon as ICO (browser default request)"""
    if os.path.exists("tab.png"):
        return FileResponse("tab.png", media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/Hero_img.png")
async def hero_image():
    """Serve the hero image"""
    if os.path.exists("Hero_img.png"):
        return FileResponse("Hero_img.png", media_type="image/png")
    raise HTTPException(status_code=404, detail="Hero image not found")


# Mount static files directory (for any other static assets)
# app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

