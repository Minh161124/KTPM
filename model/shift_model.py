from .db_connector import Database
from mysql.connector import Error
from datetime import datetime 

class ShiftCreateModel:
    def __init__(self):
        self.db_connector = Database()

    def get_menu_from_db(self):
        """Lấy danh sách sản phẩm kèm tên danh mục để hiển thị lên Menu"""
        conn = self.db_connector.connect()
        if not conn: return []
        cursor = conn.cursor(dictionary=True) 
        try:

            query = """
                SELECT p.id, p.ten_sp, p.gia, c.ten_dm 
                FROM products p 
                LEFT JOIN categories c ON p.ma_dm = c.ma_dm
                ORDER BY c.ten_dm, p.ten_sp
            """
            cursor.execute(query)
            results = cursor.fetchall()

            menu_list = []
            for row in results:
                cat_name = row['ten_dm'] if row['ten_dm'] else "Khác"

                cat_key = "Khac"
                if "nước" in cat_name.lower() or "nuoc" in cat_name.lower(): cat_key = "Nuoc"
                elif "ăn" in cat_name.lower() or "mì" in cat_name.lower(): cat_key = "DoAn"
                elif "thẻ" in cat_name.lower(): cat_key = "The"
                
                menu_list.append({
                    "id": row['id'],
                    "name": row['ten_sp'],
                    "price": row['gia'],
                    "category": cat_key, 
                    "unit": "Cái"
                })
            return menu_list
        except Error as e:
            print(f"Lỗi lấy menu: {e}")
            return []
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def get_open_shift(self):
        """Tìm xem có ca nào đang trạng thái 'dang_mo' không"""
        conn = self.db_connector.connect()
        if not conn: return None
        cursor = conn.cursor()
        try:

            query = "SELECT id FROM shifts WHERE trang_thai = 'dang_mo' ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                return row[0] 
            return None
        except Error as e:
            print(e)
            return None
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def add_shift_product(self, shift_id, sp_name, unit, qty, price, total):
        conn = self.db_connector.connect()
        if not conn: return False, "Lỗi kết nối"
        cursor = conn.cursor()
        try:

            check_query = "SELECT id, khach_mua, thanh_tien FROM shift_items WHERE shift_id = %s AND san_pham = %s"
            cursor.execute(check_query, (shift_id, sp_name))
            existing_item = cursor.fetchone()

            if existing_item:

                item_id = existing_item[0]
                old_qty = existing_item[1]
                
                new_qty = old_qty + qty
                new_total = new_qty * price
                
                update_query = "UPDATE shift_items SET khach_mua = %s, thanh_tien = %s WHERE id = %s"
                cursor.execute(update_query, (new_qty, new_total, item_id))
                msg = "Đã cập nhật số lượng"
            else:
                insert_query = """
                    INSERT INTO shift_items 
                    (shift_id, san_pham, don_vi, khach_mua, khuyen_mai, nhan_vien_mua, gia_ban, thanh_tien)
                    VALUES (%s, %s, %s, %s, 0, 0, %s, %s)
                """
                cursor.execute(insert_query, (shift_id, sp_name, unit, qty, price, total))
                msg = "Thêm món mới thành công"

            conn.commit()
            return True, msg
        except Error as e:
            print(f"Lỗi DB: {e}")
            return False, str(e)
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def create_new_shift(self, tu_gio, den_gio, nhan_vien):

        conn = self.db_connector.connect()
        if not conn: return None
        cursor = conn.cursor()
        try:
            query = "INSERT INTO shifts (gio_bat_dau, gio_ket_thuc, nhan_vien, trang_thai) VALUES (%s, %s, %s, 'dang_mo')"
            cursor.execute(query, (tu_gio, den_gio, nhan_vien))
            conn.commit()
            return cursor.lastrowid
        except Error:
            return None
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def get_shift_summary_data(self, shift_id):
        products = self.get_shift_products(shift_id)
        expenses = self.get_shift_items(shift_id, 'expenses') 
        additions = self.get_shift_items(shift_id, 'additions')
        return products, expenses, additions

    def get_shift_products(self, shift_id):
        conn = self.db_connector.connect()
        if not conn: return []
        cursor = conn.cursor()
        try:

            query = "SELECT id, san_pham, don_vi, khach_mua, gia_ban, thanh_tien FROM shift_items WHERE shift_id = %s ORDER BY id DESC"
            cursor.execute(query, (shift_id,))
            return cursor.fetchall()
        except Error:
            return []
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def get_shift_items(self, shift_id, item_type):
        conn = self.db_connector.connect()
        if not conn: return []
        cursor = conn.cursor()
        try:
            query = f"SELECT id, loai, thanh_toan, don_gia, thoi_gian FROM {item_type} WHERE ca_truc_id = %s ORDER BY id DESC"
            cursor.execute(query, (shift_id,))
            return cursor.fetchall()
        except Error:
            return []
        finally:
            cursor.close()
            self.db_connector.disconnect()

    def save_item(self, shift_id, table_type, data, item_id=None):

        conn = self.db_connector.connect()
        if not conn: return False, "Lỗi"
        cursor = conn.cursor()
        try:
            if item_id:
                q = f"UPDATE {table_type} SET loai=%s, thanh_toan=%s, don_gia=%s, thoi_gian=%s WHERE id=%s"
                cursor.execute(q, (*data, item_id))
            else:
                q = f"INSERT INTO {table_type} (ca_truc_id, loai, thanh_toan, don_gia, thoi_gian) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(q, (shift_id, *data))
            conn.commit()
            return True, "Ok"
        except Error as e:
            return False, str(e)
        finally:
            cursor.close()
            self.db_connector.disconnect()
    
    def delete_shift_product(self, item_id):
 
        conn = self.db_connector.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM shift_items WHERE id=%s", (item_id,))
            conn.commit()
            return True
        except: return False
        finally: cursor.close(); self.db_connector.disconnect()
        
    def delete_item(self, table, item_id):

        conn = self.db_connector.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {table} WHERE id=%s", (item_id,))
            conn.commit()
            return True
        except: return False
        finally: cursor.close(); self.db_connector.disconnect()

    def close_current_shift(self, shift_id, tong_he_thong, thuc_te, chenh_lech):

        conn = self.db_connector.connect()
        if not conn: return False, "Lỗi kết nối CSDL"
        
        cursor = conn.cursor()
        try:

            query = """
                UPDATE shifts 
                SET trang_thai = 'ket_thuc', 
                    gio_ket_thuc = NOW(),
                    tong_tien_he_thong = %s,
                    tien_thuc_te = %s,
                    tien_chenh_lech = %s
                WHERE id = %s
            """

            params = (tong_he_thong, thuc_te, chenh_lech, shift_id)
            
            cursor.execute(query, params)
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Chốt ca và lưu doanh thu thành công!"
            else:
                return False, "Không tìm thấy ca cần chốt."
                
        except Error as e:
            print(f"Lỗi đóng ca: {e}")
            return False, str(e)
        finally:
            cursor.close()
            self.db_connector.disconnect()