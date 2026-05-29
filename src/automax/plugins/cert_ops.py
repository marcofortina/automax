# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Certificate operation plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



class CertGenerateCsrPlugin(BasePlugin):
    name = "security.pki.csr.generate"
    description = "Generate a CSR from an existing private key using openssl."
    required_params = ("key", "dest", "subject")
    optional_params = ("config", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.csr.generate creates a CSR artifact; use manual commands for the exact openssl invocation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        config = f" -config {quote(params['config'])}" if params.get("config") else ""
        return [f"{sudo_prefix(params, default=True)}openssl req -new -key {quote(params['key'])} -out {quote(params['dest'])} -subj {quote(params['subject'])}{config}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.pki.csr.generate failed")

class CertSelfSignedPlugin(BasePlugin):
    name = "security.pki.cert.self_signed"
    description = "Generate a self-signed certificate using an existing private key."
    required_params = ("key", "cert", "subject")
    optional_params = ("days", "extensions", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.self_signed creates a certificate artifact; use manual commands for the exact openssl invocation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        days = int(params.get("days", 365))
        extensions = f" -extensions {quote(params['extensions'])}" if params.get("extensions") else ""
        return [f"{sudo_prefix(params, default=True)}openssl req -x509 -new -key {quote(params['key'])} -out {quote(params['cert'])} -subj {quote(params['subject'])} -days {days}{extensions}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.pki.cert.self_signed failed")

class CertVerifyChainPlugin(BasePlugin):
    name = "security.pki.cert.chain_check"
    description = "Verify a certificate chain against a CA bundle with openssl verify."
    required_params = ("cert", "ca_file")
    optional_params = ("untrusted", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.chain_check is a read-only certificate chain verification"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        untrusted = f" -untrusted {quote(params['untrusted'])}" if params.get("untrusted") else ""
        return [f"{sudo_prefix(params, default=True)}openssl verify -CAfile {quote(params['ca_file'])}{untrusted} {quote(params['cert'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.pki.cert.chain_check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)

class CertInstallKeypairPlugin(BasePlugin):
    name = "security.pki.cert.install_keypair"
    description = "Install a certificate and private key with safe permissions and optional validation."
    required_params = ("cert", "key", "cert_dest", "key_dest")
    optional_params = ("backup", "backup_suffix", "validate", "owner", "group", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.install_keypair installs certificate material and enforces file permissions"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
        cert_dest = str(params["cert_dest"])
        key_dest = str(params["key_dest"])
        commands = []
        if bool(params.get("validate", True)):
            commands.append(f"openssl x509 -in {quote(params['cert'])} -noout")
            commands.append(f"openssl pkey -in {quote(params['key'])} -noout")
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(cert_dest)} || {sudo}cp -p {quote(cert_dest)} {quote(cert_dest + str(params.get('backup_suffix', '.bak')))}")
            commands.append(f"test ! -e {quote(key_dest)} || {sudo}cp -p {quote(key_dest)} {quote(key_dest + str(params.get('backup_suffix', '.bak')))}")
        commands.extend([
            f"{sudo}install -D -m 0644 {quote(params['cert'])} {quote(cert_dest)}",
            f"{sudo}install -D -m 0600 {quote(params['key'])} {quote(key_dest)}",
        ])
        if params.get("owner") or params.get("group"):
            owner = str(params.get("owner", ""))
            group = str(params.get("group", ""))
            commands.append(f"{sudo}chown {quote(owner + ':' + group)} {quote(cert_dest)} {quote(key_dest)}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.pki.cert.install_keypair failed")

class CertExpiryReportPlugin(BasePlugin):
    name = "security.pki.cert.expiry_report"
    description = "Report certificate expiry and optionally fail inside a warning window."
    required_params = ("cert",)
    optional_params = ("warning_days", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.expiry_report is a read-only certificate expiry inspection"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        seconds = int(params.get("warning_days", 30)) * 86400
        return [f"{sudo_prefix(params, default=True)}openssl x509 -in {quote(params['cert'])} -noout -enddate && {sudo_prefix(params, default=True)}openssl x509 -in {quote(params['cert'])} -noout -checkend {seconds}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.pki.cert.expiry_report failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class CertFingerprintPlugin(BasePlugin):
    name = "security.pki.cert.fingerprint"
    description = "Read a certificate fingerprint with openssl."
    required_params = ("cert",)
    optional_params = ("algorithm", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.fingerprint is a read-only certificate fingerprint query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        algorithm = str(params.get("algorithm", "sha256"))
        return [f"{sudo_prefix(params, default=True)}openssl x509 -in {quote(params['cert'])} -noout -fingerprint -{quote(algorithm)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.pki.cert.fingerprint failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"fingerprint": out.strip()})


class CertMatchesKeyPlugin(BasePlugin):
    name = "security.pki.cert.key_match_check"
    description = "Assert that a certificate public key matches a private key."
    required_params = ("cert", "key")
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.key_match_check is a read-only certificate/private-key assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = sudo_prefix(params, default=True)
        cert = quote(params["cert"])
        key = quote(params["key"])
        return [f"test \"$({sudo}openssl x509 -in {cert} -pubkey -noout | openssl pkey -pubin -outform DER | openssl sha256)\" = \"$({sudo}openssl pkey -in {key} -pubout -outform DER | openssl sha256)\""]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.pki.cert.key_match_check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class CertSanAssertPlugin(BasePlugin):
    name = "security.pki.cert.san_check"
    description = "Assert that a certificate contains required Subject Alternative Names."
    required_params = ("cert", "names")
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.san_check is a read-only certificate SAN assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        names = params["names"] if isinstance(params["names"], list) else [params["names"]]
        base = f"{sudo_prefix(params, default=True)}openssl x509 -in {quote(params['cert'])} -noout -ext subjectAltName"
        commands = [base]
        for name in names:
            commands.append(f"{base} | grep -F -- {quote(name)}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.pki.cert.san_check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class CertSubjectAssertPlugin(BasePlugin):
    name = "security.pki.cert.subject_check"
    description = "Assert that a certificate subject contains an expected string."
    required_params = ("cert", "subject")
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.subject_check is a read-only certificate subject assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=True)}openssl x509 -in {quote(params['cert'])} -noout -subject | grep -F -- {quote(params['subject'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.pki.cert.subject_check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class CertIssuerAssertPlugin(BasePlugin):
    name = "security.pki.cert.issuer_check"
    description = "Assert that a certificate issuer contains an expected string."
    required_params = ("cert", "issuer")
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.cert.issuer_check is a read-only certificate issuer assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=True)}openssl x509 -in {quote(params['cert'])} -noout -issuer | grep -F -- {quote(params['issuer'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.pki.cert.issuer_check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class CertInstallCaBundlePlugin(BasePlugin):
    name = "security.pki.trust.install_bundle"
    description = "Install a CA bundle file with safe permissions and optional trust-store refresh."
    required_params = ("src", "dest")
    optional_params = ("backup", "backup_suffix", "mode", "owner", "group", "update_trust", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.pki.trust.install_bundle installs CA material; use manual commands for exact file operations"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
        src = str(params["src"])
        dest = str(params["dest"])
        mode = str(params.get("mode", "0644"))
        commands = [f"openssl x509 -in {quote(src)} -noout"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(dest)} || {sudo}cp -p {quote(dest)} {quote(dest + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -D -m {quote(mode)} {quote(src)} {quote(dest)}")
        if params.get("owner") or params.get("group"):
            owner = str(params.get("owner", ""))
            group = str(params.get("group", ""))
            commands.append(f"{sudo}chown {quote(owner + ':' + group)} {quote(dest)}")
        if bool(params.get("update_trust", True)):
            commands.append(f"{sudo}update-ca-certificates 2>/dev/null || {sudo}update-ca-trust extract 2>/dev/null || true")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.pki.trust.install_bundle failed")
