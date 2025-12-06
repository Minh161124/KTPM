import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
from datetime import datetime
import threading
import os
from PIL import Image, ImageTk  # Cần thư viện: pip install pillow
import database as db

# ---------- Floating Chat Button ----------
class FloatingChatButton(tk.Canvas):
    """Nút tròn nổi góc phải, mở chat AI khi click."""
    def __init__(self, parent, command=None, size=60, margin_x=30, margin_y=160):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bg=parent['bg'])
        
        self.command = command

        # Vẽ nút tròn
        pad = 4
        self.circle = self.create_oval(
            pad, pad, size - pad, size - pad,
            fill=COLOR_ACCENT, outline=""
        )
        self.text = self.create_text(
            size // 2, size // 2,
            text="🤖", font=("Segoe UI", int(size * 0.45))
        )

        # Sự kiện
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Enter>", lambda e: self.itemconfigure(self.circle, fill=COLOR_ACCENT_HOVER))
        self.bind("<Leave>", lambda e: self.itemconfigure(self.circle, fill=COLOR_ACCENT))

        # Đặt nút tròn ở góc phải dưới
        self.place(relx=1.0, rely=1.0, x=-margin_x, y=-margin_y, anchor="se")

    def _on_click(self):
        try:
            if callable(self.command):
                self.command()
        except Exception:
            pass

