# view/prod_view_list.py
import tkinter as tk
from tkinter import ttk, messagebox
from config import * # Giả sử config.py tồn tại và chứa các màu
import math

class ProductListPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_DARK)
        
        self.controller = controller
        
        self.current_display_data = [] 
        self.current_page = 1
        self.items_per_page = 10 
        self.total_records = 0
        self.total_pages = 1
        
        self.page_labels = {}
        
        # --- Màu sắc (cần cho placeholder) ---
        self.COLOR_BG_INPUT = COLOR_BG_INPUT
        self.COLOR_TEXT_LIGHT = COLOR_TEXT_LIGHT
        self.COLOR_PLACEHOLDER = COLOR_TEXT_DISABLED # Dùng màu xám nhạt

        # --- Giao diện (Header) ---
        header_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        header_frame.pack(fill='x')
        tk.Label(header_frame, text="Trang chủ/ Quản lý sản phẩm/ ",  
                 fg=COLOR_TEXT_LIGHT, bg=COLOR_BG_DARK, font=font_header).pack(side='left')
        tk.Label(header_frame, text="Danh sách sản phẩm ↻",  
                 fg=COLOR_ACCENT, bg=COLOR_BG_DARK, font=font_header).pack(side='left')

        title_bar = tk.Frame(self, bg=COLOR_ACCENT)
        title_bar.pack(fill='x', pady=(10, 5))
        tk.Label(title_bar, text="Danh sách sản phẩm", font=font_bold,  
                 bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=10, pady=5)

        # --- Giao diện (Filter) ---
        filter_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        filter_frame.pack(fill='x', pady=5)
        
        # Ô tìm kiếm (có placeholder, không có label)
        self.search_placeholder = "Nhập mã SP, tên SP"
        self.search_entry = self._create_filter_input(filter_frame, 
                                                      label="", 
                                                      placeholder=self.search_placeholder)
        self.search_entry.bind("<KeyRelease>", self._on_filter_change) 
        
        tk.Button(filter_frame, text="Lưu 💾", bg=COLOR_BLUE, fg=COLOR_TEXT_LIGHT,
                   font=font_bold, width=8, relief='flat', activebackground=COLOR_BLUE,
                   cursor="hand2", command=self._on_save).pack(side='right', padx=(5,0), ipady=2)

        tk.Button(filter_frame, text="Thêm +", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT,
                   font=font_bold, width=8, relief='flat', activebackground="#007a3c",
                   cursor="hand2", command=self._on_add).pack(side='right', ipady=2)

        # --- Giao diện (Table) ---
        self.table_frame = tk.Frame(self, bg=COLOR_BG_CELL)
        self.table_frame.pack(fill='both', expand=True)

        # --- Giao diện (Footer/Pagination) ---
        footer = tk.Frame(self, bg=COLOR_BG_DARK)
        footer.pack(fill='x', pady=(5,0))
        footer_left = tk.Frame(footer, bg=COLOR_BG_DARK)
        footer_left.pack(side='left')
        tk.Label(footer_left, text="Hiển thị tối đa",  
                 bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_page).pack(side='left')
        self.cb_limit = ttk.Combobox(footer_left, width=5, font=font_page, style="TCombobox")
        self.cb_limit['values'] = ('10','20','50')
        self.cb_limit.current(0)
        self.cb_limit.bind("<<ComboboxSelected>>", self._on_filter_change) 
        self.cb_limit.pack(side='left', padx=5)

        footer_right = tk.Frame(footer, bg=COLOR_BG_DARK)
        footer_right.pack(side='right')
        for text in ["<<", "<", "Trang 1 / 1", ">", ">>"]: 
            is_page = "Trang" in text
            fg = COLOR_YELLOW if is_page else COLOR_TEXT_LIGHT
            f = font_bold if is_page else font_page
            lbl = tk.Label(footer_right, text=text, bg=COLOR_BG_DARK, fg=fg, font=f, cursor="hand2" if not is_page else "")
            lbl.pack(side='left', padx=5)
            if not is_page: lbl.bind("<Button-1>", lambda e, t=text: self._on_page_nav(t))
            self.page_labels[text] = lbl 
            if is_page: self.page_label_main = lbl
            
    # --- Tương tác với Controller ---

    def trigger_refresh(self):
        search = self.search_entry.get()
        # Nếu vẫn là placeholder thì coi như rỗng
        if search == self.search_placeholder and self.search_entry.cget('fg') == self.COLOR_PLACEHOLDER:
            search = ""
            
        self.items_per_page = int(self.cb_limit.get())
        
        self.controller.refresh_products(search, self.items_per_page, self.current_page)

    def update_display(self, data, total_records):
        self.current_display_data = data
        self.total_records = total_records

        self.total_pages = math.ceil(self.total_records / self.items_per_page)
        if self.total_pages == 0: self.total_pages = 1 
        if self.current_page > self.total_pages:
             self.current_page = self.total_pages 

        self._draw_table()
        self._update_pagination_ui()

    # --- Vẽ giao diện ---
    
    def _draw_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Cột theo hình ảnh
        columns = ["#", "Mã SP", "Tên sản phẩm", "Mã DM", "Mã vạch", "Giá", "Số lượng", "Actions"]
        col_widths = [40, 80, 250, 80, 120, 100, 80, 100] # Điều chỉnh độ rộng

        for i, width in enumerate(col_widths):
            self.table_frame.grid_columnconfigure(i, minsize=width)

        for i, col in enumerate(columns):
            cell_frame = tk.Frame(self.table_frame, bg=COLOR_BG_HEADER) 
            cell_frame.grid(row=0, column=i, sticky='nsew', padx=(0,1), pady=(0,1))
            lbl = tk.Label(cell_frame, text=col, bg=COLOR_BG_HEADER,
                           fg=COLOR_TEXT_LIGHT, font=font_bold, anchor='w')
            lbl.pack(pady=5, padx=5, fill='x')

        if not self.current_display_data:
            cell_frame = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
            cell_frame.grid(row=1, column=0, columnspan=len(columns), sticky='nsew', padx=(0,1))
            lbl = tk.Label(cell_frame, text="Không tìm thấy dữ liệu", bg=COLOR_BG_CELL, 
                           fg=COLOR_TEXT_LIGHT, font=font_default)
            lbl.pack(pady=20, padx=5)
        else:
            for row_index, row_data in enumerate(self.current_display_data, start=1):
                stt = (self.current_page - 1) * self.items_per_page + row_index
                display_row = [stt] + list(row_data[1:]) # Bỏ qua ID (row_data[0])

                for i, val in enumerate(display_row):
                    cell_frame = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
                    cell_frame.grid(row=row_index, column=i, sticky='nsew', padx=(0,1), pady=0)
                    
                    lbl = tk.Label(cell_frame, text=val, bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT,
                                   font=font_default, anchor='w')
                    lbl.pack(pady=5, padx=5, fill='x')

                # Cột cuối là Action
                action_cell_frame = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
                action_cell_frame.grid(row=row_index, column=len(columns)-1, sticky='nsew', padx=(0,1), pady=0)
                
                self._create_action_icons(action_cell_frame, row_data)

    def _create_action_icons(self, parent, row):
        frame = tk.Frame(parent, bg=COLOR_BG_CELL)
        frame.pack(pady=2) 
        
        tk.Button(frame, text="✏️", bg=COLOR_YELLOW, fg=COLOR_TEXT_LIGHT,
                  font=font_icon, width=2, height=1, relief='flat',
                  command=lambda r=row: self._edit_product(r)).pack(side='left', padx=2)
        tk.Button(frame, text="❌", bg=COLOR_RED, fg=COLOR_TEXT_LIGHT,
                  font=font_icon, width=2, height=1, relief='flat',
                  command=lambda r=row: self._delete_product(r)).pack(side='left', padx=2)

    def _update_pagination_ui(self):
        # (Giữ nguyên)
        new_text = f"Trang {self.current_page} / {self.total_pages}"
        self.page_label_main.config(text=new_text)
        # ... (code cập nhật màu mũi tên giữ nguyên) ...

    # ==== HÀM XỬ LÝ SỰ KIỆN ====

    def _on_filter_change(self, event=None):
        self.current_page = 1
        self.trigger_refresh() 

    def _on_page_nav(self, action):
        # ... (code giữ nguyên) ...
        original_page = self.current_page
        if action == "<<" and self.current_page > 1: self.current_page = 1
        elif action == "<" and self.current_page > 1: self.current_page -= 1
        elif action == ">" and self.current_page < self.total_pages: self.current_page += 1
        elif action == ">>" and self.current_page < self.total_pages: self.current_page = self.total_pages
        if original_page != self.current_page:
            self.trigger_refresh()

    def _on_save(self):
        messagebox.showinfo("Thông báo", "Chức năng này có thể dùng để Xuất Excel/CSV.")

    def _on_add(self):
        self.controller.show_add_form()

    def _edit_product(self, row):
        product_id = row[0] # Lấy ID
        self.controller.show_edit_form(product_id)

    def _delete_product(self, row):
        product_id = row[0]
        product_name = row[2] # Tên sản phẩm
        
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa sản phẩm {product_name} (ID: {product_id})?"):
            self.controller.delete_product(product_id)

    # ==== TẠO Ô TÌM KIẾM (Đã sửa để hỗ trợ placeholder) ====
    def _create_filter_input(self, parent, label, type="entry", placeholder=None):
      group = tk.Frame(parent, bg=COLOR_BG_DARK)
      group.pack(side='left', padx=(5,10)) # Thêm padx(5)
      
      # Chỉ tạo label nếu label text được cung cấp
      if label:
          tk.Label(group, text=label, bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_default).pack(side='left')
          
      entry_frame = tk.Frame(group, bg=COLOR_BG_INPUT, bd=1, relief='solid', highlightbackground=COLOR_BORDER, highlightthickness=1)
      entry_frame.pack(side='left')
      
      if type == "combobox":
          cb = ttk.Combobox(entry_frame, width=20, font=font_default, style="TCombobox")
          cb.pack(side='left', ipady=2)
          return cb
      else:
          e = tk.Entry(entry_frame, width=20, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, font=font_default, relief='flat', insertbackground=COLOR_TEXT_LIGHT)
          e.pack(side='left', ipady=2)
          if placeholder:
              self.add_placeholder(e, placeholder)
          return e

    # --- Các hàm xử lý Placeholder (cho ô tìm kiếm) ---
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