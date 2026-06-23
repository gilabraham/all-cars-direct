"""Send deal-request emails to the customer and the admin.

SMTP settings are read from .streamlit/secrets.toml, e.g.:

    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "you@example.com"
    smtp_password = "app-password"
    smtp_from = "All Cars Direct <you@example.com>"
    admin_email = "you@example.com"

If SMTP isn't configured the inquiry is still saved; this just reports that no
email could be sent so the UI can tell the customer accordingly.
"""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

import streamlit as st

_REQUIRED = ["smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from"]


def _cfg(key: str, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default


def is_configured() -> bool:
    return all(_cfg(k) for k in _REQUIRED)


def admin_email() -> str | None:
    return _cfg("admin_email") or _cfg("smtp_from")


def _customer_message(inq: dict, sender: str) -> EmailMessage:
    deal = inq.get("listing_label") or "your selected vehicle"
    msg = EmailMessage()
    msg["Subject"] = f"We received your request — {deal}"
    msg["From"] = sender
    msg["To"] = inq["customer_email"]
    msg.set_content(
        f"Hi {inq['customer_name']},\n\n"
        f"Thanks for your interest in {deal}. We've received your request and a "
        f"specialist will reach out shortly to finalize the details.\n\n"
        f"Summary of your request:\n"
        f"  Vehicle: {deal}\n"
        f"  Phone:   {inq.get('customer_phone') or '—'}\n"
        f"  Message: {inq.get('message') or '—'}\n\n"
        f"Talk soon,\nAll Cars Direct"
    )
    return msg


def _admin_message(inq: dict, sender: str, to_addr: str) -> EmailMessage:
    deal = inq.get("listing_label") or "—"
    msg = EmailMessage()
    msg["Subject"] = f"New deal request — {deal}"
    msg["From"] = sender
    msg["To"] = to_addr
    msg["Reply-To"] = inq["customer_email"]
    msg.set_content(
        "A new deal request has come in:\n\n"
        f"  Vehicle:  {deal}\n"
        f"  Name:     {inq['customer_name']}\n"
        f"  Email:    {inq['customer_email']}\n"
        f"  Phone:    {inq.get('customer_phone') or '—'}\n"
        f"  Message:  {inq.get('message') or '—'}\n\n"
        "Manage it in the admin Requests page."
    )
    return msg


def send_request_emails(inquiry: dict) -> tuple[bool, str]:
    """Return (sent, info). Never raises."""
    if not is_configured():
        return (False, "Email isn't configured on this site, so no confirmation was emailed.")

    host = _cfg("smtp_host")
    port = int(_cfg("smtp_port", 587))
    user = _cfg("smtp_user")
    password = _cfg("smtp_password")
    sender = _cfg("smtp_from")
    admin = admin_email()

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.send_message(_customer_message(inquiry, sender))
            if admin:
                server.send_message(_admin_message(inquiry, sender, admin))
        return (True, "Confirmation emails sent.")
    except Exception as exc:  # noqa: BLE001
        return (False, f"Could not send email: {exc}")
