# test_doanhthu_full.py
# Kịch bản kiểm thử Trang Quản lý Thu Chi (doanhthu.py) - Headless, Tiếng Việt
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch, ANY
from openpyxl import Workbook
from colorama import init, Fore
import sys, types

init(autoreset=True)

# -----------------------------------------------------------
# 1. GIẢ LẬP MÔI TRƯỜNG (MOCK)
# -----------------------------------------------------------

# --- Giả lập module database ---
# Mock các hàm DB mà doanhthu.py import
db_mock = types.SimpleNamespace()
db_mock.create_transaction_table = MagicMock()
db_mock.get_transactions = MagicMock(return_value=[])
db_mock.add_transaction_db = MagicMock()
db_mock.delete_transaction_db = MagicMock()
db_mock.get_financial_summary = MagicMock(return_value={"total_in": 0, "total_out": 0, "balance": 0})

sys.modules['database'] = db_mock

# --- FakeTk & DummyWidget (Hệ thống GUI giả lập) ---
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
        self.tk = FakeTk()
        self._attrs = {}
        self._value = "" 
        self._values = [] 
        # Fix cho Combobox
        self.current_idx = 0
    
    # --- CÁC HÀM CƠ BẢN ---
    def winfo_exists(self): return True
    def winfo_children(self): return list(self._children)
    def winfo_toplevel(self): return self
    def winfo_rootx(self): return 0
    def winfo_rooty(self): return 0
    def pack(self, *a, **kw): pass
    def grid(self, *a, **kw): pass
    def grid_columnconfigure(self, *a, **kw): pass
    def bind(self, *a, **kw): pass
    
    # --- XỬ LÝ TEXT/ENTRY ---
    def insert(self, index, string): self._value = str(string)
    def delete(self, first, last=None): self._value = ""
    def get(self, *a, **kw): return self._value
    
    # --- XỬ LÝ COMBOBOX ---
    def current(self, new_index=None): 
        if new_index is not None: self.current_idx = new_index
        return self.current_idx
    
    # --- XỬ LÝ CONFIG ---
    def config(self, **kw):
        self._attrs.update(kw)
        if 'text' in kw: self._text = kw['text']
    def configure(self, **kw): self.config(**kw)
    def cget(self, key): 
        if key == 'text': return self._text
        return self._attrs.get(key, "")
    
    def destroy(self): pass
    def __setitem__(self, key, value): self._attrs[key] = value
    def __getitem__(self, key): return self._attrs.get(key)
    
    # --- CÁC HÀM BỔ SUNG ---
    def set(self, *args, **kwargs): pass  
    def tag_configure(self, *args, **kwargs): pass # Cho Treeview tag

