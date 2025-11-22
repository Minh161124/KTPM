import tkinter as tk
from tkinter import font as tkFont
from tkinter import messagebox
from view.emp_view_list import EmployeeListPage
from controller.emp_contr import EmployeeController
from controller.cust_contr import CustomerController
from controller.cat_contr import CategoryController
from controller.prod_contr import ProductController
from controller.report_contr import ReportController
from controller.shift_contr import ShiftCreateController
from model.dashboard_model import get_dashboard_data

# try:
#     from quanlymay import MachineManagerPage
# except ImportError:
#     print("Warning: quanlymay missing")
#     class MachineManagerPage(tk.Frame):
#         def __init__(self, parent):
#             super().__init__(parent, bg="#2a2a2a")
#             tk.Label(self, text="Quản lý máy trạm (Placeholder)",
#                      fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)

# try:
#     import danhsachcatruc
# except ImportError:
#     print("Warning: danhsachcatruc missing")
#     class ShiftListPage(tk.Frame):
#         def __init__(self, parent):
#             super().__init__(parent, bg="#2a2a2a")
#             tk.Label(self, text="Danh sách ca trực (Placeholder)",
#                      fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)
#     class danhsachcatruc:
#         ShiftListPage = ShiftListPage

try:
    import view.emp_view_list as emp_view_list
except ImportError:
    print("Warning: EmployeeListPage missing")
    class EmployeeListPage(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg="#2a2a2a")
            tk.Label(self, text="Quản lý nhân viên (Placeholder)",
                     fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)
    class emp_view_list:
        EmployeeListPage = EmployeeListPage

try:
    import view.cust_view_list as cust_view_list
except ImportError:
    print("Warning: CustomerListPage missing")
    class CustomerListPage(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg="#2a2a2a")
            tk.Label(self, text="Quản lý khách hàng (Placeholder)",
                     fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)
    class cust_view_list:
        CustomerListPage = CustomerListPage

try:
    import view.cat_view_list as cat_view_list
except ImportError:
    print("Warning: CategoryListPage missing")
    class CategoryListPage(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg="#2a2a2a")
            tk.Label(self, text="Quản lý danh mục (Placeholder)",
                     fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)
    class cat_view_list:
        CategoryListPage = CategoryListPage

try:
    import view.cust_view_list as prod_view_list
except ImportError:
    print("Warning: ProductListPage missing")
    class ProductListPage(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg="#2a2a2a")
            tk.Label(self, text="Quản lý sản phẩm (Placeholder)",
                     fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)
    class prod_view_list:
        ProductListPage = ProductListPage

try:
    import view.report_view as report_view
except ImportError:
    print("Warning: ReportView missing")
    class ReportView(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg="#2a2a2a")
            tk.Label(self, text="Báo cáo, thống kê (Placeholder)",
                     fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)
    class report_view:
        ReportView = ReportView

try:
    import view.shift_view as shift_view
except ImportError:
    print("Warning: ToplevelAddItem missing")
    class ShiftCreateView(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg="#2a2a2a")
            tk.Label(self, text="Báo cáo, thống kê (Placeholder)",
                     fg="white", bg="#2a2a2a", font=("Arial", 20)).pack(pady=50)
    class shift_view:
        ShiftCreateView = ShiftCreateView

try:
    from model.dashboard_model import get_dashboard_data
except ImportError:
    print("Warning: database missing")
    def get_dashboard_data():
        return {"active": 32, "revenue": 3275350, "maintenance": 5}

COLOR_BG = "#0E0E0E"
COLOR_HEADER = "#2D2D2D"
COLOR_SIDEBAR = "#353535"
COLOR_SIDEBAR_HOVER = "#4A4A4A"
COLOR_TEXT = "#FFFFFF"
COLOR_TEXT_FADE = "#D0D0D0"
COLOR_BLUE_CARD = "#0B63CE"
COLOR_GREEN_CARD = "#0AA351"
COLOR_RED_CARD = "#E53935"

