import mysql.connector
from mysql.connector import Error

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
        """Lấy thông tin mới nhất của thành viên"""
        conn = self.get_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True)
            sql = "SELECT * FROM members WHERE id = %s"
            cursor.execute(sql, (member_id,))
            return cursor.fetchone()
        finally:
            if conn.is_connected(): conn.close()

    def get_menu(self):
        """Trả về danh sách dịch vụ (có thể lấy từ DB hoặc hardcode demo)"""
        # Trong thực tế nên tạo bảng 'products', ở đây mình demo list
        return [
            {"name": "Sting dâu", "price": 10000, "category": "Nước uống"},
            {"name": "Coca Cola", "price": 10000, "category": "Nước uống"},
            {"name": "Mì tôm trứng", "price": 15000, "category": "Đồ ăn"},
            {"name": "Cơm rang dưa bò", "price": 30000, "category": "Đồ ăn"},
            {"name": "Thẻ nạp 20k", "price": 20000, "category": "Thẻ"},
        ]

    def order_service(self, member_id, item_name, price):
        """Trừ tiền tài khoản và ghi log"""
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            
            # 1. Kiểm tra số dư
            cursor.execute("SELECT balance FROM members WHERE id = %s", (member_id,))
            row = cursor.fetchone()
            if not row or row[0] < price:
                return False # Không đủ tiền

            # 2. Trừ tiền
            new_balance = row[0] - price
            cursor.execute("UPDATE members SET balance = %s WHERE id = %s", (new_balance, member_id))

            # 3. Ghi log (vào bảng logs hoặc orders_log)
            # Giả sử dùng bảng logs có sẵn: machine_name lưu tên món, amount lưu giá
            cursor.execute("INSERT INTO logs (machine_name, amount) VALUES (%s, %s)", 
                           (f"Order: {item_name}", price))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi order: {e}")
            conn.rollback()
            return False
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