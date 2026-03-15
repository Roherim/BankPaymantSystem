from fastapi import HTTPException
from api.datamodels import PaymentResponse, RefundResponse
from api.dbfuncs import get_db_cursor, PaymentRepository, OrderStatusRepository, OrderRepository, PaymentStatusRepository, PaymentTypeRepository
from api.config import config as conf
from api.bank_api.bank_api import BankAPI
from typing import Optional
import uuid

class PaymentService:
    def __init__(self, bank_client: BankAPI):
        self.bank_client = bank_client
    
    async def create_payment(self, order_id: str, payment_type: str, amount: int) -> PaymentResponse:
        with get_db_cursor() as cursor:
            order_repository = OrderRepository(cursor)
            payment_repository = PaymentRepository(cursor)
            order_status_repository = OrderStatusRepository(cursor)
            payment_status_repository = PaymentStatusRepository(cursor)
            payment_type_repository = PaymentTypeRepository(cursor)
            
            current_order = order_repository.get_by_id(order_id)
            
            if not current_order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            if amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be positive")
            
            payment_type_id = payment_type_repository.get_by_name(payment_type)
            if not payment_type_id:
                raise HTTPException(status_code=400, detail=f"Invalid payment type: {payment_type}")
            
            current_order_amount = order_repository.get_amount(order_id)
            payments_amounts = payment_repository.get_sum_by_order(order_id)
            
            if payments_amounts + amount > current_order_amount:
                remaining = current_order_amount - payments_amounts
                raise HTTPException(
                    status_code=400, 
                    detail=f"Amount exceeds order total. Max remaining: {remaining}"
                )
            
            if payment_type == conf.PAYMENT_TYPE_ACQUIRING:
                bank_result = await self.bank_client.create_payment(order_id, amount)
                status_id = payment_status_repository.get_by_name(conf.PAYMENT_STATUS_PENDING)
                external_id = bank_result.bank_payment_id
            else:
                status_id = payment_status_repository.get_by_name(conf.PAYMENT_STATUS_COMPLETED)
                external_id = None
            
            payment = payment_repository.create(
                order_id=order_id,
                payment_type_id=payment_type_id,
                amount=amount,
                status_id=status_id,
                external_id=external_id
            )
            
            new_total = payments_amounts + amount
            if new_total < current_order_amount:
                new_status_id = order_status_repository.get_by_name(conf.ORDER_STATUS_PARTIALLY_PAID)
            else:
                new_status_id = order_status_repository.get_by_name(conf.ORDER_STATUS_PAID)
            
            order_status_repository.change(order_id, new_status_id)
            
            status_name = payment_status_repository.get_by_id(status_id)
            
            return PaymentResponse(
                id=payment["id"],
                order_id=payment["order_id"],
                amount=payment["amount"],
                status=status_name,
                external_id=payment.get("external_id")
            )
    
    async def refund_payment(self, payment_id: str) -> RefundResponse:
        with get_db_cursor() as cursor:
            payment_repository = PaymentRepository(cursor)
            order_repository = OrderRepository(cursor)
            order_status_repository = OrderStatusRepository(cursor)
            payment_status_repository = PaymentStatusRepository(cursor)
            
            original_payment = payment_repository.get_by_id(payment_id)
            
            if not original_payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            completed_status_id = payment_status_repository.get_by_name(conf.PAYMENT_STATUS_COMPLETED)
            if original_payment["status_id"] != completed_status_id:
                raise HTTPException(status_code=400, detail="Only completed payments can be refunded")
            
            # Просто меняем статус
            refunded_status_id = payment_status_repository.get_by_name(conf.PAYMENT_STATUS_REFUNDED)
            payment_status_repository.change(payment_id, refunded_status_id)
            
            # Пересчитываем статус заказа
            order_id = original_payment["order_id"]
            current_order_amount = order_repository.get_amount(order_id)
            payments_amounts = payment_repository.get_sum_by_order(order_id)
            
            if payments_amounts == 0:
                new_status_id = order_status_repository.get_by_name(conf.ORDER_STATUS_UNPAID)
            elif payments_amounts < current_order_amount:
                new_status_id = order_status_repository.get_by_name(conf.ORDER_STATUS_PARTIALLY_PAID)
            else:
                new_status_id = order_status_repository.get_by_name(conf.ORDER_STATUS_PAID)
            
            order_status_repository.change(order_id, new_status_id)
            
            return RefundResponse(
                id=payment_id,
                amount=original_payment["amount"],
                status=conf.PAYMENT_STATUS_REFUNDED
            )