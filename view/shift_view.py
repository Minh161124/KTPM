import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time

# --- THEME COLORS (NET CAFE STYLE) ---
COLOR_BG = "#1e1e2e"          # Nền chính tối
COLOR_PANEL = "#252537"       # Nền các khối
COLOR_ACCENT = "#00d2ff"      # Xanh Neon (Cyberpunk)
COLOR_ACCENT_HOVER = "#33ddff"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_MUTED = "#a0a0a0"
COLOR_RED = "#ff4757"
COLOR_GREEN = "#2ed573"
COLOR_YELLOW = "#ffa502"
FONT_MAIN = ('Segoe UI', 10)
FONT_BOLD = ('Segoe UI', 10, 'bold')
FONT_HEADER = ('Segoe UI', 14, 'bold')

class ShiftCreateView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG)
        self.controller = controller
        
        # Setup Style cho Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=COLOR_PANEL, 
                        foreground=COLOR_TEXT, 
                        fieldbackground=COLOR_PANEL, 
                        borderwidth=0,
                        font=FONT_MAIN)
        style.configure("Treeview.Heading", 
                        background="#2f2f45", 
                        foreground=COLOR_ACCENT, 
                        font=FONT_BOLD, 
                        borderwidth=0)
        style.map("Treeview", background=[('selected', COLOR_ACCENT)], foreground=[('selected', '#000')])

        # --- LAYOUT CHÍNH: 3 CỘT ---
        self.columnconfigure(0, weight=3) # Menu (Trái)
        self.columnconfigure(1, weight=4) # Danh sách (Giữa)
        self.columnconfigure(2, weight=2) # Tổng kết (Phải)
        self.rowconfigure(0, weight=1)

        self._init_left_panel()   # Menu chọn món
        self._init_center_panel() # Danh sách item trong ca
        self._init_right_panel()  # Tổng kết & Action

    # ==========================================================================
    # 1. LEFT PANEL: QUICK MENU (POS)
    # ==========================================================================
    def _init_left_panel(self):
        pnl_left = tk.Frame(self, bg=COLOR_PANEL, padx=10, pady=10)
        pnl_left.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        tk.Label(pnl_left, text="📦 MENU DỊCH VỤ", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        # Tab chọn loại (Nước, Ăn, Thẻ)
        self.tab_control = ttk.Notebook(pnl_left)
        self.tab_control.pack(expand=1, fill="both")

        # Tạo 3 tab
        self.tab_nuoc = tk.Frame(self.tab_control, bg=COLOR_PANEL)
        self.tab_doan = tk.Frame(self.tab_control, bg=COLOR_PANEL)
        self.tab_the = tk.Frame(self.tab_control, bg=COLOR_PANEL)

        self.tab_control.add(self.tab_nuoc, text='Nước Uống')
        self.tab_control.add(self.tab_doan, text='Đồ Ăn')
        self.tab_control.add(self.tab_the, text='Thẻ Game/ĐT')

    def render_menu_items(self, menu_list):
        """Hàm được Controller gọi để vẽ các nút món ăn"""
        
        def draw_grid(parent, items):
            # Xóa cũ
            for widget in parent.winfo_children(): widget.destroy()
            
            # Vẽ Grid
            col_count = 3
            for i, item in enumerate(items):
                r, c = divmod(i, col_count)
                
                # Card sản phẩm
                btn = tk.Button(parent, text=f"{item['name']}\n{item['price']:,}", 
                                bg="#3a3a50", fg=COLOR_TEXT, font=FONT_BOLD,
                                relief="flat", borderwidth=0, cursor="hand2",
                                command=lambda x=item: self.controller.add_product_quick(x))
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2, ipady=10)
                
                parent.grid_columnconfigure(c, weight=1)

        # Lọc theo danh mục
        nuoc = [x for x in menu_list if x['category'] == 'Nuoc']
        doan = [x for x in menu_list if x['category'] == 'DoAn']
        the = [x for x in menu_list if x['category'] == 'The']

        draw_grid(self.tab_nuoc, nuoc)
        draw_grid(self.tab_doan, doan)
        draw_grid(self.tab_the, the)

    # ==========================================================================
    # 2. CENTER PANEL: SHIFT DETAILS
    # ==========================================================================
    def _init_center_panel(self):
        pnl_center = tk.Frame(self, bg=COLOR_PANEL, padx=10, pady=10)
        pnl_center.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Header
        header = tk.Frame(pnl_center, bg=COLOR_PANEL)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="📝 CHI TIẾT CA", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_YELLOW).pack(side="left")
        
        # Nút thêm Chi phí / Nạp tiền thủ công
        btn_box = tk.Frame(header, bg=COLOR_PANEL)
        btn_box.pack(side="right")
        
        tk.Button(btn_box, text="➖ Chi Phí", bg=COLOR_RED, fg="white", font=FONT_BOLD, relief="flat",
                  command=lambda: self.controller.show_add_form('expenses')).pack(side="left", padx=2)
        tk.Button(btn_box, text="➕ Phụ Thu", bg=COLOR_GREEN, fg="white", font=FONT_BOLD, relief="flat",
                  command=lambda: self.controller.show_add_form('additions')).pack(side="left", padx=2)

        # Bảng danh sách (Treeview)
        cols = ("ID", "Loại", "Nội dung/Tên", "SL", "Đơn giá", "Thành tiền")
        self.tree = ttk.Treeview(pnl_center, columns=cols, show="headings", selectmode="browse")
        
        # Cấu hình cột
        self.tree.heading("ID", text="#")
        self.tree.column("ID", width=30, anchor="center")
        self.tree.heading("Loại", text="Loại")
        self.tree.column("Loại", width=60, anchor="center")
        self.tree.heading("Nội dung/Tên", text="Nội dung")
        self.tree.column("Nội dung/Tên", width=150)
        self.tree.heading("SL", text="SL")
        self.tree.column("SL", width=40, anchor="center")
        self.tree.heading("Đơn giá", text="Đơn giá")
        self.tree.column("Đơn giá", width=80, anchor="e")
        self.tree.heading("Thành tiền", text="Thành tiền")
        self.tree.column("Thành tiền", width=80, anchor="e")

        self.tree.pack(fill="both", expand=True)
        
        # Sự kiện double click để xóa
        self.tree.bind("<Double-1>", self.controller.on_tree_double_click)

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_tree_row(self, r_id, r_type, name, sl, price, total, tags):
        self.tree.insert("", "end", values=(r_id, r_type, name, sl, f"{price:,}", f"{total:,}"), tags=(tags,))

    def _init_right_panel(self):
        pnl_right = tk.Frame(self, bg=COLOR_BG, padx=0, pady=5)
        pnl_right.grid(row=0, column=2, sticky="nsew")

        fr_info = tk.Frame(pnl_right, bg=COLOR_PANEL, padx=15, pady=15)
        fr_info.pack(fill="x", pady=5)
        
        tk.Label(fr_info, text="THÔNG TIN CA", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).pack(anchor="w")
        
        self.lbl_shift_id = tk.Label(fr_info, text="Chưa tạo ca", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_ACCENT)
        self.lbl_shift_id.pack(pady=5)
        
        self.combo_ca = ttk.Combobox(fr_info, values=["Sáng (06-14)", "Chiều (14-22)", "Đêm (22-06)"], state="readonly")
        self.combo_ca.current(0)
        self.combo_ca.pack(fill="x", pady=5)
        
        self.btn_start = tk.Button(fr_info, text="▶ BẮT ĐẦU CA", bg=COLOR_ACCENT, fg="#000", font=FONT_BOLD, 
                                   relief="flat", pady=5, command=self.controller.create_shift)
        self.btn_start.pack(fill="x", pady=5)

        # --- Block 2: Thống kê tiền ---
        fr_sum = tk.Frame(pnl_right, bg=COLOR_PANEL, padx=15, pady=15)
        fr_sum.pack(fill="both", expand=True, pady=5)

        tk.Label(fr_sum, text="TỔNG KẾT", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).pack(anchor="w")

        # Grid thống kê
        grid_sum = tk.Frame(fr_sum, bg=COLOR_PANEL)
        grid_sum.pack(fill="x", pady=10)
        
        self.lbl_doanh_thu = self._add_stat_row(grid_sum, 0, "Doanh thu:", COLOR_GREEN)
        self.lbl_thu_khac = self._add_stat_row(grid_sum, 1, "Phụ thu:", COLOR_GREEN)
        self.lbl_chi_phi = self._add_stat_row(grid_sum, 2, "Chi phí:", COLOR_RED)
        tk.Frame(grid_sum, height=1, bg=COLOR_TEXT_MUTED).grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.lbl_can_co = self._add_stat_row(grid_sum, 4, "PHẢI CÓ:", COLOR_ACCENT, font=FONT_HEADER)

        # Input thực đếm
        tk.Label(fr_sum, text="Thực đếm tại quầy:", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(anchor="w", pady=(15,0))
        self.entry_thuc_dem = tk.Entry(fr_sum, font=FONT_HEADER, bg="#111", fg=COLOR_YELLOW, justify="right", insertbackground="white")
        self.entry_thuc_dem.insert(0, "0")
        self.entry_thuc_dem.pack(fill="x", pady=5, ipady=5)
        self.entry_thuc_dem.bind("<KeyRelease>", self.controller.update_summary_calc)

        self.lbl_chenh_lech = tk.Label(fr_sum, text="Chênh lệch: 0", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.lbl_chenh_lech.pack(anchor="e", pady=5)

        # --- Block 3: Chốt ca ---
        self.btn_end = tk.Button(fr_sum, text="🔒 CHỐT CA & IN", bg=COLOR_RED, fg="white", font=FONT_BOLD, 
                                 relief="flat", pady=10, state="disabled", command=self.controller.close_shift)
        self.btn_end.pack(side="bottom", fill="x")

    def _add_stat_row(self, parent, row, label, color, font=FONT_BOLD):
        tk.Label(parent, text=label, bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED, font=FONT_MAIN).grid(row=row, column=0, sticky="w", pady=2)
        lbl_val = tk.Label(parent, text="0", bg=COLOR_PANEL, fg=color, font=font)
        lbl_val.grid(row=row, column=1, sticky="e", pady=2)
        return lbl_val

    def update_status(self, is_active, shift_id_text):
        if is_active:
            self.btn_start.config(state="disabled", bg="#444", text="Đang trong ca")
            self.btn_end.config(state="normal", bg=COLOR_RED)
            self.lbl_shift_id.config(text=f"Ca #{shift_id_text}")
            self.combo_ca.config(state="disabled")
        else:
            self.btn_start.config(state="normal", bg=COLOR_ACCENT, text="▶ BẮT ĐẦU CA")
            self.btn_end.config(state="disabled", bg="#444")
            self.lbl_shift_id.config(text="Chưa tạo ca")
            self.combo_ca.config(state="readonly")