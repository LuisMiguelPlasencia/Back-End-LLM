# Registration routes for bulk user creation via company codes
# Public endpoints (no auth required) — access is controlled by the company code itself
#
# POST /register/validate-code → checks if code is valid and returns remaining uses
# POST /register/bulk-users    → creates employees and sends welcome emails

from fastapi import APIRouter, HTTPException
from ..schemas.registration import (
    ValidateCodeRequest,
    ValidateCodeResponse,
    BulkRegisterRequest,
    BulkRegisterResponse,
    EmployeeResult,
)
from ..services.registration_service import (
    validate_company_code,
    register_employee,
    increment_code_usage,
    send_welcome_email,
)

router = APIRouter(prefix="/register", tags=["registration"])


@router.post("/validate-code", response_model=ValidateCodeResponse)
async def validate_code(request: ValidateCodeRequest):
    """
    Validate a company registration code.
    Returns company name and remaining uses if valid.
    """
    code_info = await validate_company_code(request.code)

    if not code_info:
        return ValidateCodeResponse(
            valid=False,
            message="Código inválido, agotado o expirado",
        )

    return ValidateCodeResponse(
        valid=True,
        company_name=code_info["company_name"],
        remaining_uses=code_info["remaining_uses"],
        message="Código válido",
    )


@router.post("/bulk-users", response_model=BulkRegisterResponse)
async def bulk_register(request: BulkRegisterRequest):
    """
    Register multiple users using a company code.
    
    Flow:
    1. Re-validate the code and check remaining capacity
    2. Loop through employees, creating each in DB
    3. Send welcome email to each successfully created user
    4. Increment the code usage counter by the number of created users
    5. Return detailed results per employee
    """
    # 1. Validate code and capacity
    code_info = await validate_company_code(request.code)
    if not code_info:
        raise HTTPException(status_code=400, detail="Código inválido, agotado o expirado")

    if len(request.employees) > code_info["remaining_uses"]:
        raise HTTPException(
            status_code=400,
            detail=f"El código solo tiene {code_info['remaining_uses']} usos disponibles, "
                   f"pero se intentan registrar {len(request.employees)} empleados",
        )

    # 2. Register each employee
    results: list[EmployeeResult] = []
    created_count = 0

    for emp in request.employees:
        reg = await register_employee(
            company_id=code_info["company_id"],
            name=emp.name,
            last_name=emp.last_name,
            email=emp.email,
            role=emp.role,
        )

        if reg["success"]:
            created_count += 1
            # 3. Send welcome email (non-blocking from user creation perspective)
            send_welcome_email(
                to_email=emp.email,
                name=emp.name,
                temp_password=reg["temp_password"],
                company_name=code_info["company_name"],
            )

        results.append(EmployeeResult(
            email=emp.email,
            success=reg["success"],
            message=reg["message"],
        ))

    # 4. Increment code usage counter
    if created_count > 0:
        await increment_code_usage(request.code, created_count)

    return BulkRegisterResponse(
        total_submitted=len(request.employees),
        total_created=created_count,
        total_failed=len(request.employees) - created_count,
        results=results,
    )
