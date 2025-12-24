from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# 기본 Alert 스키마
class AlertBase(BaseModel):
    alert_name: str
    instance: Optional[str] = None
    severity: Optional[str] = "warning"
    status: Optional[str] = "firing"
    description: Optional[str] = None

class AlertCreate(AlertBase):
    fingerprint: Optional[str] = None
    starts_at: Optional[datetime] = None

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None

class AlertResponse(AlertBase):
    id: int
    fingerprint: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Prometheus Alertmanager Webhook 스키마
class AlertmanagerLabel(BaseModel):
    alertname: str
    instance: Optional[str] = None
    severity: Optional[str] = None
    job: Optional[str] = None

    class Config:
        extra = "allow"

class AlertmanagerAnnotation(BaseModel):
    description: Optional[str] = None
    summary: Optional[str] = None

    class Config:
        extra = "allow"

class AlertmanagerAlert(BaseModel):
    status: str
    labels: Dict[str, Any]
    annotations: Optional[Dict[str, Any]] = {}
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    fingerprint: Optional[str] = None

class AlertmanagerWebhook(BaseModel):
    version: Optional[str] = None
    groupKey: Optional[str] = None
    status: str
    receiver: Optional[str] = None
    alerts: List[AlertmanagerAlert]
