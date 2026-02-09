from fastapi import APIRouter, HTTPException
from ..services.payments_stripe_service import StripeCheckoutService, CheckoutRequest

router = APIRouter(prefix="/billing", tags=["Billing & Payments"])

@router.post("/checkout", status_code=201)
async def create_checkout_session(request: CheckoutRequest):
    """
    Simula el proceso de Checkout completo.
    - **payment_method_id**: Usa "tok_visa" para pruebas exitosas.
    - **plan_id**: Debe existir en tu tabla conversapay.billing_plans.
    """
    try:
        # Llamamos a la lógica maestra que creamos antes
        result = await StripeCheckoutService.process_checkout(request)
        return result
    except Exception as e:
        # Capturamos errores para mostrarlos claros en Swagger
        raise HTTPException(status_code=400, detail=str(e))