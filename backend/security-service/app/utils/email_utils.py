import smtplib
from email.message import EmailMessage

from config import Config


def send_password_reset_email(recipient_email: str, reset_token: str) -> None:
    if not recipient_email:
        raise ValueError("recipient_email es requerido")

    reset_url = f"{Config.RESET_PASSWORD_URL_BASE}?token={reset_token}"
    message = EmailMessage()
    message["Subject"] = "Recuperación de contraseña"
    message["From"] = Config.SMTP_FROM_EMAIL
    message["To"] = recipient_email
    message.set_content(
        f"Hola,\n\nRecibimos una solicitud para restablecer tu contraseña.\n\n"
        f"Haz clic en el siguiente enlace para continuar:\n\n{reset_url}\n\n"
        "Si no solicitaste este cambio, ignora este correo.\n\n"
        "Saludos,\nEl equipo de seguridad"
    )

    try:
        if Config.SMTP_USE_SSL:
            smtp = smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, timeout=Config.SMTP_TIMEOUT)
        else:
            smtp = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=Config.SMTP_TIMEOUT)

        with smtp:
            if Config.SMTP_USE_TLS and not Config.SMTP_USE_SSL:
                smtp.starttls()

            if Config.SMTP_USER and Config.SMTP_PASSWORD:
                smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)

            smtp.send_message(message)
    except Exception as exc:
        raise RuntimeError(f"No se pudo enviar el correo de recuperación: {exc}") from exc
