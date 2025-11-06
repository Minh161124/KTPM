# page_list_games.py
from tkinter import Image
import customtkinter as ctk
import mysql.connector
from mysql.connector import Error
from PIL import Image
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class GameListPage:
    def __init__(self, root, switch_page):
        self.root = root
        self.switch_page = switch_page
        self.setup_ui()
        self.load_games()

    def get_db(self):
        try:
            return mysql.connector.connect(host='localhost', user='root', password='', database='qlnet')
        except Error as e:
            print("DB Error:", e)
            return None

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

        # Content
        content = ctk.CTkFrame(main)
        content.pack(side="right", fill="both", expand=True)
        ctk.CTkLabel(content, text="Trang chủ / Quản lý game / Danh sách game đã cài").pack(anchor="w", padx=20, pady=(10,5))

        top = ctk.CTkFrame(content)
        top.pack(fill="x", padx=20, pady=10)
        self.search = ctk.CTkEntry(top, placeholder_text="Tìm kiếm", width=300)
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda e: self.load_games())
        ctk.CTkButton(top, text="Cài thêm +", fg_color="#00c853", command=lambda: self.switch_page("install")).pack(side="right")

        self.games_frame = ctk.CTkScrollableFrame(content)
        self.games_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_games(self, term=""):
        for w in self.games_frame.winfo_children():
            w.destroy()
        conn = self.get_db()
        if not conn: return
        cur = conn.cursor(dictionary=True)
        sql = "SELECT * FROM game"
        if term := self.search.get():
            sql += " WHERE tenGame LIKE %s"
            cur.execute(sql, (f"%{term}%",))
        else:
            cur.execute(sql)
        games = cur.fetchall()
        cur.close()
        conn.close()

        for i, g in enumerate(games):
            card = ctk.CTkFrame(self.games_frame, width=160, height=240)
            card.grid(row=i//4, column=i%4, padx=10, pady=10)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=g['tenGame'], font=ctk.CTkFont(weight="bold")).pack()
            ctk.CTkLabel(card, text=f"Ver: {g['ver'] or 'N/A'}").pack()
            ctk.CTkLabel(card, text=f"Thể loại: {g['theLoai'] or 'N/A'}").pack()
            ctk.CTkLabel(card, text=f"Giá giờ: {g['giaGio'] or 0}VNĐ").pack()
            ctk.CTkLabel(card, text=f"Giá Combo: {g['giaCombo'] or 0}VNĐ").pack()

            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.pack(fill="x", pady=5)
