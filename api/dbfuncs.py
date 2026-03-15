import psycopg2
import psycopg2.extras
from contextlib import contextmanager
import datetime
from api.config import config as conf


# Утилиты для работы с БД
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=conf.DBHOST,
            port=conf.DBPORT,
            user=conf.DBUSER,
            password=conf.DBPASS,
            database=conf.DBNAME,
            client_encoding='UTF8'
        )
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_cursor():
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

class PaymentRepository:
    def __init__(self, cursor):
        self.cursor = cursor
    
    def create(self, order_id: str, payment_type_id: int, amount: int, 
               status_id: int, external_id: str = None) -> dict:
        self.cursor.execute("""
            INSERT INTO payments (
                id, order_id, payment_type_id, amount, 
                status_id, external_id, created_at, updated_at
            ) VALUES (
                uuid_generate_v4(), %s, %s, %s, %s, %s, NOW(), NOW()
            ) RETURNING id, order_id, amount, status_id
        """, (order_id, payment_type_id, amount, status_id, external_id))
        
        result = self.cursor.fetchone()
        return result if result else None  

    def get_by_id(self, payment_id: str) -> dict:
        self.cursor.execute(
            "SELECT * FROM payments WHERE id = %s",
            (payment_id,)
        )
        return self.cursor.fetchone()
    
    def get_by_order(self, order_id: str) -> list:
        self.cursor.execute(
            "SELECT * FROM payments WHERE order_id = %s",
            (order_id,)
        )
        return self.cursor.fetchall()
    
    def get_sum_by_order(self, order_id: str) -> int:
        self.cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM payments 
            WHERE order_id = %s AND status_id = 2  
        """, (order_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_pending_acquiring_payments(self, acquiring_type_id: int, pending_status_id: int, older_than: datetime) -> list:
        self.cursor.execute("""
            SELECT * FROM payments 
            WHERE status_id = %s 
            AND payment_type_id = %s
            AND created_at < %s
        """, (pending_status_id, acquiring_type_id, older_than))
        return self.cursor.fetchall()
    
class OrderStatusRepository:

    def __init__(self, cursor):
        self.cursor = cursor

    def get_by_name(self, name:str):
        self.cursor.execute(
            "SELECT id FROM order_statuses WHERE name = %s",
            (name,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def change(self, order_id: str, status_id: int):
        self.cursor.execute(
            "UPDATE orders SET status_id = %s, updated_at = NOW() WHERE id = %s",
            (status_id, order_id)
        )
        

class OrderRepository:

    def __init__(self, cursor):
        self.cursor = cursor

    def get_by_id(self, order_id: str):
        self.cursor.execute(
            "SELECT * FROM orders WHERE id = %s",
            (order_id,)
        )
        return self.cursor.fetchone()
    
    def get_amount(self, order_id: str):
        self.cursor.execute(
            "SELECT amount FROM orders WHERE id = %s",
            (order_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_status(self, order_id: str):
        self.cursor.execute(
            "SELECT status_id FROM orders WHERE id = %s",
            (order_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    

class PaymentStatusRepository:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_by_name(self, name: str) -> int:
        self.cursor.execute(
            "SELECT id FROM payment_statuses WHERE name = %s",
            (name,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_by_id(self, status_id: int) -> str:
        self.cursor.execute(
            "SELECT name FROM payment_statuses WHERE id = %s",
            (status_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def change(self, payment_id: str, status_id: int):
        self.cursor.execute(
            "UPDATE payments SET status_id = %s, updated_at = NOW() WHERE id = %s",
            (status_id, payment_id)
        )

class PaymentTypeRepository:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_by_name(self, name: str) -> int:
        self.cursor.execute(
            "SELECT id FROM payment_types WHERE name = %s",
            (name,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_by_id(self, type_id: int) -> str:
        self.cursor.execute(
            "SELECT name FROM payment_types WHERE id = %s",
            (type_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None