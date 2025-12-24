from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.database import get_db
from api.redis_client import get_redis

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {"status": "healthy"}

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    result = {
        "status": "ready",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # DB 연결 확인
    try:
        db.execute(text("SELECT 1"))
        result["database"] = "connected"
    except Exception as e:
        result["database"] = f"error: {str(e)}"
        result["status"] = "not ready"
    
    # Redis 연결 확인
    try:
        redis = get_redis()
        redis.ping()
        result["redis"] = "connected"
    except Exception as e:
        result["redis"] = f"error: {str(e)}"
        result["status"] = "not ready"
    
    return result
