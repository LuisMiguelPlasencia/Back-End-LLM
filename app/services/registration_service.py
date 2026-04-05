# Service for bulk user registration via company codes
# Handles code validation, user creation with temp passwords, and email notification
# Uses conversaconfig.company_codes table for code management
# and conversaconfig.user_info table for user creation

import os
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from dotenv import load_dotenv
import bcrypt

from .db import execute_query, execute_query_one

load_dotenv(override=True)

# Email configuration (SMTP — Office 365)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Conversa")


def generate_temp_password(length: int = 12) -> str:
    """Generate a random temporary password with letters, digits, and punctuation"""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(plain: str) -> str:
    """Hash a password with bcrypt, matching the auth_service pattern"""
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def validate_company_code(code: str) -> Optional[Dict]:
    """
    Validate a company registration code.
    Returns dict with company_name, remaining_uses if valid, else None.
    
    Checks:
    - Code exists in conversaconfig.company_codes
    - Code is active
    - Code has remaining uses (current_uses < max_uses)
    - Code has not expired
    """
    query = """
        SELECT 
            cc.code_id,
            cc.company_id,
            cc.max_uses,
            cc.current_uses,
            ci.company_name
        FROM conversaaccesses.company_codes cc
        LEFT JOIN conversaaccesses.company_info ci ON cc.company_id = ci.company_id
        WHERE cc.code = $1
          AND cc.is_active = TRUE
          AND cc.current_uses < cc.max_uses
          AND (cc.expires_at IS NULL OR cc.expires_at > NOW())
    """
    result = await execute_query_one(query, code)
    if not result:
        return None

    row = dict(result)
    return {
        "code_id": str(row["code_id"]),
        "company_id": str(row["company_id"]),
        "company_name": row.get("company_name", ""),
        "remaining_uses": row["max_uses"] - row["current_uses"],
        "max_uses": row["max_uses"],
    }


async def register_employee(
    company_id: str, name: str, last_name: str, email: str, role: str
) -> Dict:
    """
    Create a single user in conversaconfig.user_info.
    Returns dict with success status and temp password (for email).

    Steps:
    1. Check if email already exists
    2. Generate temp password and hash it
    3. INSERT into user_info
    4. Return result
    """
    # Check for duplicate email
    existing = await execute_query_one(
        "SELECT user_id FROM conversaconfig.user_info WHERE email = $1", email
    )
    if existing:
        return {"success": False, "message": "El email ya está registrado", "temp_password": None}

    temp_password = generate_temp_password()
    hashed = hash_password(temp_password)

    insert_query = """
        INSERT INTO conversaconfig.user_info 
            (user_id, email, password, name, last_name, user_type, is_active, company_id)
        VALUES 
            (gen_random_uuid(), $1, $2, $3, $4, $5, TRUE, $6)
        RETURNING user_id
    """
    try:
        result = await execute_query_one(
            insert_query, email, hashed, name, last_name, role, company_id
        )
        if result:
            return {
                "success": True,
                "message": "Usuario creado correctamente",
                "temp_password": temp_password,
                "user_id": str(result["user_id"]),
            }
        return {"success": False, "message": "Error al insertar usuario", "temp_password": None}
    except Exception as e:
        return {"success": False, "message": f"Error de base de datos: {str(e)}", "temp_password": None}


async def increment_code_usage(code: str, count: int = 1):
    """Increment the current_uses counter on a company code after successful registrations"""
    query = """
        UPDATE conversaconfig.company_codes 
        SET current_uses = current_uses + $1 
        WHERE code = $2
    """
    await execute_query(query, count, code)


def send_welcome_email(to_email: str, name: str, temp_password: str, company_name: str):
    """
    Send a welcome email to a newly registered employee with their temp credentials.
    Uses SMTP (e.g. Gmail with App Password).
    Fails silently (logs error) so a mail failure doesn't block user creation.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"⚠️ SMTP not configured — skipping email to {to_email}")
        return

    subject = f"Bienvenido a Conversa — {company_name}"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
        <div style="background: #2563EB; padding: 24px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="color: white; margin: 0;">Conversa</h1>
        </div>
        <div style="padding: 24px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Hola <strong>{name}</strong>,</p>
            <p>Tu empresa <strong>{company_name}</strong> te ha dado acceso a <strong>Conversa</strong>, 
               la plataforma de entrenamiento de ventas con IA conversacional.</p>
            <p>Tus credenciales de acceso:</p>
            <div style="background: #f3f4f6; padding: 16px; border-radius: 6px; margin: 16px 0;">
                <p style="margin: 4px 0;"><strong>Email:</strong> {to_email}</p>
                <p style="margin: 4px 0;"><strong>Contraseña temporal:</strong> {temp_password}</p>
            </div>
            <p>Te recomendamos cambiar tu contraseña tras el primer inicio de sesión.</p>
            <a href="https://app.conversa.com/login" 
               style="display: inline-block; background: #2563EB; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; margin-top: 12px;">
                Iniciar sesión
            </a>
            <p style="margin-top: 24px; font-size: 12px; color: #9ca3af;">
                Si no esperabas este correo, puedes ignorarlo.
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"✅ Email enviado a {to_email}")
    except Exception as e:
        print(f"❌ Error enviando email a {to_email}: {e}")
