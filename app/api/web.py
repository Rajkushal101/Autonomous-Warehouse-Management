from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

router = APIRouter(prefix="/web", tags=["Web UI"])

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Sign In"})

@router.get("/orders", response_class=HTMLResponse)
def orders_page(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request, "title": "Customer Orders"})

@router.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request):
    return templates.TemplateResponse("inventory.html", {"request": request, "title": "Inventory Management"})

@router.get("/results", response_class=HTMLResponse)
def results_page(request: Request):
    return templates.TemplateResponse("results.html", {"request": request, "title": "Fulfillment Results"})

@router.get("/operations", response_class=HTMLResponse)
def operations_page(request: Request):
    return templates.TemplateResponse("operations.html", {"request": request, "title": "Robot Fleet Operations"})

@router.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request):
    return templates.TemplateResponse("audit.html", {"request": request, "title": "Security Audit Trail"})
