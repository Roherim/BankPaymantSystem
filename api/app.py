from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import uuid

from api.datamodels import PaymentResponse, RefundResponse, Order
from api.payment_service import PaymentService
from api.bank_api.bank_api import BankAPI
from api.dbfuncs import get_db_cursor, OrderRepository, PaymentRepository

app = FastAPI(title="Payment Service API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bank_client = BankAPI()
payment_service = PaymentService(bank_client)

@app.post("/orders/{order_id}/payments", response_model=PaymentResponse)
async def create_payment_endpoint(order_id: str, payment_type: str, amount: int):
    return await payment_service.create_payment(order_id, payment_type, amount)

@app.post("/payments/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment_endpoint(payment_id: str, amount: Optional[int] = None):
    return await payment_service.refund_payment(payment_id, amount)

@app.get("/orders/{order_id}", response_model=Order)
async def get_order_endpoint(order_id: str):
    with get_db_cursor() as cursor:
        order_repository = OrderRepository(cursor)
        payment_repository = PaymentRepository(cursor)
        
        order = order_repository.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        payments = payment_repository.get_by_order(order_id)
        
        return Order(
            id=order["id"],
            amount=order["amount"],
            order_date=order["created_at"],
            status_id=order["status_id"],
            customer_id=order.get("customer_id"),
            created_at=order["created_at"],
            updated_at=order["updated_at"],
            payments=payments
        )

@app.get("/health")
async def health_check():
    return {"status": "ok"}