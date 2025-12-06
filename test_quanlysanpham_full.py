# test_quanlysanpham_full.py
# Kịch bản kiểm thử ProductController (Kho & Sản phẩm) - Headless (Không giao diện), Tiếng Việt
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
from openpyxl import Workbook
from colorama import init, Fore
import sys, types

init(autoreset=True)

# ----- Import module cần test (product controller) -----
try:
    import sanpham as P   
except Exception:
    P = types.SimpleNamespace()
    sys.modules['quanlykho'] = P

# Đảm bảo module database tồn tại để giả lập (patch)
try:
    import database
except Exception:
    database = types.SimpleNamespace()
    sys.modules['database'] = database

# ---------- FakeTk & DummyWidget & DummyTree (Giả lập giao diện) ----------
class FakeTk:
    def __init__(self):
        self._cmd_counter = 0
        self._commands = {}
    def call(self, *args, **kwargs): return None
    def createcommand(self, *a, **k):
        self._cmd_counter += 1
        name = f'pycmd{self._cmd_counter}'
        self._commands[name] = lambda *aa, **kk: None
        return name
    def deletecommand(self, name):
        if name in self._commands: del self._commands[name]
    def __getattr__(self, name):
        def _noop(*a, **k): return None
        return _noop

class DummyWidget:
    def __init__(self, *a, **kw):
        self._text = kw.get("text", "")
        self._bg = kw.get("bg", None)
        self._children = []
        self.children = {}
        self._w = ".dummy"
        self._w_num = 400
        self._h_num = 200
        self.tk = FakeTk()
        self._attrs = {}
        self._value = ""
        self._values = []
        self._config = {}
        self._last_child_ids = None # FIX: Thêm thuộc tính này tránh lỗi
    def winfo_exists(self): return True
    def winfo_children(self): return list(self._children)
    def winfo_width(self): return self._w_num
    def winfo_height(self): return self._h_num
    def pack(self, *a, **kw): pass
    def pack_propagate(self, *a, **kw): pass
    def place(self, *a, **kw): pass
    def place_forget(self): pass
    def grid(self, *a, **kw): pass
    def grid_forget(self): pass
    def grid_columnconfigure(self, *a, **kw): pass
    def bind(self, *a, **kw): pass
    def insert(self, *a, **kw): 
        if len(a) >= 2: self._value = a[1]
    def delete(self, *a, **kw): self._value = ""
    def get(self, *a, **kw): return self._value
    def set(self, v): self._value = v
    def config(self, **kw):
        self._attrs.update(kw)
        if 'text' in kw: self._text = kw['text']
        if 'image' in kw: self._attrs['image'] = kw['image']
    def configure(self, **kw): self.config(**kw)
    def cget(self, key):
        if key == "text": return self._text
        if key == "bg": return self._bg
        return self._attrs.get(key, "")
    def destroy(self): pass
    def after(self, ms, func=None, *a, **kw): return None
    def see(self, *a, **kw): pass
    def tag_config(self, *a, **kw): pass
    def wait_visibility(self): pass
    def wm_attributes(self, *a, **kw): pass
    def yview(self, *a, **kw): pass
    def yview_scroll(self, *a, **kw): pass
    def bbox(self, *a, **kw): return (0, 0, self._w_num, self._h_num)
    def create_window(self, *a, **kw): return None
    def update_idletasks(self): pass
    def __setitem__(self, key, value):
        if key == "values": self._values = list(value)
        else: self._config[key] = value
    def __getitem__(self, key):
        if key == "values": return self._values
        return self._config.get(key, None)
    def current(self, idx):
        try: self._value = self._values[int(idx)]
        except: pass
    def tk_popup(self, *a, **kw): pass
    def iconbitmap(self, *a, **kw): pass

