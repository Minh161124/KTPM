# view/cat_add.py
import tkinter as tk
from tkinter import ttk, messagebox

# --- Giả lập config.py (Màu sắc từ hình ảnh) ---
COLOR_BG = "#4E4E4E"  
COLOR_ENTRY_BG = "#555555" 
COLOR_TEXT_LIGHT = "#FFFFFF" 
COLOR_PLACEHOLDER = "#AAAAAA" 
COLOR_GREEN = "#4CAF50" 
COLOR_RED = "#F44336"   
font_default = ("Arial", 10)
font_bold = ("Arial", 10, "bold")
# --- Kết thúc giả lập ---

class CategoryForm(tk.Toplevel):
    def __init__(self, parent, controller, category_id=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.category_id = category_id 

        # --- Thiết lập màu sắc và phông chữ ---
        self.COLOR_BG = COLOR_BG
        self.COLOR_ENTRY_BG = COLOR_ENTRY_BG
        self.COLOR_TEXT_LIGHT = COLOR_TEXT_LIGHT
        self.COLOR_PLACEHOLDER = COLOR_PLACEHOLDER
        self.COLOR_GREEN = COLOR_GREEN
        self.COLOR_RED = COLOR_RED

        self.font_default = font_default
        self.font_bold = font_bold
        
        # --- Cấu hình cửa sổ chính ---
        if self.category_id:
            self.title("Chỉnh sửa danh mục")
        else:
            self.title("Thêm danh mục mới")
            
        self.category_data = None
        self.config(bg=self.COLOR_BG)
        self.geometry("400x200") # Kích thước nhỏ
        self.grab_set()
        self.resizable(False, False)

        # Các trường nhập từ hình ảnh
        self.placeholders = {
            "Mã danh mục": "Nhập mã danh mục",
            "Tên danh mục": "Nhập tên danh mục"
        }
        self.entries = {}
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=self.COLOR_BG)
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)

        fields = ["Mã danh mục", "Tên danh mục"]
        
        for i, field in enumerate(fields):
            label_text = field + ":"
            label = tk.Label(main_frame, text=label_text, bg=self.COLOR_BG, fg=self.COLOR_TEXT_LIGHT, font=self.font_default)
            label.grid(row=i, column=0, sticky='w', pady=10, padx=5)
            
            entry = tk.Entry(main_frame, font=self.font_default, width=32,
                             bg=self.COLOR_ENTRY_BG, fg=self.COLOR_TEXT_LIGHT,
                             relief='flat', insertbackground=self.COLOR_TEXT_LIGHT)
            self.entries[field] = entry
            entry.grid(row=i, column=1, sticky='w', pady=10, ipady=5)
            
            # Thêm placeholder
            if field in self.placeholders:
                self.add_placeholder(self.entries[field], self.placeholders[field])

        # --- Các nút ---
        save_text = "Thêm +" if self.category_id is None else "Cập nhật"
        
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

    # --- Tải dữ liệu (Cho chế độ Edit) ---
    def load_data(self, category_data):
        self.category_data = category_data

        # Nạp dữ liệu vào các entry
        self.load_entry_data(self.entries["Mã danh mục"], 'ma_dm')
        self.load_entry_data(self.entries["Tên danh mục"], 'ten_dm')
        
        # QUAN TRỌNG: Vô hiệu hóa ô Mã DM khi ở chế độ Sửa
        self.entries["Mã danh mục"].config(state='disabled', fg=self.COLOR_PLACEHOLDER)


    def load_entry_data(self, entry, data_key):
        value = self.category_data.get(data_key, '')
        entry_key = None
        for key, widget in self.entries.items():
            if widget == entry: entry_key = key; break
        placeholder_text = self.placeholders.get(entry_key, None)

        current_val = entry.get()
        if placeholder_text and current_val == placeholder_text and entry.cget('fg') == self.COLOR_PLACEHOLDER:
            entry.delete(0, 'end')
        else:
            entry.delete(0, 'end')
        
        if value is not None:
            entry.insert(0, str(value))
            entry.config(fg=self.COLOR_TEXT_LIGHT)
        elif placeholder_text:
            self.on_entry_focus_out(None, entry, placeholder_text)

    # --- Lưu dữ liệu ---
    def on_save(self):
        data = {}
        for field_name, entry in self.entries.items():
            # Lấy cả giá trị từ ô bị vô hiệu hóa (Mã DM)
            if entry.cget('state') == 'disabled':
                data[field_name] = entry.get()
                continue
                
            if field_name in self.placeholders:
                value = entry.get()
                placeholder = self.placeholders[field_name]
                if value == placeholder and entry.cget('fg') == self.COLOR_PLACEHOLDER:
                    data[field_name] = ""
                else:
                    data[field_name] = value
        
        final_data = {
            'ma_dm': data.get("Mã danh mục", ""),
            'ten_dm': data.get("Tên danh mục", ""),
        }
        
        self.controller.save_category(final_data, self.category_id)

    # === Các hàm tiện ích (Show Error/Info) ===
    def show_error(self, message):
        messagebox.showerror("Lỗi", message, parent=self)

    def show_info_and_close(self, message):
        messagebox.showinfo("Thành công", message, parent=self.parent)
        self.destroy()