"""
Plugin for sending emails.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class SendEmailPlugin(BasePlugin):
    """
    Send emails via SMTP.
    """

    METADATA = PluginMetadata(
        name="send_email",
        version="2.0.0",
        description="Send emails via SMTP",
        author="Automax Team",
        category="communication",
        tags=["email", "smtp", "mail"],
        required_config=[
            "smtp_server",
            "port",
            "username",
            "password",
            "to",
            "subject",
            "body",
        ],
        optional_config=["from_addr", "cc", "bcc", "is_html"],
    )

    SCHEMA = {
        "smtp_server": {"type": str, "required": True},
        "port": {"type": int, "required": True},
        "username": {"type": str, "required": True},
        "password": {"type": str, "required": True},
        "to": {"type": (list, str), "required": True},
        "subject": {"type": str, "required": True},
        "body": {"type": str, "required": True},
        "from_addr": {"type": str, "required": False},
        "cc": {"type": str, "required": False},
        "bcc": {"type": str, "required": False},
        "is_html": {"type": bool, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Send an email.

        Returns:
            Dictionary containing the send status.

        Raises:
            PluginExecutionError: If the email cannot be sent.

        """
        smtp_server = self.config["smtp_server"]
        port = self.config["port"]
        username = self.config["username"]
        password = self.config["password"]
        to_addrs = self.config["to"]
        subject = self.config["subject"]
        body = self.config["body"]
        from_addr = self.config.get("from_addr", username)
        cc = self.config.get("cc", [])
        bcc = self.config.get("bcc", [])
        is_html = self.config.get("is_html", False)

        self.logger.info(f"Sending email to: {to_addrs} via {smtp_server}:{port}")

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = ", ".join(to_addrs) if isinstance(to_addrs, list) else to_addrs
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc) if isinstance(cc, list) else cc

            # Add body
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Combine all recipients
            all_recipients = to_addrs if isinstance(to_addrs, list) else [to_addrs]
            if cc:
                all_recipients.extend(cc if isinstance(cc, list) else [cc])
            if bcc:
                all_recipients.extend(bcc if isinstance(bcc, list) else [bcc])

            # Send email
            with smtplib.SMTP(smtp_server, port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            result = {
                "smtp_server": smtp_server,
                "port": port,
                "from": from_addr,
                "to": to_addrs,
                "subject": subject,
                "status": "success",
            }

            self.logger.info(f"Successfully sent email to: {to_addrs}")
            return result

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error while sending email: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
