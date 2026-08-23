from __future__ import annotations

import logging
import mimetypes
import smtplib
import socket
import ssl
import time
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

DEFAULT_SMTP_PORT = 25
DEFAULT_SSL_PORT = 465
DEFAULT_SUBMISSION_PORT = 587

EICAR_STRING = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

# Prefixes used by smtplib's debug output that we clean up for readability
_DEBUG_PREFIX_MAP = {
    "send: b'": (8, "send: "),
    "reply: b'": (9, "reply: "),
    "data: b'": (8, "data: "),
}


def _setup_file_logging() -> None:
    log_dir = Path(
        __import__("os").environ.get("SMTP_LOG_DIR", ".")
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "smtp_tool.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)


_setup_file_logging()


def _capture_smtp_log(
    smtp_instance: smtplib.SMTP | smtplib.SMTP_SSL,
    smtp_log: list[str],
    prefix: str = "",
) -> None:
    original_debug = smtp_instance._print_debug

    def custom_debug(self: object, *args: object) -> object:
        message = " ".join(str(a) for a in args)

        for marker, (strip_len, replacement) in _DEBUG_PREFIX_MAP.items():
            if message.startswith(marker) and message.endswith("'"):
                content = message[strip_len:-1]
                content = content.replace("\\r\\n", "\n").replace("\\n", "\n")
                message = f"{replacement}{content}"
                break

        smtp_log.append(f"{prefix}{message}")
        return original_debug(self, *args)

    smtp_instance._print_debug = custom_debug  # type: ignore[attr-defined]


def _extract_tls_info(
    sock: ssl.SSLSocket,
    smtp_log: list[str],
    header: str,
) -> None:
    if not (hasattr(sock, "cipher") and callable(sock.cipher)):
        return

    cipher_info = sock.cipher()
    if not cipher_info:
        return

    tls_protocol = sock.version() if hasattr(sock, "version") else "Unknown"
    cipher_name = cipher_info[0] if cipher_info else "Unknown"
    cipher_version = cipher_info[1] if len(cipher_info) > 1 else "Unknown"
    cipher_bits = cipher_info[2] if len(cipher_info) > 2 else "Unknown"

    smtp_log.append(f"{header}:")
    smtp_log.append(f"  - Protocol: {tls_protocol}")
    smtp_log.append(f"  - Cipher: {cipher_name}")
    smtp_log.append(f"  - Version: {cipher_version}")
    smtp_log.append(f"  - Bits: {cipher_bits}")

    if hasattr(sock, "getpeercert"):
        cert = sock.getpeercert()
        if cert:
            subject = dict(x[0] for x in cert.get("subject", []))
            issuer = dict(x[0] for x in cert.get("issuer", []))
            smtp_log.append(
                f"  - Server Certificate: {subject.get('commonName', 'Unknown')}"
            )
            smtp_log.append(
                f"  - Issuer: {issuer.get('commonName', 'Unknown')}"
            )
            if "notAfter" in cert:
                smtp_log.append(f"  - Expires: {cert['notAfter']}")


def _create_ssl_context(no_tls_verify: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()
    if no_tls_verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


class SMTPService:
    def __init__(self) -> None:
        self.eicar_string = EICAR_STRING

    def send_email(
        self,
        server: str,
        port: int,
        use_tls: bool,
        use_ssl: bool,
        username: str,
        password: str,
        sender: str,
        recipients: list[str],
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        subject: str = "",
        body: str = "",
        body_type: str = "plain",
        attachments: list[str] | None = None,
        custom_headers: dict[str, str] | None = None,
        hostname: str | None = None,
        ehlo_as: str | None = None,
        helo_as: str | None = None,
        mail_options: list[str] | None = None,
        no_tls_verify: bool = False,
    ) -> dict[str, object]:
        smtp_log: list[str] = []
        start_time = time.time()
        smtp_log.append(
            f"Email Sending Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}"
        )

        try:
            cc = cc or []
            bcc = bcc or []
            attachments = attachments or []
            custom_headers = custom_headers or {}
            mail_options = mail_options or []

            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = ", ".join(recipients)
            if cc:
                msg["Cc"] = ", ".join(cc)
            msg["Subject"] = subject
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid(domain=hostname or socket.getfqdn())

            logger.info("Email has %d custom headers to process", len(custom_headers))

            for header_name, header_value in custom_headers.items():
                try:
                    msg[header_name] = header_value
                    logger.info("Added custom header: %s", header_name)
                except Exception as exc:
                    logger.warning("Failed to add custom header %s: %s", header_name, exc)

            if body_type == "html":
                if not body.strip().startswith("<!DOCTYPE") and not body.strip().startswith("<html"):
                    body = (
                        "<!DOCTYPE html>\n"
                        "<html>\n"
                        "<head>\n"
                        '  <meta charset="UTF-8">\n'
                        "</head>\n"
                        "<body>\n"
                        f"  {body}\n"
                        "</body>\n"
                        "</html>"
                    )
                logger.info("Sending email with HTML body type, length: %d", len(body))

            msg.attach(MIMEText(body, body_type))

            for attachment_path_str in attachments:
                attachment_path = Path(attachment_path_str)
                if attachment_path.exists():
                    attachment_data = attachment_path.read_bytes()
                    attachment_filename = attachment_path.name
                    content_type, encoding = mimetypes.guess_type(str(attachment_path))
                    if content_type is None or encoding is not None:
                        content_type = "application/octet-stream"

                    _maintype, subtype = content_type.split("/", 1)
                    attachment = MIMEApplication(attachment_data, subtype)
                    attachment.add_header(
                        "Content-Disposition", "attachment", filename=attachment_filename
                    )
                    msg.attach(attachment)

            smtp_log.append("Connection Info:")
            smtp_log.append(f"  - Server: {server}:{port}")
            smtp_log.append(f"  - SSL: {'Yes' if use_ssl else 'No'}")
            smtp_log.append(f"  - STARTTLS: {'Yes' if use_tls and not use_ssl else 'No'}")
            smtp_log.append(f"  - Local Hostname: {hostname or 'Default'}")
            if no_tls_verify and (use_tls or use_ssl):
                smtp_log.append("  - TLS Verification: Disabled")
            elif use_tls or use_ssl:
                smtp_log.append("  - TLS Verification: Enabled")

            if use_ssl:
                context = _create_ssl_context(no_tls_verify)
                smtp = smtplib.SMTP_SSL(server, port, local_hostname=hostname, context=context)

                try:
                    _extract_tls_info(smtp.sock, smtp_log, "SSL/TLS Connection Details")  # type: ignore[arg-type]
                except Exception as exc:
                    smtp_log.append(f"SSL Info: {exc}")
            else:
                smtp = smtplib.SMTP(server, port, local_hostname=hostname)

            smtp.set_debuglevel(1)
            _capture_smtp_log(smtp, smtp_log)

            if ehlo_as:
                smtp.ehlo(ehlo_as)
                if hasattr(smtp, "esmtp_features") and smtp.esmtp_features:
                    smtp_log.append("Server Capabilities:")
                    for feature, params in smtp.esmtp_features.items():
                        if params:
                            smtp_log.append(f"  - {feature}: {params}")
                        else:
                            smtp_log.append(f"  - {feature}")
            elif helo_as:
                smtp.helo(helo_as)

            if use_tls and not use_ssl:
                context = _create_ssl_context(no_tls_verify)
                smtp.starttls(context=context)

                try:
                    _extract_tls_info(smtp.sock, smtp_log, "TLS Connection Established")  # type: ignore[arg-type]
                except Exception as exc:
                    smtp_log.append(
                        f"TLS Info: Could not retrieve detailed TLS information: {exc}"
                    )

                # Re-EHLO after STARTTLS per RFC 3207
                if ehlo_as:
                    smtp.ehlo(ehlo_as)

            if username and password:
                if hasattr(smtp, "esmtp_features") and "auth" in smtp.esmtp_features:
                    auth_methods = smtp.esmtp_features["auth"]
                    smtp_log.append("Authentication Info:")
                    smtp_log.append(f"  - Methods Available: {auth_methods}")
                    smtp_log.append(f"  - Using: {username}")

                smtp.login(username, password)
                smtp_log.append("  - Status: Authentication successful")

            all_recipients = recipients + cc + bcc
            smtp.sendmail(sender, all_recipients, msg.as_string(), mail_options=mail_options)

            smtp.quit()

            end_time = time.time()
            duration = end_time - start_time
            smtp_log.append(
                f"Email Sending Completed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}"
            )
            smtp_log.append(f"Total Duration: {duration:.2f} seconds")

            logger.info("Email sent successfully to %s", ", ".join(recipients))
            return {
                "success": True,
                "smtp_log": smtp_log,
                "message_id": msg["Message-ID"],
            }

        except Exception as exc:
            logger.exception("Failed to send email: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "smtp_log": smtp_log,
            }

    def test_connection(
        self,
        server: str,
        port: int,
        use_tls: bool,
        use_ssl: bool,
        username: str,
        password: str,
        hostname: str | None = None,
        ehlo_as: str | None = None,
        helo_as: str | None = None,
        no_tls_verify: bool = False,
    ) -> dict[str, object]:
        smtp_log: list[str] = []

        try:
            if use_ssl:
                context = _create_ssl_context(no_tls_verify)
                smtp = smtplib.SMTP_SSL(server, port, local_hostname=hostname, context=context)
            else:
                smtp = smtplib.SMTP(server, port, local_hostname=hostname)

            smtp.set_debuglevel(1)
            _capture_smtp_log(smtp, smtp_log)

            if ehlo_as:
                server_info = smtp.ehlo(ehlo_as)
            elif helo_as:
                server_info = smtp.helo(helo_as)
                try:
                    server_info = smtp.ehlo()
                except Exception:
                    pass
            else:
                server_info = smtp.ehlo()

            if use_tls and not use_ssl:
                context = _create_ssl_context(no_tls_verify)
                smtp.starttls(context=context)
                if ehlo_as:
                    server_info = smtp.ehlo(ehlo_as)
                else:
                    server_info = smtp.ehlo()

            if username and password:
                smtp.login(username, password)

            capabilities: list[str] = []
            if hasattr(server_info, "__getitem__") and len(server_info) > 1:
                for item in server_info[1]:
                    if isinstance(item, bytes):
                        item = item.decode("utf-8")
                    capabilities.append(item)

            smtp.quit()

            logger.info("Successfully connected to SMTP server %s:%d", server, port)
            return {
                "success": True,
                "message": "Connection successful",
                "capabilities": capabilities,
                "smtp_log": smtp_log,
            }

        except Exception as exc:
            logger.exception("Failed to connect to SMTP server: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "smtp_log": smtp_log,
            }

    def create_eicar_attachment(self) -> tuple[str, bytes]:
        filename = "eicar.com"
        return filename, self.eicar_string.encode("utf-8")

    def create_pdf_attachment(
        self,
        filename: str = "test.pdf",
        malformed: bool = False,
        active_content: bool = False,
    ) -> tuple[str, bytes]:
        buffer = BytesIO()

        if malformed:
            buffer.write(b"%PDF-1.7\n")
            buffer.write(b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n")
            buffer.write(b"2 0 obj\n<</Type/Pages/Kids[]/Count 0>>\nendobj\n")
            buffer.write(b"This PDF is intentionally malformed for testing")
        else:
            pdf = canvas.Canvas(buffer, pagesize=letter)
            pdf.drawString(100, 750, "Test PDF Document")
            pdf.drawString(100, 700, "Generated for SMTP Testing")

            if active_content:
                pdf.setFillColorRGB(1, 0, 0)
                pdf.drawString(100, 650, "WARNING: This PDF contains simulated active content!")
                pdf.setFillColorRGB(0, 0, 0)
                pdf.drawString(100, 630, "This PDF simulates having JavaScript that would:")
                pdf.drawString(120, 610, "- Auto-execute when the document is opened")
                pdf.drawString(120, 590, "- Potentially access network resources")
                pdf.drawString(120, 570, "- Could attempt to exploit reader vulnerabilities")

                pdf.setFillColorRGB(1, 0, 0)
                pdf.rect(100, 500, 200, 40, fill=1)
                pdf.setFillColorRGB(1, 1, 1)
                pdf.drawString(125, 520, "SIMULATED MALICIOUS BUTTON")

                pdf.setAuthor("SMTP Testing Tool - Security Test")
                pdf.setTitle("TEST - PDF with Active Content")
                pdf.setSubject("SECURITY TEST - JavaScript simulation")
                pdf.setKeywords("security test javascript active content")

                # OpenAction triggers email security systems to flag the PDF
                buffer.write(
                    b"%OpenAction <</S/JavaScript/JS(app.alert("
                    b"'This is a simulated JavaScript alert. "
                    b"In a real malicious PDF, arbitrary code could run here."
                    b"\\nThis file is used for testing email security systems.'))>>"
                )

            pdf.save()

        buffer.seek(0)
        return filename, buffer.getvalue()

    def create_spf_test_email(self, recipient: str) -> dict[str, object]:
        return {
            "sender": "spf-test@gmail.com",
            "recipients": [recipient],
            "subject": "SPF Test Email",
            "body": (
                "This is a test email specifically for checking SPF validation.\n"
                "\n"
                "The From: address claims to be from gmail.com, but this email was not sent "
                "from Google's servers.\n"
                "This should cause SPF (Sender Policy Framework) to fail because:\n"
                "- Gmail has SPF records published in DNS\n"
                "- This mail server is not authorized to send from gmail.com\n"
                "- The receiving server should detect this SPF failure\n"
                "\n"
                "This test is useful for confirming that SPF checks are working properly "
                "on the receiving mail server.\n"
            ),
            "body_type": "plain",
            "custom_headers": {
                "X-SMTP-Test": "SPF-Test",
                "X-SPF-Test": "This email should fail SPF validation",
            },
        }