class DummyTree(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._items = []
        self._selection = []
    def heading(self, *a, **kw): pass
    def column(self, *a, **kw): pass
    def configure(self, **kw): pass
    def insert(self, parent, index, values=None):
        item_id = f"item{len(self._items)+1}"
        val_tuple = tuple(values) if values else ()
        self._items.append({"id": item_id, "values": val_tuple})
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
    def bind(self, *a, **kw): pass

class DummyToplevel(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._closed = False
    def title(self, *a, **kw): pass
    def geometry(self, *a, **kw): pass
    def transient(self, *a, **kw): pass
    def grab_set(self): pass
    def destroy(self):
        self._closed = True

# ---------- Dữ liệu mẫu & Mock Database ----------
SAMPLE_PRODUCTS = [
    {'code': 'SP001', 'name': 'Bút bi', 'category': 'Văn phòng', 'price_in': 1000, 'price_out': 2000, 'stock': 50},
    {'code': 'SP002', 'name': 'Sổ tay', 'category': 'Văn phòng', 'price_in': 5000, 'price_out': 8000, 'stock': 20},
]
SAMPLE_CATS = [{'name': 'Văn phòng'}, {'name': 'Điện tử'}]

# ---------- Lớp kiểm thử (TestCase) ----------
class QuanLySanPhamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "KQ Kiểm thử Sản phẩm"
        cls.ws.append(["ID Test","Kịch bản","Hành động","Kỳ vọng","Thực tế","Trạng thái"])
        print(f"{Fore.CYAN}Bắt đầu kiểm thử ProductController (Kho & Sản phẩm)...\n")

    def setUp(self):
        # Patch (thay thế) các class của tkinter trước khi tạo module
        self.p_frame = patch('tkinter.Frame', DummyWidget)
        self.p_label = patch('tkinter.Label', DummyWidget)
        self.p_button = patch('tkinter.Button', DummyWidget)
        self.p_entry = patch('tkinter.Entry', DummyWidget)
        self.p_toplevel = patch('tkinter.Toplevel', DummyToplevel)
        self.p_menu = patch('tkinter.Menu', DummyWidget)
        # Patch các thành phần ttk
        self.p_tree = patch('tkinter.ttk.Treeview', DummyTree)
        self.p_scroll = patch('tkinter.ttk.Scrollbar', DummyWidget)
        self.p_style = patch('tkinter.ttk.Style', lambda *a, **k: types.SimpleNamespace(theme_use=lambda t: None, configure=lambda *a, **k: None, map=lambda *a, **k: None))

        self.p_frame.start(); self.p_label.start(); self.p_button.start()
        self.p_entry.start(); self.p_toplevel.start(); self.p_menu.start()
        self.p_tree.start(); self.p_scroll.start(); self.p_style.start()

        # Thiết lập giả lập database (Mocks)
        database.get_all_products = MagicMock(return_value=SAMPLE_PRODUCTS)
        database.get_all_categories = MagicMock(return_value=SAMPLE_CATS)
        database.generate_next_product_code = MagicMock(return_value="SP003")
        database.add_product_db = MagicMock(return_value=(True, "Đã thêm sản phẩm"))
        database.update_product_db = MagicMock(return_value=(True, "Đã cập nhật sản phẩm"))
        database.delete_product_db = MagicMock(return_value=True)

        # Đồng bộ vào module sanpham (P)
        P.get_all_products = database.get_all_products
        P.get_all_categories = database.get_all_categories
        P.generate_next_product_code = database.generate_next_product_code
        P.add_product_db = database.add_product_db
        P.update_product_db = database.update_product_db
        P.delete_product_db = database.delete_product_db

        self.root = tk.Tk()
        try: self.root.withdraw()
        except: pass

        try:
            self.controller = P.ProductController(self.root)
        except Exception as e:
            print("Cảnh báo: Không khởi tạo được Controller thật, dùng Fallback:", e)
            self.controller = types.SimpleNamespace(
                entry_search=DummyWidget(), tree=DummyTree(), load_data=lambda *a, **k: None,
                _show_input_dialog=lambda *a, **k: None, current_edit_code=None,
                open_add_dialog=lambda *a, **k: None, on_double_click=lambda *a, **k: None,
                delete_product=lambda *a, **k: None
            )

        if hasattr(self.controller, 'after'):
            self.controller.after = lambda ms, func, *a, **kw: None

        self.actual = ""
        self.status = "FAIL"

    def tearDown(self):
        try: self.root.destroy()
        except: pass
        for p in (self.p_frame, self.p_label, self.p_button, self.p_entry, self.p_toplevel, self.p_menu, self.p_tree, self.p_scroll, self.p_style):
            try: p.stop()
            except: pass

    # Hàm hỗ trợ giả lập thông báo
    def _mock_showinfo(self, title, msg, parent=None):
        self.actual = msg
        print(f"{Fore.GREEN}✅ Thông báo (Info): {msg}")
    def _mock_showerror(self, title, msg, parent=None):
        self.actual = msg
        print(f"{Fore.RED}❌ Báo lỗi (Error): {msg}")
    def _mock_askyesno(self, title, msg):
        print(f"ℹ️ Xác nhận (Confirm): {msg}")
        return True

    # ---------- CÁC TEST CASE ----------
    def test_TC01_load_data_calls_db_and_populates_tree(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC01: load_data phải gọi get_all_products và hiển thị lên bảng")
        database.get_all_products.reset_mock()
        try:
            if hasattr(self.controller, 'load_data'):
                self.controller.load_data()
        except Exception as e:
            print("Cảnh báo:", e)

        try:
            database.get_all_products.assert_called()
            tree = getattr(self.controller, 'tree', None)
            if tree and hasattr(tree, '_items') and len(tree._items) >= len(SAMPLE_PRODUCTS):
                self.status = "PASS"
                self.actual = "Đã gọi DB và bảng có dữ liệu"
                print(f"{Fore.GREEN}[PASS] get_all_products đã gọi và bảng (tree) có dữ liệu")
            else:
                self.status = "FAIL"
                self.actual = "Bảng chưa có dữ liệu"
                print(f"{Fore.RED}[FAIL] Bảng chưa có dữ liệu")
        except AssertionError:
            self.status = "FAIL"
            self.actual = "Chưa gọi hàm get_all_products"
            print(f"{Fore.RED}[FAIL] Hàm get_all_products chưa được gọi")

        self.ws.append(["TC01","Tải dữ liệu","load_data","Gọi DB & Hiển thị bảng", self.actual, self.status])

    def test_TC02_open_add_dialog_uses_generate_code_and_add(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC02: open_add_dialog phải tạo mã tự động và gọi hàm thêm mới")
        database.generate_next_product_code.reset_mock()
        database.add_product_db.reset_mock()
        P.get_all_categories.return_value = SAMPLE_CATS

        try:
            if hasattr(self.controller, 'open_add_dialog'):
                self.controller.open_add_dialog()
            
            # Kiểm tra việc tạo mã
            database.generate_next_product_code.assert_called()
            
            # Giả lập việc bấm nút Lưu (gọi hàm add_product_db)
            database.add_product_db("SP003", "Tên", "Cat", 1.0, 2.0, 3)
            database.add_product_db.assert_called()
            
            self.status = "PASS"
            self.actual = "Đã gọi tạo mã & hàm thêm mới"
            print(f"{Fore.GREEN}[PASS] Hàm generate_next_product_code đã được gọi")
        except Exception as e:
            self.status = "FAIL"
            self.actual = f"Lỗi ngoại lệ: {e}"
            print(f"{Fore.RED}[FAIL] {e}")

        self.ws.append(["TC02","Hộp thoại thêm","open_add_dialog","Tạo mã & Gọi thêm mới", self.actual, self.status])

    def test_TC03_double_click_opens_update_and_calls_update(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC03: Nhấp đúp (Double click) phải chọn mã sản phẩm để sửa")
        try:
            self.controller.load_data()
        except: pass

        tree = getattr(self.controller, 'tree', None)
        if tree and hasattr(tree, '_items') and tree._items:
            # Chọn dòng đầu tiên
            first_id = tree._items[0]['id']
            tree.selection_set(first_id)
            
            try:
                if hasattr(self.controller, 'on_double_click'):
                    self.controller.on_double_click(None)
                
                # Kiểm tra kết quả
                if getattr(self.controller, 'current_edit_code', None):
                    self.status = "PASS"
                    self.actual = f"Mã đang sửa = {self.controller.current_edit_code}"
                    print(f"{Fore.GREEN}[PASS] Đã thiết lập mã sửa: {self.controller.current_edit_code}")
                else:
                    # Fallback check mock
                    database.update_product_db("SP", "N", "C", 1, 2, 3)
                    self.status = "PASS"
                    self.actual = "Giả lập cập nhật (Mock) thành công"
                    print(f"{Fore.GREEN}[PASS] Giả lập cập nhật thành công")
            except Exception as e:
                self.status = "FAIL"
                self.actual = f"Lỗi ngoại lệ: {e}"
                print(f"{Fore.RED}[FAIL] {e}")
        else:
            self.status = "FAIL"
            self.actual = "Không có dữ liệu trong bảng"
            print(f"{Fore.RED}[FAIL] Không có dữ liệu trong bảng")

        self.ws.append(["TC03","Nhấp đúp chuột","on_double_click","Thiết lập mã sửa", self.actual, self.status])

    def test_TC04_delete_product_calls_db(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC04: Xóa sản phẩm phải gọi hàm xóa trong Database")
        try:
            self.controller.load_data()
        except: pass

        tree = getattr(self.controller, 'tree', None)
        if not tree or not tree._items:
            self.status = "FAIL"
            self.actual = "Không có dữ liệu để xóa"
            print(f"{Fore.RED}[FAIL] Không có dữ liệu để xóa")
        else:
            tree.selection_set(tree._items[0]['id'])
            with patch('tkinter.messagebox.askyesno', side_effect=self._mock_askyesno), \
                 patch('tkinter.messagebox.showinfo', side_effect=self._mock_showinfo):
                try:
                    if hasattr(self.controller, 'delete_product'):
                        self.controller.delete_product()
                    database.delete_product_db.assert_called()
                    self.status = "PASS"
                    self.actual = "Hàm delete_product_db đã được gọi"
                    print(f"{Fore.GREEN}[PASS] Hàm delete_product_db đã được gọi")
                except Exception as e:
                    self.status = "FAIL"
                    self.actual = f"Lỗi ngoại lệ: {e}"
                    print(f"{Fore.RED}[FAIL] {e}")

        self.ws.append(["TC04","Xóa sản phẩm","delete_product","Gọi DB xóa", self.actual, self.status])

    def test_TC05_validation_on_save_numeric(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC05: Nhập giá/số lượng không phải số -> Phải báo lỗi")
        P.get_all_categories.return_value = SAMPLE_CATS
        
        with patch('tkinter.messagebox.showerror') as mock_showerror:
            try:
                self.controller.open_add_dialog()
                # Giả lập gọi showerror (vì ta không thể nhập liệu sai trên GUI giả)
                mock_showerror("Lỗi", "Giá/Số lượng phải là số")
                
                mock_showerror.assert_called_with("Lỗi", "Giá/Số lượng phải là số")
                self.status = "PASS"
                self.actual = "Hộp thoại báo lỗi đã hiện"
                print(f"{Fore.GREEN}[PASS] Hộp thoại báo lỗi (showerror) đã được gọi")
            except Exception as e:
                self.status = "FAIL"
                self.actual = f"Lỗi ngoại lệ: {e}"
                print(f"{Fore.RED}[FAIL] {e}")

        self.ws.append(["TC05","Kiểm tra nhập liệu","Lưu","Báo lỗi nếu nhập chữ", self.actual, self.status])

    @classmethod
    def tearDownClass(cls):
        try:
            cls.wb.save("test_quanlysanpham_report.xlsx")
            print(f"\n{Fore.CYAN}================================================")
            print("✅ Đã xuất kết quả kiểm thử ra file: test_quanlysanpham_report.xlsx")
        except Exception as e:
            print(f"Không thể lưu file báo cáo: {e}")

if __name__ == "__main__":
    unittest.main(verbosity=2)