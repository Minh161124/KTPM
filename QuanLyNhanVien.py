import tkinter as tk
from tkinter import ttk, messagebox
import math

# --- IMPORT CÁC HÀM TỪ FILE database.py (ĐÃ KẾT NỐI XAMPP) ---
try:
    from database import get_employees_paginated, add_employee_db, update_employee_db, delete_employee_db
except ImportError:
    messagebox.showerror("Lỗi", "Không tìm thấy file database.py hoặc thiếu hàm xử lý nhân viên!")

# --- CẤU HÌNH GIAO DIỆN ---
COLOR_BG_DARK = "#2C3E50"
COLOR_BG_CELL = "#34495E"
COLOR_BG_HEADER = "#2C3E50"
COLOR_BG_INPUT = "#ECF0F1"
COLOR_TEXT_LIGHT = "#ECF0F1"
COLOR_ACCENT = "#27AE60" # Xanh lá
COLOR_BLUE = "#2980B9"   # Xanh dương
COLOR_RED = "#E74C3C"    # Đỏ
COLOR_YELLOW = "#F1C40F" # Vàng

FONT_HEADER = ("Arial", 12, "bold")
FONT_LABEL = ("Arial", 10)
FONT_ENTRY = ("Arial", 10)

# =============================================================================
# 1. VIEW: FORM NHẬP LIỆU (POPUP)
# =============================================================================
class EmployeeForm(tk.Toplevel):
    def __init__(self, parent, callback_refresh, emp_data=None):
        super().__init__(parent)
        self.title("Thông tin nhân viên")
        self.geometry("400x530")
        self.callback_refresh = callback_refresh
        self.emp_data = emp_data # Nếu có data là chế độ Sửa, None là Thêm mới

        # Tạo giao diện form
        self._setup_ui()
        
        # Nếu là sửa, điền dữ liệu cũ vào
        if self.emp_data:
            self._fill_data()

    def _setup_ui(self):
        padding = {'padx': 10, 'pady': 5}
        
        # Các trường nhập liệu
        self.entries = {}
        # Key khớp với thứ tự tham số trong database.py
        fields = [
            ("Mã NV (*)", "code"),
            ("Họ và Tên (*)", "name"),
            ("Tài khoản", "account"),
            ("Số điện thoại", "phone"),
            ("Lương cơ bản", "salary")
        ]

        for idx, (label_text, key) in enumerate(fields):
            tk.Label(self, text=label_text, font=FONT_LABEL).pack(anchor='w', padx=10)
            entry = tk.Entry(self, font=FONT_ENTRY)
            entry.pack(fill='x', **padding)
            self.entries[key] = entry

        # Combobox Giới tính
        tk.Label(self, text="Giới tính", font=FONT_LABEL).pack(anchor='w', padx=10)
        self.cb_gender = ttk.Combobox(self, values=["Nam", "Nữ"], state="readonly")
        self.cb_gender.current(0)
        self.cb_gender.pack(fill='x', **padding)

        # Combobox Chức vụ
        tk.Label(self, text="Chức vụ", font=FONT_LABEL).pack(anchor='w', padx=10)
        self.cb_role = ttk.Combobox(self, values=["Quản lý", "Nhân viên", "NV khác"], state="readonly")
        self.cb_role.current(1)
        self.cb_role.pack(fill='x', **padding)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        
        btn_save = tk.Button(btn_frame, text="Lưu Dữ Liệu", bg=COLOR_ACCENT, fg="white", font=("Arial", 10, "bold"), 
                             width=15, command=self._save)
        btn_save.pack(side='left', padx=5)
        
        btn_cancel = tk.Button(btn_frame, text="Hủy", bg=COLOR_RED, fg="white", font=("Arial", 10), 
                               width=10, command=self.destroy)
        btn_cancel.pack(side='left', padx=5)

    def _fill_data(self):
        # emp_data từ database trả về: (id, code, name, account, gender, phone, role, salary)
        d = self.emp_data
        
        self.entries['code'].insert(0, d[1])
        self.entries['name'].insert(0, d[2])
        if d[3]: self.entries['account'].insert(0, d[3])
        if d[4]: self.cb_gender.set(d[4])
        if d[5]: self.entries['phone'].insert(0, d[5])
        if d[6]: self.cb_role.set(d[6])
        if d[7]: self.entries['salary'].insert(0, str(d[7]).replace(",","")) # Bỏ dấu phẩy nếu có
        
        # Nếu đang sửa, khóa ô Mã NV
        self.entries['code'].config(state='disabled')

    def _save(self):
        # Lấy dữ liệu từ form
        # Thứ tự phải khớp với hàm add_employee_db trong database.py
        # data = (code, name, account, gender, phone, role, salary)
        
        # Xử lý lương (xóa dấu phẩy nếu người dùng nhập 10,000)
        salary_str = self.entries['salary'].get().replace(",", "").replace(".", "")
        try:
            salary_val = float(salary_str) if salary_str else 0
        except:
            salary_val = 0

        data = (
            self.entries['code'].get(),
            self.entries['name'].get(),
            self.entries['account'].get(),
            self.cb_gender.get(),
            self.entries['phone'].get(),
            self.cb_role.get(),
            salary_val
        )

        # Validate đơn giản
        if not data[0] or not data[1]:
            messagebox.showerror("Lỗi", "Mã NV và Tên không được để trống!")
            return

        if self.emp_data: # Chế độ UPDATE
            # self.emp_data[0] là ID
            success, msg = update_employee_db(self.emp_data[0], data)
        else: # Chế độ ADD
            success, msg = add_employee_db(data)

        if success:
            messagebox.showinfo("Thông báo", msg)
            self.callback_refresh() # Gọi hàm làm mới danh sách ở cửa sổ chính
            self.destroy() # Đóng form
        else:
            messagebox.showerror("Lỗi", msg)

