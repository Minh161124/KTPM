# model/cat_model.py
import re # [Mới] Import thư viện regex
from .db_connector import Database
from mysql.connector import Error

class CategoryModel:
    def __init__(self):
        self.db_connector = Database()
    
    def check_duplicate_ma_dm(self, ma_dm, category_id=None):
        """
        Kiểm tra xem Mã DM đã tồn tại chưa.
        Nếu cung cấp category_id (chế độ Sửa), loại trừ chính nó ra.
        """
        conn = self.db_connector.connect()
        if not conn: return True 
        cursor = conn.cursor()
        try:
            query = "SELECT id FROM categories WHERE ma_dm = %s"
            params = [ma_dm]
            
            if category_id:
                query += " AND id != %s"
                params.append(category_id)
                
            cursor.execute(query, params)
            if cursor.fetchone():
                return True 
            return False 
        except Error as e:
            print(f"Lỗi khi kiểm tra trùng Mã DM: {e}")
            return True
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def fetch_categories(self, search="", limit=10, page=1):
        """
        Lấy danh sách danh mục với tìm kiếm và phân trang
        """
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
                where_clauses.append("(ma_dm LIKE %s OR ten_dm LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param])
                
            where_sql = " AND ".join(where_clauses)
            if where_sql: where_sql = " WHERE " + where_sql

            count_query = f"SELECT COUNT(*) FROM categories {where_sql}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]

            query = f"""
                SELECT id, ma_dm, ten_dm 
                FROM categories 
                {where_sql} 
                ORDER BY id DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [limit, offset])
            results = cursor.fetchall()
            
        except Error as e:
            print(f"Lỗi khi lấy dữ liệu danh mục: {e}")
        finally:
            cursor.close()
            self.db_connector.disconnect()
            
        return results, total_records

    def get_category_by_id(self, category_id):
        conn = self.db_connector.connect()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, ma_dm, ten_dm FROM categories WHERE id = %s", (category_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Lỗi khi lấy thông tin danh mục: {e}")
            return None
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def add_category(self, data):
        conn = self.db_connector.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO categories (ma_dm, ten_dm) 
                VALUES (%s, %s)
            """
            cursor.execute(query, (data['ma_dm'], data['ten_dm']))
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi thêm danh mục: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def update_category(self, category_id, data):
        conn = self.db_connector.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            query = """
                UPDATE categories SET ma_dm=%s, ten_dm=%s 
                WHERE id = %s
            """
            params = (data['ma_dm'], data['ten_dm'], category_id)
            cursor.execute(query, params)
            conn.commit()
            return True
        except Error as e:
            print(f"Lỗi khi cập nhật danh mục: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def delete_category(self, category_id):
        """Xóa danh mục. Trả về (True/False)"""
        conn = self.db_connector.connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
            conn.commit()
            return True
        except Error as e:
            # Mã lỗi 1451: Cannot delete or update a parent row (Foreign key constraint fails)
            if e.errno == 1451:
                print("Lỗi: Không thể xóa danh mục vì đang chứa sản phẩm.")
                # Trong thực tế, bạn có thể muốn trả về một thông báo lỗi cụ thể thay vì chỉ False
                # Nhưng để giữ cấu trúc return giống các hàm khác, ta log ra console.
            else:
                print(f"Lỗi khi xóa danh mục: {e}")
            
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.db_connector.disconnect()
    
    def get_all_categories_for_lookup(self):
        """
        Lấy danh sách (ma_dm, ten_dm) để nạp vào Combobox.
        """
        conn = self.db_connector.connect()
        if not conn: return []
        cursor = conn.cursor()
        try:
            query = "SELECT ma_dm, ten_dm FROM categories ORDER BY ma_dm"
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f"Lỗi khi lấy danh sách danh mục cho lookup: {e}")
            return []
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def save_category(self, data, category_id=None):
        """
        Hàm logic chính: Validate chi tiết và Lưu
        """
        
        # --- 1. Trim dữ liệu ---
        data['ma_dm'] = data['ma_dm'].strip()
        data['ten_dm'] = data['ten_dm'].strip()

        # --- 2. Kiểm tra trống ---
        if not data['ma_dm'] or not data['ten_dm']:
            return (False, "Mã danh mục và Tên danh mục là bắt buộc.")

        # --- 3. Validate Mã Danh Mục ---
        # Kiểm tra độ dài
        if len(data['ma_dm']) < 2 or len(data['ma_dm']) > 20:
            return (False, "Mã danh mục phải từ 2 đến 20 ký tự.")
        
        # Kiểm tra ký tự đặc biệt (Chỉ cho phép Chữ, Số và Gạch dưới)
        if not re.match("^[A-Za-z0-9_]+$", data['ma_dm']):
            return (False, "Mã danh mục không được chứa khoảng trắng hoặc ký tự đặc biệt.")

        # Chuẩn hóa: Viết hoa toàn bộ
        data['ma_dm'] = data['ma_dm'].upper()

        # --- 4. Validate Tên Danh Mục ---
        if len(data['ten_dm']) < 3:
            return (False, "Tên danh mục quá ngắn.")
        
        # Chuẩn hóa: Viết hoa chữ cái đầu
        data['ten_dm'] = data['ten_dm'].title()

        # --- 5. Kiểm tra Trùng lặp ---
        if self.check_duplicate_ma_dm(data['ma_dm'], category_id):
            return (False, f"Mã danh mục '{data['ma_dm']}' đã tồn tại.")

        # --- 6. Lưu xuống DB ---
        if category_id:
            success = self.update_category(category_id, data)
            message = "Cập nhật danh mục thành công!" if success else "Cập nhật thất bại."
        else:
            success = self.add_category(data)
            message = "Thêm danh mục thành công!" if success else "Thêm thất bại."
        
        return (success, message)