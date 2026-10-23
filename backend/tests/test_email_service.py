import pytest
import asyncio
from app.notifications.email_service import EmailService
from app.models import NotificationLog

@pytest.mark.asyncio
async def test_email_alert_simulation_and_duplicate_suppression(db):
    service = EmailService(db)

    # 1. Send first alert
    success, msg = await service.send_alert(
        event_type="finding_high_confidence",
        subject="[Test] High Severity Vuln",
        body="Details on vulnerability...",
        recipient="researcher@example.com"
    )
    assert success is True
    assert "Notification logged in database" in msg

    # Verify record in DB
    log1 = db.query(NotificationLog).filter(NotificationLog.subject == "[Test] High Severity Vuln").first()
    assert log1 is not None
    assert log1.status == "sent"

    # 2. Immediately send duplicate alert -> Should be suppressed
    dup_success, dup_msg = await service.send_alert(
        event_type="finding_high_confidence",
        subject="[Test] High Severity Vuln",
        body="Details on vulnerability...",
        recipient="researcher@example.com"
    )
    assert dup_success is True
    assert "duplicate alert prevention" in dup_msg.lower()

    # Verify suppressed record in DB
    suppressed_log = db.query(NotificationLog).filter(NotificationLog.status == "suppressed").first()
    assert suppressed_log is not None