# =============================================================================
# 2. VIEW: DANH SÁCH NHÂN VIÊN (MAIN FRAME)
# =============================================================================
class EmployeeListPage(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg=COLOR_BG_DARK)
        
        # Biến trạng thái
        self.page = 1
        self.limit = 10
        self.total_pages = 1
        self.current_data = []

        self._setup_ui()
        self.refresh() 

    def _setup_ui(self):
        # Header
        top = tk.Frame(self, bg=COLOR_BG_DARK)
        top.pack(fill='x', padx=10, pady=5)
        tk.Label(top, text="QUẢN LÝ NHÂN VIÊN (XAMPP/MySQL)", fg=COLOR_TEXT_LIGHT, bg=COLOR_BG_DARK, font=FONT_HEADER).pack(side='left')

        # Filter
        filter_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        self.entry_search = tk.Entry(filter_frame, width=20)
        self.entry_search.pack(side='left', ipady=3)
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh())
        tk.Label(filter_frame, text="🔍", bg=COLOR_BG_DARK, fg="white").pack(side='left', padx=2)

        self.cb_role = ttk.Combobox(filter_frame, values=["Tất cả", "Quản lý", "Nhân viên", "NV khác"], state="readonly", width=12)
        self.cb_role.current(0)
        self.cb_role.pack(side='left', padx=10, ipady=3)
        self.cb_role.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        tk.Button(filter_frame, text="+ Thêm Mới", bg=COLOR_ACCENT, fg="white", font=("Arial", 10, "bold"),
                  command=self._open_add_form).pack(side='right')

        # Table
        self.table_frame = tk.Frame(self, bg=COLOR_BG_CELL)
        self.table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Footer
        footer = tk.Frame(self, bg=COLOR_BG_DARK)
        footer.pack(fill='x', padx=10, pady=5)
        self.lbl_page = tk.Label(footer, text="", fg=COLOR_TEXT_LIGHT, bg=COLOR_BG_DARK)
        self.lbl_page.pack(side='right')
        
        btn_nav = tk.Frame(footer, bg=COLOR_BG_DARK)
        btn_nav.pack(side='right', padx=10)
        tk.Button(btn_nav, text="<", command=lambda: self._nav(-1)).pack(side='left')
        tk.Button(btn_nav, text=">", command=lambda: self._nav(1)).pack(side='left')

    def refresh(self):
        search = self.entry_search.get()
        role = self.cb_role.get()
        
        # GỌI HÀM TỪ DATABASE.PY (MySQL)
        try:
            data, total = get_employees_paginated(search, role, self.limit, self.page)
        except Exception as e:
            print("Lỗi refresh:", e)
            data, total = [], 0
        
        self.current_data = data
        self.total_pages = math.ceil(total / self.limit) or 1
        if self.page > self.total_pages: self.page = self.total_pages

        self._draw_table()
        self.lbl_page.config(text=f"Trang {self.page}/{self.total_pages} (Tổng: {total})")

    def _draw_table(self):
        for w in self.table_frame.winfo_children(): w.destroy()
        
        cols = ["Mã", "Họ Tên", "Tài khoản", "Giới tính", "SĐT", "Chức vụ", "Lương", "Hành động"]
        widths = [60, 150, 100, 60, 100, 100, 100, 120]

        # Header
        for i, c in enumerate(cols):
            f = tk.Frame(self.table_frame, bg=COLOR_BG_HEADER)
            f.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)
            tk.Label(f, text=c, bg=COLOR_BG_HEADER, fg="white", font=("Arial", 10, "bold")).pack(pady=5)
            self.table_frame.grid_columnconfigure(i, weight=1 if i==1 else 0, minsize=widths[i])

        # Rows
        if not self.current_data:
             tk.Label(self.table_frame, text="Không có dữ liệu", bg=COLOR_BG_CELL, fg="white").grid(row=1, columnspan=8, pady=20)
             return

        for idx, row in enumerate(self.current_data):
            # row từ database: (id, code, name, account, gender, phone, role, salary)
            vals = [row[1], row[2], row[3], row[4], row[5], row[6], row[7]]
            
            for i, val in enumerate(vals):
                f = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
                f.grid(row=idx+1, column=i, sticky="nsew", padx=1, pady=1)
                tk.Label(f, text=val, bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT).pack(anchor="w", padx=5, pady=5)
            
            # Action Buttons
            act_frame = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
            act_frame.grid(row=idx+1, column=7, sticky="nsew", padx=1, pady=1)
            
            tk.Button(act_frame, text="Sửa", bg=COLOR_YELLOW, width=4, 
                      command=lambda r=row: self._open_edit_form(r)).pack(side='left', padx=2)
            tk.Button(act_frame, text="Xóa", bg=COLOR_RED, fg="white", width=4, 
                      command=lambda r=row: self._delete(r)).pack(side='left', padx=2)

    def _nav(self, direction):
        if (direction == -1 and self.page > 1) or (direction == 1 and self.page < self.total_pages):
            self.page += direction
            self.refresh()

    def _delete(self, row):
        # row[0] là ID, row[2] là Tên
        if messagebox.askyesno("Xác nhận", f"Xóa nhân viên {row[2]}?"):
            if delete_employee_db(row[0]):
                self.refresh()
            else:
                messagebox.showerror("Lỗi", "Không thể xóa nhân viên này!")

    def _open_add_form(self):
        EmployeeForm(self, self.refresh, emp_data=None)

    def _open_edit_form(self, row_data):
        EmployeeForm(self, self.refresh, emp_data=row_data)

# =============================================================================
# CHẠY THỬ
# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Quản lý nhân viên (MySQL XAMPP)")
    root.geometry("1000x600")
    
    app = EmployeeListPage(root)
    app.pack(fill='both', expand=True)
    
    root.mainloop()