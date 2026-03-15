import asyncio
import logging
from datetime import datetime, timedelta
from api.bank_api.bank_api import BankAPI
from api.dbfuncs import get_db_cursor, PaymentRepository, PaymentStatusRepository, OrderRepository, OrderStatusRepository, PaymentTypeRepository
from api.config import config as conf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentWorker:
    def __init__(self, bank_client: BankAPI):
        self.bank_client = bank_client
        self.is_running = False
    
    async def check_pending_payments(self):
        while self.is_running:
            try:
                with get_db_cursor() as cursor:
                    payment_repository = PaymentRepository(cursor)
                    payment_status_repository = PaymentStatusRepository(cursor)
                    order_repository = OrderRepository(cursor)
                    order_status_repository = OrderStatusRepository(cursor)
                    payment_type_repository = PaymentTypeRepository(cursor)
                    
                    pending_status_id = payment_status_repository.get_by_name(conf.PAYMENT_STATUS_PENDING)
                    acquiring_type_id = payment_type_repository.get_by_name(conf.PAYMENT_TYPE_ACQUIRING)
                    
                    five_minutes_ago = datetime.now() - timedelta(minutes=5)
                    
                    pending_payments = payment_repository.get_pending_acquiring_payments(acquiring_type_id, pending_status_id, five_minutes_ago)
                    
                    for payment in pending_payments:
                        try:
                            bank_status = await self.bank_client.check_payment(payment["external_id"])
                            
                            if bank_status.status == "completed":
                                completed_status_id = payment_status_repository.get_by_name(conf.PAYMENT_STATUS_COMPLETED)
                                payment_status_repository.change(payment["id"], completed_status_id)
                                
                                order_id = payment["order_id"]
                                order_amount = order_repository.get_amount(order_id)
                                payments_sum = payment_repository.get_sum_by_order(order_id)
                                
                                if payments_sum >= order_amount:
                                    paid_status_id = order_status_repository.get_by_name(conf.ORDER_STATUS_PAID)
                                    order_status_repository.change(order_id, paid_status_id)
                                elif payments_sum > 0:
                                    partial_status_id = order_status_repository.get_by_name(conf.ORDER_STATUS_PARTIALLY_PAID)
                                    order_status_repository.change(order_id, partial_status_id)
                                
                                logger.info(f"Payment {payment['id']} completed via bank check")
                            
                            elif bank_status.status in ["failed", "cancelled"]:
                                cancelled_status_id = payment_status_repository.get_by_name(conf.PAYMENT_STATUS_CANCELLED)
                                payment_status_repository.change(payment["id"], cancelled_status_id)
                                logger.info(f"Payment {payment['id']} cancelled via bank check")
                                
                        except Exception as e:
                            logger.error(f"Error checking payment {payment['id']}: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
            
            await asyncio.sleep(300)
    
    async def start(self):
        self.is_running = True
        logger.info("Payment worker started")
        await self.check_pending_payments()
    
    async def stop(self):
        self.is_running = False
        logger.info("Payment worker stopped")

async def run_worker():
    bank_client = BankAPI()
    worker = PaymentWorker(bank_client)
    await worker.start()

if __name__ == "__main__":
    asyncio.run(run_worker())