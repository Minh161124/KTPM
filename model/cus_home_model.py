import mysql.connector
from mysql.connector import Error
from datetime import datetime

class CustomerModel:
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "btl_ai"
        }

    def get_connection(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            if conn.is_connected():
                return conn
        except Error as e:
            print(f"Lỗi kết nối: {e}")
        return None

    def get_member_info(self, member_id):
        conn = self.get_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True)
            sql = "SELECT * FROM members WHERE id = %s"
            cursor.execute(sql, (member_id,))
            return cursor.fetchone()
        finally:
            if conn.is_connected(): conn.close()

    def get_menu_from_db(self):
        """Lấy danh sách sản phẩm từ bảng products"""
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            # Chỉ lấy những món còn hàng (so_luong > 0)
            sql = "SELECT id, ten_sp, gia, ma_dm, so_luong FROM products WHERE so_luong > 0 ORDER BY ma_dm"
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            print(f"Lỗi lấy menu: {e}")
            return []
        finally:
            if conn.is_connected(): conn.close()

    def send_chat_message(self, member_id, message, sender_type='CLIENT'):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO messages (member_id, sender_type, message, created_at) VALUES (%s, %s, %s, NOW())"
            cursor.execute(sql, (member_id, sender_type, message))
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi gửi tin nhắn: {e}")
            return False
        finally:
            if conn.is_connected(): conn.close()

    def get_new_messages(self, member_id, last_id=0):
        """Lấy các tin nhắn có ID lớn hơn last_id (tin mới)"""
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            sql = "SELECT * FROM messages WHERE member_id = %s AND id > %s ORDER BY created_at ASC"
            cursor.execute(sql, (member_id, last_id))
            return cursor.fetchall()
        except Error as e:
            print(f"Lỗi lấy tin nhắn: {e}")
            return []
        finally:
            if conn.is_connected(): conn.close()

    def order_service(self, member_id, product_id, item_name, price):
        conn = self.get_connection()
        if not conn: return "DB_ERROR"
        try:
            conn.start_transaction()
            cursor = conn.cursor()

            cursor.execute("SELECT balance FROM members WHERE id = %s FOR UPDATE", (member_id,))
            mem_row = cursor.fetchone()
            if not mem_row or mem_row[0] < price:
                conn.rollback()
                return "NOT_ENOUGH_MONEY"

            cursor.execute("SELECT so_luong FROM products WHERE id = %s FOR UPDATE", (product_id,))
            prod_row = cursor.fetchone()
            if not prod_row or prod_row[0] <= 0:
                conn.rollback()
                return "OUT_OF_STOCK"

            new_balance = mem_row[0] - price
            cursor.execute("UPDATE members SET balance = %s WHERE id = %s", (new_balance, member_id))

            new_qty = prod_row[0] - 1
            cursor.execute("UPDATE products SET so_luong = %s WHERE id = %s", (new_qty, product_id))

            log_desc = f"Mua: {item_name}"
            sql_log = "INSERT INTO logs (member_id, machine_name, amount, created_at) VALUES (%s, %s, %s, NOW())"
            cursor.execute(sql_log, (member_id, log_desc, -price)) 
            
            conn.commit()
            return "SUCCESS"
            
        except Error as e:
            print(f"Lỗi order: {e}")
            conn.rollback()
            return "DB_ERROR"
        finally:
            if conn.is_connected(): conn.close()
    
    def get_transaction_history(self, member_id, limit=20):
        """Lấy lịch sử CỦA RIÊNG THÀNH VIÊN ĐÓ"""
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT machine_name as content, amount, created_at 
                FROM logs 
                WHERE member_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """
            cursor.execute(sql, (member_id, limit))
            return cursor.fetchall()
        except Error as e:
            print(f"Lỗi lấy lịch sử: {e}")
            return []
        finally:
            if conn.is_connected(): conn.close()

    def update_balance_only(self, member_id, new_balance):
        conn = self.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            sql = "UPDATE members SET balance = %s WHERE id = %s"
            cursor.execute(sql, (new_balance, member_id))
            conn.commit()
        except Error as e:
            print(f"Lỗi update balance: {e}")
        finally:
            if conn.is_connected(): conn.close()

    def change_password(self, member_id, new_pass):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            # Lưu ý: Thực tế nên mã hóa mật khẩu (MD5/SHA256) trước khi lưu
            sql = "UPDATE members SET password = %s WHERE id = %s"
            cursor.execute(sql, (new_pass, member_id))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn.is_connected(): conn.close()