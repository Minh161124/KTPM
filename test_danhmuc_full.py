# test_danhmuc_full.py
# Kịch bản kiểm thử CategoryManagerPage (Quản lý Danh Mục) - Headless, Tiếng Việt
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch, ANY
from openpyxl import Workbook
from colorama import init, Fore
import sys, types

init(autoreset=True)

# -----------------------------------------------------------
# 1. GIẢ LẬP MÔI TRƯỜNG (MOCK) TRƯỚC KHI IMPORT CODE CHÍNH
# -----------------------------------------------------------

# Giả lập module database và hàm connect_db
db_mock = types.SimpleNamespace()
db_mock.connect_db = MagicMock()
sys.modules['database'] = db_mock

# ---------- FakeTk & DummyWidget (Hệ thống GUI giả lập) ----------
class FakeTk:
    def __init__(self):
        self._cmd_counter = 0
        self._commands = {}
    def call(self, *args, **kwargs): return None
    def createcommand(self, *a, **k):
        self._cmd_counter += 1
        return f'pycmd{self._cmd_counter}'
    def deletecommand(self, name): pass
    def __getattr__(self, name): return lambda *a, **k: None

class DummyWidget:
    def __init__(self, *a, **kw):
        self._text = kw.get("text", "")
        self._bg = kw.get("bg", None)
        self._children = []
        self.children = {}
        self._w_num = 400
        self.tk = FakeTk()
        self._attrs = {}
        self._value = "" # Chứa giá trị cho Entry
        self._values = []
        self._last_child_ids = None 
    
    # --- CÁC HÀM CƠ BẢN CỦA WIDGET ---
    def winfo_exists(self): return True
    def winfo_children(self): return list(self._children)
    def pack(self, *a, **kw): pass
    def pack_propagate(self, *a, **kw): pass
    def place(self, *a, **kw): pass
    def grid(self, *a, **kw): pass
    def bind(self, *a, **kw): pass
    
    # --- XỬ LÝ ENTRY ---
    def insert(self, index, string): 
        self._value = str(string)
    def delete(self, first, last=None): 
        self._value = ""
    def get(self, *a, **kw): return self._value
    
    # --- XỬ LÝ CONFIG ---
    def config(self, **kw):
        self._attrs.update(kw)
    def configure(self, **kw): self.config(**kw)
    def cget(self, key): return self._attrs.get(key, "")
    def destroy(self): pass
    def __setitem__(self, key, value): self._attrs[key] = value
    def __getitem__(self, key): return self._attrs.get(key)
    def selection_clear(self): pass

    # --- FIX LỖI: CÁC HÀM BỔ SUNG CHO SCROLLBAR VÀ MENU ---
    def set(self, *args, **kwargs): pass  
    def add_command(self, *args, **kwargs): pass 
    def post(self, *args, **kwargs): pass 

