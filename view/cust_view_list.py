# view/cust_view_list.py
import tkinter as tk
from tkinter import ttk, messagebox
from config import * 
import math

class CustomerListPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_DARK)
        self.controller = controller
        self.current_display_data = [] 
        self.current_page = 1
        self.items_per_page = 10 
        self.total_records = 0
        self.page_labels = {}

        # --- Header ---
        header_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        header_frame.pack(fill='x', pady=5)
        tk.Label(header_frame, text="Trang chủ / Quản lý Hội viên",  
                 fg=COLOR_TEXT_LIGHT, bg=COLOR_BG_DARK, font=font_header).pack(side='left', padx=10)

        title_bar = tk.Frame(self, bg=COLOR_ACCENT)
        title_bar.pack(fill='x', pady=(5, 5))
        tk.Label(title_bar, text="DANH SÁCH HỘI VIÊN", font=("Arial", 14, "bold"),  
                 bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=10, pady=8)

        # --- Filter Bar ---
        filter_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        filter_frame.pack(fill='x', pady=5, padx=10)
        
        self.search_entry = self._create_filter_input(filter_frame, "Tìm kiếm (TK/SĐT):")
        self.search_entry.bind("<Return>", lambda e: self.trigger_refresh()) # Enter để tìm

        tk.Button(filter_frame, text="Tìm kiếm 🔍", bg=COLOR_BLUE, fg=COLOR_TEXT_LIGHT,
                   font=font_bold, width=10, relief='flat', command=self.trigger_refresh).pack(side='left', padx=5)

        tk.Button(filter_frame, text="Thêm Hội Viên +", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT,
                   font=font_bold, padx=10, relief='flat', cursor="hand2", 
                   command=self._on_add).pack(side='right', ipady=2)

        # --- Table ---
        self.table_frame = tk.Frame(self, bg=COLOR_BG_CELL)
        self.table_frame.pack(fill='both', expand=True, padx=10)

        # --- Footer ---
        self._create_footer()

    def _create_footer(self):
        footer = tk.Frame(self, bg=COLOR_BG_DARK)
        footer.pack(fill='x', pady=10, padx=10)
        
        # Limit selector
        tk.Label(footer, text="Hiển thị:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).pack(side='left')
        self.cb_limit = ttk.Combobox(footer, width=5, values=('10','20','50'), state="readonly")
        self.cb_limit.current(0)
        self.cb_limit.bind("<<ComboboxSelected>>", self._on_filter_change) 
        self.cb_limit.pack(side='left', padx=5)

        # Pagination
        nav_frame = tk.Frame(footer, bg=COLOR_BG_DARK)
        nav_frame.pack(side='right')
        for text in ["<<", "<", "Trang 1/1", ">", ">>"]: 
            is_lbl = "Trang" in text
            fg = COLOR_YELLOW if is_lbl else COLOR_TEXT_LIGHT
            lbl = tk.Label(nav_frame, text=text, bg=COLOR_BG_DARK, fg=fg, 
                           font=font_bold if is_lbl else font_default,
                           cursor="hand2" if not is_lbl else "")
            lbl.pack(side='left', padx=5)
            if not is_lbl: lbl.bind("<Button-1>", lambda e, t=text: self._on_page_nav(t))
            self.page_labels[text] = lbl
            if is_lbl: self.page_label_main = lbl

    # --- Logic ---
    def trigger_refresh(self):
        search = self.search_entry.get()
        limit = int(self.cb_limit.get())
        self.controller.refresh_customers(search, limit, self.current_page)

    def update_display(self, data, total_records):
        self.current_display_data = data
        self.total_records = total_records
        self.total_pages = math.ceil(self.total_records / int(self.cb_limit.get())) or 1
        if self.current_page > self.total_pages: self.current_page = self.total_pages
        
        self._draw_table()
        self._update_pagination_ui()

    def _draw_table(self):
        for w in self.table_frame.winfo_children(): w.destroy()

        # Cột phù hợp quán NET
        columns = ["STT", "Tài khoản", "Họ tên", "SĐT", "Nhóm", "Số dư (VND)", "Trạng thái", "Thao tác"]
        # Độ rộng tương đối
        col_widths = [40, 100, 150, 100, 80, 120, 80, 150]

        for i, (col, width) in enumerate(zip(columns, col_widths)):
            self.table_frame.grid_columnconfigure(i, weight=1 if i==2 else 0, minsize=width)
            lbl = tk.Label(self.table_frame, text=col, bg=COLOR_BG_HEADER, fg=COLOR_TEXT_LIGHT, font=font_bold, pady=8)
            lbl.grid(row=0, column=i, sticky='nsew', padx=1, pady=1)

        if not self.current_display_data:
            tk.Label(self.table_frame, text="Không có dữ liệu hội viên", bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT).grid(row=1, column=0, columnspan=8, pady=20)
            return

        for idx, row in enumerate(self.current_display_data, start=1):
            # row: (id, username, ho_ten, sdt, group_name, balance, status)
            stt = (self.current_page - 1) * int(self.cb_limit.get()) + idx
            
            # Format tiền tệ
            balance_str = "{:,.0f} đ".format(row[5])
            
            # Format trạng thái
            status_str = "Hoạt động" if row[6] == 1 else "Đã khóa"
            status_color = "#4CAF50" if row[6] == 1 else "#F44336" # Xanh / Đỏ

            display_vals = [stt, row[1], row[2], row[3], row[4], balance_str, status_str]

            for c, val in enumerate(display_vals):
                bg_color = COLOR_BG_CELL
                fg_color = COLOR_TEXT_LIGHT
                if c == 5: fg_color = COLOR_YELLOW # Tiền màu vàng cho nổi
                if c == 6: fg_color = status_color

                lbl = tk.Label(self.table_frame, text=val, bg=bg_color, fg=fg_color, font=font_default, pady=5)
                lbl.grid(row=idx, column=c, sticky='nsew', padx=1, pady=1)

            # Cột Action
            action_frame = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
            action_frame.grid(row=idx, column=7, sticky='nsew', padx=1, pady=1)
            
            # Nút Nạp Tiền ($)
            tk.Button(action_frame, text="💲", bg=COLOR_ACCENT, fg="white", width=3, 
                      command=lambda r=row: self.controller.show_topup_dialog(r)).pack(side='left', padx=2, pady=2)
            # Nút Sửa
            tk.Button(action_frame, text="✏️", bg=COLOR_BLUE, fg="white", width=3,
                      command=lambda r=row: self._edit_customer(r)).pack(side='left', padx=2)
            # Nút Xóa
            tk.Button(action_frame, text="🗑️", bg=COLOR_RED, fg="white", width=3,
                      command=lambda r=row: self._delete_customer(r)).pack(side='left', padx=2)

    def _create_filter_input(self, parent, label):
        frame = tk.Frame(parent, bg=COLOR_BG_DARK)
        frame.pack(side='left')
        tk.Label(frame, text=label, bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=5)
        entry = tk.Entry(frame, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, insertbackground='white')
        entry.pack(side='left', ipady=3)
        return entry

    def _on_filter_change(self, event): self.current_page = 1; self.trigger_refresh()
    def _on_page_nav(self, action):
        # (Logic phân trang giữ nguyên như cũ)
        if action == "<<" and self.current_page > 1: self.current_page = 1
        elif action == "<" and self.current_page > 1: self.current_page -= 1
        elif action == ">" and self.current_page < self.total_pages: self.current_page += 1
        elif action == ">>" and self.current_page < self.total_pages: self.current_page = self.total_pages
        self.trigger_refresh()
    
    def _update_pagination_ui(self):
        self.page_label_main.config(text=f"Trang {self.current_page} / {self.total_pages}")

    def _on_add(self): self.controller.show_add_form()
    def _edit_customer(self, row): self.controller.show_edit_form(row[0]) # row[0] is ID
    def _delete_customer(self, row):
        if messagebox.askyesno("Xác nhận", f"Xóa tài khoản '{row[1]}' không?"):
            self.controller.delete_customer(row[0])