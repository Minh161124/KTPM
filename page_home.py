# page_home.py
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class HomePage:
    def __init__(self, root, switch_page):
        self.root = root
        self.switch_page = switch_page
        self.setup_ui()

    def setup_ui(self):
        # === HEADER ===
        header = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Logo
        try:
            logo_img = Image.open("logo.png").resize((40, 40), Image.Resampling.LANCZOS)
            ctk.CTkLabel(header, image=ctk.CTkImage(logo_img, size=(40,40)), text="").pack(side="left", padx=15)
        except:
            pass

        # Header Buttons – Trang chủ chỉ mục "home"
        header_buttons = ["Trang chủ", "Doanh thu", "Hướng dẫn sử dụng"]
        for idx, text in enumerate(header_buttons):
            if text == "Trang chủ":
                command = lambda: self.switch_page("home")
            else:
                command = lambda t=text: print(f"Header: {t} clicked")

            btn = ctk.CTkButton(
                header, text=text, fg_color="transparent", hover_color="#333",
                command=command
            )
            btn.pack(side="left", padx=10)
            btn.id = f"header_btn_{idx}"

        # User info
        user = ctk.CTkFrame(header, fg_color="transparent")
        user.pack(side="right", padx=15)
        ctk.CTkLabel(user, text="Nguyễn Khánh Ngân", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ctk.CTkLabel(user, text="Nhân viên ", text_color="#aaa", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=(0, 10))

        # === MAIN ===
        main = ctk.CTkFrame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Sidebar
        sidebar = ctk.CTkFrame(main, width=200, corner_radius=10)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        # === MENU "QUẢN LÝ GAME" ===
        submenu = ctk.CTkFrame(sidebar, fg_color="#2b2b2b")
        submenu_visible = False

        def toggle_submenu():
            nonlocal submenu_visible
            if submenu_visible:
                submenu.pack_forget()
                submenu_visible = False
            else:
                submenu.pack(fill="x", pady=(0, 2), padx=5)
                submenu_visible = True

        # Nút cha
        btn_game = ctk.CTkButton(
            sidebar, text="  Quản lý game", fg_color="transparent", hover_color="#444",
            anchor="w", height=40, command=toggle_submenu
        )
        btn_game.pack(fill="x", pady=2, padx=5)
        btn_game.id = "sidebar_btn_game"

        # Menu con
        ctk.CTkButton(
            submenu, text="    Danh sách game đã cài", fg_color="transparent", hover_color="#555",
            anchor="w", height=35,
            command=lambda: [self.switch_page("list"), toggle_submenu()]
        ).pack(fill="x", pady=1)

        ctk.CTkButton(
            submenu, text="    Cài game", fg_color="transparent", hover_color="#555",
            anchor="w", height=35,
            command=lambda: [self.switch_page("install"), toggle_submenu()]
        ).pack(fill="x", pady=1)

        # Các nút khác
        items = [
            "Quản lý máy trạm", "Quản lý ca trực", "Quản lý nhân viên",
            "Quản lý sản phẩm", "Quản lý khách hàng", "Quản lý danh mục",
            "Quản lý thu chi", "Báo cáo, thống kê", "Cài đặt hệ thống"
        ]
        for idx, item in enumerate(items):
            btn = ctk.CTkButton(
                sidebar, text=f"  {item}", fg_color="transparent", hover_color="#333",
                anchor="w", height=40,
                command=lambda i=item: print(f"Sidebar: {i}")
            )
            btn.pack(fill="x", pady=2, padx=5)
            btn.id = f"sidebar_btn_{idx}"

        # === CONTENT TRANG CHỦ ===
        content = ctk.CTkFrame(main)
        content.pack(side="right", fill="both", expand=True)
        ctk.CTkLabel(content, text="Chào mừng đến G Gaming!", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=50)
        ctk.CTkLabel(content, text="Chọn chức năng từ menu bên trái", font=ctk.CTkFont(size=16)).pack(pady=10)