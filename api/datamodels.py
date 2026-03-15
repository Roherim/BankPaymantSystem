from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import re
import uuid



class PaymentStatus(BaseModel):
    id:int
    name: str

class Order(BaseModel):
    id: uuid.UUID
    amount: int
    order_date: datetime
    status_id: int
    customer_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    payments: Optional[List] = []
    
class Payment(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    payment_type_id: int
    amount: float
    payment_date: datetime
    status_id: int
    external_id: str
    created_at: datetime
    updated_at: datetime

class CreateBankPaymentRequest(BaseModel):
    order_number: str
    amount: int

class CreateBankPaymentResponse(BaseModel):
    bank_payment_id: str
    status: str

class CheckBankPaymentRequest(BaseModel):
    payment_id: str

class CheckBankPaymentResponse(BaseModel):
    bank_payment_id: str
    status: str
    amount: int
    payment_date: Optional[datetime] = None

class PaymentResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    amount: int
    status: str
    external_id: Optional[str] = None

class RefundResponse(BaseModel):
    id: uuid.UUID
    original_payment_id: uuid.UUID
    amount: int
    status: str
    