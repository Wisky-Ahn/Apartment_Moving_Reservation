"""
에러 알림 시스템
중요한 에러 발생 시 관리자에게 알림을 보내는 시스템
"""
import asyncio
import smtplib
import json
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class NotificationLevel(str, Enum):
    """알림 레벨 정의"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """알림 채널 정의"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"  # 향후 구현


class ErrorAlert:
    """에러 알림 데이터 구조"""
    
    def __init__(
        self,
        title: str,
        message: str,
        level: NotificationLevel,
        error_code: str = None,
        request_id: str = None,
        user_info: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        timestamp: datetime = None
    ):
        self.title = title
        self.message = message
        self.level = level
        self.error_code = error_code
        self.request_id = request_id
        self.user_info = user_info or {}
        self.context = context or {}
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        return {
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "error_code": self.error_code,
            "request_id": self.request_id,
            "user_info": self.user_info,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


class NotificationRateLimiter:
    """
    알림 발송 빈도 제한
    같은 에러가 반복적으로 발생할 때 스팸 방지
    """
    
    def __init__(self):
        self._alerts: Dict[str, datetime] = {}
        self._cooldown_minutes = {
            NotificationLevel.CRITICAL: 5,   # 5분
            NotificationLevel.HIGH: 15,      # 15분
            NotificationLevel.MEDIUM: 60,    # 1시간
            NotificationLevel.LOW: 240       # 4시간
        }
    
    def should_send(self, alert: ErrorAlert) -> bool:
        """알림을 보낼지 결정"""
        # 알림 키 생성 (에러 코드 + 레벨)
        alert_key = f"{alert.error_code}_{alert.level.value}"
        
        # 마지막 알림 시간 확인
        last_sent = self._alerts.get(alert_key)
        if not last_sent:
            self._alerts[alert_key] = alert.timestamp
            return True
        
        # 쿨다운 시간 확인
        cooldown_minutes = self._cooldown_minutes.get(alert.level, 60)
        time_diff = alert.timestamp - last_sent
        
        if time_diff.total_seconds() >= (cooldown_minutes * 60):
            self._alerts[alert_key] = alert.timestamp
            return True
        
        return False
    
    def reset_alerts(self):
        """알림 기록 초기화 (테스트용)"""
        self._alerts.clear()


class BaseNotificationHandler:
    """알림 핸들러 기본 클래스"""
    
    async def send(self, alert: ErrorAlert) -> bool:
        """알림 발송 (서브클래스에서 구현)"""
        raise NotImplementedError
    
    def format_message(self, alert: ErrorAlert) -> str:
        """알림 메시지 포맷팅"""
        return f"""
🚨 **{alert.title}** [{alert.level.value.upper()}]

**Message:** {alert.message}
**Time:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Error Code:** {alert.error_code or 'N/A'}
**Request ID:** {alert.request_id or 'N/A'}

**User Info:**
{json.dumps(alert.user_info, indent=2) if alert.user_info else 'None'}

**Context:**
{json.dumps(alert.context, indent=2) if alert.context else 'None'}
        """.strip()


class EmailNotificationHandler(BaseNotificationHandler):
    """이메일 알림 핸들러"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    async def send(self, alert: ErrorAlert) -> bool:
        """이메일 알림 발송"""
        try:
            # 이메일 메시지 구성
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[FNM Alert] {alert.title} [{alert.level.value.upper()}]"
            
            # HTML 버전과 텍스트 버전 생성
            html_body = self._create_html_message(alert)
            text_body = self.format_message(alert)
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # SMTP 서버를 통해 이메일 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent successfully: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _create_html_message(self, alert: ErrorAlert) -> str:
        """HTML 형태의 이메일 메시지 생성"""
        level_colors = {
            NotificationLevel.CRITICAL: "#dc3545",
            NotificationLevel.HIGH: "#fd7e14", 
            NotificationLevel.MEDIUM: "#ffc107",
            NotificationLevel.LOW: "#17a2b8"
        }
        
        color = level_colors.get(alert.level, "#6c757d")
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                <h2 style="margin: 0;">🚨 {alert.title}</h2>
                <span style="background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 3px; font-size: 12px;">
                    {alert.level.value.upper()}
                </span>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px;">
                <h3>Message</h3>
                <p style="background-color: white; padding: 15px; border-left: 4px solid {color};">
                    {alert.message}
                </p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Time:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Error Code:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{alert.error_code or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Request ID:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{alert.request_id or 'N/A'}</td>
                    </tr>
                </table>
                
                {self._format_json_section("User Info", alert.user_info)}
                {self._format_json_section("Context", alert.context)}
            </div>
        </body>
        </html>
        """
    
    def _format_json_section(self, title: str, data: Dict[str, Any]) -> str:
        """JSON 데이터를 HTML 섹션으로 포맷팅"""
        if not data:
            return ""
        
        return f"""
        <div style="margin-top: 20px;">
            <h4>{title}</h4>
            <pre style="background-color: white; padding: 15px; border: 1px solid #dee2e6; border-radius: 3px; overflow-x: auto;">
{json.dumps(data, indent=2)}
            </pre>
        </div>
        """


class SlackNotificationHandler(BaseNotificationHandler):
    """Slack 알림 핸들러"""
    
    def __init__(self, webhook_url: str, channel: str = None):
        self.webhook_url = webhook_url
        self.channel = channel
    
    async def send(self, alert: ErrorAlert) -> bool:
        """Slack 알림 발송"""
        try:
            # Slack 메시지 페이로드 구성
            payload = {
                "text": f"🚨 {alert.title}",
                "attachments": [
                    {
                        "color": self._get_color(alert.level),
                        "fields": [
                            {
                                "title": "Level",
                                "value": alert.level.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Error Code",
                                "value": alert.error_code or "N/A",
                                "short": True
                            },
                            {
                                "title": "Request ID", 
                                "value": alert.request_id or "N/A",
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            }
                        ],
                        "footer": "FNM Error Alert System",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            if self.channel:
                payload["channel"] = self.channel
            
            # 추가 정보가 있으면 포함
            if alert.user_info or alert.context:
                additional_info = []
                if alert.user_info:
                    additional_info.append(f"**User Info:**\n```{json.dumps(alert.user_info, indent=2)}```")
                if alert.context:
                    additional_info.append(f"**Context:**\n```{json.dumps(alert.context, indent=2)}```")
                
                payload["attachments"][0]["fields"].append({
                    "title": "Additional Info",
                    "value": "\n\n".join(additional_info),
                    "short": False
                })
            
            # Slack Webhook으로 POST 요청
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent successfully: {alert.title}")
                        return True
                    else:
                        logger.error(f"Slack webhook returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _get_color(self, level: NotificationLevel) -> str:
        """알림 레벨에 따른 색상 반환"""
        colors = {
            NotificationLevel.CRITICAL: "danger",
            NotificationLevel.HIGH: "warning",
            NotificationLevel.MEDIUM: "#ffc107",
            NotificationLevel.LOW: "good"
        }
        return colors.get(level, "#6c757d")


class WebhookNotificationHandler(BaseNotificationHandler):
    """웹훅 알림 핸들러"""
    
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
    
    async def send(self, alert: ErrorAlert) -> bool:
        """웹훅 알림 발송"""
        try:
            payload = alert.to_dict()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if 200 <= response.status < 300:
                        logger.info(f"Webhook alert sent successfully: {alert.title}")
                        return True
                    else:
                        logger.error(f"Webhook returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


class NotificationManager:
    """
    알림 관리자
    여러 채널을 통해 알림을 발송하고 빈도를 제한
    """
    
    def __init__(self):
        self.handlers: Dict[NotificationChannel, BaseNotificationHandler] = {}
        self.rate_limiter = NotificationRateLimiter()
        self.enabled_levels: List[NotificationLevel] = [
            NotificationLevel.HIGH,
            NotificationLevel.CRITICAL
        ]
    
    def add_handler(self, channel: NotificationChannel, handler: BaseNotificationHandler):
        """알림 핸들러 추가"""
        self.handlers[channel] = handler
        logger.info(f"Added {channel.value} notification handler")
    
    def set_enabled_levels(self, levels: List[NotificationLevel]):
        """활성화할 알림 레벨 설정"""
        self.enabled_levels = levels
    
    async def send_alert(self, alert: ErrorAlert, channels: List[NotificationChannel] = None):
        """알림 발송"""
        # 레벨 확인
        if alert.level not in self.enabled_levels:
            return
        
        # 빈도 제한 확인
        if not self.rate_limiter.should_send(alert):
            logger.debug(f"Alert rate limited: {alert.title}")
            return
        
        # 발송할 채널 결정
        target_channels = channels or list(self.handlers.keys())
        
        # 모든 채널에 비동기 발송
        tasks = []
        for channel in target_channels:
            if channel in self.handlers:
                handler = self.handlers[channel]
                tasks.append(self._send_to_handler(handler, alert, channel))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
            logger.info(f"Alert sent to {success_count}/{len(tasks)} channels: {alert.title}")
    
    async def _send_to_handler(
        self, 
        handler: BaseNotificationHandler, 
        alert: ErrorAlert, 
        channel: NotificationChannel
    ) -> bool:
        """개별 핸들러로 알림 발송"""
        try:
            return await handler.send(alert)
        except Exception as e:
            logger.error(f"Failed to send alert via {channel.value}: {e}")
            return False


# 전역 알림 관리자 인스턴스
notification_manager = NotificationManager()


def setup_notifications():
    """
    알림 시스템 설정
    환경 변수를 기반으로 알림 핸들러들을 설정
    """
    # 이메일 알림 설정 (환경변수가 있는 경우)
    if all([
        hasattr(settings, 'SMTP_SERVER'),
        hasattr(settings, 'SMTP_PORT'),
        hasattr(settings, 'SMTP_USERNAME'),
        hasattr(settings, 'SMTP_PASSWORD'),
        hasattr(settings, 'ALERT_EMAIL_FROM'),
        hasattr(settings, 'ALERT_EMAIL_TO')
    ]):
        email_handler = EmailNotificationHandler(
            smtp_server=settings.SMTP_SERVER,
            smtp_port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            from_email=settings.ALERT_EMAIL_FROM,
            to_emails=settings.ALERT_EMAIL_TO.split(',') if isinstance(settings.ALERT_EMAIL_TO, str) else settings.ALERT_EMAIL_TO
        )
        notification_manager.add_handler(NotificationChannel.EMAIL, email_handler)
    
    # Slack 알림 설정 (환경변수가 있는 경우)
    if hasattr(settings, 'SLACK_WEBHOOK_URL') and settings.SLACK_WEBHOOK_URL:
        slack_handler = SlackNotificationHandler(
            webhook_url=settings.SLACK_WEBHOOK_URL,
            channel=getattr(settings, 'SLACK_CHANNEL', None)
        )
        notification_manager.add_handler(NotificationChannel.SLACK, slack_handler)
    
    # 웹훅 알림 설정 (환경변수가 있는 경우)
    if hasattr(settings, 'ALERT_WEBHOOK_URL') and settings.ALERT_WEBHOOK_URL:
        webhook_handler = WebhookNotificationHandler(
            webhook_url=settings.ALERT_WEBHOOK_URL,
            headers=getattr(settings, 'ALERT_WEBHOOK_HEADERS', {})
        )
        notification_manager.add_handler(NotificationChannel.WEBHOOK, webhook_handler)
    
    # 알림 레벨 설정
    enabled_levels_str = getattr(settings, 'ALERT_LEVELS', 'HIGH,CRITICAL')
    enabled_levels = [
        NotificationLevel(level.strip().lower()) 
        for level in enabled_levels_str.split(',')
        if level.strip()
    ]
    notification_manager.set_enabled_levels(enabled_levels)
    
    logger.info(f"Notification system setup complete. Handlers: {list(notification_manager.handlers.keys())}")


# 편의 함수들
async def send_error_alert(
    title: str,
    message: str,
    level: NotificationLevel = NotificationLevel.HIGH,
    error_code: str = None,
    request_id: str = None,
    user_info: Dict[str, Any] = None,
    context: Dict[str, Any] = None
):
    """에러 알림 발송 편의 함수"""
    alert = ErrorAlert(
        title=title,
        message=message,
        level=level,
        error_code=error_code,
        request_id=request_id,
        user_info=user_info,
        context=context
    )
    await notification_manager.send_alert(alert)


async def send_critical_alert(title: str, message: str, **kwargs):
    """치명적 에러 알림 발송"""
    await send_error_alert(title, message, NotificationLevel.CRITICAL, **kwargs)


async def send_security_alert(title: str, message: str, **kwargs):
    """보안 관련 알림 발송"""
    await send_error_alert(title, message, NotificationLevel.HIGH, **kwargs) 