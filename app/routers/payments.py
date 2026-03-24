# ---------------------------------------------------------------------------
# Payments / Billing router
# ---------------------------------------------------------------------------

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.payments_stripe_service import CheckoutRequest, StripeCheckoutService

router = APIRouter(prefix="/billing", tags=["Billing & Payments"])


@router.post("/checkout", status_code=201)
async def create_checkout_session(request: CheckoutRequest):
    """Process a full Stripe checkout (customer → subscription → persistence)."""
    try:
        result = await StripeCheckoutService.process_checkout(request)
        return result
    except HTTPException:
        raise  # Re-raise structured HTTP errors from the service layer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