class App(tk.Tk):
    def __init__(self, user_role="nhanvien", user_email="User"):
        super().__init__()
        self.user_role = user_role
        self.user_email = user_email
        
        self.title(f"Quản lý - AI Game Center [{self.user_role.upper()}]")
        self.geometry("1200x700")
        self.configure(bg=COLOR_BG)

        self._setup_theme()
        self._setup_layout()
        self._setup_header()
        self._setup_sidebar()

        self.show_dashboard()

    def _setup_theme(self):
        self.font_header = tkFont.Font(size=16, weight="bold")
        self.font_menu = tkFont.Font(size=13)
        self.font_card_title = tkFont.Font(size=22, weight="bold")
        self.font_card_value = tkFont.Font(size=42, weight="bold")
        self.font_card_icon = tkFont.Font(size=40)

        all_menu_items = [
            ("Quản lý máy trạm", "🖥", ["admin", "nhanvien"]),
            ("Quản lý ca trực", "⏱️", ["admin", "nhanvien"]),
            ("Quản lý game", "🎮", ["admin"]),
            ("Quản lý nhân viên", "👥", ["admin"]),
            ("Quản lý sản phẩm", "📦", ["admin", "nhanvien"]),
            ("Quản lý khách hàng", "👤", ["admin", "nhanvien"]),
            ("Quản lý danh mục", "📋", ["admin"]),
            ("Quản lý thu chi", "💰", ["admin"]), 
            ("Báo cáo, thống kê", "📊", ["admin"]), 
            ("Cài đặt hệ thống", "⚙️", ["admin"]),
        ]

        self.sidebar_state = []
        for label, icon, allowed_roles in all_menu_items:
            if self.user_role in allowed_roles:
                self.sidebar_state.append((label, icon))

    def _setup_layout(self):
        self.header_frame = tk.Frame(self, bg=COLOR_HEADER, height=65)
        self.header_frame.pack(fill="x")

        self.sidebar_frame = tk.Frame(self, bg=COLOR_SIDEBAR, width=240)
        self.sidebar_frame.pack(side="left", fill="y")

        self.content_frame = tk.Frame(self, bg=COLOR_BG)
        self.content_frame.pack(side="right", fill="both", expand=True)

    def _setup_header(self):
        lbl_logo = tk.Label(self.header_frame, text="🕹  G Gaming",
                            fg="#FF8A00", bg=COLOR_HEADER,
                            font=("Arial", 20, "bold"))
        lbl_logo.pack(side="left", padx=25)

        nav = tk.Frame(self.header_frame, bg=COLOR_HEADER)
        nav.pack(side="left", padx=50)

        def nav_btn(text):
            return tk.Button(nav, text=text, fg="white", bg="#3A3A3A",
                             font=("Arial", 12), relief="flat",
                             padx=15, pady=5, activebackground="#4A4A4A")

        tk.Button(nav, text="🏠 Trang chủ", fg="white", bg="#3A3A3A",
          font=("Arial", 12), relief="flat",
          padx=15, pady=5, activebackground="#4A4A4A",
          command=self.show_dashboard).pack(side="left", padx=20)

        tk.Button(nav, text="📈 Doanh thu", fg="white", bg="#3A3A3A",
                font=("Arial", 12), relief="flat",
                padx=15, pady=5, activebackground="#4A4A4A",
                command=lambda: messagebox.showinfo("Thông báo", "Tính năng đang phát triển!")
                ).pack(side="left", padx=20)

        tk.Button(nav, text="❓ Hướng dẫn sử dụng", fg="white", bg="#3A3A3A",
                font=("Arial", 12), relief="flat",
                padx=15, pady=5, activebackground="#4A4A4A",
                command=lambda: messagebox.showinfo("Hướng dẫn", "Tính năng đang cập nhật!")
                ).pack(side="left", padx=20)

        user_frame = tk.Frame(self.header_frame, bg=COLOR_HEADER)
        user_frame.pack(side="right", padx=25)

        self.user_menu = tk.Menu(self, tearoff=0, bg="#2D2D2D", fg="white")
        self.user_menu.add_command(label="Đăng xuất", command=self._logout)

        def show_menu(event):
            try:
                self.user_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.user_menu.grab_release()

        lbl_user = tk.Label(
            user_frame,
            text="👤",  
            fg="white",
            bg=COLOR_HEADER,
            font=("Arial", 12, "bold"),
            cursor="hand2"
        )
        lbl_user.pack(anchor="e")
        lbl_user.bind("<Button-1>", show_menu)

        lbl_role = tk.Label(
            user_frame,
            text=f"{self.user_email} ({self.user_role})",
            fg="#CCCCCC", bg=COLOR_HEADER, font=("Arial", 11)
        )
        lbl_role.pack(anchor="e")

    def _logout(self):
        confirm = messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất không?")
        if confirm:
            self.destroy()
            # Import bên trong hàm để tránh circular import vòng lặp
            from controller.login_contr import LoginController
            app = LoginController()
            app.run()

    def _setup_sidebar(self):
         for w in self.sidebar_frame.winfo_children():
            w.destroy()

         for text, emoji in self.sidebar_state:
            frame = tk.Frame(self.sidebar_frame, bg=COLOR_SIDEBAR)
            frame.pack(fill="x", expand=True) 

            icon_lbl = tk.Label(frame, text=emoji, fg=COLOR_TEXT_FADE,
                     bg=COLOR_SIDEBAR, font=("Arial", 14))
            icon_lbl.pack(side="left", padx=15)

            label = tk.Label(frame, text=text, fg=COLOR_TEXT_FADE,
                             bg=COLOR_SIDEBAR, font=self.font_menu)
            label.pack(side="left")

            def on_enter(e, fr=frame, lb=label, ic=icon_lbl):
                fr.config(bg="#3F3F3F")
                lb.config(fg="white", bg="#3F3F3F")
                ic.config(fg="white", bg="#3F3F3F")

            def on_leave(e, fr=frame, lb=label, ic=icon_lbl):
                fr.config(bg=COLOR_SIDEBAR)
                lb.config(fg=COLOR_TEXT_FADE, bg=COLOR_SIDEBAR)
                ic.config(fg=COLOR_TEXT_FADE, bg=COLOR_SIDEBAR)

            frame.bind("<Enter>", on_enter)
            frame.bind("<Leave>", on_leave)
            label.bind("<Enter>", on_enter)
            label.bind("<Leave>", on_leave)
            icon_lbl.bind("<Enter>", on_enter)
            icon_lbl.bind("<Leave>", on_leave)

            frame.bind("<Button-1>", lambda e, t=text: self._menu_click(t))
            label.bind("<Button-1>", lambda e, t=text: self._menu_click(t))
            icon_lbl.bind("<Button-1>", lambda e, t=text: self._menu_click(t))

    def _menu_click(self, text):

        if text == "Quản lý nhân viên" and self.user_role != "admin":
             messagebox.showwarning("Cảnh báo", "Bạn không có quyền truy cập!")
             return

        if text == "Quản lý máy trạm":
            self.show_machine_manager()
        elif text == "Quản lý ca trực":
            self.show_shift()
        elif text == "":
            self.show_shift_list()
        elif text == "Quản lý nhân viên":
            self.show_emp_list()
        elif text == "Quản lý khách hàng":
            self.show_cust_list()
        elif text == "Quản lý sản phẩm":
            self.show_prod_list()
        elif text == "Quản lý danh mục":
            self.show_cat_list()
        elif text == "Báo cáo, thống kê":
            self.show_report()

    # def show_machine_manager(self):
    #     self._clear_content()
    #     page = MachineManagerPage(self.content_frame)
    #     page.pack(fill="both", expand=True)

    def show_shift(self):
        self._clear_content()
        self.shifts_controller = ShiftCreateController(self.content_frame)

    # def show_shift_list(self):
    #     self._clear_content()
    #     page = danhsachcatruc.ShiftListPage(self.content_frame)
    #     page.pack(fill="both", expand=True)

    def show_emp_list(self):
        self._clear_content()
        self.emp_controller = EmployeeController(self.content_frame)

    def show_cust_list(self):
        self._clear_content()
        self.cust_controller = CustomerController(self.content_frame)

    def show_prod_list(self):
        self._clear_content()
        self.prod_controller = ProductController(self.content_frame)

    def show_cat_list(self):
        self._clear_content()
        self.cat_controller = CategoryController(self.content_frame)

    def show_report(self):
        self._clear_content()
        self.report_controller = ReportController(self.content_frame)

    def _create_card(self, parent, color, title, value, emoji):
        card = tk.Frame(parent, bg=color, highlightbackground="white",
                        highlightthickness=4, bd=0)
        card.configure(width=450, height=200)
        card.grid_propagate(False)

        tk.Label(card, text=title, fg="white", bg=color,
                 font=self.font_card_title).place(relx=0.5, rely=0.18, anchor="center")

        tk.Label(card, text=value, fg="white", bg=color,
                 font=self.font_card_value).place(relx=0.35, rely=0.55, anchor="center")

        tk.Label(card, text=emoji, fg="white", bg=color,
                 font=self.font_card_icon).place(relx=0.75, rely=0.60, anchor="center")

        return card

    def show_dashboard(self):
        self._clear_content()

        data = get_dashboard_data()

        active = data.get("active") or data.get("dang_hoat_dong") or 0
        revenue = f"{(data.get('revenue') or data.get('doanh_thu') or 0):,} VNĐ"
        maintenance = data.get("maintenance") or data.get("bao_tri") or 0

        wrapper = tk.Frame(self.content_frame, bg=COLOR_BG)
        wrapper.pack(expand=True)

        row1 = tk.Frame(wrapper, bg=COLOR_BG)
        row1.pack(pady=40)

        self._create_card(row1, COLOR_BLUE_CARD,
                          "Máy đang hoạt động", str(active), "🖥").pack(side="left", padx=30)

        self._create_card(row1, COLOR_GREEN_CARD,
                          "Doanh thu hôm nay", revenue, "📈").pack(side="left", padx=30)

        row2 = tk.Frame(wrapper, bg=COLOR_BG)
        row2.pack()

        self._create_card(row2, COLOR_RED_CARD,
                          "Số máy bảo trì", str(maintenance), "🖥").pack(pady=20)

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()