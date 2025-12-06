import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime # <--- QUAN TRỌNG: THÊM DÒNG NÀY ĐỂ XỬ LÝ NGÀY

# Import database
from database import get_all_employees_for_shift, add_shift_db, get_all_shifts, delete_shift_db

# --- CẤU HÌNH MÀU SẮC (GIỮ NGUYÊN) ---
COLOR_BG_DARK = "#2C3E50"
COLOR_BG_CELL = "#34495E"
COLOR_TEXT_LIGHT = "#ECF0F1"
COLOR_ACCENT = "#27AE60"
COLOR_BLUE = "#2980B9"
COLOR_RED = "#E74C3C"

FONT_HEADER = ("Arial", 14, "bold")
FONT_LABEL = ("Arial", 10)
FONT_ENTRY = ("Arial", 10)

class ShiftManagerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG_DARK)
        self.staff_list = []
        self._setup_ui()
        self._refresh_data()

    def _setup_ui(self):
        # === 1. KHUNG TRÁI: NHẬP LIỆU ===
        left_frame = tk.Frame(self, bg=COLOR_BG_DARK, width=320)
        left_frame.pack(side='left', fill='y', padx=20, pady=20)
        
        tk.Label(left_frame, text="XẾP LỊCH TRỰC", font=FONT_HEADER, 
                 bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(pady=(0, 20), anchor='w')

        # Dropdown Chọn Nhân sự
        tk.Label(left_frame, text="Chọn Nhân sự:", font=FONT_LABEL, bg=COLOR_BG_DARK, fg="white").pack(anchor='w')
        self.cb_staff = ttk.Combobox(left_frame, state="readonly", font=FONT_ENTRY, width=35)
        self.cb_staff.pack(fill='x', pady=5)
        
        # Nhập ngày (Đã sửa label)
        tk.Label(left_frame, text="Ngày trực (dd/mm/yyyy):", font=FONT_LABEL, bg=COLOR_BG_DARK, fg="white").pack(anchor='w')
        self.entry_date = tk.Entry(left_frame, font=FONT_ENTRY) 
        self.entry_date.pack(fill='x', pady=5)
        # Gợi ý ngày hôm nay
        today_str = datetime.now().strftime("%d/%m/%Y")
        self.entry_date.insert(0, today_str)

        # Chọn Ca
        tk.Label(left_frame, text="Ca làm việc:", font=FONT_LABEL, bg=COLOR_BG_DARK, fg="white").pack(anchor='w')
        self.cb_shift = ttk.Combobox(left_frame, values=["Ca Sáng (7h-11h)", "Ca Chiều (13h-17h)", "Ca Tối (17h-22h)", "Ca Đêm", "Full-time"], 
                                     state="readonly", font=FONT_ENTRY)
        self.cb_shift.current(0)
        self.cb_shift.pack(fill='x', pady=5)

        # Ghi chú
        tk.Label(left_frame, text="Ghi chú:", font=FONT_LABEL, bg=COLOR_BG_DARK, fg="white").pack(anchor='w')
        self.entry_note = tk.Entry(left_frame, font=FONT_ENTRY)
        self.entry_note.pack(fill='x', pady=5)

        # Nút Lưu
        tk.Button(left_frame, text="LƯU CA TRỰC", bg=COLOR_BLUE, fg="white", font=("Arial", 11, "bold"),
                  command=self._save, cursor="hand2").pack(fill='x', pady=25)

        # === 2. KHUNG PHẢI: DANH SÁCH ===
        right_frame = tk.Frame(self, bg=COLOR_BG_CELL)
        right_frame.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        tk.Label(right_frame, text="DANH SÁCH PHÂN CÔNG", font=("Arial", 12, "bold"), 
                 bg=COLOR_BG_CELL, fg="white").pack(pady=(0, 10), anchor='w')

        # Treeview
        cols = ("ID", "Mã NV", "Họ Tên", "Chức vụ", "Ngày", "Ca", "Ghi chú")
        self.tree = ttk.Treeview(right_frame, columns=cols, show='headings', height=20)
        
        self.tree.column("ID", width=30, anchor="center")
        self.tree.column("Mã NV", width=60, anchor="center")
        self.tree.column("Họ Tên", width=140)
        self.tree.column("Chức vụ", width=80)
        self.tree.column("Ngày", width=80, anchor="center") # Cột ngày
        self.tree.column("Ca", width=100)
        self.tree.column("Ghi chú", width=100)

        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill='both', expand=True)

        # Nút Xóa
        tk.Button(right_frame, text="Xóa Ca Đã Chọn", bg=COLOR_RED, fg="white", font=("Arial", 10),
                  command=self._del_shift).pack(fill='x', pady=10)

    def _refresh_data(self):
        # 1. Load Combobox
        emps = get_all_employees_for_shift() 
        self.staff_list = emps
        self.cb_staff['values'] = [f"{e[1]} - {e[2]} ({e[3]})" for e in emps]
        if emps: self.cb_staff.current(0)

        # 2. Load Table (Dữ liệu lúc này đã là dd/mm/yyyy nhờ SQL DATE_FORMAT)
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        shifts = get_all_shifts()
        for s in shifts:
            self.tree.insert("", "end", values=s)

    def _save(self):
        idx = self.cb_staff.current()
        if idx == -1 or not self.staff_list:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn nhân sự!")
            return
            
        emp_id = self.staff_list[idx][0]
        
        # --- XỬ LÝ NGÀY THÁNG ---
        raw_date = self.entry_date.get()
        if not raw_date:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập ngày!")
            return
        
        try:
            # 1. Chuyển từ chuỗi "dd/mm/yyyy" sang đối tượng datetime
            date_obj = datetime.strptime(raw_date, "%d/%m/%Y")
            # 2. Chuyển đối tượng datetime thành chuỗi "yyyy-mm-dd" để lưu vào MySQL
            db_date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Lỗi định dạng", "Ngày phải nhập theo dạng: dd/mm/yyyy\nVí dụ: 05/12/2025")
            return

        shift = self.cb_shift.get()
        note = self.entry_note.get()

        # Gọi hàm lưu (truyền db_date_str chuẩn SQL)
        success, msg = add_shift_db(emp_id, db_date_str, shift, note)
        if success:
            self._refresh_data()
            messagebox.showinfo("Thành công", "Đã lưu ca trực!")
        else:
            messagebox.showerror("Lỗi", msg)

    def _del_shift(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Chọn dòng cần xóa!")
            return
        shift_id = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Xác nhận", "Xóa ca trực này?"):
            if delete_shift_db(shift_id):
                self._refresh_data()
            else:
                messagebox.showerror("Lỗi", "Không thể xóa!")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Quản Lý Ca Trực")
    root.geometry("1000x600")
    app = ShiftManagerPage(root)
    app.pack(fill='both', expand=True)
    root.mainloop()