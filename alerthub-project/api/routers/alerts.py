from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from api.database import get_db
from api.redis_client import get_redis
from api.models.alert import Alert
from api.schemas.alert import (
    AlertCreate, AlertUpdate, AlertResponse, AlertmanagerWebhook
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/", response_model=AlertResponse)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    db_alert = Alert(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    
    # Redis 큐에 알림 발행
    try:
        redis = get_redis()
        redis.lpush("alerts:notification", json.dumps({
            "id": db_alert.id,
            "alert_name": db_alert.alert_name,
            "severity": db_alert.severity,
            "status": db_alert.status,
            "instance": db_alert.instance,
            "description": db_alert.description
        }))
    except Exception:
        pass  # Redis 실패해도 Alert은 저장됨
    
    return db_alert

@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    for key, value in alert_update.model_dump(exclude_unset=True).items():
        setattr(alert, key, value)
    
    db.commit()
    db.refresh(alert)
    return alert

@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted"}

# Prometheus Alertmanager Webhook 엔드포인트
@router.post("/webhook/prometheus")
def alertmanager_webhook(
    webhook: AlertmanagerWebhook,
    db: Session = Depends(get_db)
):
    processed = []
    
    for alert_data in webhook.alerts:
        labels = alert_data.labels
        annotations = alert_data.annotations or {}
        
        # fingerprint로 기존 Alert 확인
        existing = None
        if alert_data.fingerprint:
            existing = db.query(Alert).filter(
                Alert.fingerprint == alert_data.fingerprint
            ).first()
        
        if existing:
            # 기존 Alert 업데이트
            existing.status = alert_data.status
            if alert_data.status == "resolved":
                existing.ends_at = datetime.utcnow()
            db.commit()
            processed.append({"fingerprint": alert_data.fingerprint, "action": "updated"})
        else:
            # 새 Alert 생성
            new_alert = Alert(
                alert_name=labels.get("alertname", "Unknown"),
                instance=labels.get("instance"),
                severity=labels.get("severity", "warning"),
                status=alert_data.status,
                description=annotations.get("description") or annotations.get("summary"),
                fingerprint=alert_data.fingerprint,
                starts_at=datetime.utcnow()
            )
            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)
            
            # Redis 큐에 알림 발행
            try:
                redis = get_redis()
                redis.lpush("alerts:notification", json.dumps({
                    "id": new_alert.id,
                    "alert_name": new_alert.alert_name,
                    "severity": new_alert.severity,
                    "status": new_alert.status,
                    "instance": new_alert.instance,
                    "description": new_alert.description
                }))
            except Exception:
                pass
            
            processed.append({"fingerprint": alert_data.fingerprint, "action": "created"})
    
    return {"status": "ok", "processed": processed}
