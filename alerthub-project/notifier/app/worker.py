import redis
import json
import requests
import os
import time
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("notifier")

# 환경변수
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# Redis 연결
def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

# Slack 메시지 발송
def send_slack_notification(alert: dict):
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured, skipping notification")
        return False
    
    # 심각도에 따른 색상
    color_map = {
        "critical": "#dc3545",  # 빨강
        "warning": "#ffc107",   # 노랑
        "info": "#17a2b8"       # 파랑
    }
    
    color = color_map.get(alert.get("severity", "warning"), "#6c757d")
    status_emoji = "🔥" if alert.get("status") == "firing" else "✅"
    
    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"{status_emoji} [{alert.get('severity', 'warning').upper()}] {alert.get('alert_name', 'Unknown Alert')}",
                "fields": [
                    {
                        "title": "Status",
                        "value": alert.get("status", "unknown"),
                        "short": True
                    },
                    {
                        "title": "Instance",
                        "value": alert.get("instance", "N/A"),
                        "short": True
                    },
                    {
                        "title": "Description",
                        "value": alert.get("description", "No description"),
                        "short": False
                    }
                ],
                "footer": "AlertHub",
                "ts": int(time.time())
            }
        ]
    }
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Slack notification sent for alert: {alert.get('alert_name')}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False

# 콘솔 출력 (Slack 미설정 시)
def log_notification(alert: dict):
    logger.info(
        f"[ALERT] {alert.get('status', 'unknown').upper()} - "
        f"{alert.get('severity', 'unknown').upper()} - "
        f"{alert.get('alert_name', 'Unknown')}: "
        f"{alert.get('description', 'No description')}"
    )

# 메인 워커 루프
def main():
    logger.info("Notifier worker starting...")
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Slack configured: {bool(SLACK_WEBHOOK_URL)}")
    
    redis_client = None
    
    while True:
        try:
            if redis_client is None:
                redis_client = get_redis_client()
                redis_client.ping()
                logger.info("Connected to Redis")
            
            # 블로킹 팝 (10초 타임아웃)
            result = redis_client.brpop("alerts:notification", timeout=10)
            
            if result:
                _, message = result
                alert = json.loads(message)
                logger.info(f"Processing alert: {alert.get('alert_name')}")
                
                # 알림 발송
                if SLACK_WEBHOOK_URL:
                    send_slack_notification(alert)
                else:
                    log_notification(alert)
                    
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            redis_client = None
            time.sleep(5)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
