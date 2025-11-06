# page_install_game.py
from email import header
import customtkinter as ctk
from PIL import Image
import mysql.connector

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class GameInstallPage:
    def __init__(self, root, switch_page):
        self.root = root
        self.switch_page = switch_page
        self.selected_machines = []
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

        # Breadcrumb – SỬA VỊ TRÍ
        ctk.CTkLabel(main, text="Trang chủ / Quản lý game / Cài game").pack(anchor="w", padx=20, pady=(10,5))

        # Content
        content = ctk.CTkFrame(main)
        content.pack(side="right", fill="both", expand=True)

        # Form cài đặt
        form = ctk.CTkFrame(content, fg_color="#2b2b2b", corner_radius=10)
        form.pack(pady=20, padx=50, fill="both", expand=True)

        # Icon + Tiêu đề
        top = ctk.CTkFrame(form, fg_color="transparent")
        top.pack(pady=15, fill="x")
        try:
            img = Image.open("z_icon.png").resize((60,60), Image.Resampling.LANCZOS)
            ctk.CTkLabel(top, image=ctk.CTkImage(img, size=(60,60)), text="").pack(side="left", padx=10)
        except:
            ctk.CTkLabel(top, text="Game", font=ctk.CTkFont(size=40)).pack(side="left", padx=10)
        ctk.CTkLabel(top, text="Cài đặt game", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        # Chọn máy
        ctk.CTkLabel(form, text="Chọn máy cài:", anchor="w").pack(pady=(10,5), padx=20, anchor="w")
        machine_frame = ctk.CTkFrame(form)
        machine_frame.pack(fill="x", padx=20, pady=5)

        def add_tag(name):
            tag = ctk.CTkFrame(machine_frame, fg_color="#444", corner_radius=15, height=25)
            tag.pack(side="left", padx=2)
            tag.pack_propagate(False)
            ctk.CTkLabel(tag, text=name, font=ctk.CTkFont(size=10)).pack(side="left", padx=8)
            ctk.CTkButton(tag, text="×", width=20, fg_color="transparent",
                          command=lambda: [tag.destroy(), self.selected_machines.remove(name)]).pack(side="right")

        def select_machines():
            dialog = ctk.CTkInputDialog(text="Nhập số máy (cách nhau bởi dấu phẩy):", title="Chọn máy")
            nums = dialog.get_input()
            if nums:
                for n in nums.split(","):
                    name = f"Máy {n.strip()}"
                    if name not in self.selected_machines:
                        self.selected_machines.append(name)
                        add_tag(name)

        ctk.CTkComboBox(machine_frame, values=["Chọn máy"], state="readonly", command=lambda x: select_machines()).pack(side="left")

        # Version
        ctk.CTkLabel(form, text="Version:", anchor="w").pack(pady=(15,5), padx=20, anchor="w")
        self.version_combo = ctk.CTkComboBox(form, values=["Ver 3.3.3025", "Ver 3.2.1001", "Ver 3.1.500"], state="readonly")
        self.version_combo.pack(fill="x", padx=20, pady=5)
        self.version_combo.set("Ver 3.3.3025")

        # Nút Cài đặt
        ctk.CTkButton(form, text="Cài đặt", fg_color="#f44336", hover_color="#d32f2f", height=35,
                      command=self.install_game).pack(pady=30)

    def install_game(self):
        if not self.selected_machines:
            ctk.CTkMessageBox(title="Lỗi", message="Chưa chọn máy!", icon="cancel")
            return

        try:
            conn = mysql.connector.connect(host='localhost', user='root', password='', database='qlnet')
            cur = conn.cursor()
            cur.execute("UPDATE game SET machines_installed = machines_installed + %s WHERE tenGame = %s",
                        (len(self.selected_machines), "Z.Z"))
            conn.commit()
            cur.close()
            conn.close()

            popup = ctk.CTkToplevel(self.root)
            popup.geometry("300x150")
            popup.title("")
            frame = ctk.CTkFrame(popup, fg_color="#333")
            frame.pack(pady=20, padx=20, fill="both", expand=True)
            ctk.CTkLabel(frame, text="Thông báo").pack(pady=5)
            ctk.CTkLabel(frame, text="Cài đặt thành công", text_color="#4caf50").pack(pady=5)
            ctk.CTkButton(frame, text="Xong", command=lambda: [popup.destroy(), self.switch_page("list")]).pack(pady=10)
        except Exception as e:
            ctk.CTkMessageBox(title="Lỗi", message=f"Cài đặt thất bại: {e}", icon="cancel")