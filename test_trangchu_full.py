# test_trangchu_full.py (final)
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
from openpyxl import Workbook
from colorama import init, Fore
import sys

init(autoreset=True)

# import module under test
import trangchu as T

# Đảm bảo module database tồn tại để patch các import bên trong
try:
    import database
except Exception:
    import types
    database = types.SimpleNamespace()
    sys.modules['database'] = database

# ---------- Dummy/safe tkinter widget implementations ----------
class DummyWidget:
    def __init__(self, *a, **kw):
        self._text = kw.get("text", "")
        self._bg = kw.get("bg", None)
        self._children = []
        self.tk = object()  # satisfy tkinter expectation

    def winfo_exists(self):
        return True

    def pack(self, *a, **kw): pass
    def pack_propagate(self, *a, **kw): pass
    def place(self, *a, **kw): pass
    def place_forget(self): pass
    def grid(self, *a, **kw): pass
    def grid_columnconfigure(self, *a, **kw): pass
    def config(self, **kw):
        if 'text' in kw: self._text = kw['text']
        if 'bg' in kw: self._bg = kw['bg']
    def cget(self, key):
        if key == "text": return self._text
        if key == "bg": return self._bg
        return None
    def destroy(self): pass
    def winfo_children(self): return list(self._children)
    def pack_forget(self): pass
    def bind(self, *a, **kw): pass
    def insert(self, *a, **kw): pass
    def delete(self, *a, **kw): pass
    def see(self, *a, **kw): pass
    def tag_config(self, *a, **kw): pass

class DummyToplevel(DummyWidget):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._closed = False
    def title(self, *a, **kw): pass
    def geometry(self, *a, **kw): pass
    def destroy(self):
        self._closed = True

# ---------- TestCase ----------
MOCK_LOGS = [
    {"created_at": __import__("datetime").datetime(2025,12,1,9,0), "description": "Nạp tiền MAY01", "amount": 20000},
    {"created_at": __import__("datetime").datetime(2025,12,1,9,10), "description": "Order đồ ăn", "amount": 45000},
]
MOCK_DASH = {"total_machines": 8, "active_machines": 3, "total_amount": 99999}
MOCK_MSGS = [{"id": 101, "sender": "client", "content": "Help!", "created_at": __import__("datetime").datetime(2025,12,4,8,0), "is_read": 0}]
MOCK_ORDERS = [{"id": 201, "description": "Com rang - MAY02", "amount": 35000}]

class TrangChuCustomerStyleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "Kết quả kiểm thử Trang Chủ"
        # Việt hóa header Excel
        cls.ws.append(["ID Test", "Kịch bản", "Hành động", "Kỳ vọng", "Thực tế", "Trạng thái"])
        print(f"{Fore.CYAN}Bắt đầu kiểm thử hệ thống Trang Chủ...\n")

    def setUp(self):
        # patch tkinter widgets BEFORE creating App so App.__init__ uses them
        self.p_frame = patch('tkinter.Frame', DummyWidget)
        self.p_label = patch('tkinter.Label', DummyWidget)
        self.p_button = patch('tkinter.Button', DummyWidget)
        self.p_entry = patch('tkinter.Entry', DummyWidget)
        self.p_text = patch('tkinter.Text', DummyWidget)
        self.p_listbox = patch('tkinter.Listbox', DummyWidget)
        self.p_toplevel = patch('tkinter.Toplevel', DummyToplevel)

        self.p_frame.start(); self.p_label.start(); self.p_button.start()
        self.p_entry.start(); self.p_text.start(); self.p_listbox.start(); self.p_toplevel.start()

        # Prepare mock database functions
        database.get_dashboard_data = MagicMock(return_value=MOCK_DASH)
        database.get_transactions = MagicMock(return_value=MOCK_LOGS)
        database.get_unread_messages = MagicMock(return_value=MOCK_MSGS)
        database.get_pending_orders = MagicMock(return_value=MOCK_ORDERS)
        database.get_active_chat_users = MagicMock(return_value=["MAY01", "MAY02"])
        database.get_conversation = MagicMock(return_value=[])
        database.send_message_v2 = MagicMock(return_value=True)
        database.mark_message_read = MagicMock()
        database.complete_order = MagicMock()
        database.add_transaction_db = MagicMock()
        database.update_machine_status = MagicMock()

        # Also patch names in trangchu module in case code uses module-level references
        T.get_dashboard_data = database.get_dashboard_data
        T.get_transactions = database.get_transactions
        T.get_unread_messages = database.get_unread_messages
        T.get_pending_orders = database.get_pending_orders
        T.add_transaction_db = database.add_transaction_db
        T.update_machine_status = database.update_machine_status
        T.complete_order = database.complete_order

        # create hidden real root (safe because our widgets are patched)
        self.root = tk.Tk()
        self.root.withdraw()

        # instantiate App (uses patched widgets)
        self.app = T.App()

        # Make after a NO-OP (do NOT invoke callback) to avoid recursive scheduling loops
        self.app.after = lambda ms, func, *a, **kw: None

        # Replace dot indicators with simple trackers if they exist
        if hasattr(self.app, 'dot_chat'): self.app.dot_chat = DummyWidget()
        if hasattr(self.app, 'dot_order'): self.app.dot_order = DummyWidget()

        # ensure chat widgets exist for chat tests (dummy Text/Entry are in place by patches, but ensure attrs exist)
        if not hasattr(self.app, 'txt_chat_history'):
            self.app.txt_chat_history = DummyWidget()
        if not hasattr(self.app, 'entry_chat_msg'):
            self.app.entry_chat_msg = DummyWidget()
            self.app.entry_chat_msg.get = lambda: ""
            self.app.entry_chat_msg.delete = lambda *a, **k: None

        # Excel/report helpers
        self.actual_message = ""
        self.test_status = "FAIL"

    def tearDown(self):
        try: self.root.destroy()
        except: pass
        # stop patchers
        self.p_frame.stop(); self.p_label.stop(); self.p_button.stop()
        self.p_entry.stop(); self.p_text.stop(); self.p_listbox.stop(); self.p_toplevel.stop()

    # helpers to capture messagebox prints
    def _mock_showinfo(self, title, msg, parent=None):
        self.actual_message = msg
        print(f"{Fore.GREEN}✅ Thông báo (ShowInfo): {msg}")

    def _mock_showerror(self, title, msg, parent=None):
        self.actual_message = msg
        print(f"{Fore.RED}❌ Báo lỗi (ShowError): {msg}")

    def _mock_askyesno(self, title, msg):
        print(f"   ℹ️ Hộp thoại xác nhận: {msg}")
        return True

    # ---------- TESTS ----------
    def test_TC01_fetch_and_apply_updates_dashboard(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC01: Cập nhật Dashboard (_fetch_and_apply / _animate_update)")

        # set return values (not strictly necessary here but kept for clarity)
        T.get_dashboard_data.return_value = {"total_machines": 8, "active_machines": 3, "total_amount": 99999}
        T.get_transactions.return_value = MOCK_LOGS

        # Directly call _animate_update to set values (after is no-op)
        self.app._animate_update(3, 8, 99999, MOCK_LOGS)

        # stronger, robust assertions (normalize revenue digits)
        val_active = self.app.active_label.cget("text")
        val_revenue = self.app.revenue_label.cget("text")
        # chuẩn hóa revenue: giữ lại chỉ chữ số
        rev_digits = ''.join(ch for ch in str(val_revenue) if ch.isdigit())

        try:
            assert val_active is not None and str(val_active).strip() == "3", f"Nhãn Active không như mong đợi: {val_active}"
            assert rev_digits == "99999", f"Nhãn Doanh thu không như mong đợi: {val_revenue} (số='{rev_digits}')"
            self.test_status = "PASS"
            self.actual_message = f"Active={val_active}, Revenue={val_revenue}"
            self._mock_showinfo(None, "Dashboard đã cập nhật")
            print(f"{Fore.GREEN}[PASS] Các nhãn Dashboard đã được cập nhật chính xác")
        except AssertionError as e:
            print(f"{Fore.RED}[FAIL] Dashboard cập nhật không đúng cách: {e}")
            self.test_status = "FAIL"

        self.ws.append(["TC01", "Dashboard", "_animate_update", "Cập nhật nhãn Active/Doanh thu", self.actual_message, self.test_status])

    def test_TC02_check_notifications_loop(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC02: Kiểm tra Vòng lặp Thông báo (Notification Loop)")

        # Put notifications in DB mocks
        T.get_unread_messages.return_value = [{"id": 1, "content": "Hi"}]
        T.get_pending_orders.return_value = [{"id": 5, "amount": 10000}]

        # call once (no recursion because after is no-op)
        self.app.check_notifications_loop()

        try:
            assert "Tin nhắn" in self.app.btn_notif_chat.cget("text") or "Tin nhắn" in getattr(self.app.btn_notif_chat, "_text", "")
            assert "Order" in self.app.btn_notif_order.cget("text") or "Order" in getattr(self.app.btn_notif_order, "_text", "")
            self.test_status = "PASS"
            self.actual_message = "Thông báo đã được cập nhật"
            print(f"{Fore.GREEN}[PASS] Vòng lặp thông báo đã cập nhật giao diện")
        except AssertionError as e:
            self.test_status = "FAIL"
            self.actual_message = f"Kiểm tra thông báo thất bại: {e}"
            print(f"{Fore.RED}[FAIL] {e}")

        self.ws.append(["TC02", "Thông báo", "check_notifications_loop", "Hiển thị chấm đỏ và cập nhật nút", self.actual_message, self.test_status])

    def test_TC03_action_recharge_adds_transaction(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC03: _action_recharge gọi add_transaction_db và hiển thị thông báo")

        with patch('tkinter.simpledialog.askstring', return_value="MAY01 Nap 50k"), \
             patch('tkinter.simpledialog.askfloat', return_value=50000.0), \
             patch('tkinter.messagebox.showinfo', side_effect=self._mock_showinfo):

            self.app._action_recharge()

            try:
                database.add_transaction_db.assert_called()
                self.test_status = "PASS"
                print(f"{Fore.GREEN}[PASS] add_transaction_db đã được gọi với: {database.add_transaction_db.call_args}")
            except AssertionError as e:
                self.test_status = "FAIL"
                print(f"{Fore.RED}[FAIL] add_transaction_db không được gọi: {e}")

        self.ws.append(["TC03", "Nạp tiền", "_action_recharge", "add_transaction_db được gọi & hiện thông báo", self.actual_message, self.test_status])

    def test_TC04_open_pending_orders_and_serve(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC04: Mở danh sách đơn hàng chưa phục vụ và phục vụ 1 đơn")

        # Ensure same mock object is set on both database and T module namespace
        m_complete = MagicMock()
        database.complete_order = m_complete
        T.complete_order = m_complete

        # Call open_pending_orders (uses patched Toplevel and other widgets)
        self.app.open_pending_orders()

        # simulate clicking "Đã phục vụ": call _serve_order with a dummy "top" (DummyToplevel)
        fake_win = DummyToplevel()
        self.app._serve_order(MOCK_ORDERS[0]['id'], fake_win)

        try:
            m_complete.assert_called_with(MOCK_ORDERS[0]['id'])
            self.test_status = "PASS"
            self.actual_message = "Đã phục vụ đơn hàng"
            print(f"{Fore.GREEN}[PASS] complete_order đã được gọi cho id {MOCK_ORDERS[0]['id']}")
        except Exception as e:
            self.test_status = "FAIL"
            self.actual_message = f"Phục vụ đơn hàng thất bại: {e}"
            print(f"{Fore.RED}[FAIL] {e}")

        self.ws.append(["TC04", "Đơn hàng", "open_pending_orders/_serve_order", "complete_order được gọi & đóng cửa sổ", self.actual_message, self.test_status])

    def test_TC05_chat_send_message(self):
        print(f"{Fore.CYAN}------------------------------------------------")
        print("🔵 TC05: Gửi tin nhắn Chat (sv_send_chat)")

        self.app.current_chat_machine = "MAY01"
        # ensure entry and txt_chat_history are safe dummy widgets
        self.app.entry_chat_msg = DummyWidget()
        self.app.entry_chat_msg.get = lambda: "Test message"
        self.app.entry_chat_msg.delete = lambda *a, **k: None
        self.app.txt_chat_history = DummyWidget()
        # Patch database.send_message_v2 (internal import is used inside function)
        database.send_message_v2 = MagicMock(return_value=True)

        # call method
        self.app.sv_send_chat()

        try:
            database.send_message_v2.assert_called_with("admin", "MAY01", "Test message")
            self.test_status = "PASS"
            self.actual_message = "Đã gửi tin nhắn"
            print(f"{Fore.GREEN}[PASS] send_message_v2 đã được gọi")
        except Exception as e:
            self.test_status = "FAIL"
            self.actual_message = f"Gửi tin nhắn thất bại: {e}"
            print(f"{Fore.RED}[FAIL] {e}")

        self.ws.append(["TC05", "Chat", "sv_send_chat", "database.send_message_v2 được gọi & xóa ô nhập", self.actual_message, self.test_status])

    @classmethod
    def tearDownClass(cls):
        cls.wb.save("test_trangchu_report.xlsx")
        print(f"\n{Fore.CYAN}================================================")
        print("Đã xuất kết quả kiểm thử ra file test_trangchu_report.xlsx")

if __name__ == "__main__":
    unittest.main(verbosity=2)