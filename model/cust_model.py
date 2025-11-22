# model/cust_model.py
from .db_connector import Database
from mysql.connector import Error

class CustomerModel:
    def __init__(self):
        self.db_connector = Database()
    
    # --- LẤY DANH SÁCH HỘI VIÊN ---
    def fetch_customers(self, search="", limit=10, page=1):
        conn = self.db_connector.connect()
        if not conn: return [], 0
        
        cursor = conn.cursor()
        results = []
        total_records = 0
        
        try:
            offset = (page - 1) * limit
            where_clauses = []
            params = []
            
            if search:
                # Tìm theo Username hoặc SĐT hoặc Tên
                where_clauses.append("(username LIKE %s OR ho_ten LIKE %s OR sdt LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            where_sql = " AND ".join(where_clauses)
            if where_sql: where_sql = " WHERE " + where_sql

            # Đếm tổng
            count_query = f"SELECT COUNT(*) FROM members {where_sql}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]

            # Lấy dữ liệu: ID, Username, Họ tên, SĐT, Nhóm, Số dư, Trạng thái
            query = f"""
                SELECT id, username, ho_ten, sdt, group_name, balance, status 
                FROM members {where_sql} 
                ORDER BY balance DESC, id DESC LIMIT %s OFFSET %s
            """
            # balance DESC để hiển thị khách VIP nhiều tiền lên đầu (tùy chọn)
            cursor.execute(query, params + [limit, offset])
            results = cursor.fetchall()
            
        except Error as e:
            print(f"Lỗi DB: {e}")
        finally:
            cursor.close()
            self.db_connector.disconnect()
            
        return results, total_records

    def get_customer_by_id(self, customer_id):
        conn = self.db_connector.connect()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM members WHERE id = %s", (customer_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.db_connector.disconnect()

    # --- CÁC HÀM CẬP NHẬT DỮ LIỆU ---

    def save_customer(self, data, customer_id=None):
        """Validate và lưu (Thêm mới hoặc Sửa)"""
        
        # 1. Validate cơ bản
        if not data['username']: return (False, "Tài khoản không được để trống.")
        if len(data['username']) < 4: return (False, "Tài khoản phải từ 4 ký tự.")
        if not data['ho_ten']: return (False, "Họ tên không được để trống.")

        # 2. Kiểm tra trùng Username
        if self.check_duplicate(data['username'], 'username', customer_id):
            return (False, f"Tài khoản '{data['username']}' đã tồn tại.")
            
        # 3. Kiểm tra trùng SĐT (nếu có nhập)
        if data['sdt'] and self.check_duplicate(data['sdt'], 'sdt', customer_id):
            return (False, f"SĐT '{data['sdt']}' đã được sử dụng.")

        conn = self.db_connector.connect()
        if not conn: return (False, "Lỗi kết nối CSDL.")
        cursor = conn.cursor()
        
        try:
            if customer_id:
                # UPDATE
                query = """
                    UPDATE members SET ho_ten=%s, sdt=%s, group_name=%s, password=%s, status=%s
                    WHERE id = %s
                """
                # Lưu ý: Không update username và balance ở đây (balance dùng hàm nạp tiền riêng)
                params = (data['ho_ten'], data['sdt'], data['group_name'], data['password'], data['status'], customer_id)
                cursor.execute(query, params)
                msg = "Cập nhật thông tin hội viên thành công!"
            else:
                # INSERT
                query = """
                    INSERT INTO members (username, password, ho_ten, sdt, group_name, balance, status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (data['username'], data['password'], data['ho_ten'], data['sdt'], 
                          data['group_name'], data.get('balance', 0), 1)
                cursor.execute(query, params)
                msg = "Thêm hội viên mới thành công!"

            conn.commit()
            return (True, msg)
        except Error as e:
            return (False, f"Lỗi SQL: {e}")
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def top_up_money(self, customer_id, amount):
        """Nạp tiền vào tài khoản"""
        conn = self.db_connector.connect()
        cursor = conn.cursor()
        try:
            # Cộng dồn tiền
            query = "UPDATE members SET balance = balance + %s WHERE id = %s"
            cursor.execute(query, (amount, customer_id))
            conn.commit()
            return True, "Nạp tiền thành công!"
        except Error as e:
            return False, f"Lỗi nạp tiền: {e}"
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def delete_customer(self, customer_id):
        conn = self.db_connector.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM members WHERE id = %s", (customer_id,))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def check_duplicate(self, value, field, exclude_id=None):
        conn = self.db_connector.connect()
        cursor = conn.cursor()
        query = f"SELECT id FROM members WHERE {field} = %s"
        params = [value]
        if exclude_id:
            query += " AND id != %s"
            params.append(exclude_id)
        cursor.execute(query, params)
        exists = cursor.fetchone() is not None
        cursor.close()
        self.db_connector.disconnect()
        return exists