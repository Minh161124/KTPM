import tkinter as tk
from tkinter import messagebox
from model.emp_model import EmployeeModel
from view.emp_add import EmployeeForm
from view.emp_view_list import EmployeeListPage

 

class EmployeeController:
    def __init__(self, main_frame):
        self.model = EmployeeModel()
        self.view_form = None
        self.view_list = EmployeeListPage(main_frame, self)
        self.view_list.pack(fill='both', expand=True)
        self.view_list.trigger_refresh()

    def refresh_employees(self, search, role, limit, page):
        """Xử lý yêu cầu làm mới từ view_list"""
        try:
            data, total_records = self.model.fetch_employees(search, role, limit, page)
            # Gọi view để cập nhật
            self.view_list.update_display(data, total_records)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách nhân viên: {e}")

    def show_add_form(self):
        """Hiển thị form thêm mới"""
        # Đảm bảo chỉ có 1 form được mở
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift()
            return
            
        self.view_form = EmployeeForm(self.view_list, self) # employee_id=None
        self.view_list.wait_window(self.view_form) # Chờ cho đến khi form đóng

    def show_edit_form(self, employee_id):
        """Hiển thị form chỉnh sửa"""
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift()
            return
            
        # Lấy dữ liệu từ Model trước
        employee_data = self.model.get_employee_by_id(employee_id)
        if not employee_data:
            messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu nhân viên.")
            return

        self.view_form = EmployeeForm(self.view_list, self, employee_id)
        self.view_form.load_data(employee_data) # Nạp dữ liệu vào form
        self.view_list.wait_window(self.view_form)

    def save_employee(self, data, employee_id):
        """Xử lý yêu cầu lưu từ view_form"""
        
        # Gửi dữ liệu cho Model để validate và lưu
        success, message = self.model.save_employee(data, employee_id)
        
        if success:
            # Nếu thành công, đóng form và làm mới danh sách
            if self.view_form:
                # view_form sẽ tự đóng sau khi hiển thị thông báo
                self.view_form.show_info_and_close(message)
            self.view_list.trigger_refresh() # Yêu cầu view_list tự làm mới
        else:
            # Nếu thất bại, hiển thị lỗi trên form
            if self.view_form:
                self.view_form.show_error(message)

    def delete_employee(self, employee_id):
        """Xử lý yêu cầu xóa từ view_list"""
        success = self.model.delete_employee(employee_id)
        if success:
            messagebox.showinfo("Thành công", "Đã xóa nhân viên.")
            self.view_list.trigger_refresh() # Làm mới danh sách
        else:
            messagebox.showerror("Thất bại", "Không thể xóa nhân viên.")

    