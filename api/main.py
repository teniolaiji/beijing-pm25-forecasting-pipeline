"""
Beijing PM2.5 API: CRUD and time-series queries over MySQL and MongoDB.

Run from the repo root:
    uvicorn api.main:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

app = FastAPI(
    title="Beijing PM2.5 API",
    description="Hourly PM2.5 and weather records, served from MySQL (/sql) and MongoDB (/mongo).",
    version="1.0.0",
)



@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "docs": "/docs", "databases": ["/sql", "/mongo"]}
