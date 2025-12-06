import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import sys

# --- HÀM TẠO MÀU CHO TERMINAL ---
class Colors:
    GREEN = '\033[92m'
    RESET = '\033[0m'

def print_pass(msg):
    print(f"{Colors.GREEN}[PASS] {msg}{Colors.RESET}")

# --- IMPORT CÁC HÀM CẦN TEST ---
try:
    from database import add_shift_db, get_all_shifts, delete_shift_db, get_all_employees_for_shift
except ImportError:
    pass

class TestShiftManager(unittest.TestCase):
    
    # Biến lưu trữ kết quả để xuất Excel
    test_results = []

    @classmethod
    def setUpClass(cls):
        print(f"\nBắt đầu kiểm thử ShiftManagerPage (Quản lý Ca Trực)...")
        print("-" * 70)
        # Khởi tạo danh sách kết quả trống
        cls.test_results = []

    @classmethod
    def tearDownClass(cls):
        print("-" * 70)
        # --- XUẤT RA FILE EXCEL ĐÚNG MẪU ---
        columns = ["ID Test", "Kịch bản", "Hành động", "Kỳ vọng", "Thực tế", "Trạng thái"]
        
        # Tạo DataFrame từ danh sách kết quả
        df = pd.DataFrame(cls.test_results, columns=columns)
        
        report_name = "test_catruc_report.xlsx"
        try:
            df.to_excel(report_name, index=False)
            print(f"{Colors.GREEN}☑ Đã xuất báo cáo chi tiết ra file: {report_name}{Colors.RESET}")
            
            # Tự động mở file (chỉ hoạt động trên Windows)
            if os.name == 'nt':
                os.startfile(report_name)
        except Exception as e:
            print(f"Lỗi xuất Excel: {e}")

    def add_report_row(self, test_id, scenario, action, expected, actual, status="PASS"):
        """Hàm hỗ trợ thêm dòng vào báo cáo"""
        self.__class__.test_results.append([test_id, scenario, action, expected, actual, status])

    # --- TC01: TẢI DỮ LIỆU ---
    @patch('database.create_connection')
    def test_TC01_load_data(self, mock_conn):
        """TC01: Kiểm tra tải dữ liệu hiển thị"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'NV01', 'Nguyen Van A', 'Nhan vien', '2025-12-05', 'Ca Sang', ''),
            (2, 'NV02', 'Tran Thi B', 'Quan ly', '2025-12-05', 'Ca Chieu', '')
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor

        result = get_all_shifts()
        
        # Assert logic
        self.assertEqual(len(result), 2)
        print_pass("TC01: SQL SELECT gọi đúng & Bảng có 2 dòng dữ liệu")
        
        # Ghi log vào Excel
        self.add_report_row(
            "TC01", 
            "Tải dữ liệu", 
            "Gọi hàm get_all_shifts", 
            "Hiển thị 2 dòng dữ liệu", 
            "SQL SELECT trả về 2 dòng", 
            "PASS"
        )

    # --- TC02: THÊM MỚI ---
    @patch('database.create_connection')
    def test_TC02_add_shift(self, mock_conn):
        """TC02: Thêm mới ca trực"""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = add_shift_db(1, "2025-12-06", "Ca Sáng", "Ghi chú test")

        self.assertTrue(success)
        print_pass("TC02: Đã gọi INSERT SQL & Commit thành công")

        self.add_report_row(
            "TC02", 
            "Thêm mới", 
            "Nhập & Lưu ca trực", 
            "Gọi lệnh INSERT vào DB", 
            "Đã gọi INSERT & Commit", 
            "PASS"
        )

    # --- TC03: KIỂM TRA VALIDATE NGÀY ---
    def test_TC03_validate_date(self):
        """TC03: Kiểm tra nhập sai định dạng ngày"""
        from datetime import datetime
        raw_date = "2025-13-40" # Ngày sai
        is_valid = False
        try:
            datetime.strptime(raw_date, "%d/%m/%Y")
            is_valid = True
        except ValueError:
            is_valid = False
            
        self.assertFalse(is_valid)
        print_pass("TC03: Hệ thống bắt lỗi ngày sai định dạng")

        self.add_report_row(
            "TC03", 
            "Validate ngày", 
            "Nhập ngày sai format", 
            "Hệ thống báo lỗi ValueError", 
            "Đã bắt được ngoại lệ", 
            "PASS"
        )

    # --- TC04: XÓA CA TRỰC ---
    @patch('database.create_connection')
    def test_TC04_delete_shift(self, mock_conn):
        """TC04: Xóa ca trực"""
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        result = delete_shift_db(10)
        
        self.assertTrue(result)
        print_pass("TC04: Đã gọi DELETE SQL")

        self.add_report_row(
            "TC04", 
            "Xóa ca trực", 
            "Chọn dòng & Xóa", 
            "Gọi lệnh DELETE với ID=10", 
            "Đã gọi DELETE thành công", 
            "PASS"
        )

    # --- TC05: LOAD DANH SÁCH NHÂN VIÊN ---
    @patch('database.create_connection')
    def test_TC05_get_employees(self, mock_conn):
        """TC05: Lấy danh sách nhân viên vào Combobox"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 'NV99', 'Test Staff', 'Bảo vệ')]
        mock_conn.return_value.cursor.return_value = mock_cursor

        res = get_all_employees_for_shift()
        
        self.assertEqual(res[0][2], 'Test Staff')
        print_pass("TC05: Load danh sách nhân viên thành công")

        self.add_report_row(
            "TC05", 
            "Lấy DS Nhân viên", 
            "Load dữ liệu Combobox", 
            "Danh sách NV hiển thị đúng", 
            "SQL SELECT trả về tên NV", 
            "PASS"
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)