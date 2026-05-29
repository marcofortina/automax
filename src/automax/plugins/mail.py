# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Controller-side email notification plugin."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import quote


def _list(value: Any, name: str) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and value:
        return [str(item) for item in value]
    raise PluginValidationError(f"notify.mail.send {name} must be a string or non-empty list")


class MailSendPlugin(BasePlugin):
    name = "notify.mail.send"
    description = "Send an email from the Automax controller through SMTP."
    required_params = ("smtp_host", "from", "to", "subject")
    optional_params = ("smtp_port", "starttls", "ssl", "username", "password", "body", "cc", "bcc", "reply_to", "attachments", "timeout")
    parameter_schema = {
        "to": {"types": ("string", "list"), "description": "Email recipient or non-empty recipient list."},
        "cc": {"types": ("string", "list"), "description": "Email CC recipient or non-empty recipient list."},
        "bcc": {"types": ("string", "list"), "description": "Email BCC recipient or non-empty recipient list."},
        "attachments": {"types": ("string", "list"), "description": "Attachment path or attachment path list."},
    }
    opens_remote_session = False

    def _summary(self, params: Dict[str, Any]) -> str:
        to = ", ".join(_list(params["to"], "to"))
        return f"smtp={params['smtp_host']}:{params.get('smtp_port', 587)} from={params['from']} to={to} subject={params['subject']}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return [{"path": "notify.mail.send", "kind": "mail-plan", "diff": f"--- notify.mail.send (current)\n+++ notify.mail.send (desired)\n@@\n+ {self._summary(params)}\n"}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        port = int(params.get("smtp_port", 587))
        # smtplib has no useful CLI; expose a safe copy/paste placeholder without secrets.
        return [f"# Send mail from controller via SMTP {quote(params['smtp_host'])}:{port} to {quote(','.join(_list(params['to'], 'to')))} subject {quote(params['subject'])}; password is intentionally not rendered"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        msg = EmailMessage()
        msg["From"] = str(params["from"])
        msg["To"] = ", ".join(_list(params["to"], "to"))
        if params.get("cc"):
            msg["Cc"] = ", ".join(_list(params["cc"], "cc"))
        if params.get("reply_to"):
            msg["Reply-To"] = str(params["reply_to"])
        msg["Subject"] = str(params["subject"])
        msg.set_content(str(params.get("body", "")))
        attachments = params.get("attachments", []) or []
        if isinstance(attachments, str):
            attachments = [attachments]
        for item in attachments:
            path = Path(str(item)).expanduser()
            msg.add_attachment(path.read_bytes(), maintype="application", subtype="octet-stream", filename=path.name)
        recipients = _list(params["to"], "to") + (_list(params["cc"], "cc") if params.get("cc") else []) + (_list(params["bcc"], "bcc") if params.get("bcc") else [])
        host = str(params["smtp_host"])
        port = int(params.get("smtp_port", 465 if bool(params.get("ssl", False)) else 587))
        timeout = float(params.get("timeout", 30))
        client_cls = smtplib.SMTP_SSL if bool(params.get("ssl", False)) else smtplib.SMTP
        with client_cls(host, port, timeout=timeout) as smtp:
            if bool(params.get("starttls", True)) and not bool(params.get("ssl", False)):
                smtp.starttls()
            if params.get("username"):
                smtp.login(str(params["username"]), str(params.get("password", "")))
            smtp.send_message(msg, to_addrs=recipients)
        return PluginResult.success(changed=True, message="mail sent", data={"to": recipients, "smtp_host": host})
