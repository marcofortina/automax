"""
Plugin for sending email utility.
"""

from email.mime.text import MIMEText
import smtplib

from automax.core.exceptions import AutomaxError


def send_email(
    smtp_server: str,
    smtp_port: int,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    username: str = None,
    password: str = None,
    logger=None,
    fail_fast=True,
    dry_run=False,
):
    """
    Send an email via SMTP.

    Args:
        smtp_server (str): SMTP server host.
        smtp_port (int): SMTP port.
        from_email (str): Sender email.
        to_email (str): Recipient email.
        subject (str): Email subject.
        body (str): Email body.
        username (str, optional): SMTP username.
        password (str, optional): SMTP password.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.
        dry_run (bool): If True, simulate sending.

    Raises:
        AutomaxError: If fail_fast is True and sending fails, with level 'FATAL'.

    """
    from automax.core.utils.common_utils import echo

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    if logger:
        echo(f"Sending email to {to_email}", logger, level="INFO")

    if dry_run:
        if logger:
            echo(f"[DRY-RUN] Email to {to_email}: {subject}", logger, level="INFO")
        return

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if username and password:
                server.login(username, password)
            server.sendmail(from_email, to_email, msg.as_string())
    except Exception as e:
        msg = f"Email sending failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")


REGISTER_UTILITIES = [("send_email", send_email)]

SCHEMA = {
    "smtp_server": {"type": str, "required": True},
    "smtp_port": {"type": int, "required": True},
    "from_email": {"type": str, "required": True},
    "to_email": {"type": str, "required": True},
    "subject": {"type": str, "required": True},
    "body": {"type": str, "required": True},
    "username": {"type": str, "default": None},
    "password": {"type": str, "default": None},
    "fail_fast": {"type": bool, "default": True},
    "dry_run": {"type": bool, "default": False},
}
