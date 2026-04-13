# Service for bulk user registration via company codes
# Handles code validation, user creation with temp passwords, and email notification
# Uses conversaconfig.company_codes table for code management
# and conversaconfig.user_info table for user creation

import os
import base64
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
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


#def hash_password(plain: str) -> str:
#    """Hash a password with bcrypt, matching the auth_service pattern"""
#    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def hash_password(password: str) -> str:
    """
    Toma una contraseña en texto plano y devuelve el hash seguro (string) 
    para guardar en la base de datos.
    """
    # 1. Convertimos la contraseña a bytes
    pwd_bytes = password.encode('utf-8')
    
    # 2. Generamos el salt (aleatoriedad)
    salt = bcrypt.gensalt()
    
    # 3. Hasheamos
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    
    # 4. Devolvemos como string para que Postgres lo entienda bien (VARCHAR)
    return hashed_bytes.decode('utf-8')


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
            code_id,
            company_id,
            max_uses,
            current_uses,
            journey_id
        FROM conversaaccesses.company_codes
        WHERE code = $1
          AND is_active = TRUE
          AND current_uses < max_uses
          AND (expires_at IS NULL OR expires_at > NOW())
    """
    result = await execute_query_one(query, code)
    if not result:
        return None

    row = dict(result)
    return {
        "code_id": str(row["code_id"]),
        "company_id": str(row["company_id"]),
        "company_name": str(row["company_id"]),
        "remaining_uses": row["max_uses"] - row["current_uses"],
        "max_uses": row["max_uses"],
        "journey_id": row["journey_id"],
    }


async def assign_courses_to_user(user_id: str, journey_id: str):
    '''
    - insert new record into user_journeys_assigments with user_id and journey_id
    - find all courses linked to the journey_id in journey_courses
    - for each course, insert into user_course_assignments with user_id, course_id
    '''
    assign_journey_query = """
        INSERT INTO conversaconfig.user_journeys_assigments 
            (user_journey_id, user_id, journey_id, status, progress, assigned_at, completed_at, updated_at)
        VALUES 
            (gen_random_uuid(), $1, $2, $3, $4, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP)
    """
    try:
        await execute_query(
          assign_journey_query, user_id, journey_id, "not_started", 0
        )
    except Exception as e:
        print(f"Error asignando journey al usuario {user_id}: {e}")
        return
    
    read_journey_courses_query = """
        SELECT course_id, is_mandatory FROM conversaconfig.journey_courses WHERE journey_id = $1
    """
    try:
        courses = await execute_query(
            read_journey_courses_query, journey_id
        )
    except Exception as e:
        print(f"Error leyendo cursos de la journey {journey_id}: {e}")
        return

    for course in courses:
        assign_course_query = """
            INSERT INTO conversaconfig.user_course_assignments 
                (assignment_id, user_id, course_id, assigned_at, estimated_duration_days, is_mandatory)
            VALUES 
                (gen_random_uuid(), $1, $2, CURRENT_TIMESTAMP, 30, $3)
        """
        try:
            await execute_query(assign_course_query, user_id, course["course_id"], course["is_mandatory"])
        except Exception as e:
            print(f"Error asignando curso al usuario {user_id}: {e}")
            return
    return True



async def register_employee(
    company_id: str, name: str, last_name: str, email: str, role: str, journey_id: Optional[str] = None
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
            if journey_id:
                _ = await assign_courses_to_user(str(result["user_id"]), journey_id)
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
        UPDATE conversaaccesses.company_codes 
        SET current_uses = current_uses + $1 
        WHERE code = $2
    """
    await execute_query(query, count, code)


def send_welcome_email(to_email: str, name: str, temp_password: str, company_name: str):
    """
    Send a welcome email to a newly registered employee with their temp credentials.
    Uses SMTP (Office 365). Logo is embedded inline from logo_new.png.
    Fails silently (logs error) so a mail failure doesn't block user creation.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"⚠️ SMTP not configured — skipping email to {to_email}")
        return

    subject = f"Bienvenido a Conversa — Tu acceso a la plataforma"

    html_body = f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f9;padding:40px 0;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

              <!-- HEADER -->
              <tr>
                <td style="background-color:#ffffff;padding:32px 40px;text-align:center;border-bottom:3px solid #242b5d;">
                  <img src="cid:logo_conversa" alt="Conversa" style="height:90px;display:block;margin:0 auto;" />
                </td>
              </tr>

              <!-- HERO -->
              <tr>
                <td style="background-color:#447aa8;padding:24px 40px;text-align:center;">
                  <p style="margin:0;color:#ffffff;font-size:18px;font-weight:600;letter-spacing:0.3px;">
                    Bienvenido/a a la plataforma de entrenamiento con IA
                  </p>
                </td>
              </tr>

              <!-- BODY -->
              <tr>
                <td style="padding:40px;">
                  <p style="margin:0 0 16px;font-size:16px;color:#1a1a2e;">
                    Hola <strong>{name}</strong>,
                  </p>
                  <p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">
                    <strong>{company_name}</strong> te ha dado acceso a <strong>Conversa</strong>.
                    A continuación encontrarás tus credenciales de acceso provisionales.
                  </p>

                  <!-- CREDENTIALS BOX -->
                  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;border-left:4px solid #447aa8;border-radius:6px;margin-bottom:24px;">
                    <tr>
                      <td style="padding:20px 24px;">
                        <p style="margin:0 0 8px;font-size:13px;color:#888;text-transform:uppercase;letter-spacing:0.8px;font-weight:600;">Tus credenciales</p>
                        <p style="margin:0 0 6px;font-size:15px;color:#1a1a2e;">
                          <span style="color:#888;">Email:</span>&nbsp;&nbsp;<strong>{to_email}</strong>
                        </p>
                        <p style="margin:0;font-size:15px;color:#1a1a2e;">
                          <span style="color:#888;">Contraseña temporal:</span>&nbsp;&nbsp;
                          <strong style="font-family:monospace;background:#fff;padding:3px 8px;border-radius:4px;border:1px solid #d1d5db;">{temp_password}</strong>
                        </p>
                      </td>
                    </tr>
                  </table>

                  <p style="margin:0 0 28px;font-size:14px;color:#666;line-height:1.6;">
                    Por seguridad, te recomendamos cambiar tu contraseña tras el primer inicio de sesión.
                  </p>

                  <!-- CTA BUTTON -->
                  <table cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="background-color:#242b5d;border-radius:8px;">
                        <a href="https://conversa-app.es/login"
                           style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;letter-spacing:0.3px;">
                          Iniciar sesión →
                        </a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- FOOTER -->
              <tr>
                <td style="background-color:#f9fafb;padding:24px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;font-size:12px;color:#9ca3af;line-height:1.6;">
                    Este correo ha sido enviado automáticamente por Conversa.<br/>
                    Si no esperabas este mensaje, puedes ignorarlo con seguridad.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email

    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_body, "html"))

    # Embed logo inline
    logo_path = Path(__file__).parent.parent.parent / "logo_new.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo = MIMEImage(f.read())
            logo.add_header("Content-ID", "<logo_conversa>")
            logo.add_header("Content-Disposition", "inline", filename="logo_new.png")
            msg.attach(logo)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"✅ Email enviado a {to_email}")
    except Exception as e:
        print(f"❌ Error enviando email a {to_email}: {e}")
