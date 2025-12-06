# test_system_settings_full.py
# Kịch bản kiểm thử Trang Cài Đặt (system_settings.py) - Headless
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
db_mock = types.SimpleNamespace()
# Mock các hàm get/save setting
db_mock.get_setting = MagicMock(side_effect=lambda k, d="": d) # Mặc định trả về default
db_mock.save_setting = MagicMock()
db_mock.change_admin_password = MagicMock(return_value=True)

# Inject vào sys.modules để khi system_settings.py import 'database' sẽ nhận mock này
sys.modules['database'] = db_mock

# --- FakeTk & DummyWidget (Hệ thống GUI giả lập) ---
class FakeTk:
    def __init__(self):
        self._cmd_counter = 0
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
        self.children = {} # Dictionary cho pack/grid
        self.tk = FakeTk()
        self._attrs = {}
        
    # --- Widget Hierarchy ---
    def winfo_exists(self): return True
    def winfo_children(self): return list(self._children)
    def destroy(self): self._children = [] 
    
    # --- Layout ---
    def pack(self, *a, **kw): pass
    def pack_propagate(self, *a, **kw): pass
    def place(self, *a, **kw): pass
    def grid(self, *a, **kw): pass
    
    # --- Configuration ---
    def config(self, **kw):
        self._attrs.update(kw)
        if 'text' in kw: self._text = kw['text']
    def configure(self, **kw): self.config(**kw)
    def cget(self, key): 
        if key == 'text': return self._text
        return self._attrs.get(key, "")

    def bind(self, *a, **kw): pass # Mock bind event
    
    # --- Entry specifics ---
    def insert(self, *a): pass

    def __setitem__(self, key, value): self._attrs[key] = value
    def __getitem__(self, key): return self._attrs.get(key)

# Patch Tkinter Classes
# Lưu ý: Ta KHÔNG patch StringVar vì ta sẽ khởi tạo root thật (nhưng ẩn)
# để logic StringVar hoạt động đúng trong ModernEntry
patch('tkinter.Frame', DummyWidget).start()
patch('tkinter.Label', DummyWidget).start()
patch('tkinter.Button', DummyWidget).start()
patch('tkinter.Entry', DummyWidget).start()

# ----- IMPORT MODULE CẦN TEST: SYSTEM_SETTINGS -----
try:
    # Import system_settings nhưng đặt tên là 'caidat' để tái sử dụng logic test bên dưới dễ dàng
    import system_settings as caidat
except ImportError:
    caidat = types.SimpleNamespace()
    caidat.SettingsPage = MagicMock()
    print(f"{Fore.RED}Cảnh báo: Không tìm thấy file 'system_settings.py'. Hãy kiểm tra lại tên file.")

# -----------------------------------------------------------
# 2. THIẾT LẬP TEST CASE
# -----------------------------------------------------------

class TestSettingsPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "KQ Test Cài Đặt"
        cls.ws.append(["ID Test", "Kịch bản", "Hành động", "Kỳ vọng", "Thực tế", "Trạng thái"])
        print(f"{Fore.CYAN}Bắt đầu kiểm thử SettingsPage (system_settings.py)...\n")

    def setUp(self):
        # Tạo root thật để StringVar hoạt động, nhưng các Widget con bị Patch thành Dummy
        self.root = tk.Tk()
        self.root.withdraw() # Ẩn window chính
        
        # Reset mocks
        db_mock.save_setting.reset_mock()
        db_mock.change_admin_password.reset_mock()
        
        try:
            self.page = caidat.SettingsPage(self.root)
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

    def test_TC01_navigate_info_and_save(self):
        print(f"{Fore.CYAN}--- TC01: Sửa thông tin quán ---")
        if not self.page: return

        # 1. Điều hướng vào trang Thông tin
        # Giả lập click vào tile đầu tiên (Thông tin quán)
        self.page._view_info()

        # 2. Nhập liệu vào ModernEntry
        # Lưu ý: ModernEntry dùng self.var (StringVar). Ta set trực tiếp vào var.
        self.page.inp_name.set("Quán Net Test")
        self.page.inp_addr.set("123 Test Street")
        self.page.inp_wifi.set("wifi123")

        # 3. Patch messagebox & Click Save
        with patch('tkinter.messagebox.showinfo') as mock_info:
            self.page._save_info()

            # 4. Kiểm tra
            try:
                # Kiểm tra DB save được gọi 3 lần (tên, địa chỉ, wifi)
                calls = db_mock.save_setting.call_args_list
                saved_data = {c[0][0]: c[0][1] for c in calls} # Dict {key: val}
                
                if saved_data.get('shop_name') == "Quán Net Test" and \
                   saved_data.get('wifi_pass') == "wifi123":
                    self.status = "PASS"
                    self.actual = "Đã lưu đúng tên quán và wifi xuống DB"
                else:
                    self.status = "FAIL"
                    self.actual = f"Dữ liệu lưu sai: {saved_data}"
            except Exception as e:
                self.status = "FAIL"
                self.actual = f"Lỗi: {e}"

        self.log_result("TC01", "Thông tin quán", "Sửa & Lưu", "Gọi save_setting đúng key/value")

    def test_TC02_update_prices(self):
        print(f"{Fore.CYAN}--- TC02: Cập nhật bảng giá ---")
        if not self.page: return

        # 1. Vào trang giá
        self.page._view_price()

        # 2. Sửa giá
        # ModernEntry được lưu trong dict self.prices
        self.page.prices['price_standard'].set("6000")
        self.page.prices['price_competition'].set("20000")

        # 3. Save
        with patch('tkinter.messagebox.showinfo'):
            self.page._save_price()

            # 4. Kiểm tra
            try:
                calls = db_mock.save_setting.call_args_list
                saved_data = {c[0][0]: c[0][1] for c in calls}
                
                if saved_data.get('price_standard') == "6000" and \
                   saved_data.get('price_competition') == "20000":
                    self.status = "PASS"
                    self.actual = "Đã cập nhật giá mới xuống DB"
                else:
                    self.status = "FAIL"
                    self.actual = f"Lưu sai giá: {saved_data}"
            except Exception as e:
                self.status = "FAIL"
                self.actual = f"Lỗi: {e}"

        self.log_result("TC02", "Bảng giá", "Sửa giá & Lưu", "DB cập nhật giá mới")

    def test_TC03_security_password_mismatch(self):
        print(f"{Fore.CYAN}--- TC03: Đổi mật khẩu (Không khớp) ---")
        if not self.page: return

        self.page._view_security()

        # Nhập 2 pass khác nhau
        self.page.inp_new.set("123456")
        self.page.inp_confirm.set("654321")

        with patch('tkinter.messagebox.showerror') as mock_err:
            self.page._save_security()
            
            if mock_err.called:
                # Đảm bảo KHÔNG gọi DB đổi pass
                db_mock.change_admin_password.assert_not_called()
                self.status = "PASS"
                self.actual = "Hiện lỗi & Không gọi DB"
            else:
                self.status = "FAIL"
                self.actual = "Không hiện thông báo lỗi"

        self.log_result("TC03", "Bảo mật", "Nhập pass lệch", "Báo lỗi, không lưu")

    def test_TC04_security_password_success(self):
        print(f"{Fore.CYAN}--- TC04: Đổi mật khẩu (Thành công) ---")
        if not self.page: return

        self.page._view_security()

        # Nhập pass khớp
        self.page.inp_new.set("newpass")
        self.page.inp_confirm.set("newpass")

        with patch('tkinter.messagebox.showinfo') as mock_info:
            self.page._save_security()
            
            try:
                db_mock.change_admin_password.assert_called_with("newpass")
                self.status = "PASS"
                self.actual = "Đã gọi change_admin_password('newpass')"
            except AssertionError:
                self.status = "FAIL"
                self.actual = "Chưa gọi hàm đổi pass DB"

        self.log_result("TC04", "Bảo mật", "Nhập pass khớp", "Gọi DB đổi pass")

    def test_TC05_navigation_flow(self):
        print(f"{Fore.CYAN}--- TC05: Kiểm tra điều hướng (Back) ---")
        if not self.page: return

        # 1. Đang ở trang Home -> Vào Info
        self.page._view_info()
        
        frame_id_1 = id(self.page.current_frame)
        
        # 2. Bấm Back (gọi _show_home)
        self.page._show_home()
        frame_id_2 = id(self.page.current_frame)

        if frame_id_1 != frame_id_2:
            self.status = "PASS"
            self.actual = "Frame đã được thay đổi (Navigation OK)"
        else:
            self.status = "FAIL"
            self.actual = "Frame không đổi"

        self.log_result("TC05", "Điều hướng", "Vào trang con -> Back", "Quay về trang chủ")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.wb.save("test_system_settings_report.xlsx")
            print(f"\n{Fore.CYAN}================================================")
            print("✅ Đã xuất báo cáo: test_system_settings_report.xlsx")
        except: pass

if __name__ == "__main__":
    unittest.main(verbosity=2)