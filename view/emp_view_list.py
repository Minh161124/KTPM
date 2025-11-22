import tkinter as tk
from tkinter import ttk, messagebox
from config import * 
import math


class EmployeeListPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_DARK)
        
        self.controller = controller # Nhận controller từ bên ngoài
        # self.db = Database() # XÓA DÒNG NÀY
        
        self.current_display_data = [] 
        self.current_page = 1
        self.items_per_page = 10 
        self.total_records = 0
        self.total_pages = 1
        
        self.page_labels = {}

        # --- Code giao diện (giữ nguyên) ---
        header_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        header_frame.pack(fill='x')
        tk.Label(header_frame, text="Trang chủ/ Quản lý nhân viên/ ",  
                 fg=COLOR_TEXT_LIGHT, bg=COLOR_BG_DARK, font=font_header).pack(side='left')
        tk.Label(header_frame, text="Danh sách nhân viên ↻",  
                 fg=COLOR_ACCENT, bg=COLOR_BG_DARK, font=font_header).pack(side='left')

        title_bar = tk.Frame(self, bg=COLOR_ACCENT)
        title_bar.pack(fill='x', pady=(10, 5))
        tk.Label(title_bar, text="Danh sách nhân viên", font=font_bold,  
                 bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=10, pady=5)

        filter_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        filter_frame.pack(fill='x', pady=5)
        self.search_entry = self._create_filter_input(filter_frame, "Tìm kiếm")
        self.search_entry.bind("<KeyRelease>", self._on_filter_change) 

        self.cb_nhanvien = self._create_filter_input(filter_frame, "Tất cả chức vụ", "combobox")
        self.cb_nhanvien['values'] = ('Tất cả chức vụ', 'NV khác', 'Nhân viên chính', 'Quản lý') 
        self.cb_nhanvien.current(0)
        self.cb_nhanvien.bind("<<ComboboxSelected>>", self._on_filter_change)

        tk.Button(filter_frame, text="Lưu 💾", bg=COLOR_BLUE, fg=COLOR_TEXT_LIGHT,
                   font=font_bold, width=8, relief='flat', activebackground=COLOR_BLUE,
                   cursor="hand2", command=self._on_save).pack(side='right', padx=(5,0), ipady=2)

        tk.Button(filter_frame, text="Thêm +", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT,
                   font=font_bold, width=8, relief='flat', activebackground="#007a3c",
                   cursor="hand2", command=self._on_add).pack(side='right', ipady=2) # Sửa: gọi _on_add

        self.table_frame = tk.Frame(self, bg=COLOR_BG_CELL)
        self.table_frame.pack(fill='both', expand=True)

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

    def trigger_refresh(self):
        """
        Hàm này chỉ gọi controller để yêu cầu làm mới.
        """
        search = self.search_entry.get()
        role = self.cb_nhanvien.get()
        self.items_per_page = int(self.cb_limit.get())
        
        # Gọi controller, thay vì tự mình gọi db
        self.controller.refresh_employees(search, role, self.items_per_page, self.current_page)

    def update_display(self, data, total_records):
        """
        Hàm này được controller gọi để cập nhật UI
        """
        self.current_display_data = data
        self.total_records = total_records

        self.total_pages = math.ceil(self.total_records / self.items_per_page)
        if self.total_pages == 0: self.total_pages = 1 
        if self.current_page > self.total_pages:
             self.current_page = self.total_pages 

        self._draw_table()
        self._update_pagination_ui()

    def _draw_table(self):
        # (Giữ nguyên code _draw_table của bạn)
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        columns = ["#", "Mã NV", "Họ tên", "Tài khoản", "Giới tính", "Số điện thoại", "Chức vụ", "Lương", "Actions"]
        col_widths = [40, 100, 150, 100, 70, 120, 120, 100, 100]

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
                # Hiển thị STT thay vì ID từ DB
                stt = (self.current_page - 1) * self.items_per_page + row_index
                display_row = [stt] + list(row_data[1:]) # Bỏ qua ID (row_data[0])

                for i, val in enumerate(display_row):
                    cell_frame = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
                    cell_frame.grid(row=row_index, column=i, sticky='nsew', padx=(0,1), pady=0)
                    
                    lbl = tk.Label(cell_frame, text=val, bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT,
                                   font=font_default, anchor='w')
                    lbl.pack(pady=5, padx=5, fill='x')

                action_cell_frame = tk.Frame(self.table_frame, bg=COLOR_BG_CELL)
                action_cell_frame.grid(row=row_index, column=8, sticky='nsew', padx=(0,1), pady=0)

                # Truyền toàn bộ row_data (bao gồm cả ID) vào
                self._create_action_icons(action_cell_frame, row_data)

    def _create_action_icons(self, parent, row):
        # (Giữ nguyên code _create_action_icons của bạn)
        frame = tk.Frame(parent, bg=COLOR_BG_CELL)
        frame.pack(pady=2) 
        
        tk.Button(frame, text="✏️", bg=COLOR_YELLOW, fg=COLOR_TEXT_LIGHT,
                  font=font_icon, width=2, height=1, relief='flat',
                  command=lambda r=row: self._edit_employee(r)).pack(side='left', padx=2)
        tk.Button(frame, text="❌", bg=COLOR_RED, fg=COLOR_TEXT_LIGHT,
                  font=font_icon, width=2, height=1, relief='flat',
                  command=lambda r=row: self._delete_employee(r)).pack(side='left', padx=2)

    def _update_pagination_ui(self):
        # (Giữ nguyên code _update_pagination_ui của bạn)
        new_text = f"Trang {self.current_page} / {self.total_pages}"
        self.page_label_main.config(text=new_text)

        self.page_labels["<"].config(fg=COLOR_TEXT_LIGHT if self.current_page > 1 else COLOR_TEXT_DISABLED)
        self.page_labels["<<"].config(fg=COLOR_TEXT_LIGHT if self.current_page > 1 else COLOR_TEXT_DISABLED)
        self.page_labels[">"].config(fg=COLOR_TEXT_LIGHT if self.current_page < self.total_pages else COLOR_TEXT_DISABLED)
        self.page_labels[">>"].config(fg=COLOR_TEXT_LIGHT if self.current_page < self.total_pages else COLOR_TEXT_DISABLED)

    # ==== HÀM XỬ LÝ SỰ KIỆN (Đã sửa đổi) ====

    def _on_filter_change(self, event=None):
        self.current_page = 1
        self.trigger_refresh() # Chỉ gọi refresh

    def _on_page_nav(self, action):
        original_page = self.current_page
        if action == "<<" and self.current_page > 1:
            self.current_page = 1
        elif action == "<" and self.current_page > 1:
            self.current_page -= 1
        elif action == ">" and self.current_page < self.total_pages:
            self.current_page += 1
        elif action == ">>" and self.current_page < self.total_pages:
            self.current_page = self.total_pages
        
        if original_page != self.current_page:
            self.trigger_refresh() # Chỉ gọi refresh nếu trang thay đổi

    def _on_save(self):
        messagebox.showinfo("Thông báo", "Chức năng này có thể dùng để Xuất Excel/CSV.")

    def _on_add(self):
        # Ủy quyền cho controller
        self.controller.show_add_form()

    def _edit_employee(self, row):
        employee_id = row[0] # Lấy ID
        # Ủy quyền cho controller
        self.controller.show_edit_form(employee_id)

    def _delete_employee(self, row):
        employee_id = row[0]
        employee_name = row[2]
        
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa nhân viên {employee_name} (ID: {employee_id})?"):
            # Ủy quyền cho controller
            self.controller.delete_employee(employee_id)

    # ==== TẠO Ô TÌM KIẾM / COMBOBOX ====
    def _create_filter_input(self, parent, label, type="entry"):
      # (Giữ nguyên code _create_filter_input của bạn)
      group = tk.Frame(parent, bg=COLOR_BG_DARK)
      group.pack(side='left', padx=(0,10))
      tk.Label(group, text=label, bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_default).pack(side='left')
      entry_frame = tk.Frame(group, bg=COLOR_BG_INPUT, bd=1, relief='solid', highlightbackground=COLOR_BORDER, highlightthickness=1)
      entry_frame.pack(side='left')
      if type == "combobox":
          cb = ttk.Combobox(entry_frame, width=15, font=font_default, style="TCombobox")
          cb.pack(side='left', ipady=2)
          return cb
      else:
          e = tk.Entry(entry_frame, width=15, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, font=font_default, relief='flat', insertbackground=COLOR_TEXT_LIGHT)
          e.pack(side='left', ipady=2)
          return e