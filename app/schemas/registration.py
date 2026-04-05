# Pydantic models for bulk user registration via company codes
# Validates input for code verification and employee profile creation

from pydantic import BaseModel, EmailStr
from typing import List, Optional


class ValidateCodeRequest(BaseModel):
    """Request to validate a company registration code"""
    code: str


class ValidateCodeResponse(BaseModel):
    """Response after validating a company code"""
    valid: bool
    company_name: Optional[str] = None
    remaining_uses: Optional[int] = None
    message: str


class EmployeeInput(BaseModel):
    """Single employee data for bulk registration"""
    name: str
    last_name: str
    email: EmailStr
    role: str = "employee"


class BulkRegisterRequest(BaseModel):
    """Request to register multiple employees using a company code"""
    code: str
    employees: List[EmployeeInput]


class EmployeeResult(BaseModel):
    """Result of a single employee registration attempt"""
    email: str
    success: bool
    message: str


class BulkRegisterResponse(BaseModel):
    """Response after bulk registration attempt"""
    total_submitted: int
    total_created: int
    total_failed: int
    results: List[EmployeeResult]
