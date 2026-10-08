"""FastAPI Application factory and server configuration."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from autodiag.api.routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI AutoDiag-AI application."""
    app = FastAPI(
        title="AutoDiag-AI Platform",
        description="Automotive UDS Diagnostic Specification Analysis & Automated Test Generation Platform (ISO 14229)",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for frontend integrations
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static docs directory for benchmark graphs
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
    if os.path.exists(docs_dir):
        app.mount("/docs-assets", StaticFiles(directory=docs_dir), name="docs-assets")

    # Include Diagnostic Routes
    app.include_router(router)

    # Root endpoint serving built-in Web Dashboard
    @app.get("/", response_class=HTMLResponse)
    def index():
        dashboard_path = os.path.join(os.path.dirname(__file__), "..", "ui", "web_dashboard.html")
        if os.path.exists(dashboard_path):
            with open(dashboard_path, "r", encoding="utf-8") as f:
                return f.read()
        return """
        <html>
            <head><title>AutoDiag-AI Platform</title></head>
            <body style="font-family: sans-serif; padding: 40px; background: #0f172a; color: #f8fafc;">
                <h1>🚗 AutoDiag-AI Platform Running</h1>
                <p>Automotive ISO 14229 UDS Diagnostic & Test Generation Engine.</p>
                <p><a style="color: #38bdf8;" href="/docs">Open Interactive Swagger API Documentation (/docs)</a></p>
            </body>
        </html>
        """

    return app


app = create_app()
