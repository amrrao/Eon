import stripe  
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from database import database
from dependancies import get_current_user
from pydantic import BaseModel

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter()

PRICE_IDS = {
    1: os.getenv("STRIPE_PRICE_1_CREDIT"),
    100: os.getenv("STRIPE_PRICE_100_CREDITS"),
    500: os.getenv("STRIPE_PRICE_500_CREDITS"),
}

class PurchaseRequest(BaseModel):
    credits: int
    return_path: str = "/profile"

@router.post("/purchase")
async def purchase_credits(body: PurchaseRequest, user = Depends(get_current_user)):
    customer_row = await database.fetch_one(
        "SELECT stripe_customer_id FROM users WHERE id = :id",
        {"id": str(user.id)}
    )
    if customer_row["stripe_customer_id"]:
        customer_id = customer_row["stripe_customer_id"]
    else:
        customer = stripe.Customer.create(email=user.email)
        customer_id = customer.id
        await database.execute(
            "UPDATE users SET stripe_customer_id = :stripe_customer_id WHERE id = :id",
            {"stripe_customer_id": customer_id, "id": str(user.id)}
        )

    if body.credits in PRICE_IDS:
        price_id = PRICE_IDS[body.credits]
        quantity = 1
    else:
        price_id = PRICE_IDS[1]
        quantity = body.credits
    
    session = stripe.checkout.Session.create(
        customer = customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": quantity}],
        mode="payment",
        success_url=f"http://localhost:3000{body.return_path}?payment=success",
        cancel_url=f"http://localhost:3000{body.return_path}",
        metadata={"user_id": str(user.id), "credits": str(body.credits)}
    )

    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        existing = await database.fetch_one(
            "SELECT id FROM processed_events WHERE stripe_event_id = :id",
            {"id": event["id"]}
        )
        if existing:
            return {"status": "already processed"}

        user_id = session["metadata"]["user_id"]
        credits = int(session["metadata"]["credits"])

        await database.execute(
            "UPDATE users SET credits = credits + :credits WHERE id = :id",
            {"credits": credits, "id": user_id}
        )
        await database.execute(
            "INSERT INTO processed_events (stripe_event_id) VALUES (:id)",
            {"id": event["id"]}
        )

    return {"status": "success"}