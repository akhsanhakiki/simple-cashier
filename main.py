from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from database import create_db_and_tables
from routers import products, transactions

app = FastAPI(
    title="Simple Cashier API",
    description="A simple cashier API for managing products and transactions",
    version="1.0.0"
)

# Add GZip compression middleware for faster response times
# Compresses responses larger than 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Include routers
app.include_router(products.router)
app.include_router(transactions.router)

@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Simple Cashier API",
        "version": "1.0.0",
        "docs": "/docs"
    }
