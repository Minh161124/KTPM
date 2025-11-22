# model/prod_model.py
from .db_connector import Database
from mysql.connector import Error

class ProductModel:
    def __init__(self):
        self.db_connector = Database()

    # ==================================================
    # ::: CÁC HÀM TRUY VẤN CSDL (DATABASE QUERIES) :::
    # ==================================================
    
    def get_next_product_code(self):
        """Lấy mã SP lớn nhất hiện tại để tạo mã mới (ví dụ: SP001)"""
        conn = self.db_connector.connect()
        if not conn: return 0
        cursor = conn.cursor()
        try:
            query = "SELECT MAX(CAST(SUBSTRING(ma_sp, 3) AS UNSIGNED)) FROM products WHERE ma_sp LIKE 'SP%'"
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
        except Error as e:
            print(f"Lỗi khi lấy mã SP tiếp theo: {e}")
            return 0
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def fetch_products(self, search="", limit=10, page=1):
        """Lấy danh sách sản phẩm với tìm kiếm và phân trang"""
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
                where_clauses.append("(ma_sp LIKE %s OR ten_sp LIKE %s OR ma_vach LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
                
            where_sql = " AND ".join(where_clauses)
            if where_sql: where_sql = " WHERE " + where_sql

            count_query = f"SELECT COUNT(*) FROM products {where_sql}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]

            query = f"""
                SELECT id, ma_sp, ten_sp, ma_dm, ma_vach, FORMAT(gia, 0), FORMAT(so_luong, 0) 
                FROM products 
                {where_sql} 
                ORDER BY id DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [limit, offset])
            results = cursor.fetchall()
            
        except Error as e:
            print(f"Lỗi khi lấy dữ liệu sản phẩm: {e}")
        finally:
            cursor.close()
            self.db_connector.disconnect()
            
        return results, total_records

    def get_product_by_id(self, product_id):
        conn = self.db_connector.connect()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, ma_sp, ten_sp, ma_dm, ma_vach, gia, so_luong FROM products WHERE id = %s", (product_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Lỗi khi lấy thông tin sản phẩm: {e}")
            return None
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def add_product(self, data):
        conn = self.db_connector.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO products (ma_sp, ten_sp, ma_dm, ma_vach, gia, so_luong) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (data['ma_sp'], data['ten_sp'], data['ma_dm'], 
                                   data['ma_vach'], data['gia'], data['so_luong']))
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi thêm sản phẩm: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def update_product(self, product_id, data):
        conn = self.db_connector.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            query = """
                UPDATE products SET ten_sp=%s, ma_dm=%s, ma_vach=%s, gia=%s, so_luong=%s 
                WHERE id = %s
            """
            params = (data['ten_sp'], data['ma_dm'], data['ma_vach'], 
                      data['gia'], data['so_luong'], product_id)
            cursor.execute(query, params)
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi cập nhật sản phẩm: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def delete_product(self, product_id):
        conn = self.db_connector.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi xóa sản phẩm: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()
            
    def check_duplicate_barcode(self, ma_vach, product_id=None):
        """
        Kiểm tra xem Mã vạch đã tồn tại trong hệ thống chưa.
        product_id: ID của sản phẩm đang sửa (để bỏ qua chính nó)
        """
        conn = self.db_connector.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            query = "SELECT id FROM products WHERE ma_vach = %s"
            params = [ma_vach]
            
            if product_id:
                query += " AND id != %s"
                params.append(product_id)
                
            cursor.execute(query, params)
            if cursor.fetchone():
                return True # Đã tồn tại
            return False # Chưa tồn tại
        except Error:
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()

    # ==========================================
    # ::: HÀM LOGIC NGHIỆP VỤ CHI TIẾT :::
    # ==========================================

    def save_product(self, data, product_id=None):
        """
        Hàm logic chính: Validate dữ liệu chi tiết và Lưu
        """
        
        # --- 1. Kiểm tra trường bắt buộc ---
        if not data['ten_sp'] or not data['ma_dm'] or not data['ma_vach']:
            return (False, "Tên sản phẩm, Mã DM và Mã vạch là bắt buộc.")
        
        # --- 2. Kiểm tra và Chuẩn hóa Tên SP ---
        data['ten_sp'] = data['ten_sp'].strip()
        if len(data['ten_sp']) < 3:
            return (False, "Tên sản phẩm quá ngắn (tối thiểu 3 ký tự).")
        data['ten_sp'] = data['ten_sp'].title() # Viết hoa chữ cái đầu

        # --- 3. Kiểm tra Mã Danh Mục ---
        data['ma_dm'] = data['ma_dm'].strip().upper()

        # --- 4. Kiểm tra và Validate Mã Vạch ---
        data['ma_vach'] = data['ma_vach'].strip()
        if " " in data['ma_vach']:
             return (False, "Mã vạch không được chứa khoảng trắng.")
        
        # [Quan trọng] Kiểm tra trùng Mã vạch
        if self.check_duplicate_barcode(data['ma_vach'], product_id):
            return (False, f"Mã vạch '{data['ma_vach']}' đã tồn tại trên sản phẩm khác.")

        # --- 5. Kiểm tra Giá (Số dương) ---
        try:
            gia = float(data['gia'])
            if gia <= 0:
                return (False, "Giá sản phẩm phải lớn hơn 0.")
            data['gia'] = gia # Lưu lại giá trị số
        except ValueError:
            return (False, "Giá sản phẩm không hợp lệ.")
            
        # --- 6. Kiểm tra Số lượng (Số nguyên không âm) ---
        try:
            sl = int(data['so_luong'])
            if sl < 0:
                return (False, "Số lượng không được âm.")
            data['so_luong'] = sl # Lưu lại giá trị số
        except ValueError:
            return (False, "Số lượng phải là số nguyên.")

        # --- 7. Lưu xuống CSDL ---
        if product_id:
            # Chế độ Cập nhật
            success = self.update_product(product_id, data)
            message = "Cập nhật sản phẩm thành công!" if success else "Cập nhật thất bại."
        else:
            # Chế độ Thêm mới -> Tạo MÃ SP tự động
            try:
                last_code_num = self.get_next_product_code()
                new_code_num = int(last_code_num) + 1
                data['ma_sp'] = f"SP{new_code_num:03d}" 
            except Exception as e:
                return (False, f"Lỗi tạo mã sản phẩm: {e}")

            success = self.add_product(data)
            message = "Thêm sản phẩm thành công!" if success else "Thêm sản phẩm thất bại."
        
        return (success, message)