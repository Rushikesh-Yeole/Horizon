import os
import logging
import httpx

log = logging.getLogger("mailer")

ZEPTOMAIL_TOKEN = os.getenv("ZEPTOMAIL_TOKEN", "")
ZEPTOMAIL_FROM = os.getenv("ZEPTOMAIL_FROM", "noreply@horizon.app")
ZEPTOMAIL_FROM_NAME = os.getenv("ZEPTOMAIL_FROM_NAME", "Horizon")
ZEPTOMAIL_URL = os.getenv(
    "ZEPTOMAIL_URL",
    "https://api.zeptomail.in/v1.1/email" if ZEPTOMAIL_FROM.endswith(".in") else "https://api.zeptomail.in/v1.1/email"
)


async def _send(to_email: str, to_name: str, subject: str, html: str) -> None:
    token = ZEPTOMAIL_TOKEN
    from_addr = ZEPTOMAIL_FROM
    from_name = ZEPTOMAIL_FROM_NAME
    api_url = ZEPTOMAIL_URL

    if not token:
        log.warning("ZEPTOMAIL_TOKEN not set, skipping email send.")
        return
    payload = {
        "from": {"address": from_addr, "name": from_name},
        "to": [{"email_address": {"address": to_email, "name": to_name}}],
        "subject": subject,
        "htmlbody": html,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                api_url,
                headers={"Authorization": f"Zoho-enczapikey {token}", "Content-Type": "application/json"},
                json=payload,
            )
            if resp.status_code >= 400:
                log.warning(f"ZeptoMail {resp.status_code} for {to_email}: {resp.text[:200]}")
            else:
                log.info(f"ZeptoMail sent successfully to {to_email} ({resp.status_code})")
    except Exception as e:
        log.warning(f"ZeptoMail send failed for {to_email}: {e}")


async def send_welcome(email: str, name: str) -> None:
    html = f"""
    <h2>Welcome to Horizon, {name}!</h2>
    <p>Your account is ready. Start discovering your career trajectory at
    <a href='https://horizon.app'>horizon.app</a>.</p>
    """
    await _send(email, name, "Welcome to Horizon", html)


async def send_otp(email: str, otp: str) -> None:
    html = f"""
    <h2>Your Horizon Verification Code</h2>
    <p>Your one-time password (OTP) is: <strong>{otp}</strong></p>
    <p>This code will expire in 5 minutes.</p>
    """
    await _send(email, email, "Your Horizon Verification Code", html)


async def send_login_alert(email: str) -> None:
    import datetime
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html = f"""
    <p>A new login to your Horizon account was detected at <strong>{ts}</strong>.</p>
    <p>If this was not you, please reset your password immediately.</p>
    """
    await _send(email, email, "New login to your Horizon account", html)
