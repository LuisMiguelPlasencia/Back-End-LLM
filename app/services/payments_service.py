# Conversation service for managing user conversations
# Handles conversation creation and retrieval from conversaApp.conversations
# Note: course_id is accepted in payload but not stored (no field in table)

from tokenize import String
from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional
from decimal import Decimal
from pydantic import BaseModel
from fastapi import HTTPException


class InvestmentSimulation(BaseModel):
    plan_id: str
    num_users: int
    num_custom_courses: int
    coupon_code: Optional[str] = None


async def get_billing_plans():
    """Return the billing plans for the selectors in the front"""
    query = "SELECT plan_id, name, base_price_per_user FROM conversapay.billing_plans WHERE is_active = TRUE"
    results = await execute_query(query)
    return [dict(r) for r in results]

async def validate_coupon(code: str):
    """Validate the coupon"""
    query = """
        SELECT discount_percentage, valid_until 
        FROM conversapay.coupons 
        WHERE coupon_id = $1 AND is_active = TRUE AND (valid_until > CURRENT_TIMESTAMP OR valid_until IS NULL)
    """
    results = await execute_query(query, code)
    return [dict(r) for r in results]

async def simulate_investment(data: InvestmentSimulation):
    # 1. Obtener datos del plan de la DB
    plan_query = "SELECT base_price_per_user FROM conversapay.billing_plans WHERE plan_id = $1"
    plan = await execute_query(plan_query, data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    price_per_user = Decimal(str(plan[0]['base_price_per_user']))
    setup_fee_unit = Decimal("50.00") # Hardcoded o de una tabla de variables globales

    # 2. Cálculos Base
    monthly_sub = data.num_users * price_per_user
    setup_total = data.num_custom_courses * data.num_users * setup_fee_unit
    subtotal = monthly_sub + setup_total
    
    discount = Decimal("0.00")
    
    # 3. Validación de Cupón en Base de Datos
    if data.coupon_code:
        coupon_query = """
            SELECT discount_percentage 
            FROM conversapay.coupons 
            WHERE coupon_id = $1 
              AND is_active = TRUE 
              AND (valid_until > CURRENT_TIMESTAMP OR valid_until IS NULL)
        """
        coupon_res = await execute_query(coupon_query, data.coupon_code)
        
        if coupon_res:
            pct = Decimal(str(coupon_res[0]['discount_percentage']))
            discount = subtotal * (pct / Decimal("100"))
        else:
            # Si el usuario mandó un código pero no es válido, podemos optar por
            # ignorarlo o devolver un error. Aquí lanzamos error para avisar al usuario.
            raise HTTPException(status_code=400, detail="El cupón ingresado no es válido")

    total = subtotal - discount

    return {
        "summary": {
            "monthly_subscription": monthly_sub,
            "setup_courses": setup_total,
            "discount": discount,
            "subtotal": subtotal,
            "total_to_pay_today": total,
            "next_monthly_payment": monthly_sub
        }
    }