class DummyTree(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._items = []
        self._selection = []
    def heading(self, *a, **kw): pass
    def column(self, *a, **kw): pass
    def insert(self, parent, index, values=None):
        item_id = f"item{len(self._items)+1}"
        self._items.append({"id": item_id, "values": tuple(values) if values else ()})
        return item_id
    def get_children(self):
        return [it['id'] for it in self._items]
    def delete(self, item):
        self._items = [it for it in self._items if it['id'] != item]
    def selection(self):
        return list(self._selection)
    def selection_set(self, item):
        self._selection = [item]
    def item(self, item, option=None):
        found = next((it for it in self._items if it['id'] == item), None)
        if not found: return {}
        if option == "values": return found['values']
        return {'values': found['values']}
    def identify_row(self, y):
        return self._items[0]['id'] if self._items else ""
    def yview(self, *a, **kw): pass

# Patch Tkinter Classes
patch('tkinter.Frame', DummyWidget).start()
patch('tkinter.Label', DummyWidget).start()
patch('tkinter.Button', DummyWidget).start()
patch('tkinter.Entry', DummyWidget).start()
patch('tkinter.Menu', DummyWidget).start()
patch('tkinter.ttk.Treeview', DummyTree).start()
patch('tkinter.ttk.Style', MagicMock).start()
patch('tkinter.ttk.Scrollbar', DummyWidget).start()

# ----- IMPORT MODULE CẦN TEST -----
try:
    import danhmuc
except ImportError:
    danhmuc = types.SimpleNamespace()
    danhmuc.CategoryManagerPage = MagicMock()
    print(f"{Fore.RED}Cảnh báo: Không tìm thấy file 'danhmuc.py'.")

# -----------------------------------------------------------
# 2. THIẾT LẬP TEST CASE
# -----------------------------------------------------------

class TestCategoryManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "KQ Test Danh Mục"
        cls.ws.append(["ID Test", "Kịch bản", "Hành động", "Kỳ vọng", "Thực tế", "Trạng thái"])
        print(f"{Fore.CYAN}Bắt đầu kiểm thử CategoryManagerPage...\n")

    def setUp(self):
        self.root = tk.Tk()
        
        # Mock kết nối DB
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_conn.is_connected.return_value = True
        
        # Gán mock cho connect_db
        db_mock.connect_db.return_value = self.mock_conn
        
        # Mock fetchall để tránh lỗi khi init gọi load_data
        self.mock_cursor.fetchall.return_value = [] 
        
        try:
            self.page = danhmuc.CategoryManagerPage(self.root)
        except Exception as e:
            self.page = None
            print(f"{Fore.RED}Lỗi khởi tạo Page: {e}")

        self.actual = ""
        self.status = "FAIL"

    def tearDown(self):
        db_mock.connect_db.reset_mock()
        self.mock_cursor.reset_mock()
        self.mock_conn.reset_mock()
        try: self.root.destroy()
        except: pass

    # --- HÀM HỖ TRỢ LOG ---
    def log_result(self, tc_id, scenario, action, expected):
        self.ws.append([tc_id, scenario, action, expected, self.actual, self.status])
        color = Fore.GREEN if self.status == "PASS" else Fore.RED
        print(f"{color}[{self.status}] {tc_id}: {self.actual}")

    # --- CÁC TEST CASE CHI TIẾT ---

    def test_TC01_load_data_hien_thi_dung(self):
        print(f"{Fore.CYAN}--- TC01: Kiểm tra tải dữ liệu lên bảng ---")
        if not self.page: return

        sample_data = [
            (1, 'DM01', 'Đồ ăn', 'Mô tả 1'),
            (2, 'DM02', 'Đồ uống', 'Mô tả 2')
        ]
        self.mock_cursor.fetchall.return_value = sample_data
        
        self.page.load_data()
        
        try:
            self.mock_cursor.execute.assert_called()
            call_args = self.mock_cursor.execute.call_args[0][0]
            tree_items = self.page.tree._items
            
            if "SELECT" in call_args and len(tree_items) == 2:
                self.status = "PASS"
                self.actual = "SQL SELECT gọi đúng & Bảng có 2 dòng"
            else:
                self.status = "FAIL"
                self.actual = f"Lỗi: SQL={call_args}, Items={len(tree_items)}"
        except Exception as e:
            self.status = "FAIL"
            self.actual = f"Lỗi exception: {e}"

        self.log_result("TC01", "Tải dữ liệu", "Gọi load_data()", "Hiển thị 2 danh mục")

    def test_TC02_them_moi_danh_muc(self):
        print(f"{Fore.CYAN}--- TC02: Thêm mới danh mục (INSERT) ---")
        if not self.page: return

        self.page.entry_code.insert(0, "TEST_NEW")
        self.page.entry_name.insert(0, "Danh mục test")
        self.page.entry_desc.insert(0, "Mô tả test")
        self.page.current_edit_id = None
        
        with patch('tkinter.messagebox.showinfo') as mock_info:
            self.page.save_category()
            
            try:
                self.mock_cursor.execute.assert_called()
                calls = self.mock_cursor.execute.call_args_list
                insert_called = False
                for call in calls:
                    sql = call[0][0]
                    if "INSERT INTO" in sql:
                        params = call[0][1]
                        if params[0] == "TEST_NEW":
                            insert_called = True
                            break
                
                if insert_called:
                    self.mock_conn.commit.assert_called()
                    self.status = "PASS"
                    self.actual = "Đã gọi INSERT SQL & Commit"
                else:
                    self.status = "FAIL"
                    self.actual = "Chưa gọi đúng lệnh INSERT"
            except Exception as e:
                self.status = "FAIL"
                self.actual = f"Lỗi: {e}"

        self.log_result("TC02", "Thêm mới", "Nhập & Lưu", "Gọi INSERT SQL")

    def test_TC03_cap_nhat_danh_muc(self):
        print(f"{Fore.CYAN}--- TC03: Cập nhật danh mục (UPDATE) ---")
        if not self.page: return

        self.page.current_edit_id = 5
        self.page.entry_code.insert(0, "DM_UPD")
        self.page.entry_name.insert(0, "Tên mới")
        
        with patch('tkinter.messagebox.showinfo'):
            self.page.save_category()
            
            try:
                calls = self.mock_cursor.execute.call_args_list
                update_called = False
                for call in calls:
                    if "UPDATE categories" in call[0][0]:
                        update_called = True
                        break

                if update_called:
                    self.status = "PASS"
                    self.actual = "Đã gọi UPDATE SQL"
                else:
                    self.status = "FAIL"
                    self.actual = "Chưa gọi lệnh UPDATE"
            except Exception as e:
                self.status = "FAIL"
                self.actual = f"Lỗi: {e}"

        self.log_result("TC03", "Cập nhật", "Sửa & Lưu", "Gọi UPDATE SQL")

    def test_TC04_validate_rong(self):
        print(f"{Fore.CYAN}--- TC04: Kiểm tra nhập rỗng ---")
        if not self.page: return

        # 1. Để trống Entry
        self.page.entry_code.delete(0)
        self.page.entry_name.delete(0)
        
        # --- FIX: Reset mock để xóa các lệnh gọi từ lúc khởi tạo (load_data) ---
        self.mock_cursor.reset_mock()
        
        # 2. Patch showwarning
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            self.page.save_category()
            
            # 3. Kiểm tra
            if mock_warning.called:
                self.status = "PASS"
                self.actual = "Đã hiện cảnh báo thiếu thông tin"
                # Giờ assert_not_called sẽ đúng vì ta đã reset_mock ở trên
                try:
                    self.mock_cursor.execute.assert_not_called()
                except AssertionError:
                    self.status = "FAIL"
                    self.actual = "Vẫn gọi SQL dù dữ liệu rỗng!"
            else:
                self.status = "FAIL"
                self.actual = "Không hiện cảnh báo"

        self.log_result("TC04", "Validate", "Lưu với form rỗng", "Hiện showwarning")

    def test_TC05_xoa_danh_muc(self):
        print(f"{Fore.CYAN}--- TC05: Xóa danh mục (DELETE) ---")
        if not self.page: return

        item_id = self.page.tree.insert("", "end", values=(10, "DEL", "Xoa", "Mo ta"))
        self.page.tree.selection_set(item_id)
        
        with patch('tkinter.messagebox.askyesno', return_value=True), \
             patch('tkinter.messagebox.showinfo'):
            
            self.page.delete_category()
            
            try:
                calls = self.mock_cursor.execute.call_args_list
                delete_called = False
                for call in calls:
                    sql = call[0][0]
                    if "DELETE FROM" in sql:
                        params = call[0][1]
                        if params[0] == 10:
                            delete_called = True
                            break
                
                if delete_called:
                    self.status = "PASS"
                    self.actual = "Đã gọi DELETE SQL với ID=10"
                else:
                    self.status = "FAIL"
                    self.actual = "Chưa gọi đúng lệnh DELETE"
            except Exception as e:
                self.status = "FAIL"
                self.actual = f"Lỗi: {e}"

        self.log_result("TC05", "Xóa", "Chọn & Xóa", "Gọi DELETE SQL")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.wb.save("test_danhmuc_report.xlsx")
            print(f"\n{Fore.CYAN}================================================")
            print("✅ Đã xuất báo cáo ra file: test_danhmuc_report.xlsx")
        except:
            print("Lỗi lưu file báo cáo.")

if __name__ == "__main__":
    unittest.main(verbosity=2)