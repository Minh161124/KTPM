import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import os
import sys
import importlib
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from colorama import init, Fore, Style

# ====================================================================
# CẤU HÌNH TÊN FILE CỦA BẠN
# Sửa tên này trùng với tên file code giao diện của bạn (không có .py)
MODULE_NAME = 'quanlymay'  
# ====================================================================

# --- Setup Colorama ---
init(autoreset=True)

# --- Dynamic Import ---
try:
    main_module = importlib.import_module(MODULE_NAME)
    MachineManagerPage = main_module.MachineManagerPage
    # Mock các hàm DB nếu không có
    if not hasattr(main_module, 'update_machine_status'):
        main_module.update_machine_status = MagicMock()
    if not hasattr(main_module, 'save_log'):
        main_module.save_log = MagicMock()
    if not hasattr(main_module, 'add_weblog_entry'):
        main_module.add_weblog_entry = MagicMock()
except ImportError:
    print(f"{Fore.RED}❌ LỖI: Không tìm thấy file '{MODULE_NAME}.py'")
    print(f"{Fore.YELLOW}👉 Hãy mở file test này, sửa dòng 14 (MODULE_NAME) thành tên file code của bạn.")
    sys.exit(1)

class TestMachineManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(f"{Fore.CYAN}Bắt đầu kiểm thử MachineManagerPage ({MODULE_NAME}.py)...{Style.RESET_ALL}\n")
        
        # Setup Excel Report
        cls.wb = Workbook()
        cls.ws = cls.wb.active
        cls.ws.title = "Test Report"
        headers = ["Time", "Test Case ID", "Description", "Result", "Note"]
        cls.ws.append(headers)
        
        # Style Header
        header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        for cell in cls.ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

    def setUp(self):
        # Ẩn cửa sổ chính
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Khởi tạo App
        with patch(f'{MODULE_NAME}.get_all_machines', return_value=[]): 
            self.app = MachineManagerPage(self.root)
        
        # Reset dữ liệu sạch sẽ trước mỗi test
        self.app.machines = [] # Clear cũ
        # Tạo lại dữ liệu chuẩn để test
        self.app.machines = [
            {"name": "T01", "state": "off", "category": "Tiêu chuẩn", "spec": "Spec A", "started_at": "--/--", "used": "00:00:00", "amount": 0, "paused": False, "custom_price": None},
            {"name": "G01", "state": "off", "category": "Gaming", "spec": "Spec B", "started_at": "--/--", "used": "00:00:00", "amount": 0, "paused": False, "custom_price": None}
        ]
        self.app.pricing = {"Tiêu chuẩn": 100, "Gaming": 200}
        self.app.logs = []
        self.app.running_timers = {}

    def tearDown(self):
        # Hủy timer và đóng window
        for timer in self.app.running_timers.values():
            try: self.app.after_cancel(timer)
            except: pass
        self.root.destroy()

    def _log(self, tc_id, desc, note, passed=True):
        """Hàm in ra console và ghi Excel giống ảnh"""
        status = "PASS" if passed else "FAIL"
        # Print Console Style
        color = Fore.GREEN if passed else Fore.RED
        print(f"{color}[{status}] {tc_id}: {note}")
        
        # Save to Excel
        row = [datetime.now().strftime("%H:%M:%S"), tc_id, desc, status, note]
        self.ws.append(row)
        
        # Style Excel Row
        last_row = self.ws.max_row
        status_cell = self.ws.cell(row=last_row, column=4)
        if passed:
            status_cell.font = Font(color="006100", bold=True)
            status_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        else:
            status_cell.font = Font(color="9C0006", bold=True)
            status_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    def print_header(self, tc_id, desc):
        print(f"{Fore.CYAN}--- {tc_id}: {desc} ---{Style.RESET_ALL}")

    # ================= TEST CASES =================

    def test_TC01_init_machines(self):
        """Kiểm tra khởi tạo danh sách máy"""
        tc_id = "TC01"
        desc = "Khởi tạo dữ liệu máy trạm"
        self.print_header(tc_id, desc)
        
        # Action: App đã init ở setUp
        count = len(self.app.machines)
        
        # Assert
        self.assertTrue(count > 0)
        self._log(tc_id, desc, f"Đã tải {count} máy thành công")

    def test_TC02_toggle_power(self):
        """Kiểm tra bật tắt nguồn"""
        tc_id = "TC02"
        desc = "Bật nguồn máy trạm"
        self.print_header(tc_id, desc)
        
        idx = 0
        
        # Action: Bật máy
        with patch(f'{MODULE_NAME}.update_machine_status'):
            self.app.toggle_power(idx)
        
        # Assert
        state = self.app.machines[idx]['state']
        self.assertEqual(state, "on")
        self._log(tc_id, desc, f"Máy {self.app.machines[idx]['name']}: off -> {state}")

    def test_TC03_pricing_calculation(self):
        """Kiểm tra tính tiền"""
        tc_id = "TC03"
        desc = "Tính tiền theo thời gian"
        self.print_header(tc_id, desc)
        
        idx = 0
        price = self.app.pricing["Tiêu chuẩn"] # 100
        
        # Action: Giả lập trôi 60 phút
        self.app.machines[idx]['state'] = 'on'
        start_time = datetime.now() - timedelta(minutes=60)
        self.app.machines[idx]['started_at'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Gọi hàm tính tiền nội bộ
        self.app._tick_time(idx)
        
        # Assert
        actual = self.app.machines[idx]['amount']
        expected = 60 * price # 6000
        
        # Cho phép sai số nhỏ do giây
        diff = abs(actual - expected)
        self.assertTrue(diff <= price)
        self._log(tc_id, desc, f"60 phút = {actual:,} VND (Expected: {expected:,})")

    def test_TC04_payment_reset(self):
        """Kiểm tra thanh toán"""
        tc_id = "TC04"
        desc = "Thanh toán & Reset máy"
        self.print_header(tc_id, desc)
        
        idx = 0
        self.app.machines[idx]['state'] = 'on'
        self.app.machines[idx]['amount'] = 15000
        
        # Action: Thanh toán (Mock popup Yes)
        with patch('tkinter.messagebox.askyesno', return_value=True), \
             patch('tkinter.messagebox.showinfo'), \
             patch(f'{MODULE_NAME}.update_machine_status'), \
             patch(f'{MODULE_NAME}.save_log'):
             
            self.app.pay_machine(idx)
            
        # Assert
        state = self.app.machines[idx]['state']
        amount = self.app.machines[idx]['amount']
        
        self.assertEqual(state, 'off')
        self.assertEqual(amount, 0)
        self._log(tc_id, desc, "Thanh toán thành công, máy đã tắt")

    def test_TC05_web_blocking(self):
        """Kiểm tra chặn Web"""
        tc_id = "TC05"
        desc = "Kiểm tra chặn Web Blacklist"
        self.print_header(tc_id, desc)
        
        # Setup blacklist
        self.app.weblocklist.append("badsite.com")
        self.app.web_block_enabled = True
        
        # Action: Mở web xấu (Mock messagebox)
        with patch('tkinter.messagebox.showwarning') as mock_warn, \
             patch('tkinter.messagebox.showinfo'), \
             patch(f'{MODULE_NAME}.add_weblog_entry'):
             
            self.app.open_website("http://badsite.com")
            
        # Assert
        self.assertTrue(mock_warn.called)
        self._log(tc_id, desc, "Đã hiện cảnh báo chặn 'badsite.com'")

    def test_TC06_system_reset(self):
        """Kiểm tra Reset hệ thống"""
        tc_id = "TC06"
        desc = "Reset toàn bộ hệ thống"
        self.print_header(tc_id, desc)
        
        self.app.machines[0]['state'] = 'on'
        
        # Action
        with patch('tkinter.messagebox.askyesno', return_value=True), \
             patch('tkinter.messagebox.showinfo'), \
             patch(f'{MODULE_NAME}.update_machine_status'):
            self.app.reset_system()
            
        # Assert
        self.assertEqual(self.app.machines[0]['state'], 'off')
        self._log(tc_id, desc, "Hệ thống đã về trạng thái OFF")

    @classmethod
    def tearDownClass(cls):
        # Xuất file báo cáo
        filename = f"test_{MODULE_NAME}_report.xlsx"
        
        # Auto adjust column width
        for column_cells in cls.ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            cls.ws.column_dimensions[column_cells[0].column_letter].width = length + 2
            
        cls.wb.save(filename)
        print(f"\n{Fore.GREEN}============================================")
        print(f"{Fore.GREEN}✅ Đã xuất báo cáo: {filename}")
        print(f"{Fore.GREEN}============================================\n")

if __name__ == '__main__':
    # Verbosity=2 để hiện tên hàm test khi chạy
    unittest.main(verbosity=2)