from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import engine, Base
from api.routers import health, alerts

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AlertHub API",
    description="Alert Management System for Prometheus/Alertmanager",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": "AlertHub API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
