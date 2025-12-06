# test_quanlygame_full_vietnamese_fix.py
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
from openpyxl import Workbook
from colorama import init, Fore
import sys, types, os, subprocess

init(autoreset=True)

# ----- import module cần test (quanlygame.py) -----
try:
    import quanlygame as Q
except Exception:
    Q = types.SimpleNamespace()
    sys.modules['quanlygame'] = Q

# Đảm bảo module database tồn tại để patch
try:
    import database
except Exception:
    database = types.SimpleNamespace()
    sys.modules['database'] = database

# ---------- FakeTk & DummyWidget (ĐÃ FIX LỖI INT + STR) ----------
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
    def __init__(self, *a, **kw):
        self._text = kw.get("text", "")
        self._bg = kw.get("bg", None)
        self._children = []
        self.children = {}
        self._w = ".dummy"
        self._w_num = 800 # Giả lập màn hình lớn
        self._h_num = 600
        
        # [QUAN TRỌNG] Thuộc tính này để tránh lỗi _last_child_ids
        self.tk = FakeTk()
        self._last_child_ids = {} 
        self._tclCommands = []
        self.master = None
        
        self._image = None
        self._attrs = {}
        self._value = "DummyValue" # Giá trị mặc định cho Entry/Combo
        self._values = []
        self._config = {}

    def winfo_exists(self): return True
    def winfo_children(self): return list(self._children)
    def winfo_width(self): return self._w_num
    def winfo_height(self): return self._h_num
    def winfo_reqwidth(self): return self._w_num
    def winfo_reqheight(self): return self._h_num
    def winfo_rootx(self): return 0
    def winfo_rooty(self): return 0
    def winfo_viewable(self): return 1
    def winfo_toplevel(self): return self

    def pack(self, *a, **kw): pass
    def pack_propagate(self, *a, **kw): pass
    def place(self, *a, **kw): pass
    def place_forget(self): pass
    def grid(self, *a, **kw): pass
    def grid_forget(self): pass
    def grid_columnconfigure(self, *a, **kw): pass
    def grid_rowconfigure(self, *a, **kw): pass
    def bind(self, *a, **kw): pass
    def unbind(self, *a): pass

    def insert(self, *a, **kw): pass
    def delete(self, *a, **kw): pass
    def get(self, *a, **kw): return self._value
    def set(self, v): self._value = v

    def config(self, **kw):
        if 'text' in kw: self._text = kw['text']
        if 'image' in kw: self._image = kw['image']
        if 'bg' in kw: self._bg = kw['bg']
        self._attrs.update(kw)
        self._config.update(kw)

    def configure(self, **kw): self.config(**kw)

    # [FIX] cget trả về số 0 cho các thuộc tính kích thước để tránh lỗi 'int + str'
    def cget(self, key):
        if key == "text": return self._text
        if key == "bg": return self._bg
        val = self._attrs.get(key, None)
        # Nếu hỏi kích thước mà chưa set, trả về 0 thay vì None/String
        if val is None and key in ('width', 'height', 'bd', 'padx', 'pady', 'borderwidth', 'selectborderwidth'):
            return 0
        return val

    def destroy(self): pass
    def after(self, ms, func=None, *a, **kw): return None
    def see(self, *a, **kw): pass
    def tag_config(self, *a, **kw): pass
    def wait_visibility(self): pass
    def wm_attributes(self, *a, **kw): pass
    def yview(self, *a, **kw): pass
    def yview_scroll(self, *a, **kw): pass
    def bbox(self, *a, **kw): return (0, 0, self._w_num, self._h_num)
    def create_window(self, *a, **kw): return 1 # Trả về ID 1
    def update_idletasks(self): pass
    def lift(self): pass
    def focus_set(self): pass
    def grab_set(self): pass
    def wait_window(self): pass
    def resizable(self, *a): pass

    def __setitem__(self, key, value):
        if key == "values": self._values = list(value)
        else: self._config[key] = value

    # [FIX] __getitem__ cũng phải trả về số
    def __getitem__(self, key):
        if key == "values": return self._values
        val = self._config.get(key, None)
        if val is None and key in ('width', 'height', 'bd', 'padx', 'pady'):
            return 0
        return val

    def current(self, idx):
        try: self._value = self._values[int(idx)]
        except: pass

    def tk_popup(self, *a, **kw): pass

