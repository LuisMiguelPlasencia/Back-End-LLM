import os
import json
import stripe
from datetime import datetime
from uuid import uuid4
from decimal import Decimal
from typing import Optional, Dict, List
from pydantic import BaseModel
from fastapi import HTTPException
from .db import execute_query, execute_query_one 


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_SETUP_FEE_PRICE_ID = os.getenv("STRIPE_SETUP_FEE_PRICE_ID") 

class CheckoutRequest(BaseModel):
    company_id: str          # ID de la empresa en tu sistema (company_info)
    user_email: str          # Email del administrador que paga
    user_name: str           # Nombre del administrador
    plan_id: str             # UUID de tu tabla billing_plans
    payment_method_id: str   # Token 'pm_...' que viene del Frontend
    num_users: int           # Slider de usuarios
    num_custom_courses: int  # Slider de cursos
    coupon_code: Optional[str] = None

class StripeCheckoutService:
    
    @staticmethod
    async def process_checkout(data: CheckoutRequest):
        """
        Orquesta todo el flujo: Cliente Stripe -> Suscripción Stripe -> Persistencia BBDD Local
        """
        try:
            # ---------------------------------------------------------
            # 1. VALIDACIÓN PREVIA Y OBTENCIÓN DE DATOS
            # ---------------------------------------------------------
            
            # A. Obtener detalles del Plan de la BBDD
            plan_query = """
                SELECT plan_id, base_price_per_user, product_stripe_id 
                FROM conversapay.billing_plans 
                WHERE plan_id = $1 AND is_active = TRUE
            """
            # Asumimos que product_stripe_id guarda el 'price_id' recurrente de Stripe (ej: price_H5gg...)
            db_plan = await execute_query_one(plan_query, data.plan_id)
            
            if not db_plan:
                raise HTTPException(status_code=404, detail="El plan seleccionado no existe o no está activo.")

            stripe_price_id_recurrente = db_plan['product_stripe_id']
            base_price = Decimal(str(db_plan['base_price_per_user']))

            # B. Validar Cupón (Si existe) y obtener ID de Stripe si aplica
            stripe_coupon_id = None
            db_coupon_id = None
            
            if data.coupon_code:
                coupon_query = """
                    SELECT external_coupon_id, discount_percentage 
                    FROM conversapay.coupons 
                    WHERE coupon_id = $1 AND is_active = TRUE 
                    AND (valid_until > CURRENT_TIMESTAMP OR valid_until IS NULL)
                """
                db_coupon = await execute_query_one(coupon_query, data.coupon_code)
                if db_coupon:
                    db_coupon_id = data.coupon_code  
                    stripe_coupon_id = db_coupon['external_coupon_id']

            # ---------------------------------------------------------
            # 2. INTERACCIÓN CON STRIPE (La parte crítica)
            # ---------------------------------------------------------

            # A. Obtener o Crear Cliente (Idempotencia)
            customers = await stripe.Customer.list_async(email=data.user_email, limit=1)
            if customers.data:
                customer_id = customers.data[0].id
            else:
                customer = await stripe.Customer.create_async(
                    email=data.user_email,
                    name=data.user_name,
                    metadata={"company_id": data.company_id}
                )
                customer_id = customer.id

            
            # ==============================================================================
            # B. ASOCIAR MÉTODO DE PAGO
            # ==============================================================================
            
            # Paso 1: Determinar el ID inicial (Token o PM)
            pm_to_attach = data.payment_method_id

            if data.payment_method_id.startswith("tok_"):
                print(f"🔄 Convirtiendo Token {data.payment_method_id} a PaymentMethod...")
                pm_object = await stripe.PaymentMethod.create_async(
                    type="card",
                    card={"token": data.payment_method_id}
                )
                pm_to_attach = pm_object.id

            # Paso 2: Adjuntar y CAPTURAR el objeto resultante
            # IMPORTANTE: Al adjuntar 'pm_card_visa', Stripe devuelve un NUEVO objeto con un ID distinto.
            attached_pm = await stripe.PaymentMethod.attach_async(
                pm_to_attach,
                customer=customer_id
            )
            
            # Actualizamos nuestra variable con el ID FINAL Y REAL que está en Stripe
            final_real_pm_id = attached_pm.id 
            print(f"✅ PaymentMethod adjuntado correctamente: {final_real_pm_id}")

            # Paso 3: Establecer como default usando el ID REAL
            await stripe.Customer.modify_async(
                customer_id,
                invoice_settings={"default_payment_method": final_real_pm_id}
            )

            # C. Construir los Ítems de la Suscripción
            # Ítem 1: Suscripción Recurrente (Usuarios)
            subscription_items = [
                {"price": stripe_price_id_recurrente, "quantity": data.num_users}
            ]
            
            # Ítem 2: Setup Fee (Pago Único). 
            # En Stripe, para cobrar algo una sola vez DENTRO de una suscripción, 
            # usamos 'add_invoice_items'.
            add_invoice_items = []
            if data.num_custom_courses > 0:
                # Calculamos cantidad total de setups: usuarios * cursos
                total_setup_units = data.num_users * data.num_custom_courses
                add_invoice_items.append({
                    "price": STRIPE_SETUP_FEE_PRICE_ID, # ID del precio de $50 en Stripe
                    "quantity": total_setup_units
                })

            # D. Crear la Suscripción
            discounts_config = []
            if stripe_coupon_id:
                discounts_config.append({"coupon": stripe_coupon_id})

            # D. Crear la Suscripción (CORREGIDO)
            subscription = await stripe.Subscription.create_async(
                customer=customer_id,
                items=subscription_items,
                add_invoice_items=add_invoice_items, 
                
                # CAMBIO AQUÍ: Usamos 'discounts' en lugar de 'coupon'
                discounts=discounts_config, 
                
                #payment_behavior="default_incomplete", 
                payment_behavior="error_if_incomplete",
                payment_settings={"save_default_payment_method": "on_subscription"},
                expand=["latest_invoice.payment_intent"],
                metadata={
                    "company_id": data.company_id,
                    "plan_internal_id": data.plan_id
                }
            )

            # D. Crear la Suscripción
            subscription = await stripe.Subscription.create_async(
                customer=customer_id,
                items=subscription_items,
                add_invoice_items=add_invoice_items, 
                discounts=discounts_config, 
                payment_behavior="default_incomplete", 
                payment_settings={"save_default_payment_method": "on_subscription"},
                expand=["latest_invoice.payment_intent"], # Expandimos datos clave
                metadata={
                    "company_id": data.company_id,
                    "plan_internal_id": data.plan_id
                }
            )

            # ---------------------------------------------------------
            # 3. PERSISTENCIA BLINDADA (Conversión a Dict)
            # ---------------------------------------------------------
            
            # 1. Convertimos TODO a diccionario de Python puro para evitar errores de librería
            # Nota: Si tu versión de librería es muy nueva, a veces devuelve dict directamente.
            # Este truco asegura que siempre trabajemos con dict.
            if hasattr(subscription, 'to_dict'):
                sub_dict = subscription.to_dict()
            else:
                sub_dict = dict(subscription)

            # ---------------------------------------------------------
            # 2. EXTRACCIÓN BLINDADA DE DATOS (Soporta objetos y IDs)
            # ---------------------------------------------------------
            sub_id_stripe = sub_dict.get('id')
            current_period_start = sub_dict.get('current_period_start')
            current_period_end = sub_dict.get('current_period_end')
            status_stripe = sub_dict.get('status')
            
            # A. Gestión de la Factura (Invoice)
            invoice_stripe = sub_dict.get('latest_invoice')
            if isinstance(invoice_stripe, str):
                invoice_stripe = {} 
            elif hasattr(invoice_stripe, 'to_dict'):
                invoice_stripe = invoice_stripe.to_dict()
            elif not isinstance(invoice_stripe, dict):
                invoice_stripe = {}

            # B. Gestión del Intento de Pago (Payment Intent) - LA CLAVE
            payment_intent = invoice_stripe.get('payment_intent')
            
            pi_id = "pending_creation"
            client_secret = None

            # CASO 1: Stripe nos devolvió el objeto completo (Ideal)
            if isinstance(payment_intent, dict):
                pi_id = payment_intent.get('id')
                client_secret = payment_intent.get('client_secret')
            
            # CASO 2: Stripe nos devolvió solo el ID "pi_..." (El error que tenías)
            elif isinstance(payment_intent, str):
                pi_id = payment_intent
                try:
                    # Hacemos una llamada rápida a Stripe para recuperar el secreto que falta
                    pi_obj = await stripe.PaymentIntent.retrieve_async(pi_id)
                    client_secret = pi_obj.client_secret
                except Exception as e:
                    print(f"⚠️ No se pudo recuperar el PaymentIntent {pi_id}: {e}")
                    client_secret = None
            
            # CASO 3: Es None (Aún no se ha generado)
            else:
                # Mantenemos los valores por defecto
                pass

            amount_total = Decimal(invoice_stripe.get('total', 0)) / 100
            amount_subtotal = Decimal(invoice_stripe.get('subtotal', 0)) / 100
            
            # URLs
            hosted_invoice_url = invoice_stripe.get('hosted_invoice_url')

            # ---------------------------------------------------------
            # 4. INSERT SQL (Usando las variables limpias)
            # ---------------------------------------------------------

            # A. Insertar en SUSCRIPCIONES
            insert_sub_query = """
                INSERT INTO conversapay.subscriptions (
                    company_id, 
                    plan_id, 
                    status, 
                    current_period_start, 
                    current_period_end, 
                    users_limit, 
                    custom_courses_limit,
                    external_subscription_id 
                ) VALUES ($1, $2, $3, to_timestamp($4), to_timestamp($5), $6, $7, $8)
                RETURNING subscription_id
            """
            
            sub_row = await execute_query_one(insert_sub_query, 
                data.company_id,
                data.plan_id,
                status_stripe,
                current_period_start, # Variable segura (int o float)
                current_period_end,   # Variable segura (int o float)
                data.num_users,
                data.num_custom_courses,
                sub_id_stripe 
            )
            internal_sub_id = sub_row['subscription_id']

            # B. Insertar en INVOICES
            insert_inv_query = """
                INSERT INTO conversapay.invoices (
                    company_id,
                    subscription_id,
                    amount_total,
                    amount_subtotal,
                    coupon_id,
                    status,
                    pdf_url
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING invoice_id
            """
            
            inv_row = await execute_query_one(insert_inv_query,
                data.company_id,
                internal_sub_id,
                amount_total,
                amount_subtotal,
                db_coupon_id,
                invoice_stripe.get('status', 'open'), 
                hosted_invoice_url
            )
            internal_inv_id = inv_row['invoice_id']

            # C. Insertar en PAYMENT_TRANSACTIONS
            insert_trans_query = """
                INSERT INTO conversapay.payment_transactions (
                    invoice_id,
                    provider_transaction_id,
                    payment_method,
                    provider_response,
                    created_at
                ) VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            """
            
            # Guardamos el dict completo como JSON
            stripe_dump = json.dumps(sub_dict)
            
            await execute_query(insert_trans_query,
                internal_inv_id,
                pi_id, 
                "card", 
                stripe_dump 
            )

            return {
                "status": "success",
                "subscription_id": internal_sub_id,
                "client_secret": client_secret,
                "stripe_status": status_stripe
            }

        except stripe.error.StripeError as e:
            # Error de Stripe (Tarjeta rechazada, API caída)
            raise HTTPException(status_code=400, detail=f"Error en pasarela de pago: {e.user_message}")
        except Exception as e:
            # Error de nuestra base de datos o lógica
            # Aquí deberías tener un log crítico
            print(f"CRITICAL ERROR IN CHECKOUT: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno procesando la suscripción")