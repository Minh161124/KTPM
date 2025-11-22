# view/cust_add.py
import tkinter as tk
from tkinter import ttk, messagebox
from config import * # Sử dụng màu từ config

class CustomerForm(tk.Toplevel):
    def __init__(self, parent, controller, customer_id=None):
        super().__init__(parent)
        self.controller = controller
        self.customer_id = customer_id
        self.config(bg=COLOR_BG_DARK)
        self.title("Thông tin Hội viên" if customer_id else "Thêm Hội viên mới")
        self.geometry("450x450")
        self.resizable(False, False)
        
        self.entries = {}
        self._create_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _create_ui(self):
        main_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        main_frame.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Các trường dữ liệu
        fields = [
            ("Tài khoản (Username):", "username", "text"),
            ("Mật khẩu:", "password", "text"), # Thực tế nên dùng 'show="*"'
            ("Họ và tên:", "ho_ten", "text"),
            ("Số điện thoại:", "sdt", "text"),
            ("Nhóm hội viên:", "group_name", "combo"),
            ("Trạng thái:", "status", "combo")
        ]

        if not self.customer_id:
            fields.insert(5, ("Số dư ban đầu:", "balance", "number"))

        for idx, (label_txt, key, f_type) in enumerate(fields):
            lbl = tk.Label(main_frame, text=label_txt, bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_default)
            lbl.grid(row=idx, column=0, sticky='w', pady=10)
            
            if f_type == "combo":
                if key == "group_name":
                    val = ["Hội viên", "VIP", "Vãng lai"]
                else:
                    val = ["Hoạt động", "Đã khóa"]
                entry = ttk.Combobox(main_frame, values=val, state="readonly", width=28)
                entry.current(0)
            else:
                entry = tk.Entry(main_frame, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, 
                                 font=font_default, width=30, insertbackground='white')
            
            entry.grid(row=idx, column=1, sticky='e', pady=10)
            self.entries[key] = entry

        # Nếu đang Edit, khóa Username
        if self.customer_id:
            self.entries['username'].config(state='disabled', disabledbackground=COLOR_BG_DARK, disabledforeground=COLOR_TEXT_DISABLED)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=COLOR_BG_DARK)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Hủy bỏ", bg=COLOR_RED, fg="white", font=font_bold, width=12,
                  command=self.destroy).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="Lưu dữ liệu", bg=COLOR_ACCENT, fg="white", font=font_bold, width=12,
                  command=self.on_save).pack(side='left', padx=10)

    def load_data(self, data):
        # Data: dict từ database
        self.entries['username'].config(state='normal')
        self.entries['username'].insert(0, data['username'])
        self.entries['username'].config(state='disabled')
        
        self.entries['password'].insert(0, data['password'])
        self.entries['ho_ten'].insert(0, data['ho_ten'])
        if data['sdt']: self.entries['sdt'].insert(0, data['sdt'])
        
        self.entries['group_name'].set(data['group_name'])
        status_text = "Hoạt động" if data['status'] == 1 else "Đã khóa"
        self.entries['status'].set(status_text)

    def on_save(self):
        data = {}
        for key, widget in self.entries.items():
            val = widget.get()
            if key == "status":
                val = 1 if val == "Hoạt động" else 0
            data[key] = val
        
        self.controller.save_customer(data, self.customer_id)


class TopUpDialog(tk.Toplevel):
    """Dialog riêng để nạp tiền nhanh"""
    def __init__(self, parent, controller, customer_info):
        super().__init__(parent)
        self.controller = controller
        self.customer_id = customer_info[0]
        self.title(f"Nạp tiền: {customer_info[1]}")
        self.config(bg=COLOR_BG_DARK)
        self.geometry("350x250")
        
        # Căn giữa
        x = parent.winfo_rootx() + 50
        y = parent.winfo_rooty() + 50
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text=f"Nạp tiền cho: {customer_info[1]}", bg=COLOR_BG_DARK, fg=COLOR_ACCENT, font=font_bold).pack(pady=15)
        
        tk.Label(self, text="Số tiền (VND):", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).pack()
        self.amount_entry = tk.Entry(self, font=("Arial", 14), justify='center')
        self.amount_entry.pack(pady=5, ipady=5)
        self.amount_entry.focus()
        self.amount_entry.bind('<Return>', self.on_confirm)

        # Gợi ý số tiền
        frame_quick = tk.Frame(self, bg=COLOR_BG_DARK)
        frame_quick.pack(pady=10)
        for amt in [10000, 20000, 50000]:
            tk.Button(frame_quick, text=f"{amt//1000}k", width=6, 
                      command=lambda a=amt: self._set_amount(a)).pack(side='left', padx=5)

        tk.Button(self, text="Xác nhận Nạp", bg=COLOR_ACCENT, fg='white', font=font_bold,
                  command=self.on_confirm).pack(pady=10, fill='x', padx=50)

    def _set_amount(self, amount):
        self.amount_entry.delete(0, 'end')
        self.amount_entry.insert(0, str(amount))

    def on_confirm(self, event=None):
        try:
            money = int(self.amount_entry.get())
            if money <= 0: raise ValueError
            self.controller.process_top_up(self.customer_id, money, self)
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số tiền hợp lệ > 0")