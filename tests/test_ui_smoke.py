import os
import pytest

def test_ui_package_imports():
    import autodiag.ui
    assert autodiag.ui is not None

def test_streamlit_app_module():
    import autodiag.ui.streamlit_app
    assert hasattr(autodiag.ui.streamlit_app, "main")

def test_web_dashboard_html_exists():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "autodiag", "ui", "web_dashboard.html")
    assert os.path.exists(dashboard_path)
    with open(dashboard_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "AutoDiag-AI" in content
    assert "CAN Bus" in content or "Diagnostic" in content
