import tkinter as tk
from tkinter import ttk, messagebox

# --- Giả lập config.py với màu sắc từ hình ảnh ---
COLOR_BG = "#4E4E4E"  # Màu nền xám tối
COLOR_BG_LIGHT = "#5A5A5A" # Màu nền sáng hơn một chút (cho radio)
COLOR_ENTRY_BG = "#555555" # Màu nền ô nhập liệu
COLOR_TEXT_LIGHT = "#FFFFFF" # Màu chữ trắng
COLOR_PLACEHOLDER = "#AAAAAA" # Màu chữ placeholder (xám nhạt)
COLOR_GREEN = "#4CAF50" # Màu xanh lá cho nút Save/Add
COLOR_RED = "#F44336"   # Màu đỏ cho nút Cancel
COLOR_YELLOW = "#FFEB3B" # Màu vàng cho checkbox "Đổi MK"

font_default = ("Arial", 10)
font_bold = ("Arial", 10, "bold")
# --- Kết thúc giả lập config.py ---


class EmployeeForm(tk.Toplevel):
    def __init__(self, parent, controller, employee_id=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.employee_id = employee_id

        # --- Thiết lập màu sắc và phông chữ ---
        self.COLOR_BG = COLOR_BG
        self.COLOR_ENTRY_BG = COLOR_ENTRY_BG
        self.COLOR_TEXT_LIGHT = COLOR_TEXT_LIGHT
        self.COLOR_PLACEHOLDER = COLOR_PLACEHOLDER
        self.COLOR_GREEN = COLOR_GREEN
        self.COLOR_RED = COLOR_RED
        self.COLOR_BG_LIGHT = COLOR_BG_LIGHT
        self.COLOR_YELLOW = COLOR_YELLOW

        self.font_default = font_default
        self.font_bold = font_bold
        
        # --- Cấu hình cửa sổ chính ---
        if self.employee_id:
            self.title("Chỉnh sửa nhân viên")
        else:
            self.title("Thêm nhân viên mới")
            
        self.employee_data = None
        self.config(bg=self.COLOR_BG)
        self.geometry("470x550") # Tăng kích thước để chứa đủ các trường
        self.grab_set()
        self.resizable(False, False)

        # --- Style cho Combobox ---
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TCombobox",
                        fieldbackground=self.COLOR_ENTRY_BG,
                        background=self.COLOR_ENTRY_BG,
                        foreground=self.COLOR_TEXT_LIGHT,
                        arrowcolor=self.COLOR_TEXT_LIGHT,
                        selectbackground=self.COLOR_ENTRY_BG,
                        selectforeground=self.COLOR_TEXT_LIGHT,
                        bordercolor=self.COLOR_BG,
                        lightcolor=self.COLOR_BG,
                        darkcolor=self.COLOR_BG)
        style.map('TCombobox',
                  fieldbackground=[('readonly', self.COLOR_ENTRY_BG)],
                  selectbackground=[('readonly', self.COLOR_ENTRY_BG)],
                  foreground=[('readonly', self.COLOR_TEXT_LIGHT)])

        # Các trường nhập từ code gốc
        self.placeholders = {
            "Mã NV": "Nhập mã nhân viên",
            "Họ tên": "Nhập họ tên",
            "Tài khoản": "Nhập tài khoản",
            "Mật khẩu": "Nhập mật khẩu",
            "Số điện thoại": "Nhập số điện thoại",
            "Lương": "Nhập lương"
        }

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=self.COLOR_BG)
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)

        # Giữ nguyên các trường từ code gốc
        fields = ["Mã NV", "Họ tên", "Tài khoản", "Mật khẩu", "Giới tính", "Số điện thoại", "Chức vụ", "Lương"]
        self.entries = {}

        for i, field in enumerate(fields):
            # Thêm dấu ":" cho nhãn
            label_text = field + ":"
            label = tk.Label(main_frame, text=label_text, bg=self.COLOR_BG, fg=self.COLOR_TEXT_LIGHT, font=self.font_default)
            label.grid(row=i, column=0, sticky='w', pady=10, padx=5)
            
            if field == "Giới tính":
                # Thay Combobox bằng Radiobutton (từ giao diện hình ảnh)
                self.gender_var = tk.StringVar(value="Nam") 
                gender_frame = tk.Frame(main_frame, bg=self.COLOR_BG)
                
                radio_nam = tk.Radiobutton(gender_frame, text="Nam", variable=self.gender_var, value="Nam",
                                           bg=self.COLOR_BG, fg=self.COLOR_TEXT_LIGHT, font=self.font_default,
                                           selectcolor=self.COLOR_BG_LIGHT, 
                                           activebackground=self.COLOR_BG,
                                           activeforeground=self.COLOR_TEXT_LIGHT,
                                           borderwidth=0, highlightthickness=0)
                radio_nu = tk.Radiobutton(gender_frame, text="Nữ", variable=self.gender_var, value="Nữ",
                                         bg=self.COLOR_BG, fg=self.COLOR_TEXT_LIGHT, font=self.font_default,
                                         selectcolor=self.COLOR_BG_LIGHT,
                                         activebackground=self.COLOR_BG,
                                         activeforeground=self.COLOR_TEXT_LIGHT,
                                         borderwidth=0, highlightthickness=0)
                
                radio_nam.pack(side='left', padx=5)
                radio_nu.pack(side='left', padx=20)
                gender_frame.grid(row=i, column=1, sticky='w', pady=10)

            elif field == "Chức vụ":
                # Giữ nguyên Combobox nhưng áp dụng style mới
                self.entries[field] = ttk.Combobox(main_frame, values=["Nhân viên", "Admin"],
                                                   font=self.font_default, width=30, state="readonly")
                self.entries[field].grid(row=i, column=1, sticky='w', pady=10, ipady=5)
            
            elif field == "Mật khẩu":
                # Giữ nguyên logic mật khẩu từ code gốc
                entry = tk.Entry(main_frame, font=self.font_default, width=32, show="*",
                                 bg=self.COLOR_ENTRY_BG, fg=self.COLOR_TEXT_LIGHT,
                                 relief='flat', insertbackground=self.COLOR_TEXT_LIGHT)
                self.entries[field] = entry
                 
                if self.employee_id:
                    entry.insert(0, "*********") # Hiển thị giả
                    entry.config(state='disabled') # Vô hiệu hóa
                    
                    # Thêm checkbox cho phép đổi mk (style lại cho nền tối)
                    self.chk_change_pass = tk.BooleanVar()
                    chk = tk.Checkbutton(main_frame, text="Đổi mật khẩu?", 
                                         bg=self.COLOR_BG, 
                                         fg=self.COLOR_YELLOW, 
                                         selectcolor=self.COLOR_BG_LIGHT,
                                         activebackground=self.COLOR_BG,
                                         activeforeground=self.COLOR_YELLOW,
                                         variable=self.chk_change_pass, 
                                         command=self.toggle_password_entry,
                                         font=self.font_default,
                                         borderwidth=0, highlightthickness=0)
                    chk.grid(row=i, column=2, padx=10, sticky='w')
                
                entry.grid(row=i, column=1, sticky='w', pady=10, ipady=5)

            elif field == "Lương":
                # Áp dụng giao diện "Nhập lương [VND]"
                salary_container = tk.Frame(main_frame, bg=self.COLOR_ENTRY_BG, relief='flat', borderwidth=0)
                
                entry = tk.Entry(salary_container, font=self.font_default, width=25,
                                 bg=self.COLOR_ENTRY_BG, fg=self.COLOR_TEXT_LIGHT,
                                 relief='flat', insertbackground=self.COLOR_TEXT_LIGHT)
                self.entries[field] = entry 
                
                unit_label = tk.Label(salary_container, text="VND", bg=self.COLOR_ENTRY_BG, fg=self.COLOR_PLACEHOLDER, font=self.font_default)

                entry.pack(side='left', fill='x', expand=True, ipady=5, padx=(5,0))
                unit_label.pack(side='right', padx=(0, 5))
                
                salary_container.grid(row=i, column=1, sticky='w', pady=10)

            else:
                # Các trường Entry còn lại (Mã NV, Họ tên, Tài khoản, SĐT)
                entry = tk.Entry(main_frame, font=self.font_default, width=32,
                                 bg=self.COLOR_ENTRY_BG, fg=self.COLOR_TEXT_LIGHT,
                                 relief='flat', insertbackground=self.COLOR_TEXT_LIGHT)
                self.entries[field] = entry
                entry.grid(row=i, column=1, sticky='w', pady=10, ipady=5)

            # Thêm placeholder
            if field in self.placeholders:
                # Không thêm placeholder cho Mật khẩu ở chế độ Sửa (vì nó bị vô hiệu hóa)
                if field == "Mật khẩu" and self.employee_id:
                    pass
                else:
                    self.add_placeholder(self.entries[field], self.placeholders[field])

        # --- Các nút (theo giao diện mới) ---
        save_text = "Thêm +" if self.employee_id is None else "Cập nhật"
        
        btn_save = tk.Button(main_frame, text=save_text, bg=self.COLOR_GREEN, fg=self.COLOR_TEXT_LIGHT,
                             font=self.font_bold, width=12, command=self.on_save,
                             relief='flat', borderwidth=0)
        btn_save.grid(row=len(fields), column=1, sticky='e', pady=20)
        
        btn_cancel = tk.Button(main_frame, text="Hủy", bg=self.COLOR_RED, fg=self.COLOR_TEXT_LIGHT,
                               font=self.font_bold, width=12, command=self.destroy,
                               relief='flat', borderwidth=0)
        btn_cancel.grid(row=len(fields), column=0, sticky='w', pady=20)

    # --- Các hàm xử lý Placeholder ---
    def add_placeholder(self, entry, placeholder_text):
        entry.insert(0, placeholder_text)
        entry.config(fg=self.COLOR_PLACEHOLDER)
        entry.bind("<FocusIn>", lambda e: self.on_entry_focus_in(e, entry, placeholder_text))
        entry.bind("<FocusOut>", lambda e: self.on_entry_focus_out(e, entry, placeholder_text))

    def on_entry_focus_in(self, event, entry, placeholder_text):
        if entry.get() == placeholder_text and entry.cget('fg') == self.COLOR_PLACEHOLDER:
            entry.delete(0, 'end')
            entry.config(fg=self.COLOR_TEXT_LIGHT)

    def on_entry_focus_out(self, event, entry, placeholder_text):
        if not entry.get():
            entry.insert(0, placeholder_text)
            entry.config(fg=self.COLOR_PLACEHOLDER)

    # --- Logic đổi mật khẩu (từ code gốc) ---
    def toggle_password_entry(self):
        password_entry = self.entries["Mật khẩu"]
        placeholder = self.placeholders["Mật khẩu"]

        if self.chk_change_pass.get():
            password_entry.config(state='normal')
            password_entry.delete(0, 'end')
            # Thêm placeholder khi bật
            self.add_placeholder(password_entry, placeholder)
            self.on_entry_focus_out(None, password_entry, placeholder) # Hiển thị ngay
            password_entry.focus()
        else:
            # Gỡ placeholder
            password_entry.unbind("<FocusIn>")
            password_entry.unbind("<FocusOut>")
            password_entry.delete(0, 'end')
            password_entry.insert(0, "*********")
            password_entry.config(state='disabled', fg=self.COLOR_TEXT_LIGHT)

    # --- Tải dữ liệu (từ code gốc, đã cập nhật) ---
    def load_data(self, employee_data):
        self.employee_data = employee_data

        # Nạp dữ liệu vào các entry
        self.load_entry_data(self.entries["Mã NV"], 'ma_nv')
        self.load_entry_data(self.entries["Họ tên"], 'ho_ten')
        self.load_entry_data(self.entries["Tài khoản"], 'tai_khoan')
        self.load_entry_data(self.entries["Số điện thoại"], 'sdt')
        self.load_entry_data(self.entries["Lương"], 'luong')

        # Nạp dữ liệu cho Combobox và Radio
        self.gender_var.set(self.employee_data.get('gioi_tinh', 'Nam'))
        self.entries["Chức vụ"].set(self.employee_data.get('chuc_vu', ''))
        
        # Mật khẩu đã được xử lý trong create_widgets

    def load_entry_data(self, entry, data_key):
        """Hàm trợ giúp nạp dữ liệu, xử lý placeholder"""
        value = self.employee_data.get(data_key, '')
        
        entry_key = None
        for key, widget in self.entries.items():
            if widget == entry: entry_key = key; break
        
        placeholder_text = self.placeholders.get(entry_key, None)

        current_val = entry.get()
        if placeholder_text and current_val == placeholder_text and entry.cget('fg') == self.COLOR_PLACEHOLDER:
            entry.delete(0, 'end')
        else:
            entry.delete(0, 'end')
        
        if value:
            entry.insert(0, str(value))
            entry.config(fg=self.COLOR_TEXT_LIGHT)
        elif placeholder_text:
            self.on_entry_focus_out(None, entry, placeholder_text)

    # --- Lưu dữ liệu (từ code gốc, đã cập nhật) ---
    def on_save(self):
        # 1. Thu thập dữ liệu
        data = {}
        for field_name, entry in self.entries.items():
            if field_name in self.placeholders:
                value = entry.get()
                placeholder = self.placeholders[field_name]
                
                # Bỏ qua mật khẩu ở đây
                if field_name == "Mật khẩu": continue

                if value == placeholder and entry.cget('fg') == self.COLOR_PLACEHOLDER:
                    data[field_name] = ""
                else:
                    data[field_name] = value
            elif field_name == "Chức vụ":
                data[field_name] = entry.get()

        # 2. Ánh xạ sang key của controller
        final_data = {
            'ma_nv': data.get("Mã NV", ""),
            'ho_ten': data.get("Họ tên", ""),
            'tai_khoan': data.get("Tài khoản", ""),
            'sdt': data.get("Số điện thoại", ""),
            'luong': data.get("Lương", ""),
            'chuc_vu': data.get("Chức vụ", ""),
            'gioi_tinh': self.gender_var.get(),
            'mat_khau': None,
            'is_changing_pass': False
        }

        # 3. Xử lý logic mật khẩu (từ code gốc)
        password_entry = self.entries["Mật khẩu"]
        password = password_entry.get()
        pass_placeholder = self.placeholders["Mật khẩu"]

        if self.employee_id: # Chế độ sửa
            if self.chk_change_pass.get():
                if password == pass_placeholder and password_entry.cget('fg') == self.COLOR_PLACEHOLDER:
                    final_data['mat_khau'] = "" # Gửi rỗng
                else:
                    final_data['mat_khau'] = password
                final_data['is_changing_pass'] = True
        else: # Chế độ thêm mới
            if password == pass_placeholder and password_entry.cget('fg') == self.COLOR_PLACEHOLDER:
                final_data['mat_khau'] = "" # Gửi rỗng
            else:
                final_data['mat_khau'] = password

        # 4. Gửi cho Controller xử lý
        self.controller.save_employee(final_data, self.employee_id)

    # === Các hàm tiện ích (Giữ nguyên) ===
    
    def show_error(self, message):
        messagebox.showerror("Lỗi", message, parent=self)

    def show_info_and_close(self, message):
        messagebox.showinfo("Thành công", message, parent=self.parent)
        self.destroy()

