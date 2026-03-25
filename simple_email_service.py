import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.image import MIMEImage
from urllib.parse import urlparse
from urllib.request import urlopen
from typing import List, Tuple, Optional
from email.utils import formataddr

logger = logging.getLogger(__name__)

def send_smtp_email(subject: str, body: str, recipients: List[str], attachments: Optional[List[Tuple[str, bytes]]] = None) -> bool:
    """Send an email using SMTP from support@connectyou.pro with optional attachments.

    recipients: list of email strings
    attachments: list of tuples (filename, file_bytes)
    """
    try:
        smtp_server = os.environ.get("SMTP_SERVER", "mail.privateemail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "support@connectyou.pro")
        smtp_pass = os.environ.get("SMTP_PASS", "")

        # Build footer
        footer_lines = [
            "",
            "--",
            "Best regards,",
            "Tin Nguyen",
            "ConnectYou.pro | Project Coordinator",
            "\U0001F4F1 Mobile: 437-983-4063",
            "\U0001F310 Website: www.connectyou.pro",
        ]
        # Always insert a separating newline before footer
        plain_body = (body or "") + ("\n" if body else "") + "\n".join(footer_lines)

        # HTML variant with inline logo
        body_html = (body or "").replace('\n', '<br>')
        footer_html = (
            "<div style=\"margin-top:16px; font-family:Arial,Helvetica,sans-serif; font-size:14px; color:#111111;\">"
            "<hr style=\"border:0;border-top:1px solid #e0e0e0;\">"
            "<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" style=\"color:#111111;\"><tr>"
            "<td style=\"padding-right:12px;\"><img src=\"cid:footer_logo\" alt=\"ConnectYou\" width=\"48\" height=\"48\" style=\"border-radius:12px;\"></td>"
            "<td>"
            "<div><strong>Best regards,</strong><br>"
            "Tin Nguyen<br>ConnectYou.pro | Project Coordinator<br>"
            "&#128241; Mobile: 437-983-4063<br>&#127760; Website: <a href=\"https://www.connectyou.pro\" style=\"color:#0d6efd;\">www.connectyou.pro</a>"
            "</div>"
            "</td></tr></table></div>"
        )
        html_full = f"<div style=\"font-family:Arial,Helvetica,sans-serif; color:#111111;\">{body_html}{footer_html}</div>"

        # Root message allows related (inline images) + attachments
        msg = MIMEMultipart('mixed')
        from_name = os.environ.get("SMTP_FROM_NAME", "ConnectYou Support")
        msg['From'] = formataddr((from_name, smtp_user))
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg['Reply-To'] = smtp_user

        related = MIMEMultipart('related')
        alternative = MIMEMultipart('alternative')
        alternative.attach(MIMEText(plain_body, 'plain', 'utf-8'))
        alternative.attach(MIMEText(html_full, 'html', 'utf-8'))
        related.attach(alternative)
        msg.attach(related)

        if attachments:
            for filename, data in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)

        # Inline footer image
        logo_path = os.environ.get('EMAIL_FOOTER_IMAGE')
        logo_url = os.environ.get('EMAIL_FOOTER_IMAGE_URL')
        if not logo_path:
            # try common locations
            candidates = [
                # Preferred: ConnectYou logo placed under static/images
                os.path.join(os.path.dirname(__file__), 'static', 'images', 'connectyou_logo.png'),
                os.path.join(os.path.dirname(__file__), 'static', 'images', 'connectyou_logo.jpg'),
                os.path.join(os.path.dirname(__file__), 'connectyou_logo.png'),
                os.path.join(os.path.dirname(__file__), 'connectyou_logo.jpg'),
                os.path.join(os.path.dirname(__file__), 'static', 'images', 'logo.png'),
                os.path.join(os.path.dirname(__file__), 'generated-icon.png'),
                os.path.join(os.path.dirname(__file__), 'static', 'images', 'app-icon.png'),
            ]
            for c in candidates:
                if os.path.exists(c):
                    logo_path = c
                    break
        # Attach logo image either from local path or URL
        try:
            if logo_path and os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<footer_logo>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
                    related.attach(img)
                logger.info('Email footer using local image: %s', logo_path)
            elif logo_url:
                parsed = urlparse(logo_url)
                if parsed.scheme in ('http', 'https'):
                    with urlopen(logo_url, timeout=10) as resp:
                        data = resp.read()
                        img = MIMEImage(data)
                        img.add_header('Content-ID', '<footer_logo>')
                        img.add_header('Content-Disposition', 'inline', filename=os.path.basename(parsed.path) or 'logo.png')
                        related.attach(img)
                    logger.info('Email footer using remote image: %s', logo_url)
        except Exception as e:
            logger.warning('Failed to attach footer image: %s', e)

        def _send_via_tls() -> None:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(str(smtp_user), str(smtp_pass))
                server.sendmail(smtp_user, recipients, msg.as_string())

        def _send_via_ssl() -> None:
            ssl_port = int(os.environ.get("SMTP_SSL_PORT", "465"))
            with smtplib.SMTP_SSL(smtp_server, ssl_port, timeout=30) as server:
                server.ehlo()
                server.login(str(smtp_user), str(smtp_pass))
                server.sendmail(smtp_user, recipients, msg.as_string())

        try:
            _send_via_tls()
        except smtplib.SMTPAuthenticationError as e:
            # Some providers prefer implicit SSL on 465; fall back if auth fails
            logger.warning("TLS auth failed, retrying with SSL: %s", e)
            _send_via_ssl()

        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def send_simple_report_email(provider_name: str, provider_phone: str, reason: str, other_reason: Optional[str] = None, user_ip: Optional[str] = None) -> bool:
    """Backward-compatible wrapper used elsewhere in the codebase.

    Builds a basic subject/body and sends to REPORT_TO (defaults to support@connectyou.pro).
    """
    # Map reason key to readable text when applicable
    reason_text = {
        'incorrect_information': 'Incorrect Information',
        'poor_service': 'Poor Service Quality',
        'unprofessional': 'Unprofessional Behavior',
        'scam_fraud': 'Scam or Fraud',
        'safety_concerns': 'Safety Concerns',
        'other': 'Other'
    }.get(reason, reason)

    subject = f"Service Provider Report: {provider_name}"
    lines = [
        "A new service provider report has been submitted through the ConnectYou platform.",
        "",
        "REPORTED PROVIDER DETAILS:",
        f"- Provider Name: {provider_name}",
        f"- Phone Number: {provider_phone}",
        "",
        "REPORT DETAILS:",
        f"- Reason for Report: {reason_text}",
    ]
    if other_reason and reason in ('other', 'Other'):
        lines.append(f"- Additional Details: {other_reason}")
    if user_ip:
        lines.append(f"- Reporter IP: {user_ip}")
    lines.extend(["", "This report was automatically generated by the ConnectYou Service Provider Directory."])
    body = "\n".join(lines)

    report_to = os.environ.get('REPORT_TO', os.environ.get('SMTP_USER', 'support@connectyou.pro'))
    return send_smtp_email(subject=subject, body=body, recipients=[report_to])