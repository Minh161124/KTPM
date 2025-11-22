# view/shift_add_item.py
import tkinter as tk
from tkinter import messagebox
import time

COLOR_BG_DARK = "#2a2a2a"
COLOR_BG_INPUT = "#3c3c3c"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DISABLED = "#AAAAAA"
COLOR_ACCENT = "#00a859"
COLOR_RED = "#e74c3c"

font_default = ('Segoe UI', 10)
font_bold = ('Segoe UI', 10, 'bold')

class ShiftAddItemForm(tk.Toplevel):
    def __init__(self, parent, controller, table_type, on_save_callback, data_to_edit=None, edit_item_id=None):
        super().__init__(parent)
        self.controller = controller
        self.table_type = table_type
        self.on_save_callback = on_save_callback
        self.data_to_edit = data_to_edit
        self.edit_item_id = edit_item_id

        # Config window
        self.configure(bg=COLOR_BG_DARK)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        
        # Title
        type_name = "Chi phí" if table_type == 'expenses' else "Phụ thu"
        action = "Cập nhật" if data_to_edit else "Thêm mới"
        self.title(f"{action} {type_name}")

        # Placeholders
        self.placeholders = {
            "Loại": "Nhập lý do (VD: Mua đá, Tiền ship...)",
            "Thanh toán": "Tiền mặt/Chuyển khoản",
            "Đơn giá": "Nhập số tiền (VD: 20000)",
            "Thời gian": "HH:MM:SS"
        }
        self.entries = {}
        
        self._create_ui()
        self._load_data()

    def _create_ui(self):
        main_frame = tk.Frame(self, bg=COLOR_BG_DARK, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        fields = ["Loại", "Thanh toán", "Đơn giá", "Thời gian"]
        
        for i, field in enumerate(fields):
            tk.Label(main_frame, text=f"{field}:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_default).grid(row=i, column=0, sticky='w', pady=10)
            
            entry = tk.Entry(main_frame, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, 
                             font=font_default, relief='flat', insertbackground=COLOR_TEXT_LIGHT, width=35)
            entry.grid(row=i, column=1, sticky='w', pady=10, padx=(10,0), ipady=4)
            
            self.entries[field] = entry
            if field in self.placeholders:
                self._add_placeholder(entry, self.placeholders[field])

        # Nút bấm
        btn_frame = tk.Frame(main_frame, bg=COLOR_BG_DARK)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(20,0), sticky='e')

        btn_save_text = "Cập nhật" if self.data_to_edit else "Lưu lại"
        tk.Button(btn_frame, text=btn_save_text, bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, font=font_bold,
                  width=10, relief='flat', command=self._on_save).pack(side='right', padx=5)
        
        tk.Button(btn_frame, text="Hủy", bg=COLOR_RED, fg=COLOR_TEXT_LIGHT, font=font_bold,
                  width=10, relief='flat', command=self.destroy).pack(side='right')

        # Căn giữa màn hình cha
        self.geometry("+%d+%d" % (self.master.winfo_rootx() + 50, self.master.winfo_rooty() + 50))

    def _add_placeholder(self, entry, text):
        entry.insert(0, text)
        entry.config(fg=COLOR_TEXT_DISABLED)
        entry.bind("<FocusIn>", lambda e: self._on_focus_in(e, entry, text))
        entry.bind("<FocusOut>", lambda e: self._on_focus_out(e, entry, text))

    def _on_focus_in(self, event, entry, text):
        if entry.get() == text and entry.cget('fg') == COLOR_TEXT_DISABLED:
            entry.delete(0, 'end')
            entry.config(fg=COLOR_TEXT_LIGHT)

    def _on_focus_out(self, event, entry, text):
        if not entry.get():
            entry.insert(0, text)
            entry.config(fg=COLOR_TEXT_DISABLED)

    def _load_data(self):
        # Tự động điền thời gian hiện tại nếu thêm mới
        if not self.data_to_edit:
            time_entry = self.entries["Thời gian"]
            # Xóa placeholder trước khi insert
            if time_entry.cget('fg') == COLOR_TEXT_DISABLED:
                 time_entry.delete(0, 'end')
                 time_entry.config(fg=COLOR_TEXT_LIGHT)
            time_entry.insert(0, time.strftime("%Y-%m-%d %H:%M:%S"))
            return

        # Fill dữ liệu nếu là Edit
        mapping = {
            "Loại": self.data_to_edit[1],
            "Thanh toán": self.data_to_edit[2],
            "Đơn giá": int(self.data_to_edit[3]),
            "Thời gian": self.data_to_edit[4]
        }
        for field, val in mapping.items():
            entry = self.entries[field]
            if entry.cget('fg') == COLOR_TEXT_DISABLED:
                entry.delete(0, 'end')
                entry.config(fg=COLOR_TEXT_LIGHT)
            entry.delete(0, 'end')
            entry.insert(0, str(val))

    def _on_save(self):
        data = {}
        for field, entry in self.entries.items():
            val = entry.get()
            if val == self.placeholders[field] and entry.cget('fg') == COLOR_TEXT_DISABLED:
                val = ""
            data[field] = val
        
        if not data["Loại"] or not data["Đơn giá"]:
            messagebox.showerror("Lỗi", "Vui lòng nhập Loại và Đơn giá", parent=self)
            return

        try:
            clean_data = (data["Loại"], data["Thanh toán"], data["Đơn giá"], data["Thời gian"])
            self.on_save_callback(self.table_type, clean_data, self.edit_item_id)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

class ShiftAddProductForm(tk.Toplevel):
    def __init__(self, parent, controller, on_save_callback):
        super().__init__(parent)
        self.controller = controller
        self.on_save_callback = on_save_callback
        
        self.config(bg=COLOR_BG_DARK)
        self.title("Thêm Sản Phẩm vào Ca")
        self.geometry("450x450")
        self.transient(parent)
        self.grab_set()
        
        self._create_ui()

    def _create_ui(self):
        main_frame = tk.Frame(self, bg=COLOR_BG_DARK, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # 1. Tên SP & Đơn vị & Giá (Giả lập nhập tay, thực tế nên là Dropdown chọn từ kho)
        self.entry_ten = self._add_field(main_frame, 0, "Tên sản phẩm:", "VD: Sting, Mì tôm...")
        self.entry_dv = self._add_field(main_frame, 1, "Đơn vị:", "Chai/Lon/Gói")
        self.entry_gia = self._add_field(main_frame, 2, "Giá bán:", "0")

        tk.Frame(main_frame, height=1, bg="#555").grid(row=3, column=0, columnspan=2, sticky='ew', pady=15)
        
        # 2. Các số lượng
        tk.Label(main_frame, text="SỐ LƯỢNG:", bg=COLOR_BG_DARK, fg=COLOR_ACCENT, font=font_bold).grid(row=4, column=0, sticky='w')
        
        self.entry_khach = self._add_field(main_frame, 5, "Khách mua (+):", "0")
        self.entry_nv = self._add_field(main_frame, 6, "Nhân viên dùng (+):", "0")
        self.entry_km = self._add_field(main_frame, 7, "Khuyến mãi (0đ):", "0")

        # 3. Buttons
        btn_frame = tk.Frame(main_frame, bg=COLOR_BG_DARK)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Lưu Sản Phẩm", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, font=font_bold,
                  width=15, relief='flat', command=self._save).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Hủy", bg=COLOR_RED, fg=COLOR_TEXT_LIGHT, font=font_bold,
                  width=10, relief='flat', command=self.destroy).pack(side='left', padx=5)

    def _add_field(self, parent, row, label, placeholder):
        tk.Label(parent, text=label, bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_default).grid(row=row, column=0, sticky='w', pady=5)
        entry = tk.Entry(parent, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, font=font_default, relief='flat', width=25)
        entry.grid(row=row, column=1, sticky='w', pady=5, ipady=3)
        entry.insert(0, placeholder)
        # Logic placeholder đơn giản
        entry.bind("<FocusIn>", lambda e: entry.delete(0, 'end') if entry.get() == placeholder else None)
        return entry

    def _save(self):
        try:
            data = {
                "san_pham": self.entry_ten.get(),
                "don_vi": self.entry_dv.get(),
                "gia_ban": self.controller._parse_currency(self.entry_gia.get()),
                "khach": int(self.entry_khach.get()) if self.entry_khach.get().isdigit() else 0,
                "nv": int(self.entry_nv.get()) if self.entry_nv.get().isdigit() else 0,
                "km": int(self.entry_km.get()) if self.entry_km.get().isdigit() else 0,
            }
            if not data["san_pham"] or data["san_pham"] == "VD: Sting, Mì tôm...":
                messagebox.showerror("Lỗi", "Chưa nhập tên sản phẩm")
                return
                
            self.on_save_callback(data)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Dữ liệu không hợp lệ: {e}")