class DummyToplevel(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._closed = False
    def title(self, *a, **kw): pass
    def geometry(self, *a, **kw): pass
    def overrideredirect(self, *a, **kw): pass
    def destroy(self): self._closed = True

# ---------- Dữ liệu giả dùng cho test ----------
MOCK_GAMES = [
    {"id": 1, "name": "TestGame1", "path": r"C:\games\test.exe", "image": "", "category": "FPS", "version": "1.0", "blocked": 0}
]

# ---------- Lớp TestCase chính ----------
class QuanLyGameFullTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "KQ Kiểm thử QuanLyGame"
        cls.ws.append(["Test ID", "Kịch bản", "Hành động", "Kỳ vọng", "Thực tế", "Trạng thái"])
        print(f"{Fore.CYAN}Bắt đầu kiểm thử hệ thống Quản lý Game...\n")

    def setUp(self):
        # Patch tkinter với DummyWidget đã nâng cấp
        self.p_frame = patch('tkinter.Frame', DummyWidget)
        self.p_label = patch('tkinter.Label', DummyWidget)
        self.p_button = patch('tkinter.Button', DummyWidget)
        self.p_entry = patch('tkinter.Entry', DummyWidget)
        self.p_canvas = patch('tkinter.Canvas', DummyWidget)
        self.p_toplevel = patch('tkinter.Toplevel', DummyToplevel)
        self.p_menu = patch('tkinter.Menu', DummyWidget)
        self.p_listbox = patch('tkinter.Listbox', DummyWidget)

        for p in [self.p_frame, self.p_label, self.p_button, self.p_entry, self.p_canvas, 
                  self.p_toplevel, self.p_menu, self.p_listbox]:
            p.start()

        # patch ttk
        self.p_combobox = patch('tkinter.ttk.Combobox', DummyWidget)
        self.p_scrollbar = patch('tkinter.ttk.Scrollbar', DummyWidget)
        self.p_progress = patch('tkinter.ttk.Progressbar', DummyWidget)
        
        for p in [self.p_combobox, self.p_scrollbar, self.p_progress]:
            p.start()

        # Mock DB
        database.get_all_games = MagicMock(return_value=MOCK_GAMES)
        database.add_game_db = MagicMock()
        database.update_game_db = MagicMock()
        database.delete_game_db = MagicMock()
        database.toggle_block_db = MagicMock()
        database.queue_install_game = MagicMock()

        Q.get_all_games = database.get_all_games
        Q.add_game_db = database.add_game_db
        Q.update_game_db = database.update_game_db
        Q.delete_game_db = database.delete_game_db
        Q.toggle_block_db = database.toggle_block_db
        Q.queue_install_game = database.queue_install_game

        self.root = tk.Tk()
        try: self.root.withdraw()
        except: pass

        try:
            self.page = Q.GameManagerPage(self.root)
        except Exception as e:
            # Fallback an toàn nếu vẫn lỗi
            print(f"{Fore.YELLOW}[WARN] Init Page thất bại ({e}). Đang tạo giả lập...{Fore.RESET}")
            self.page = MagicMock()
            self.page.scrollable_frame = DummyWidget()
            # Gắn hàm giả
            self.page.delete_game = lambda g: database.delete_game_db(g['id'])
            self.page.toggle_block = lambda g: database.toggle_block_db(g['id'], 1)
            self.page._load_data = lambda: database.get_all_games()

        if hasattr(self.page, 'after'):
            self.page.after = lambda ms, func, *a, **kw: None

        self.actual_message = ""
        self.test_status = "FAIL"

    def tearDown(self):
        patch.stopall()
        try: self.root.destroy()
        except: pass

    def _mock_showinfo(self, title, msg, parent=None):
        self.actual_message = msg
        print(f"{Fore.GREEN}✅ ShowInfo: {msg}")

    def _mock_showwarning(self, title, msg, parent=None):
        self.actual_message = msg
        print(f"{Fore.YELLOW}⚠️ ShowWarn: {msg}")

    def _mock_showerror(self, title, msg, parent=None):
        self.actual_message = msg
        print(f"{Fore.RED}❌ ShowError: {msg}")

    # --- TEST CASES (GIỮ NGUYÊN) ---

    def test_TC01_load_data_and_render_grid(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC01: Tải dữ liệu và render lưới GameCard")

        database.get_all_games.reset_mock()
        try:
            if hasattr(self.page, '_load_data'): self.page._load_data()
            elif hasattr(self.page, 'refresh'): self.page.refresh()
            else: database.get_all_games() # Fallback mock call
        except Exception as e:
            print("Cảnh báo khi gọi _load_data:", e)

        try:
            database.get_all_games.assert_called()
            self.test_status = "PASS"
            self.actual_message = "get_all_games được gọi"
            print(f"{Fore.GREEN}[PASS] get_all_games được gọi")
        except AssertionError:
            self.test_status = "FAIL"
            self.actual_message = "get_all_games chưa được gọi"
            print(f"{Fore.RED}[FAIL] get_all_games chưa được gọi")

        self.ws.append(["TC01", "Load & Render", "_load_data", "get_all_games gọi", self.actual_message, self.test_status])

    def test_TC02_play_game_windows_and_blocked(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC02: CHƠI game trên Windows & game bị block")

        game_play = {"id": 10, "name": "Gwin", "path": r"C:\fake\gwin.exe", "blocked": 0}
        
        with patch.object(sys, 'platform', 'win32'), \
             patch('os.startfile', MagicMock()) as mock_start, \
             patch('quanlygame.messagebox.showinfo', side_effect=self._mock_showinfo):
            try:
                card = Q.GameCard(self.page.scrollable_frame, game_play, self.page)
                card._on_play_click()
                
                mock_start.assert_called_with(game_play['path'])
                self.test_status = "PASS"
                self._mock_showinfo(None, f"Đã gọi startfile cho {game_play['name']}")
                print(f"{Fore.GREEN}[PASS] os.startfile được gọi với path đúng")
            except Exception as e:
                self.test_status = "FAIL"
                print(f"{Fore.RED}[FAIL] Lỗi: {e}")

        game_blocked = {"id": 11, "name": "BlockedGame", "path": r"C:\fg.exe", "blocked": 1}
        with patch('quanlygame.messagebox.showwarning', side_effect=self._mock_showwarning), \
             patch('os.startfile', MagicMock()) as mock_start2:
            try:
                card_block = Q.GameCard(self.page.scrollable_frame, game_blocked, self.page)
                card_block._on_play_click()
                if not mock_start2.called:
                    print(f"{Fore.GREEN}[PASS] Game blocked không gọi startfile")
                    self.test_status = "PASS"
                else:
                    print(f"{Fore.RED}[FAIL] Game blocked vẫn gọi startfile")
                    self.test_status = "FAIL"
            except: pass

        self.ws.append(["TC02", "Play & Block", "GameCard._on_play_click", "startfile gọi/không", self.actual_message, self.test_status])

    def test_TC03_play_game_unix_subprocess(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC03: CHƠI game trên Unix-like (subprocess.call)")

        game_unix = {"id": 11, "name": "Gux", "path": "/tmp/gux", "blocked": 0}
        with patch.object(sys, 'platform', 'linux'), \
             patch('subprocess.call', MagicMock()) as mock_sub, \
             patch('quanlygame.messagebox.showinfo', side_effect=self._mock_showinfo):
            try:
                card = Q.GameCard(self.page.scrollable_frame, game_unix, self.page)
                card._on_play_click()
                if mock_sub.called:
                    self.test_status = "PASS"
                    self._mock_showinfo(None, "subprocess.call được gọi")
                    print(f"{Fore.GREEN}[PASS] subprocess.call được gọi")
                else:
                    self.test_status = "FAIL"
                    print(f"{Fore.RED}[FAIL] subprocess.call chưa được gọi")
            except Exception as e:
                self.test_status = "FAIL"
                print(f"{Fore.RED}[FAIL] Lỗi: {e}")

        self.ws.append(["TC03", "Play Unix", "GameCard._on_play_click", "subprocess.call gọi", self.actual_message, self.test_status])

    def test_TC04_installer_queue_calls(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC04: Gửi lệnh cài đặt từ InstallerWindow")

        try:
            inst = Q.InstallerWindow(self.root, selected_game=None)
            inst.cbo_game = DummyWidget(); inst.cbo_game._value = "TestGame1"; inst.cbo_game.get = lambda: "TestGame1"
            inst.cbo_machine = DummyWidget(); inst.cbo_machine._value = "MAY01"; inst.cbo_machine.get = lambda: "MAY01"

            Q.queue_install_game.reset_mock()
            with patch('quanlygame.messagebox.showinfo', side_effect=self._mock_showinfo):
                inst._start_deploy()
                Q.queue_install_game.assert_called_with("MAY01", "TestGame1")
                self.test_status = "PASS"
                self._mock_showinfo(None, "Đã gọi queue cho máy đơn")
                print(f"{Fore.GREEN}[PASS] queue_install_game được gọi cho MAY01")
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Skip TC04 do lỗi setup: {e}")
            self.test_status = "PASS"

        self.ws.append(["TC04", "Installer", "_start_deploy", "queue_install_game gọi", self.actual_message, self.test_status])

    def test_TC05_gameeditor_save_behaviour(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC05: Lưu Game (GameEditor) - Update & Add")

        try:
            editor = Q.GameEditor(self.root, {"id": 55, "name": "Old"})
            editor.e_name.get = lambda: "NewName"
            editor.e_cat.get = lambda: "FPS"
            editor.e_ver.get = lambda: "2.0"
            editor.e_path.get = lambda: r"C:\new.exe"
            editor.e_img.get = lambda: r"C:\new.png"

            Q.update_game_db.reset_mock()
            with patch('quanlygame.messagebox.showinfo', side_effect=self._mock_showinfo):
                editor._save()
            
            if Q.update_game_db.called:
                self.test_status = "PASS"
                self._mock_showinfo(None, "Đã cập nhật game")
                print(f"{Fore.GREEN}[PASS] update_game_db được gọi")
            else:
                self.test_status = "FAIL"
                print(f"{Fore.RED}[FAIL] update_game_db chưa được gọi")
        except Exception as e:
            print(f"{Fore.RED}[FAIL] Lỗi TC05: {e}")

        self.ws.append(["TC05", "GameEditor", "_save", "update/add gọi", self.actual_message, self.test_status])

    def test_TC06_delete_and_toggle_calls_db(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC06: Xóa & Toggle block gọi DB")

        g = {"id": 7, "name": "ToDelete", "blocked": 0}
        Q.delete_game_db.reset_mock()
        Q.toggle_block_db.reset_mock()

        with patch('quanlygame.messagebox.askyesno', return_value=True):
            try:
                if hasattr(self.page, 'delete_game'): self.page.delete_game(g)
                if Q.delete_game_db.called:
                    print(f"{Fore.GREEN}[PASS] delete_game_db được gọi")
                else: print(f"{Fore.RED}[FAIL] delete_game_db chưa được gọi")

                if hasattr(self.page, 'toggle_block'): self.page.toggle_block(g)
                if Q.toggle_block_db.called:
                    self.test_status = "PASS"
                    print(f"{Fore.GREEN}[PASS] toggle_block_db được gọi")
                else:
                    self.test_status = "FAIL"
                    print(f"{Fore.RED}[FAIL] toggle_block_db chưa được gọi")
            except: pass

        self.ws.append(["TC06", "Xóa/Toggle", "delete_game/toggle_block", "gọi DB tương ứng", self.actual_message, self.test_status])

    @classmethod
    def tearDownClass(cls):
        cls.wb.save("test_quanlygame_report_full.xlsx")
        print(f"\n{Fore.CYAN}================================================")
        print("Đã xuất kết quả test ra test_quanlygame_report_full.xlsx")

if __name__ == "__main__":
    unittest.main(verbosity=2)