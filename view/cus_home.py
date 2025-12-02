import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText


class CustomerView(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cyber Cafe Client - Premium")
        self.geometry("950x650")
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
        
        # Style cho Treeview Lịch sử
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
        style.configure("Treeview.Heading", background="#444", foreground="white", font=('Arial', 10, 'bold'))
        style.map("Treeview", background=[("selected", "#D60000")])

        # --- Header ---
        header_frame = tk.Frame(self, bg="#D60000", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        lbl_brand = tk.Label(header_frame, text="GAMING CENTER CLIENT", font=("Arial", 18, "bold"), fg="white", bg="#D60000")
        lbl_brand.pack(side="left", padx=20)

        btn_logout = tk.Button(header_frame, text="ĐĂNG XUẤT", font=("Arial", 10, "bold"), 
                               bg="white", fg="#D60000", borderwidth=0, cursor="hand2",
                               command=lambda: self.controller.handle_logout())
        btn_logout.pack(side="right", padx=20, pady=10, ipadx=10)

        # --- Main Layout ---
        main_container = tk.Frame(self, bg="#1e1e1e")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Cột Trái: Sidebar
        sidebar = tk.Frame(main_container, bg="#2b2b2b", width=260)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)
        self._setup_sidebar(sidebar)

        content_area = tk.Frame(main_container, bg="#1e1e1e")
        content_area.pack(side="right", fill="both", expand=True)

        self.notebook = ttk.Notebook(content_area)
        self.notebook.pack(fill="both", expand=True)

        self.tab_service = tk.Frame(self.notebook, bg="#2b2b2b")
        self.tab_history = tk.Frame(self.notebook, bg="#2b2b2b")
        self.tab_chat = tk.Frame(self.notebook, bg="#2b2b2b") 
        
        self.notebook.add(self.tab_service, text="GỌI DỊCH VỤ")
        self.notebook.add(self.tab_history, text="LỊCH SỬ GIAO DỊCH")
        self.notebook.add(self.tab_chat, text="HỖ TRỢ / CHAT") 

        self._setup_service_tab()
        self._setup_history_tab()
        self._setup_chat_tab()

    def _setup_sidebar(self, parent):
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
        self.lbl_time_left = tk.Label(info_box, text="00:00:00", font=("Arial", 22, "bold"), bg="#333", fg="#FFC107")
        self.lbl_time_left.pack(anchor="c", pady=5)

        # Nút chức năng phụ
        btn_changepass = tk.Button(parent, text="Đổi mật khẩu", bg="#444", fg="white", relief="flat",
                                   command=lambda: self.controller.handle_change_password())
        btn_changepass.pack(side="bottom", fill="x", padx=15, pady=20, ipady=5)

    def _setup_service_tab(self):
        # Filter Frame
        filter_frame = tk.Frame(self.tab_service, bg="#2b2b2b")
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(filter_frame, text="Lọc theo:", bg="#2b2b2b", fg="white").pack(side="left")
        
        self.filter_var = tk.StringVar(value="ALL")
        filters = [("Tất cả", "ALL"), ("Đồ ăn", "DM01"), ("Nước uống", "DM02"), ("Thẻ nạp", "DM03")]
        
        for text, val in filters:
            tk.Radiobutton(filter_frame, text=text, variable=self.filter_var, value=val, 
                           bg="#2b2b2b", fg="white", selectcolor="#444", activebackground="#2b2b2b",
                           command=lambda: self.controller.filter_menu(self.filter_var.get())).pack(side="left", padx=10)

        # Canvas & Scrollbar cho Menu (để cuộn khi menu dài)
        container = tk.Frame(self.tab_service, bg="#2b2b2b")
        container.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(container, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2b2b2b")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def render_menu(self, menu_list):
        # Xóa widget cũ trong scrollable_frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not menu_list:
            tk.Label(self.scrollable_frame, text="Không có sản phẩm nào", bg="#2b2b2b", fg="#888").pack(pady=20)
            return

        # Render Grid 3 cột
        columns = 3
        for i, item in enumerate(menu_list):
            row = i // columns
            col = i % columns
            
            # Card sản phẩm
            card = tk.Frame(self.scrollable_frame, bg="#383838", bd=1, relief="solid")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Icon category (Giả lập)
            cat_icon = "🍜" if item['ma_dm'] == 'DM01' else "🥤" if item['ma_dm'] == 'DM02' else "💳"
            
            tk.Label(card, text=cat_icon, font=("Arial", 20), bg="#383838").pack(pady=(10,0))
            
            tk.Label(card, text=item['ten_sp'], font=("Arial", 11, "bold"), bg="#383838", fg="white", wraplength=140).pack(pady=5)
            tk.Label(card, text=f"Tồn: {item['so_luong']}", font=("Arial", 8), bg="#383838", fg="#aaa").pack()
            tk.Label(card, text=f"{item['gia']:,} đ", font=("Arial", 12, "bold"), bg="#383838", fg="#4CAF50").pack(pady=5)
            
            tk.Button(card, text="GỌI NGAY", bg="#D60000", fg="white", relief="flat", font=("Arial", 9, "bold"), cursor="hand2",
                      command=lambda x=item: self.controller.handle_order(x)).pack(pady=(0, 15), ipadx=20)
            
    def _setup_chat_tab(self):
        # Khung hiển thị tin nhắn
        chat_container = tk.Frame(self.tab_chat, bg="#2b2b2b", padx=10, pady=10)
        chat_container.pack(fill="both", expand=True)

        self.chat_display = ScrolledText(chat_container, state='disabled', bg="#333", fg="white", 
                                         font=("Arial", 11), wrap="word", height=15)
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Cấu hình màu sắc cho các loại tin nhắn
        self.chat_display.tag_config("CLIENT", foreground="#4CAF50", justify="right") # Khách: Xanh lá, căn phải
        self.chat_display.tag_config("ADMIN", foreground="#FFC107", justify="left")   # Admin: Vàng, căn trái
        self.chat_display.tag_config("SYSTEM", foreground="#AAAAAA", justify="center", font=("Arial", 9, "italic")) # Hệ thống: Xám, giữa

        input_frame = tk.Frame(self.tab_chat, bg="#2b2b2b", padx=10) 
        input_frame.pack(fill="x", pady=(0, 10)) 

        self.msg_entry = tk.Entry(input_frame, font=("Arial", 12), bg="white", fg="black")
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(5, 10), ipady=5)
        self.msg_entry.bind("<Return>", lambda event: self.controller.send_message()) # Enter để gửi

        btn_send = tk.Button(input_frame, text="GỬI", bg="#D60000", fg="white", font=("Arial", 10, "bold"),
                             command=lambda: self.controller.send_message())
        btn_send.pack(side="right", ipadx=20, ipady=2)

    def append_message(self, sender, text):
        self.chat_display.config(state='normal')
        
        if sender == "CLIENT":
            self.chat_display.insert(tk.END, f"Bạn: {text}\n", "CLIENT")
        elif sender == "ADMIN":
            self.chat_display.insert(tk.END, f"Admin: {text}\n", "ADMIN")
        elif sender == "SYSTEM":
            self.chat_display.insert(tk.END, f"--- {text} ---\n", "SYSTEM")
            
        self.chat_display.see(tk.END) # Tự động cuộn xuống dưới cùng
        self.chat_display.config(state='disabled')

    def clear_message_entry(self):
        self.msg_entry.delete(0, tk.END)

    def _setup_history_tab(self):
        # Treeview
        columns = ("content", "amount", "time")
        self.tree = ttk.Treeview(self.tab_history, columns=columns, show="headings")
        
        self.tree.heading("content", text="Nội dung")
        self.tree.heading("amount", text="Số tiền")
        self.tree.heading("time", text="Thời gian")
        
        self.tree.column("content", width=300)
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("time", width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        
        btn_refresh = tk.Button(self.tab_history, text="Làm mới", command=lambda: self.controller.load_history())
        btn_refresh.pack(pady=5)

    def update_history_table(self, history_list):
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        for row in history_list:
            amount_str = f"{row['amount']:,} đ"
            self.tree.insert("", "end", values=(row['content'], amount_str, row['created_at']))

    def update_info(self, name, group, balance, time_str):
        self.lbl_name.config(text=name)
        self.lbl_group.config(text=group)
        self.lbl_balance.config(text=f"{balance:,.0f} VNĐ")
        self.lbl_time_left.config(text=time_str)

    def ask_password_change(self):
        return simpledialog.askstring("Đổi mật khẩu", "Nhập mật khẩu mới:", show='*')