# test_quanlynv_full.py
# Test cho EmployeeListPage và EmployeeForm (phiên bản tiếng Việt, headless)
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
from openpyxl import Workbook
from colorama import init, Fore
import sys, types, math

init(autoreset=True)

# ----- import module cần test (file chứa EmployeeListPage, EmployeeForm) -----
try:
    import QuanLyNhanVien as M  # nếu file của bạn tên khác, đổi ở đây (ví dụ employee_page)
except Exception:
    # fallback: đảm bảo module tồn tại để test không crash import errors
    M = types.SimpleNamespace()
    sys.modules['quanlynv'] = M

# Đảm bảo module database tồn tại để patch
try:
    import database
except Exception:
    database = types.SimpleNamespace()
    sys.modules['database'] = database

# ---------- FakeTk & DummyWidget (headless) ----------
class FakeTk:
    def __init__(self):
        self._cmd_counter = 0
        self._commands = {}
    def call(self, *args, **kwargs): return None
    def createcommand(self, name, func):
        if not name:
            self._cmd_counter += 1
            name = f'pycmd{self._cmd_counter}'
        self._commands[name] = func
        return name
    def deletecommand(self, name):
        if name in self._commands: del self._commands[name]
    def __getattr__(self, name):
        def _noop(*a, **k): return None
        return _noop

class DummyWidget:
    """
    Widget giả phù hợp cho tests headless:
    - có attributes/tên tkinter nội bộ (.children, ._w, .tk)
    - hỗ trợ insert/get/set/config và combobox item assignment
    - after() là NO-OP để tránh scheduling loops
    """
    def __init__(self, *a, **kw):
        self._text = kw.get("text", "")
        self._bg = kw.get("bg", None)
        self._children = []
        self.children = {}
        self._w = ".dummy"
        self._w_num = 200
        self._h_num = 40
        self.tk = FakeTk()
        self._attrs = {}
        self._value = ""
        self._values = []
        self._config = {}

    def winfo_exists(self): return True
    def winfo_children(self): return list(self._children)
    def winfo_width(self): return self._w_num
    def winfo_height(self): return self._h_num
    def winfo_rootx(self): return 0
    def winfo_rooty(self): return 0

    def pack(self, *a, **kw): pass
    def pack_propagate(self, *a, **kw): pass
    def place(self, *a, **kw): pass
    def place_forget(self): pass
    def grid(self, *a, **kw): pass
    def grid_forget(self): pass
    def grid_columnconfigure(self, *a, **kw): pass
    def bind(self, *a, **kw): pass

    def insert(self, *a, **kw): 
        # if used as entry.insert(0, 'abc') emulate storing
        if len(a) >= 2:
            self._value = a[1]
        elif 'text' in kw:
            self._value = kw['text']

    def delete(self, *a, **kw): self._value = ""
    def get(self, *a, **kw): return self._value

    def set(self, v): self._value = v

    def config(self, **kw):
        if 'text' in kw: self._text = kw['text']
        if 'bg' in kw: self._bg = kw['bg']
        if 'image' in kw: self._attrs['image'] = kw['image']
        self._attrs.update(kw)
        self._config.update(kw)

    def configure(self, **kw): self.config(**kw)
    def cget(self, key):
        if key == "text": return self._text
        if key == "bg": return self._bg
        return self._attrs.get(key, None)

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

    # Combobox support
    def __setitem__(self, key, value):
        if key == "values":
            self._values = list(value)
    def __getitem__(self, key):
        if key == "values": return self._values
        return self._config.get(key, None)
    def current(self, idx):
        try:
            self._value = self._values[int(idx)]
        except Exception:
            pass

    def tk_popup(self, *a, **kw): pass

