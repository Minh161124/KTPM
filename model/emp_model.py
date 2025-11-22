import re 
from .db_connector import Database

class EmployeeModel:
    def __init__(self):
        self.db = Database()

    def fetch_employees(self, search, role, limit, page):
        return self.db.fetch_employees(search, role, limit, page)

    def get_employee_by_id(self, employee_id):
        return self.db.get_employee_by_id(employee_id)

    def delete_employee(self, employee_id):
        return self.db.delete_employee(employee_id)

    def save_employee(self, data, employee_id=None):

        if not data['ma_nv'] or not data['ho_ten'] or not data['tai_khoan']:
            return (False, "Vui lòng nhập đầy đủ: Mã NV, Họ tên và Tài khoản.")

        data['ma_nv'] = data['ma_nv'].strip()

        if len(data['ma_nv']) < 3 or len(data['ma_nv']) > 20:
            return (False, "Mã nhân viên phải có độ dài từ 3 đến 20 ký tự.")

        if not re.match("^[A-Za-z0-9_]+$", data['ma_nv']):
            return (False, "Mã NV không được chứa ký tự đặc biệt hoặc khoảng trắng (chỉ dùng A-Z, 0-9, _).")

        data['ho_ten'] = data['ho_ten'].strip()
        if len(data['ho_ten']) < 4:
            return (False, "Họ tên quá ngắn, vui lòng nhập đầy đủ họ tên.")

        if any(char.isdigit() for char in data['ho_ten']):
            return (False, "Họ tên không được chứa chữ số.")

        data['ho_ten'] = data['ho_ten'].title()

        sdt = data.get('sdt', '').strip()
        if sdt:
            if not sdt.isdigit():
                return (False, "Số điện thoại chỉ được chứa các chữ số.")
            if not sdt.startswith('0'):
                return (False, "Số điện thoại phải bắt đầu bằng số 0.")
            if len(sdt) != 10:
                return (False, "Số điện thoại phải có đúng 10 chữ số.")

        data['tai_khoan'] = data['tai_khoan'].strip()
        if " " in data['tai_khoan']:
            return (False, "Tên tài khoản không được chứa khoảng trắng.")
        if len(data['tai_khoan']) < 4:
            return (False, "Tên tài khoản phải có ít nhất 4 ký tự.")

        try:
            luong_val = float(data['luong'])
            if luong_val < 0:
                return (False, "Lương không được là số âm.")
        except ValueError:
            return (False, "Lương phải là một con số hợp lệ.")

        password = data.get('mat_khau')

        if not employee_id:
            if not password:
                return (False, "Mật khẩu là bắt buộc khi thêm mới.")
            if len(password) < 6:
                return (False, "Mật khẩu phải có ít nhất 6 ký tự.")

        else:
            if data.get('is_changing_pass'):
                if not password:
                    return (False, "Vui lòng nhập mật khẩu mới.")
                if len(password) < 6:
                    return (False, "Mật khẩu mới phải có ít nhất 6 ký tự.")

        if employee_id:
            success = self.db.update_employee(employee_id, data)
            message = "Cập nhật nhân viên thành công!" if success else "Cập nhật thất bại (có thể do lỗi kết nối hoặc trùng Mã NV/Tài khoản)."
        else:
            success = self.db.add_employee(data)
            message = "Thêm nhân viên thành công!" if success else "Thêm thất bại (có thể do lỗi kết nối hoặc trùng Mã NV/Tài khoản)."
        
        return (success, message)