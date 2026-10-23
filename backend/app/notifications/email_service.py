import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models import NotificationLog

class EmailService:
    def __init__(self, db: Session):
        self.db = db

    def is_configured(self) -> bool:
        if settings.APP_ENV == "testing":
            return False
        if not settings.SMTP_HOST or not settings.SMTP_FROM:
            return False
        if settings.SMTP_PASSWORD in (None, "", "your-app-password"):
            return False
        return True

    async def send_alert(
        self,
        event_type: str,
        subject: str,
        body: str,
        recipient: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Sends an email alert with duplicate notification suppression and persistent audit logging.
        """
        to_email = recipient or settings.NOTIFICATION_EMAIL_TO
        if not to_email:
            return False, "Recipient email address is not configured."

        # 1. Duplicate Notification Suppression (within 30 minutes for same event & subject)
        thirty_mins_ago = datetime.utcnow() - timedelta(minutes=30)
        recent_log = self.db.query(NotificationLog).filter(
            NotificationLog.recipient == to_email,
            NotificationLog.event_type == event_type,
            NotificationLog.subject == subject,
            NotificationLog.status == "sent",
            NotificationLog.sent_at >= thirty_mins_ago
        ).first()

        if recent_log:
            # Suppress duplicate alert
            log = NotificationLog(
                recipient=to_email,
                subject=subject,
                event_type=event_type,
                status="suppressed",
                error_message="Suppressed duplicate notification within suppression window."
            )
            self.db.add(log)
            self.db.commit()
            return True, "Notification suppressed (duplicate alert prevention)."

        # 2. Check if SMTP is configured with real credentials
        if not self.is_configured():
            # Simulated / Logged mode for dev & ₹0 free tier when SMTP credentials are not yet entered
            log = NotificationLog(
                recipient=to_email,
                subject=subject,
                event_type=event_type,
                status="sent",
                error_message="Simulated dispatch: SMTP not configured or using placeholder credentials. Notification recorded in database."
            )
            self.db.add(log)
            self.db.commit()
            return True, "Notification logged in database (SMTP not configured in local environment)."

        # 3. SMTP Dispatch
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to_email
            msg["Subject"] = subject

            # Plain text body
            footer = "\n\n---\nVulnAI X Autonomous Security Research Platform\nNote: This is an automated notification. Never reply with secrets or credentials."
            msg.attach(MIMEText(body + footer, "plain"))

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
            server.quit()

            log = NotificationLog(
                recipient=to_email,
                subject=subject,
                event_type=event_type,
                status="sent"
            )
            self.db.add(log)
            self.db.commit()
            return True, f"Email successfully dispatched to {to_email}."
        except Exception as e:
            log = NotificationLog(
                recipient=to_email,
                subject=subject,
                event_type=event_type,
                status="failed",
                error_message=str(e)
            )
            self.db.add(log)
            self.db.commit()
            return False, f"SMTP dispatch failed: {str(e)}"
