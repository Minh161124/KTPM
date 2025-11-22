# db_connector.py
import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self, host='localhost', user='root', password='', database='btl_ai'):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'auth_plugin': 'mysql_native_password' 
        }
        self.conn = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            if self.conn.is_connected():
                print("Kết nối MySQL thành công")
                return self.conn
        except Error as e:
            print(f"Lỗi khi kết nối tới MySQL: {e}")
            return None

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("Đã ngắt kết nối MySQL")

    def fetch_employees(self, search="", role="Tất cả chức vụ", limit=10, page=1):
        """
        Lấy danh sách nhân viên với tìm kiếm, lọc và phân trang
        """
        conn = self.connect()
        if not conn:
            return [], 0

        cursor = conn.cursor()
        
        try:

            offset = (page - 1) * limit
            where_clauses = []
            params = []

            if search:

                where_clauses.append("(ma_nv LIKE %s OR ho_ten LIKE %s OR sdt LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if role != "Tất cả chức vụ":
                where_clauses.append("chuc_vu = %s")
                params.append(role)

            where_sql = " AND ".join(where_clauses)
            if where_sql:
                where_sql = " WHERE " + where_sql

            count_query = f"SELECT COUNT(*) FROM employees {where_sql}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]

            query = f"""
                SELECT id, ma_nv, ho_ten, tai_khoan, gioi_tinh, sdt, chuc_vu, FORMAT(luong, 0) 
                FROM employees 
                {where_sql} 
                ORDER BY id DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [limit, offset])
            results = cursor.fetchall()
            
            return results, total_records

        except Error as e:
            print(f"Lỗi khi lấy dữ liệu nhân viên: {e}")
            return [], 0
        finally:
            cursor.close()
            self.disconnect()

    def get_employee_by_id(self, employee_id):
        conn = self.connect()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Lỗi khi lấy thông tin nhân viên: {e}")
            return None
        finally:
            cursor.close()
            self.disconnect()

    def add_employee(self, data):
        conn = self.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:

            conn.start_transaction()

            query_emp = """
                INSERT INTO employees (ma_nv, ho_ten, tai_khoan, mat_khau, gioi_tinh, sdt, chuc_vu, luong) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_emp, (data['ma_nv'], data['ho_ten'], data['tai_khoan'], 
                                   data['mat_khau'], data['gioi_tinh'], data['sdt'], 
                                   data['chuc_vu'], data['luong']))

            query_user = """
                INSERT INTO users (email, password, role) 
                VALUES (%s, %s, %s)
            """
            cursor.execute(query_user, (data['tai_khoan'], data['mat_khau'], data['chuc_vu']))
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi thêm nhân viên/user: {e}")
            conn.rollback() 
            return False
        finally:
            cursor.close()
            self.disconnect()

    def update_employee(self, employee_id, data):
        conn = self.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            conn.start_transaction()
            cursor.execute("SELECT tai_khoan FROM employees WHERE id = %s", (employee_id,))
            old_row = cursor.fetchone()
            old_email = old_row[0] if old_row else data['tai_khoan']

            if data['mat_khau']:
                query_emp = """
                    UPDATE employees SET ma_nv=%s, ho_ten=%s, tai_khoan=%s, mat_khau=%s, 
                                         gioi_tinh=%s, sdt=%s, chuc_vu=%s, luong=%s 
                    WHERE id = %s
                """
                params_emp = (data['ma_nv'], data['ho_ten'], data['tai_khoan'], data['mat_khau'],
                          data['gioi_tinh'], data['sdt'], data['chuc_vu'], data['luong'], employee_id)

                query_user = """
                    UPDATE users SET email=%s, password=%s, role=%s 
                    WHERE email=%s
                """
                params_user = (data['tai_khoan'], data['mat_khau'], data['chuc_vu'], old_email)

            else: 
                query_emp = """
                    UPDATE employees SET ma_nv=%s, ho_ten=%s, tai_khoan=%s, gioi_tinh=%s, 
                                         sdt=%s, chuc_vu=%s, luong=%s 
                    WHERE id = %s
                """
                params_emp = (data['ma_nv'], data['ho_ten'], data['tai_khoan'], data['gioi_tinh'], 
                          data['sdt'], data['chuc_vu'], data['luong'], employee_id)

                query_user = """
                    UPDATE users SET email=%s, role=%s 
                    WHERE email=%s
                """
                params_user = (data['tai_khoan'], data['chuc_vu'], old_email)

            cursor.execute(query_emp, params_emp)
            cursor.execute(query_user, params_user)

            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi cập nhật nhân viên/user: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.disconnect()

    def delete_employee(self, employee_id):
        conn = self.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            conn.start_transaction()

            cursor.execute("SELECT tai_khoan FROM employees WHERE id = %s", (employee_id,))
            row = cursor.fetchone()
            
            if row:
                email_to_delete = row[0]

                cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))

                cursor.execute("DELETE FROM users WHERE email = %s", (email_to_delete,))

            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi xóa nhân viên: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.disconnect()