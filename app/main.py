from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, orders, inventory, operations, device, audit, health, web
from app.repositories.base import init_db
from app.domain.models import WarehouseSecurityException
import uuid

app = FastAPI(
    title="Autonomous Warehouse Secure Management System",
    description="24CYS401 Secure Software Engineering End Semester Lab Exam Solution",
    version="1.0.0"
)

# Standard Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval';"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Standard Safe Error Envelope
@app.exception_handler(WarehouseSecurityException)
async def warehouse_exception_handler(request: Request, exc: WarehouseSecurityException):
    req_id = str(uuid.uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": req_id
            }
        }
    )

# Include API Routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(operations.router)
app.include_router(device.router)
app.include_router(audit.router)
app.include_router(health.router)
app.include_router(web.router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return RedirectResponse(url="/web/login")

@app.get("/dashboard")
def dashboard_redirect():
    return RedirectResponse(url="/web/operations")

@app.get("/operations")
def operations_redirect():
    return RedirectResponse(url="/web/operations")

@app.get("/inventory")
def inventory_redirect():
    return RedirectResponse(url="/web/inventory")

@app.get("/orders")
def orders_redirect():
    return RedirectResponse(url="/web/orders")

@app.get("/results")
def results_redirect():
    return RedirectResponse(url="/web/results")

@app.get("/audit")
def audit_redirect():
    return RedirectResponse(url="/web/audit")