# =========================================================================
# --- [MỚI - ĐÃ CẬP NHẬT DB] CLASS: AI CHATBOT ---
# =========================================================================
class AIChatWindow(tk.Toplevel):
    """Cửa sổ Chat AI bong bóng, kết nối Database"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Trợ lý G-Bot")
        self.geometry("380x550")
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"+{screen_w - 420}+{screen_h - 650}")
        
        self.configure(bg="#1e1e2e") 
        self.attributes('-topmost', True)
        self.resizable(False, False)

        # Header
        header = tk.Frame(self, bg="#7c3aed", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🤖", font=("Segoe UI", 24), bg="#7c3aed").pack(side="left", padx=(15, 5))
        lbl_title = tk.Label(header, text="Hỗ trợ khách hàng", fg="white", bg="#7c3aed", font=("Segoe UI", 13, "bold"))
        lbl_title.pack(side="left", pady=10)
        
        tk.Button(header, text="✕", bg="#7c3aed", fg="white", bd=0, font=("Arial", 12), 
                  command=self.destroy, activebackground="#6d28d9").pack(side="right", padx=10)

        # Khu vực chat
        self.chat_area = tk.Text(self, bg="#1e1e2e", fg="white", font=("Segoe UI", 10), 
                                 bd=0, highlightthickness=0, wrap="word", state="disabled")
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.chat_area.tag_config("user", justify="right", rmargin=10, lmargin1=80, lmargin2=80, 
                                  background="#3f3f46", foreground="white", spacing1=5, spacing3=5)
        self.chat_area.tag_config("ai", justify="left", lmargin1=10, lmargin2=10, rmargin=80, 
                                  background="#5b21b6", foreground="white", spacing1=5, spacing3=5)

        # Input
        input_frame = tk.Frame(self, bg="#27273a", pady=10)
        input_frame.pack(fill="x")
        
        self.entry_msg = tk.Entry(input_frame, bg="#3f3f46", fg="white", font=("Segoe UI", 11), 
                                  relief="flat", insertbackground="white")
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=10, ipady=6)
        self.entry_msg.bind("<Return>", self._send_message)
        
        btn_send = tk.Button(input_frame, text="GỬI", bg="#7c3aed", fg="white", font=("Arial", 9, "bold"),
                             relief="flat", bd=0, command=self._send_message)
        btn_send.pack(side="right", padx=10)

        self._add_bubble("Xin chào! Em là G-Bot AI. Anh/Chị cần giúp gì ạ? (Menu, Nạp tiền, Giờ chơi...)", "ai")

    def _add_bubble(self, text, sender):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, "\n")
        self.chat_area.insert(tk.END, f" {text} \n", sender)
        self.chat_area.see(tk.END)
        self.chat_area.config(state="disabled")

    def _send_message(self, event=None):
        msg = self.entry_msg.get().strip()
        if not msg: return
        
        self._add_bubble(msg, "user")
        self.entry_msg.delete(0, tk.END)
        
        # Gọi hàm xử lý (có kết nối DB)
        self.after(500, lambda: self._process_ai_response(msg))

    def _process_ai_response(self, msg):
        """Logic trả lời: KẾT NỐI DATABASE"""
        
        # Chạy trong luồng riêng để không bị đơ giao diện khi query SQL
        def get_answer_thread():
            try:
                # Gọi hàm tìm kiếm trong database.py (Bạn nhớ thêm hàm này vào file database nhé!)
                response = db.get_ai_response_from_db(msg)
            except AttributeError:
                # Phòng trường hợp bạn quên update file database.py
                response = "Lỗi: Bạn chưa cập nhật file database.py!"
            except Exception as e:
                response = "Lỗi hệ thống Bot."

            # Cập nhật giao diện từ luồng chính
            self.after(0, lambda: self._add_bubble(response, "ai"))

        threading.Thread(target=get_answer_thread, daemon=True).start()


# --- CẤU HÌNH ---
THIS_MACHINE_NAME = "MAY01"
PRICE_PER_HOUR = 8000
PRICE_PER_SECOND = PRICE_PER_HOUR / 3600

# --- THEME: SUPER CLEAN (NAVY & CYAN) ---
COLOR_BG = "#0f172a"        # Nền chính
COLOR_PANEL = "#1e293b"     # Nền khối
COLOR_ACCENT = "#06b6d4"    # Cyan
COLOR_ACCENT_HOVER = "#0891b2"
COLOR_TEXT_MAIN = "#f1f5f9" 
COLOR_TEXT_DIM = "#94a3b8"  
COLOR_INPUT_BG = "#334155"  
COLOR_DANGER = "#ef4444"
COLOR_SUCCESS = "#22c55e"   # Màu xanh lá

FONT_LOGO = ("Impact", 28)
FONT_H1 = ("Segoe UI", 16, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)

class ClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Client - {THIS_MACHINE_NAME}")
        
        # FULLSCREEN LOCK
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.configure(bg="#000000")
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.current_user = None
        self.balance = 0
        self.is_logged_in = False
        self.img_cache = {} 
        self.current_filter = "all"

        self.container = tk.Frame(self, bg="#000000")
        self.container.pack(fill="both", expand=True)

        try: db.update_machine_status(THIS_MACHINE_NAME, "off")
        except: pass

        self.show_login_screen()
        
        # Nút chat-bot nổi
        try:
            self.chatbot_btn = FloatingChatButton(self, command=self.open_ai_chat)
        except Exception:
            pass

        # Kích hoạt vòng lặp kiểm tra cài đặt từ Admin
        self.check_install_loop()

    # =========================================================================
    # --- [MỚI] HÀM MỞ CHAT AI ---
    # =========================================================================
    def open_ai_chat(self):
        """Mở giao diện AI Chatbot"""
        if hasattr(self, 'ai_win') and self.ai_win.winfo_exists():
            self.ai_win.lift()
            return
        self.ai_win = AIChatWindow(self)

    # =========================================================================
    # --- 1. MÀN HÌNH KHÓA (GIAO DIỆN CŨ) ---
    # =========================================================================
    def show_login_screen(self):
        for w in self.container.winfo_children(): w.destroy()
        
        bg = tk.Frame(self.container, bg=COLOR_BG)
        bg.pack(fill="both", expand=True)

        # Cột Trái (Branding)
        left_col = tk.Frame(bg, bg=COLOR_BG, width=600)
        left_col.pack(side="left", fill="both", expand=True)
        
        center_brand = tk.Frame(left_col, bg=COLOR_BG)
        center_brand.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(center_brand, text="WELCOME TO", fg=COLOR_ACCENT, bg=COLOR_BG, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(center_brand, text="G-GAMING", fg="white", bg=COLOR_BG, font=("Impact", 60)).pack(anchor="w")
        tk.Label(center_brand, text="CENTER", fg="white", bg=COLOR_BG, font=("Impact", 60)).pack(anchor="w")
        tk.Label(center_brand, text="The Ultimate Esports Experience", fg=COLOR_TEXT_DIM, bg=COLOR_BG, font=("Segoe UI", 12)).pack(anchor="w", pady=10)

        # Cột Phải (Form)
        right_col = tk.Frame(bg, bg=COLOR_PANEL, width=500)
        right_col.pack(side="right", fill="y")
        right_col.pack_propagate(False)

        header_right = tk.Frame(right_col, bg=COLOR_PANEL)
        header_right.pack(anchor="ne", padx=20, pady=20)
        tk.Label(header_right, text=THIS_MACHINE_NAME, fg=COLOR_ACCENT, bg=COLOR_PANEL, font=("Segoe UI", 12, "bold")).pack()
        
        form = tk.Frame(right_col, bg=COLOR_PANEL)
        form.place(relx=0.5, rely=0.5, anchor="center", width=350)

        tk.Label(form, text="MEMBER LOGIN", fg="white", bg=COLOR_PANEL, font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(0, 30))

        def create_modern_entry(parent, label_text, show_char=None):
            tk.Label(parent, text=label_text, fg=COLOR_TEXT_DIM, bg=COLOR_PANEL, font=FONT_SMALL).pack(anchor="w", pady=(10, 0))
            ent = tk.Entry(parent, font=("Segoe UI", 12), bg=COLOR_INPUT_BG, fg="white", 
                           relief="flat", insertbackground="white", show=show_char)
            ent.pack(fill="x", ipady=8, pady=(5, 0))
            tk.Frame(parent, bg=COLOR_ACCENT, height=2).pack(fill="x")
            return ent

        self.entry_user = create_modern_entry(form, "USERNAME")
        self.entry_pass = create_modern_entry(form, "PASSWORD", "*")

        btn_login = tk.Button(form, text="LOGIN", bg=COLOR_ACCENT, fg="#0f172a", font=("Segoe UI", 11, "bold"),
                              relief="flat", cursor="hand2", pady=10, command=self.login, activebackground="white")
        btn_login.pack(fill="x", pady=30)

        footer = tk.Frame(right_col, bg=COLOR_PANEL)
        footer.pack(side="bottom", fill="x", pady=20)
        
        tk.Button(footer, text="Guest Mode", bg=COLOR_PANEL, fg=COLOR_TEXT_DIM, bd=0, cursor="hand2", 
                  font=FONT_SMALL, command=self.quick_test_login).pack(side="left", padx=20)
        tk.Button(footer, text="Shut Down", bg=COLOR_PANEL, fg=COLOR_DANGER, bd=0, cursor="hand2", 
                  font=FONT_SMALL, command=self.shutdown_pc).pack(side="right", padx=20)

    # =========================================================================
    # --- 2. DASHBOARD & DANH SÁCH GAME (GIAO DIỆN CŨ) ---
    # =========================================================================
    def show_launcher_interface(self):
        self.attributes('-fullscreen', False)
        self.state('zoomed')
        self.attributes('-topmost', False)
        for w in self.container.winfo_children(): w.destroy()
        self.container.configure(bg=COLOR_BG)

        # Sidebar
        sidebar = tk.Frame(self.container, bg=COLOR_PANEL, width=260)
        sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        
        logo_box = tk.Frame(sidebar, bg=COLOR_PANEL, height=100)
        logo_box.pack(fill="x")
        tk.Label(logo_box, text="G", fg=COLOR_ACCENT, bg=COLOR_PANEL, font=("Impact", 32)).place(x=20, y=25)
        tk.Label(logo_box, text="GAMING", fg="white", bg=COLOR_PANEL, font=("Impact", 24)).place(x=55, y=32)
        
        # Menu Items
        self.nav_items = {}
        menus = [("Trang chủ", "🏠"), ("Trò chơi", "🎮"), ("Ứng dụng", "💠"), ("Dịch vụ", "🍔"), ("Tin nhắn", "💬")]
        
        for txt, icon in menus:
            btn_frame = tk.Frame(sidebar, bg=COLOR_PANEL, cursor="hand2")
            btn_frame.pack(fill="x", pady=2)
            
            indicator = tk.Frame(btn_frame, bg=COLOR_PANEL, width=4)
            indicator.pack(side="left", fill="y")
            
            lbl = tk.Label(btn_frame, text=f"  {icon}   {txt}", fg=COLOR_TEXT_DIM, bg=COLOR_PANEL, font=FONT_H2, anchor="w", padx=20, pady=12)
            lbl.pack(side="left", fill="x", expand=True)
            
            for w in [btn_frame, lbl]:
                w.bind("<Enter>", lambda e, f=btn_frame, i=indicator, l=lbl: self._hover_nav(f, i, l, True))
                w.bind("<Leave>", lambda e, f=btn_frame, i=indicator, l=lbl: self._hover_nav(f, i, l, False))
                
                if txt == "Trang chủ": w.bind("<Button-1>", lambda e: self.load_content("all"))
                elif txt == "Trò chơi": w.bind("<Button-1>", lambda e: self.load_content("game"))
                elif txt == "Ứng dụng": w.bind("<Button-1>", lambda e: self.load_content("app"))
                elif txt == "Dịch vụ": w.bind("<Button-1>", lambda e: self.open_food_menu())
                elif txt == "Tin nhắn": w.bind("<Button-1>", lambda e: self.chat_admin()) # Menu vẫn giữ chat admin cũ nếu muốn

        # User Profile
        user_area = tk.Frame(sidebar, bg="#161e2e", height=90)
        user_area.pack(side="bottom", fill="x")
        user_area.pack_propagate(False)
        
        tk.Label(user_area, text=str(self.current_user)[0].upper(), font=("Arial", 16, "bold"), 
                 bg=COLOR_ACCENT, fg="#0f172a", width=3).place(x=20, y=25)
        tk.Label(user_area, text=str(self.current_user), fg="white", bg="#161e2e", font=("Segoe UI", 10, "bold")).place(x=70, y=25)
        tk.Button(user_area, text="Đăng xuất", fg=COLOR_DANGER, bg="#161e2e", bd=0, font=("Segoe UI", 8), 
                  cursor="hand2", command=self.logout).place(x=68, y=48)

        # --- MAIN CONTENT ---
        self.content_area = tk.Frame(self.container, bg=COLOR_BG)
        self.content_area.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        top_bar = tk.Frame(self.content_area, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 30))

        self.lbl_clock = tk.Label(top_bar, text="", fg="white", bg=COLOR_BG, font=("Segoe UI", 24, "bold"))
        self.lbl_clock.pack(side="left")
        self._update_clock()

        bal_card = tk.Frame(top_bar, bg=COLOR_PANEL, padx=25, pady=10)
        bal_card.pack(side="right")
        tk.Label(bal_card, text="SỐ DƯ TÀI KHOẢN", fg=COLOR_TEXT_DIM, bg=COLOR_PANEL, font=("Segoe UI", 8, "bold")).pack(anchor="e")
        self.lbl_balance_display = tk.Label(bal_card, text="0 đ", fg=COLOR_ACCENT, bg=COLOR_PANEL, font=("Segoe UI", 20, "bold"))
        self.lbl_balance_display.pack(anchor="e")
        self.lbl_time_remain = tk.Label(bal_card, text="--:--", fg="white", bg=COLOR_PANEL, font=FONT_SMALL)
        self.lbl_time_remain.pack(anchor="e")

        # Grid Frame
        self.canvas = tk.Canvas(self.content_area, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.content_area, orient="vertical", command=self.canvas.yview)
        self.grid_frame = tk.Frame(self.canvas, bg=COLOR_BG)
        
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.is_logged_in = True
        self.monitor_session()
        self.load_content("all")

    def _hover_nav(self, frame, indicator, label, hover):
        if hover:
            frame.config(bg="#283547"); indicator.config(bg=COLOR_ACCENT); label.config(bg="#283547", fg="white")
        else:
            frame.config(bg=COLOR_PANEL); indicator.config(bg=COLOR_PANEL); label.config(bg=COLOR_PANEL, fg=COLOR_TEXT_DIM)

    # --- HÀM LOAD GAME TỪ DB ---
    def load_content(self, filter_type):
        self.current_filter = filter_type
        for w in self.grid_frame.winfo_children(): w.destroy()
        try: items = db.get_all_games()
        except: items = []

        filtered = []
        for item in items:
            cat = item.get('category', '').lower()
            is_app = any(x in cat for x in ['app', 'tool', 'web', 'office', 'browser'])
            if filter_type == 'game' and is_app: continue
            if filter_type == 'app' and not is_app: continue
            filtered.append(item)

        if not filtered:
            tk.Label(self.grid_frame, text="(Chưa có dữ liệu)", fg="gray", bg=COLOR_BG, font=("Arial", 12)).pack(pady=20)
            return

        r, c = 0, 0
        for item in filtered:
            self._create_card(item, r, c)
            c += 1
            if c > 4: c = 0; r += 1

    def _create_card(self, item, r, c):
        card = tk.Frame(self.grid_frame, bg=COLOR_PANEL, width=200, height=220, cursor="hand2")
        card.grid(row=r, column=c, padx=10, pady=10)
        card.pack_propagate(False)

        img_frame = tk.Frame(card, bg="#000", height=160)
        img_frame.pack(fill="x", side="top")
        img_lbl = tk.Label(img_frame, bg="#000", text=item['name'][:2], fg="gray", font=("Arial", 30))
        img_lbl.place(relx=0.5, rely=0.5, anchor="center")

        img_path = item.get('image', '')
        if img_path and os.path.exists(img_path):
            try:
                if img_path not in self.img_cache:
                    pil = Image.open(img_path).resize((200, 160))
                    self.img_cache[img_path] = ImageTk.PhotoImage(pil)
                img_lbl.config(image=self.img_cache[img_path], text="")
            except: pass

        info = tk.Frame(card, bg=COLOR_PANEL)
        info.pack(fill="both", expand=True, padx=15)
        lbl_name = tk.Label(info, text=item['name'], bg=COLOR_PANEL, fg="white", font=("Segoe UI", 11, "bold"))
        lbl_name.pack(fill="x", pady=(15, 2))
        lbl_act = tk.Label(info, text="Chơi ngay →", bg=COLOR_PANEL, fg=COLOR_TEXT_DIM, font=("Segoe UI", 9))
        lbl_act.pack(anchor="w")

        def enter(e): 
            card.config(bg=COLOR_ACCENT); info.config(bg=COLOR_ACCENT)
            lbl_name.config(bg=COLOR_ACCENT, fg="#0f172a"); lbl_act.config(bg=COLOR_ACCENT, fg="#0f172a")
        def leave(e): 
            card.config(bg=COLOR_PANEL); info.config(bg=COLOR_PANEL)
            lbl_name.config(bg=COLOR_PANEL, fg="white"); lbl_act.config(bg=COLOR_PANEL, fg=COLOR_TEXT_DIM)

        for w in [card, img_frame, img_lbl, info, lbl_name, lbl_act]:
            w.bind("<Enter>", enter); w.bind("<Leave>", leave)
            w.bind("<Button-1>", lambda e, i=item: self.launch_program(i))

    def launch_program(self, item):
        path = item.get('path', '')
        if not path: messagebox.showerror("Lỗi", "Chưa cài đặt đường dẫn!"); return
        if messagebox.askyesno("Launch", f"Mở {item['name']}?"):
            try: os.startfile(path)
            except: messagebox.showinfo("Info", f"Giả lập chạy: {path}")

    # =========================================================================
    # --- HỆ THỐNG GỌI MÓN (PRO + AUTO CLOSE) ---
    # =========================================================================
    def open_food_menu(self):
        self.cart_data = {} 
        self.current_cart_total = 0
        
        self.food_win = tk.Toplevel(self)
        self.food_win.title("MENU DỊCH VỤ")
        self.food_win.geometry("1000x650")
        self.food_win.configure(bg=COLOR_BG)
        self.food_win.attributes('-topmost', True)

        paned = tk.PanedWindow(self.food_win, orient=tk.HORIZONTAL, bg=COLOR_BG, sashwidth=4)
        paned.pack(fill="both", expand=True)

        # LEFT: MENU
        left_frame = tk.Frame(paned, bg=COLOR_BG)
        paned.add(left_frame)
        tk.Label(left_frame, text="DANH SÁCH ĐỒ ĂN & NƯỚC UỐNG", fg=COLOR_ACCENT, bg=COLOR_BG, font=FONT_H1).pack(pady=15)

        canvas = tk.Canvas(left_frame, bg=COLOR_BG, highlightthickness=0)
        sb = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        self.menu_grid = tk.Frame(canvas, bg=COLOR_BG)
        
        self.menu_grid.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.menu_grid, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        sb.pack(side="right", fill="y")

        # RIGHT: CART
        right_frame = tk.Frame(paned, bg=COLOR_PANEL, width=300)
        paned.add(right_frame)
        tk.Label(right_frame, text="GIỎ HÀNG CỦA BẠN", fg="white", bg=COLOR_PANEL, font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        self.cart_list_frame = tk.Frame(right_frame, bg=COLOR_PANEL)
        self.cart_list_frame.pack(fill="both", expand=True, padx=10)

        footer = tk.Frame(right_frame, bg="#161e2e", height=100)
        footer.pack(side="bottom", fill="x")
        
        self.lbl_total_price = tk.Label(footer, text="Tổng tiền: 0 đ", fg=COLOR_ACCENT, bg="#161e2e", font=("Arial", 16, "bold"))
        self.lbl_total_price.pack(pady=10)
        
        btn_order = tk.Button(footer, text="GỬI ĐƠN HÀNG ➤", bg=COLOR_SUCCESS, fg="white", font=("Arial", 12, "bold"),
                              command=self._submit_order)
        btn_order.pack(pady=10, ipadx=20, ipady=5)

        self._load_menu_items()

    def _load_menu_items(self):
        for w in self.menu_grid.winfo_children(): w.destroy()
        try: items = db.get_all_products()
        except: items = []

        r, c = 0, 0
        for item in items:
            if item['stock'] <= 0: continue 
            card = tk.Frame(self.menu_grid, bg=COLOR_PANEL, width=200, height=240)
            card.grid(row=r, column=c, padx=10, pady=10); card.pack_propagate(False)

            tk.Label(card, text="🍔" if "Đồ ăn" in item['category'] else "🥤", bg="#111", fg="gray", font=("Arial", 40)).place(x=0, y=0, width=200, height=120)
            tk.Label(card, text=item['name'], fg="white", bg=COLOR_PANEL, font=("Segoe UI", 11, "bold"), wraplength=180).place(x=10, y=130)
            tk.Label(card, text=f"{int(item['price_out']):,} đ", fg=COLOR_ACCENT, bg=COLOR_PANEL, font=("Arial", 12, "bold")).place(x=10, y=170)
            
            tk.Button(card, text="+ THÊM", bg=COLOR_ACCENT, fg="#0f172a", font=("Arial", 10, "bold"),
                      command=lambda i=item: self._add_to_cart(i)).place(x=10, y=200, width=180)

            c += 1
            if c > 2: c = 0; r += 1 

    def _add_to_cart(self, item):
        code = item['code']
        if code in self.cart_data: self.cart_data[code]['qty'] += 1
        else: self.cart_data[code] = {'name': item['name'], 'price': item['price_out'], 'qty': 1}
        self._update_cart_ui()

    def _update_cart_ui(self):
        for w in self.cart_list_frame.winfo_children(): w.destroy()
        total = 0
        for code, data in self.cart_data.items():
            subtotal = data['price'] * data['qty']; total += subtotal
            row = tk.Frame(self.cart_list_frame, bg=COLOR_PANEL, pady=5); row.pack(fill="x", pady=2)
            tk.Label(row, text=data['name'], fg="white", bg=COLOR_PANEL, width=15, anchor="w").pack(side="left")
            tk.Button(row, text="-", bg="#444", fg="white", width=2, bd=0, command=lambda c=code: self._change_qty(c, -1)).pack(side="left", padx=2)
            tk.Label(row, text=str(data['qty']), fg=COLOR_ACCENT, bg=COLOR_PANEL, width=3).pack(side="left")
            tk.Button(row, text="+", bg="#444", fg="white", width=2, bd=0, command=lambda c=code: self._change_qty(c, 1)).pack(side="left", padx=2)
            tk.Label(row, text=f"{int(subtotal):,}đ", fg="white", bg=COLOR_PANEL, anchor="e").pack(side="right", padx=5)
        self.lbl_total_price.config(text=f"Tổng: {int(total):,} đ")
        self.current_cart_total = total

    def _change_qty(self, code, delta):
        if code in self.cart_data:
            self.cart_data[code]['qty'] += delta
            if self.cart_data[code]['qty'] <= 0: del self.cart_data[code]
            self._update_cart_ui()

    def _submit_order(self):
        # Gửi đơn hàng ngay khi bấm, không yêu cầu xác nhận thành công từ DB
        if not self.cart_data:
            messagebox.showwarning("Giỏ hàng trống", "Bạn chưa chọn món nào!")
            return

        # Chuẩn bị mô tả đơn hàng
        details = []
        for code, data in self.cart_data.items():
            details.append(f"{data['name']} (x{data['qty']})")

        full_desc = f"[{THIS_MACHINE_NAME}] Gọi món: {', '.join(details)}"

        # Gọi DB bất đồng bộ (nếu có) nhưng không chặn UI và không hiển thị lỗi nếu thất bại
        def send_bg():
            try:
                db.add_transaction_db("thu", "Dịch vụ", self.current_cart_total, full_desc)
            except:
                pass

        try:
            threading.Thread(target=send_bg, daemon=True).start()
        except:
            # Nếu không thể tạo thread thì vẫn cố gắng gọi thủ công (không báo lỗi)
            try:
                db.add_transaction_db("thu", "Dịch vụ", self.current_cart_total, full_desc)
            except:
                pass

        # Đóng cửa sổ gọi món ngay lập tức và refresh giao diện chính
        try:
            if hasattr(self, 'food_win') and self.food_win.winfo_exists():
                self.food_win.destroy()
        except: pass

        try:
            self.after(100, lambda: self.load_content(self.current_filter))
        except: pass

        # Cập nhật hiển thị số dư (nếu cần)
        try:
            self.lbl_balance_display.config(text=f"{self.balance:,.0f} đ")
        except: pass

    # =========================================================================
    # --- INSTALLER SYSTEM ---
    # =========================================================================
    def check_install_loop(self):
        try:
            tasks = db.get_install_tasks(THIS_MACHINE_NAME)
            for task in tasks: self.start_download_game(task)
        except: pass
        self.after(5000, self.check_install_loop)

    def start_download_game(self, task):
        game_name = task['game_name']; task_id = task['id']
        db.update_install_progress(task_id, 'installing', 0)
        dl_win = tk.Toplevel(self); dl_win.geometry("300x120+50+50"); dl_win.configure(bg=COLOR_PANEL)
        dl_win.overrideredirect(True); dl_win.attributes('-topmost', True)
        tk.Label(dl_win, text=f"Đang cài đặt: {game_name}", fg=COLOR_ACCENT, bg=COLOR_PANEL, font=FONT_H2).pack(pady=10)
        pb = ttk.Progressbar(dl_win, length=250, mode='determinate'); pb.pack()
        lbl = tk.Label(dl_win, text="0%", fg="white", bg=COLOR_PANEL); lbl.pack()

        def run():
            for i in range(101):
                if not dl_win.winfo_exists(): break
                time.sleep(0.04); pb['value'] = i; lbl.config(text=f"{i}%")
                if i % 10 == 0: db.update_install_progress(task_id, 'installing', i)
            db.update_install_progress(task_id, 'completed', 100); dl_win.destroy()
            self.after(0, lambda: self._finish_install_ui(game_name))

        threading.Thread(target=run, daemon=True).start()

    def _finish_install_ui(self, game_name):
        messagebox.showinfo("Cài đặt hoàn tất", f"Game '{game_name}' đã sẵn sàng!", parent=self)
        if hasattr(self, 'load_content'): self.load_content(self.current_filter)

    # =========================================================================
    # --- LOGIC CƠ BẢN ---
    # =========================================================================
    def quick_test_login(self):
        self.current_user = "Guest"; self.balance = 50000; db.update_machine_status(THIS_MACHINE_NAME, "on")
        self.show_launcher_interface()
    
    def login(self):
        u = self.entry_user.get(); p = self.entry_pass.get(); mem = db.login_member(u, p)
        if mem:
            self.current_user = mem['username']; self.balance = mem['balance']
            db.update_machine_status(THIS_MACHINE_NAME, "on")
            self.show_launcher_interface()
        else: messagebox.showerror("Lỗi", "Sai thông tin")

    def monitor_session(self):
        if not self.is_logged_in: return
        self.balance -= PRICE_PER_SECOND; self.lbl_balance_display.config(text=f"{self.balance:,.0f} đ")
        if self.balance <= 0: self.balance = 0; self.logout("Hết tiền!"); return
        self.after(1000, self.monitor_session)

    def chat_admin(self):
        if hasattr(self, 'chat_win') and self.chat_win.winfo_exists(): self.chat_win.lift(); return
        self.chat_win = tk.Toplevel(self); self.chat_win.title("Chat"); self.chat_win.geometry("400x500"); self.chat_win.configure(bg=COLOR_BG); self.chat_win.attributes('-topmost', True)
        self.txt_chat = tk.Text(self.chat_win, bg=COLOR_PANEL, fg="white"); self.txt_chat.pack(fill="both", expand=True)
        self.txt_chat.tag_config("me", foreground=COLOR_ACCENT, justify="right"); self.txt_chat.tag_config("admin", foreground="white", justify="left")
        f = tk.Frame(self.chat_win, bg=COLOR_BG); f.pack(fill="x")
        self.ent_chat = tk.Entry(f); self.ent_chat.pack(side="left", fill="x", expand=True); self.ent_chat.bind("<Return>", self._send_chat)
        tk.Button(f, text="GỬI", command=self.cl_send_chat).pack(side="right")
        self._chat_loop_active = True; self._load_chat()
        self.chat_win.protocol("WM_DELETE_WINDOW", lambda: setattr(self, '_chat_loop_active', False) or self.chat_win.destroy())

    def _load_chat(self):
        if not getattr(self, '_chat_loop_active', False): return
        try:
            msgs = db.get_conversation(THIS_MACHINE_NAME)
            self.txt_chat.config(state="normal"); self.txt_chat.delete("1.0", tk.END)
            for m in msgs:
                tag = "me" if m['sender'] == THIS_MACHINE_NAME else "admin"
                self.txt_chat.insert(tk.END, f"{m['content']}\n", tag)
            self.txt_chat.see(tk.END); self.txt_chat.config(state="disabled")
        except: pass
        self.chat_win.after(2000, self._load_chat)

    def _send_chat(self, e):
        msg = self.ent_chat.get().strip()
        if msg and db.send_message_v2(THIS_MACHINE_NAME, "admin", msg): self.ent_chat.delete(0, tk.END); self._load_chat()

    def cl_send_chat(self): self._send_chat(None)

    def logout(self, reason=None):
        self.is_logged_in = False
        try:
            conn = db.connect_db(); cur = conn.cursor()
            cur.execute("UPDATE members SET balance=%s WHERE username=%s", (self.balance, self.current_user))
            conn.commit(); conn.close(); db.update_machine_status(THIS_MACHINE_NAME, "off")
        except: pass
        if reason: messagebox.showwarning("System", reason)
        self.current_user = None; self.attributes('-fullscreen', True); self.show_login_screen()

    def shutdown_pc(self): 
        if messagebox.askyesno("Power", "Tắt máy?"): self.destroy()
    def _update_clock(self):
        if self.is_logged_in: self.lbl_clock.config(text=datetime.now().strftime("%H:%M")); self.after(1000, self._update_clock)

if __name__ == "__main__":
    app = ClientApp()
    app.mainloop()