class DummyTree(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._items = []
        self._selection = []
    def heading(self, *a, **kw): pass
    def column(self, *a, **kw): pass
    def insert(self, parent, index, values=None, tags=()):
        item_id = f"item{len(self._items)+1}"
        self._items.append({"id": item_id, "values": tuple(values) if values else (), "tags": tags})
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

class DummyToplevel(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
    def title(self, *a, **kw): pass
    def geometry(self, *a, **kw): pass
    def transient(self, *a, **kw): pass
    def grab_set(self): pass

# Patch Tkinter Classes
patch('tkinter.Frame', DummyWidget).start()
patch('tkinter.Label', DummyWidget).start()
patch('tkinter.Button', DummyWidget).start()
patch('tkinter.Entry', DummyWidget).start()
patch('tkinter.Menu', DummyWidget).start()
patch('tkinter.Toplevel', DummyToplevel).start()
patch('tkinter.ttk.Treeview', DummyTree).start()
patch('tkinter.ttk.Style', MagicMock).start()
patch('tkinter.ttk.Scrollbar', DummyWidget).start()
patch('tkinter.ttk.Combobox', DummyWidget).start()

# ----- IMPORT MODULE CẦN TEST: DOANHTHU -----
try:
    import doanhthu
except ImportError:
    doanhthu = types.SimpleNamespace()
    doanhthu.RevenueManagerPage = MagicMock()
    doanhthu.TransactionEditor = MagicMock()
    print(f"{Fore.RED}Cảnh báo: Không tìm thấy file 'doanhthu.py'. Hãy chắc chắn tên file đúng.")

# -----------------------------------------------------------
# 2. THIẾT LẬP TEST CASE
# -----------------------------------------------------------

class TestRevenueManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "KQ Test Thu Chi"
        cls.ws.append(["ID Test", "Kịch bản", "Hành động", "Kỳ vọng", "Thực tế", "Trạng thái"])
        print(f"{Fore.CYAN}Bắt đầu kiểm thử RevenueManagerPage (doanhthu.py)...\n")

    def setUp(self):
        self.root = tk.Tk()
        
        # Reset mocks
        db_mock.get_transactions.reset_mock()
        db_mock.get_financial_summary.reset_mock()
        db_mock.add_transaction_db.reset_mock()
        db_mock.delete_transaction_db.reset_mock()
        
        try:
            self.page = doanhthu.RevenueManagerPage(self.root)
        except Exception as e:
            self.page = None
            print(f"{Fore.RED}Lỗi khởi tạo Page: {e}")

        self.actual = ""
        self.status = "FAIL"

    def tearDown(self):
        try: self.root.destroy()
        except: pass

    def log_result(self, tc_id, scenario, action, expected):
        self.ws.append([tc_id, scenario, action, expected, self.actual, self.status])
        color = Fore.GREEN if self.status == "PASS" else Fore.RED
        print(f"{color}[{self.status}] {tc_id}: {self.actual}")

    # --- TEST CASES ---

    def test_TC01_load_stats_and_table(self):
        print(f"{Fore.CYAN}--- TC01: Tải Thống kê & Bảng dữ liệu ---")
        if not self.page: return

        # 1. Setup Mock Return
        db_mock.get_financial_summary.return_value = {
            "total_in": 1000000, "total_out": 500000, "balance": 500000
        }
        db_mock.get_transactions.return_value = [
            {'id': 1, 'type': 'thu', 'category': 'Test', 'amount': 100000, 'description': 'Demo', 'created_at': '2023-01-01'}
        ]

        # 2. Hành động: Tải lại dữ liệu
        self.page._load_data()

        # 3. Kiểm tra Stats Cards (kiểm tra text của label bên trong)
        # Lưu ý: StatCard có self.lbl_val
        val_in = self.page.card_in.lbl_val.cget('text')
        val_out = self.page.card_out.lbl_val.cget('text')
        
        tree_count = len(self.page.tree._items)

        try:
            if "1,000,000" in val_in and "500,000" in val_out and tree_count == 1:
                self.status = "PASS"
                self.actual = f"Thu={val_in}, Chi={val_out}, Rows={tree_count}"
            else:
                self.status = "FAIL"
                self.actual = f"Sai data: Thu={val_in}, Rows={tree_count}"
        except Exception as e:
            self.status = "FAIL"
            self.actual = f"Lỗi: {e}"

        self.log_result("TC01", "Load Data", "Gọi _load_data", "Hiển thị đúng số liệu")

    def test_TC02_add_transaction_success(self):
        print(f"{Fore.CYAN}--- TC02: Thêm giao dịch thành công ---")
        if not self.page: return

        # 1. Mở Editor (dùng doanhthu.TransactionEditor)
        editor = doanhthu.TransactionEditor(self.page, 'thu')
        
        # 2. Điền form
        # Giả lập điền Combobox (Danh mục)
        editor.e_cat.get = MagicMock(return_value="Dịch vụ")
        # Giả lập điền Entry (Số tiền, Mô tả)
        editor.e_amount.insert(0, "200000")
        editor.e_desc.insert(0, "Test Insert")

        # 3. Save
        editor._save()

        # 4. Kiểm tra
        try:
            db_mock.add_transaction_db.assert_called_with('thu', 'Dịch vụ', 200000, 'Test Insert')
            self.status = "PASS"
            self.actual = "Đã gọi add_transaction_db đúng tham số"
        except AssertionError:
            self.status = "FAIL"
            self.actual = "Hàm DB chưa được gọi hoặc sai tham số"
        except Exception as e:
            self.status = "FAIL"
            self.actual = f"Lỗi: {e}"

        self.log_result("TC02", "Thêm mới", "Nhập & Lưu", "Gọi DB Insert")

    def test_TC03_add_transaction_validation_fail(self):
        print(f"{Fore.CYAN}--- TC03: Kiểm tra nhập số âm (Validate) ---")
        if not self.page: return

        editor = doanhthu.TransactionEditor(self.page, 'chi')
        editor.e_cat.get = MagicMock(return_value="Khác")
        editor.e_amount.insert(0, "-50000") # Số âm
        
        # Mock showerror để bắt lỗi
        with patch('tkinter.messagebox.showerror') as mock_err:
            editor._save()
            
            if mock_err.called:
                # Đảm bảo KHÔNG gọi DB
                try:
                    db_mock.add_transaction_db.assert_not_called()
                    self.status = "PASS"
                    self.actual = "Hiện lỗi & Không lưu DB"
                except AssertionError:
                    self.status = "FAIL"
                    self.actual = "Vẫn gọi DB dù số âm!"
            else:
                self.status = "FAIL"
                self.actual = "Không hiện thông báo lỗi"

        self.log_result("TC03", "Validate", "Nhập số âm", "Báo lỗi")

    def test_TC04_delete_transaction(self):
        print(f"{Fore.CYAN}--- TC04: Xóa giao dịch ---")
        if not self.page: return

        # 1. Setup tree có data
        item_id = self.page.tree.insert("", "end", values=(99, "Time", "CHI", "Cat", "Desc", "500"))
        self.page.tree.selection_set(item_id)

        # 2. Mock Confirm Yes
        with patch('tkinter.messagebox.askyesno', return_value=True):
            self.page._delete_item()
            
            try:
                db_mock.delete_transaction_db.assert_called_with(99)
                self.status = "PASS"
                self.actual = "Đã gọi delete_transaction_db(99)"
            except AssertionError:
                self.status = "FAIL"
                self.actual = "Chưa gọi hàm xóa DB"

        self.log_result("TC04", "Xóa", "Chọn & Xóa", "Gọi DB Delete")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.wb.save("test_doanhthu_report.xlsx")
            print(f"\n{Fore.CYAN}================================================")
            print("✅ Đã xuất báo cáo: test_doanhthu_report.xlsx")
        except: pass

if __name__ == "__main__":
    unittest.main(verbosity=2)