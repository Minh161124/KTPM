import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkFont

class CustomerView(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cyber Cafe Client")
        self.geometry("900x600")
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)
        
        self.controller = None
        self._setup_ui()

    def set_controller(self, controller):
        self.controller = controller

    def _setup_ui(self):
        # --- Styles ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#333", foreground="white", padding=[20, 10], font=('Arial', 10, 'bold'))
        style.map("TNotebook.Tab", background=[("selected", "#D60000")], foreground=[("selected", "white")])
        style.configure("Card.TFrame", background="#2b2b2b", relief="flat")

        # --- Header ---
        header_frame = tk.Frame(self, bg="#D60000", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        lbl_brand = tk.Label(header_frame, text="GAMING CENTER CLIENT", font=("Arial", 18, "bold"), fg="white", bg="#D60000")
        lbl_brand.pack(side="left", padx=20)

        # Nút Đăng xuất
        btn_logout = tk.Button(header_frame, text="ĐĂNG XUẤT", font=("Arial", 10, "bold"), 
                               bg="white", fg="#D60000", borderwidth=0, 
                               command=lambda: self.controller.handle_logout())
        btn_logout.pack(side="right", padx=20, pady=10, ipadx=10)

        # --- Main Layout (Grid) ---
        main_container = tk.Frame(self, bg="#1e1e1e")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Cột Trái: Thông tin tài khoản (Sidebar)
        sidebar = tk.Frame(main_container, bg="#2b2b2b", width=250)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)

        self._setup_sidebar(sidebar)

        # Cột Phải: Các chức năng (Tabs)
        content_area = tk.Frame(main_container, bg="#1e1e1e")
        content_area.pack(side="right", fill="both", expand=True)

        self.notebook = ttk.Notebook(content_area)
        self.notebook.pack(fill="both", expand=True)

        self.tab_service = tk.Frame(self.notebook, bg="#2b2b2b")
        self.tab_history = tk.Frame(self.notebook, bg="#2b2b2b")
        
        self.notebook.add(self.tab_service, text="GỌI DỊCH VỤ")
        self.notebook.add(self.tab_history, text="LỊCH SỬ")

        self._setup_service_tab()

    def _setup_sidebar(self, parent):
        # Avatar giả lập
        tk.Label(parent, text="👤", font=("Arial", 60), bg="#2b2b2b", fg="#555").pack(pady=(30, 10))
        
        self.lbl_name = tk.Label(parent, text="---", font=("Arial", 14, "bold"), bg="#2b2b2b", fg="white")
        self.lbl_name.pack(pady=5)

        self.lbl_group = tk.Label(parent, text="Member", font=("Arial", 10), bg="#2b2b2b", fg="#888")
        self.lbl_group.pack(pady=(0, 20))

        # Thông tin chỉ số
        info_box = tk.Frame(parent, bg="#333", padx=10, pady=10)
        info_box.pack(fill="x", padx=15)

        tk.Label(info_box, text="SỐ DƯ TÀI KHOẢN:", font=("Arial", 9), bg="#333", fg="#aaa").pack(anchor="w")
        self.lbl_balance = tk.Label(info_box, text="0 VNĐ", font=("Arial", 16, "bold"), bg="#333", fg="#4CAF50")
        self.lbl_balance.pack(anchor="w", pady=(0, 10))

        tk.Label(info_box, text="THỜI GIAN CÒN LẠI:", font=("Arial", 9), bg="#333", fg="#aaa").pack(anchor="w")
        self.lbl_time_left = tk.Label(info_box, text="00:00", font=("Arial", 20, "bold"), bg="#333", fg="#FFC107")
        self.lbl_time_left.pack(anchor="c", pady=5)

        tk.Label(info_box, text="Đơn giá: 5.000đ/giờ", font=("Arial", 8, "italic"), bg="#333", fg="#666").pack(anchor="c")

    def _setup_service_tab(self):
        # Tiêu đề
        tk.Label(self.tab_service, text="MENU ĐỒ ĂN & THỨC UỐNG", font=("Arial", 14, "bold"), 
                 bg="#2b2b2b", fg="#D60000").pack(pady=15)
        
        # Grid chứa các món ăn
        self.menu_container = tk.Frame(self.tab_service, bg="#2b2b2b")
        self.menu_container.pack(fill="both", expand=True, padx=20)

    def render_menu(self, menu_list):
        # Xóa cũ
        for widget in self.menu_container.winfo_children():
            widget.destroy()

        # Render menu dạng lưới
        columns = 3
        for i, item in enumerate(menu_list):
            row = i // columns
            col = i % columns
            
            frame = tk.Frame(self.menu_container, bg="#383838", bd=1, relief="solid")
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Tên món
            tk.Label(frame, text=item['name'], font=("Arial", 11, "bold"), bg="#383838", fg="white").pack(pady=(10, 5))
            # Giá
            tk.Label(frame, text=f"{item['price']:,} đ", font=("Arial", 10), bg="#383838", fg="#4CAF50").pack(pady=0)
            # Nút gọi
            tk.Button(frame, text="GỌI MÓN", bg="#D60000", fg="white", relief="flat", font=("Arial", 9, "bold"),
                      command=lambda x=item: self.controller.handle_order(x)).pack(pady=10, ipadx=15)

        self.menu_container.grid_columnconfigure((0,1,2), weight=1)

    def update_info(self, name, group, balance, time_str):
        self.lbl_name.config(text=name)
        self.lbl_group.config(text=group)
        self.lbl_balance.config(text=f"{balance:,.0f} VNĐ")
        self.lbl_time_left.config(text=time_str)