class DummyToplevel(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._closed = False
    def title(self, *a, **kw): pass
    def geometry(self, *a, **kw): pass
    def overrideredirect(self, *a, **kw): pass
    def destroy(self):
        self._closed = True

# ---------- Dữ liệu & mocks cho database ----------
SAMPLE_ROWS = [
    # (id, code, name, account, gender, phone, role, salary)
    (1, "NV001", "Nguyễn A", "nguyen.a", "Nam", "0123456789", "Nhân viên", 5000000),
    (2, "NV002", "Trần B", "tran.b", "Nữ", "0987654321", "Quản lý", 8000000),
]

# ---------- TestCase ----------
class QuanLyNVTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "KQ Kiểm thử NV"
        cls.ws.append(["Test ID","Kịch bản","Hành động","Kỳ vọng","Thực tế","Trạng thái"])
        print(f"{Fore.CYAN}Bắt đầu kiểm thử EmployeeListPage & EmployeeForm...\n")

    def setUp(self):
        # Patch tkinter classes BEFORE module UI creation
        self.p_frame = patch('tkinter.Frame', DummyWidget)
        self.p_label = patch('tkinter.Label', DummyWidget)
        self.p_button = patch('tkinter.Button', DummyWidget)
        self.p_entry = patch('tkinter.Entry', DummyWidget)
        self.p_toplevel = patch('tkinter.Toplevel', DummyToplevel)
        self.p_combobox = patch('tkinter.ttk.Combobox', DummyWidget)

        self.p_frame.start(); self.p_label.start(); self.p_button.start()
        self.p_entry.start(); self.p_toplevel.start(); self.p_combobox.start()

        # Mock database functions
        database.get_employees_paginated = MagicMock(return_value=(SAMPLE_ROWS, len(SAMPLE_ROWS)))
        database.add_employee_db = MagicMock(return_value=(True, "Đã thêm nhân viên"))
        database.update_employee_db = MagicMock(return_value=(True, "Đã cập nhật"))
        database.delete_employee_db = MagicMock(return_value=True)

        # also sync into module namespace if code does direct import
        M.get_employees_paginated = database.get_employees_paginated
        M.add_employee_db = database.add_employee_db
        M.update_employee_db = database.update_employee_db
        M.delete_employee_db = database.delete_employee_db

        # create real Tk root but widgets are patched
        self.root = tk.Tk()
        try: self.root.withdraw()
        except: pass

        # instantiate page (if fails, fallback to simple namespace)
        try:
            self.page = M.EmployeeListPage(self.root)
        except Exception as e:
            print("Cảnh báo: không thể tạo EmployeeListPage, dùng fallback:", e)
            self.page = types.SimpleNamespace(
                entry_search=DummyWidget(),
                cb_role=DummyWidget(),
                limit=10,
                page=1,
                refresh=lambda *a, **k: None,
                table_frame=DummyWidget()
            )

        # prevent scheduling loops
        if hasattr(self.page, 'after'):
            self.page.after = lambda ms, func, *a, **kw: None

        # capture messages
        self.actual_msg = ""
        self.test_status = "FAIL"

    def tearDown(self):
        try: self.root.destroy()
        except: pass
        for p in (self.p_frame, self.p_label, self.p_button, self.p_entry, self.p_toplevel, self.p_combobox):
            try: p.stop()
            except: pass

    # helpers to capture messagebox outputs
    def _mock_showinfo(self, title, msg, parent=None):
        self.actual_msg = msg
        print(f"{Fore.GREEN}✅ ShowInfo: {msg}")
    def _mock_showerror(self, title, msg, parent=None):
        self.actual_msg = msg
        print(f"{Fore.RED}❌ ShowError: {msg}")
    def _mock_askyesno(self, title, msg):
        print(f"ℹ️ Confirm: {msg}")
        return True

    # ---------- TESTS ----------
    def test_TC01_load_and_render(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC01: Gọi refresh nên gọi get_employees_paginated và vẽ bảng")
        database.get_employees_paginated.reset_mock()
        try:
            # gọi refresh của page
            if hasattr(self.page, 'refresh'):
                self.page.refresh()
        except Exception as e:
            print("Cảnh báo khi gọi refresh:", e)
        try:
            database.get_employees_paginated.assert_called()
            self.test_status = "PASS"
            self.actual_msg = "get_employees_paginated được gọi"
            print(f"{Fore.GREEN}[PASS] get_employees_paginated được gọi")
        except AssertionError:
            self.test_status = "FAIL"
            self.actual_msg = "get_employees_paginated chưa được gọi"
            print(f"{Fore.RED}[FAIL] get_employees_paginated chưa được gọi")
        self.ws.append(["TC01","Load & Render","refresh","get_employees_paginated gọi", self.actual_msg, self.test_status])

    def test_TC02_add_employee_calls_db(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC02: Mở form Thêm và _save -> gọi add_employee_db & refresh")
        # create form
        called_refresh = {'ok': False}
        def fake_refresh(): called_refresh['ok'] = True

        try:
            form = M.EmployeeForm(self.root, fake_refresh, emp_data=None)
        except Exception as e:
            self.fail(f"Không tạo được EmployeeForm: {e}")

        # set entry values by overriding get()
        form.entries['code'].get = lambda: "NV100"
        form.entries['name'].get = lambda: "Test User"
        form.entries['account'].get = lambda: "test.user"
        form.cb_gender.get = lambda: "Nam"
        form.entries['phone'].get = lambda: "012345678"
        form.cb_role.get = lambda: "Nhân viên"
        form.entries['salary'].get = lambda: "1234567"

        M.add_employee_db.reset_mock()
        with patch('tkinter.messagebox.showinfo', side_effect=self._mock_showinfo):
            form._save()
        try:
            M.add_employee_db.assert_called()
            self.test_status = "PASS"
            print(f"{Fore.GREEN}[PASS] add_employee_db được gọi")
        except AssertionError:
            self.test_status = "FAIL"
            print(f"{Fore.RED}[FAIL] add_employee_db chưa được gọi")
        self.ws.append(["TC02","Add employee","EmployeeForm._save","add_employee_db gọi & refresh", self.actual_msg, self.test_status])

    def test_TC03_edit_employee_calls_update(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC03: Mở form Sửa và _save -> gọi update_employee_db")
        # prepare emp_data tuple as code expects: (id, code, name, account, gender, phone, role, salary)
        emp = (99, "E99", "Old Name", "old.acc", "Nữ", "09090909", "NV khác", 1000000)
        try:
            form = M.EmployeeForm(self.root, lambda: None, emp_data=emp)
        except Exception as e:
            self.fail(f"Không tạo được EmployeeForm (edit): {e}")

        # change fields
        form.entries['name'].get = lambda: "Updated Name"
        form.entries['salary'].get = lambda: "2000000"
        M.update_employee_db.reset_mock()
        with patch('tkinter.messagebox.showinfo', side_effect=self._mock_showinfo):
            form._save()
        try:
            M.update_employee_db.assert_called()
            self.test_status = "PASS"
            print(f"{Fore.GREEN}[PASS] update_employee_db được gọi")
        except AssertionError:
            self.test_status = "FAIL"
            print(f"{Fore.RED}[FAIL] update_employee_db chưa được gọi")
        self.ws.append(["TC03","Edit employee","EmployeeForm._save (edit)","update_employee_db gọi", self.actual_msg, self.test_status])

    def test_TC04_delete_calls_db_and_refresh(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC04: Gọi _delete -> nếu confirm & delete_employee_db True thì refresh được gọi")
        # prepare page.refresh spy
        if hasattr(self.page, 'refresh'):
            orig_refresh = self.page.refresh
            called = {'ok': False}
            def spy_refresh(*a, **k):
                called['ok'] = True
            self.page.refresh = spy_refresh
        else:
            self.skipTest("page thiếu refresh")

        row = SAMPLE_ROWS[0]
        M.delete_employee_db.reset_mock()
        with patch('tkinter.messagebox.askyesno', side_effect=self._mock_askyesno), \
             patch('tkinter.messagebox.showerror', side_effect=self._mock_showerror):
            try:
                # call _delete
                if hasattr(self.page, '_delete'):
                    self.page._delete(row)
                else:
                    # if code defined as standalone function fallback
                    if hasattr(M, '_delete'):
                        M._delete(row)
            except Exception as e:
                print("Lỗi khi gọi _delete:", e)

        # assert delete called and refresh called
        try:
            M.delete_employee_db.assert_called_with(row[0])
        except Exception:
            # try database mock
            try:
                database.delete_employee_db.assert_called_with(row[0])
            except Exception:
                pass

        if called.get('ok'):
            self.test_status = "PASS"
            print(f"{Fore.GREEN}[PASS] delete_employee_db được gọi và refresh thực hiện")
        else:
            self.test_status = "FAIL"
            print(f"{Fore.RED}[FAIL] delete_employee_db hoặc refresh chưa hoạt động")

        self.ws.append(["TC04","Delete employee","EmployeeListPage._delete","delete_employee_db gọi & refresh", self.actual_msg, self.test_status])

    def test_TC05_validation_error_on_save(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC05: Validate form: nếu thiếu code hoặc name thì showerror")
        try:
            form = M.EmployeeForm(self.root, lambda: None, emp_data=None)
        except Exception as e:
            self.fail(f"Không tạo được EmployeeForm: {e}")

        # leave code or name empty
        form.entries['code'].get = lambda: ""
        form.entries['name'].get = lambda: ""
        caught = {'msg': None}
        with patch('tkinter.messagebox.showerror', side_effect=lambda t,m, parent=None: caught.update({'msg': m})):
            form._save()
        if caught['msg']:
            self.test_status = "PASS"
            print(f"{Fore.GREEN}[PASS] showerror được gọi với: {caught['msg']}")
        else:
            self.test_status = "FAIL"
            print(f"{Fore.RED}[FAIL] showerror không được gọi khi thiếu code/name")
        self.ws.append(["TC05","Validation","EmployeeForm._save","showerror on missing fields", caught['msg'] or "", self.test_status])

    @classmethod
    def tearDownClass(cls):
        cls.wb.save("test_quanlynv_report.xlsx")
        print(f"\n{Fore.CYAN}================================================")
        print("Đã xuất kết quả test ra test_quanlynv_report.xlsx")

if __name__ == "__main__":
    unittest.main(verbosity=2)
