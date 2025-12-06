import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import messagebox
from openpyxl import Workbook
from colorama import init, Fore, Style
import main  # File code giao diện chính của bạn

# Khởi tạo colorama
init(autoreset=True)

class LoginAutomationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Chạy 1 lần khi bắt đầu: Tạo file Excel"""
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "Test Results"
        cls.ws.append(["Test Case ID", "Input Email", "Input Password", "Expected Output", "Actual Message", "Status"])
        print(f"{Fore.CYAN}Bắt đầu quá trình kiểm thử tự động...\n")

    def setUp(self):
        """Chạy trước mỗi test suite"""
        self.app = main.LoginWindow()
        self.app.withdraw() # Ẩn cửa sổ đi cho đỡ vướng
        self.actual_message = ""
        self.test_status = "FAIL"

    def tearDown(self):
        """Chạy sau khi test xong"""
        try:
            # Gọi hàm destroy gốc của Tkinter để tắt hẳn ứng dụng sau khi test xong
            super(main.LoginWindow, self.app).destroy()
        except:
            pass

    def _mock_messagebox_info(self, title, message, parent=None):
        self.actual_message = message
        print(f"Thông báo: {message}")
        print(f"{Fore.GREEN}✅ Kết quả: Login thành công (Đúng mong đợi)")

    def _mock_messagebox_error(self, title, message, parent=None):
        self.actual_message = message
        print(f"Thông báo: {message}")
        print(f"{Fore.RED}❌ Kết quả: Login thất bại (Đúng mong đợi)")

    def _mock_messagebox_warning(self, title, message, parent=None):
        self.actual_message = message
        print(f"Thông báo: {message}")
        print(f"{Fore.YELLOW}⚠️ Kết quả: Cảnh báo thiếu thông tin (Đúng mong đợi)")

    def run_test_scenario(self, case_id, email, password, scenario_type):
        """
        scenario_type: 'success', 'fail', 'missing'
        """
        display_pass = password if password else "[Rỗng]"
        display_email = email if email else "[Rỗng]"
        print(f"{Fore.CYAN}------------------------------------------------")
        print(f"🔵 Running {case_id}: Input [{display_email}] / [{display_pass}]")

        # 1. Reset form (Xóa dữ liệu cũ)
        try:
            self.app.email_entry.delete(0, tk.END)
            self.app.password_entry.delete(0, tk.END)
            self.app.email_entry.insert(0, email)
            self.app.password_entry.insert(0, password)
        except Exception as e:
            print(f"{Fore.RED}Lỗi Critical: Không tìm thấy ô nhập liệu. Ứng dụng có thể đã bị đóng trước đó.")
            return

        # 2. Mocking (Quan trọng: Mock luôn hàm destroy để app không bị đóng khi login thành công)
        with patch('main.get_connection') as mock_db_conn, \
             patch('tkinter.messagebox.showinfo', side_effect=self._mock_messagebox_info), \
             patch('tkinter.messagebox.showerror', side_effect=self._mock_messagebox_error), \
             patch('tkinter.messagebox.showwarning', side_effect=self._mock_messagebox_warning), \
             patch.object(self.app, 'destroy', return_value=None) as mock_destroy: # <--- FIX LỖI Ở ĐÂY

            # Cấu hình giả lập Database
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_db_conn.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            if scenario_type == 'success':
                # Giả lập DB tìm thấy user (Sửa theo data bạn cung cấp: 1/1)
                mock_cursor.fetchone.return_value = {'email': email, 'role': 'admin', 'password': password}
            else:
                # Giả lập DB không tìm thấy
                mock_cursor.fetchone.return_value = None

            # 3. Kích hoạt login
            self.app.handle_login()

            # 4. Kiểm tra xem app có gọi hàm destroy (đóng cửa sổ) khi thành công không?
            if scenario_type == 'success':
                if mock_destroy.called:
                    print(f"{Fore.MAGENTA}ℹ️  Logic App: Đã gọi lệnh đóng cửa sổ (Mocked destroy)")
                else:
                    print(f"{Fore.RED}⚠️  Lỗi Logic: Login thành công nhưng chưa gọi lệnh đóng cửa sổ!")

            # 5. Đánh giá Pass/Fail
            if scenario_type == 'success' and "Xin chào" in self.actual_message:
                self.test_status = "PASS"
            elif scenario_type == 'fail' and ("không đúng" in self.actual_message or "Login thất bại" in self.actual_message):
                self.test_status = "PASS"
            elif scenario_type == 'missing' and "đầy đủ" in self.actual_message:
                self.test_status = "PASS"
            else:
                self.test_status = "FAIL"

            # 6. Ghi Excel
            self.ws.append([case_id, email, password, scenario_type, self.actual_message, self.test_status])

    def test_all_cases(self):
        # --- TEST CASE 1: Đăng nhập đúng (Sửa thành 1/1) ---
        self.run_test_scenario("TC01", "1", "1", "success")
        
        # --- TEST CASE 2: Sai thông tin ---
        self.run_test_scenario("TC02", "wrong@gmail.com", "123", "fail")

        # --- TEST CASE 3: Thiếu thông tin ---
        self.run_test_scenario("TC03", "", "", "missing")

    @classmethod
    def tearDownClass(cls):
        """Lưu file Excel"""
        filename = "test_login_report.xlsx"
        cls.wb.save(filename)
        print(f"\n{Fore.CYAN}================================================")
        print(f"{Fore.CYAN}Đã xuất kết quả ra file: {filename}")

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(LoginAutomationTest("test_all_cases"))
    runner = unittest.TextTestRunner()
    runner.run(suite)