import tkinter as tk
from tkinter import font as tkFont
from tkinter import messagebox, simpledialog
import threading
import time
import random
import datetime

# =============================================================================
# --- 1. KẾT NỐI DATABASE & CÁC MODULE ---
# =============================================================================
try:
    from database import (get_dashboard_data, add_transaction_db, update_machine_status, 
                          get_transactions, get_unread_messages, get_pending_orders, 
                          mark_message_read, complete_order)
    # Nếu bạn có hàm chat user thì import thêm ở đây
except ImportError:
    # Dummy functions phòng hờ lỗi
    def get_dashboard_data(): return {"total_machines": 0, "active_machines": 0, "total_amount": 0}
    def add_transaction_db(t, c, a, d): pass
    def update_machine_status(n, s, start=None, used=None, amt=0): pass
    def get_transactions(limit=5): return []
    def get_unread_messages(): return []
    def get_pending_orders(): return []
    def mark_message_read(id): pass
    def complete_order(id): pass

# --- IMPORT CÁC MODULE CON ---
try: from QuanLyNhanVien import EmployeeListPage
except ImportError: pass
try: from khachhang import CustomerManagerPage
except ImportError: pass
try: from quanlymay import MachineManagerPage
except ImportError: pass
try: from quanlygame import GameManagerPage
except ImportError: pass

# [QUAN TRỌNG] Import Module Ca Trực
try: from catruc import ShiftManagerPage
except ImportError: pass

try: from doanhthu import RevenueManagerPage
except ImportError: pass
try: from baocaothongke import ReportManagerPage
except ImportError: pass
try: from system_settings import SettingsPage
except ImportError: pass
try: from danhmuc import CategoryManagerPage
except ImportError: pass 
try: from sanpham import ProductController
except ImportError: pass

# =============================================================================
# --- GIAO DIỆN MIDNIGHT BLUE ---
# =============================================================================

COLOR_BG_MAIN = "#1E1E2F"
COLOR_SIDEBAR = "#27293D"
COLOR_HEADER = "#27293D"
COLOR_CARD_BG = "#27293D"
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_GRAY = "#9A9A9A"
COLOR_ACCENT_1 = "#E14ECA"
COLOR_ACCENT_2 = "#00F2C3"
COLOR_ACCENT_3 = "#1D8CF8"
COLOR_RED = "#FF6B6B" 

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Game Center Manager")
        self.geometry("1280x800")
        self.configure(bg=COLOR_BG_MAIN)
        self.is_logout = False
        self._setup_fonts()
        self._setup_layout()
        self._setup_sidebar()
        self._setup_header()
        
        self.dashboard_update_interval = 3000
        self._stop_update = False
        self._current_vals = {"active": 0, "maintenance": 0, "revenue": 0}

        self.show_dashboard()
        self.check_notifications_loop()

    def _setup_fonts(self):
        self.font_h1 = tkFont.Font(family="Helvetica", size=26, weight="bold")
        self.font_h2 = tkFont.Font(family="Helvetica", size=16, weight="bold")
        self.font_h3 = tkFont.Font(family="Helvetica", size=12, weight="bold")
        self.font_norm = tkFont.Font(family="Helvetica", size=10)
        self.font_big_num = tkFont.Font(family="Helvetica", size=36, weight="bold")
        self.font_icon = tkFont.Font(size=18)
        
        # [CẬP NHẬT] Thêm mục "Ca trực" vào danh sách Menu
        self.menu_items = [
            ("Tổng quan", "🏠"), 
            ("Máy trạm", "🖥"), 
            ("Danh sách Game", "🎮"),
            ("Nhân viên", "👥"), 
            ("Ca trực", "⏰"),       # <--- THÊM MỚI Ở ĐÂY
            ("Khách hàng", "👤"), 
            ("Sản phẩm & Kho", "📦"),
            ("Danh mục", "📂"), 
            ("Doanh thu", "💰"), 
            ("Báo cáo", "📊"), 
            ("Cài đặt", "⚙️")
        ]

    def _setup_layout(self):
        self.sidebar_frame = tk.Frame(self, bg=COLOR_SIDEBAR, width=260); self.sidebar_frame.pack(side="left", fill="y"); self.sidebar_frame.pack_propagate(False)
        self.main_area = tk.Frame(self, bg=COLOR_BG_MAIN); self.main_area.pack(side="right", fill="both", expand=True)
        self.header_frame = tk.Frame(self.main_area, bg=COLOR_BG_MAIN, height=70); self.header_frame.pack(side="top", fill="x", padx=30, pady=10); self.header_frame.pack_propagate(False)
        self.content_frame = tk.Frame(self.main_area, bg=COLOR_BG_MAIN); self.content_frame.pack(side="top", fill="both", expand=True, padx=30, pady=10)

    def _setup_header(self):
        self.lbl_page_title = tk.Label(self.header_frame, text="DASHBOARD", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_MAIN, font=self.font_h2); self.lbl_page_title.pack(side="left", anchor="sw")
        user_panel = tk.Frame(self.header_frame, bg=COLOR_BG_MAIN); user_panel.pack(side="right", anchor="se")
        tk.Label(user_panel, text="Xin chào, Admin", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_MAIN, font=("Helvetica", 11)).pack(side="right")
        tk.Label(user_panel, text="●", fg="#00F2C3", bg=COLOR_BG_MAIN, font=("Arial", 12)).pack(side="right", padx=10)

    def _setup_sidebar(self):
        logo_area = tk.Frame(self.sidebar_frame, bg=COLOR_SIDEBAR, height=80); logo_area.pack(fill="x")
        tk.Label(logo_area, text="G-GAMING", fg=COLOR_TEXT_WHITE, bg=COLOR_SIDEBAR, font=("Arial", 22, "bold", "italic")).place(relx=0.5, rely=0.5, anchor="center")
        tk.Frame(self.sidebar_frame, bg="gray", height=1).pack(fill="x", padx=20, pady=10)
        for text, icon in self.menu_items: self._create_sidebar_btn(text, icon)
        tk.Button(self.sidebar_frame, text="   🚪  Đăng xuất", fg="#FF6B6B", bg=COLOR_SIDEBAR, bd=0, anchor="w", padx=30, command=self._logout).pack(side="bottom", fill="x", pady=20, ipady=10)

    def _create_sidebar_btn(self, text, icon):
        tk.Button(self.sidebar_frame, text=f"   {icon}   {text}", fg=COLOR_TEXT_WHITE, bg=COLOR_SIDEBAR, activebackground=COLOR_ACCENT_3, activeforeground="white", font=self.font_norm, bd=0, anchor="w", padx=25, cursor="hand2", command=lambda t=text: self._menu_click(t)).pack(fill="x", pady=2, ipady=8)

    def _menu_click(self, text):
        self.lbl_page_title.config(text=text.upper())
        self._stop_update = True 
        
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children(): widget.destroy()
        
        # Điều hướng Menu
        if text == "Tổng quan": self.show_dashboard()
        elif text == "Máy trạm": MachineManagerPage(self.content_frame).pack(fill="both", expand=True)
        elif text == "Danh sách Game": GameManagerPage(self.content_frame).pack(fill="both", expand=True)
        elif text == "Doanh thu": RevenueManagerPage(self.content_frame).pack(fill="both", expand=True)
        elif text == "Cài đặt": SettingsPage(self.content_frame).pack(fill="both", expand=True)
        elif text == "Khách hàng": 
            try: CustomerManagerPage(self.content_frame).pack(fill="both", expand=True)
            except: pass
        elif text == "Nhân viên": EmployeeListPage(self.content_frame, self).pack(fill="both", expand=True)
        
        # [CẬP NHẬT] Xử lý sự kiện click vào "Ca trực"
        elif text == "Ca trực":
            try: 
                ShiftManagerPage(self.content_frame).pack(fill="both", expand=True)
            except NameError:
                tk.Label(self.content_frame, text="Module Ca trực chưa được import hoặc file catruc.py bị lỗi.", fg="white", bg=COLOR_BG_MAIN).pack(pady=20)
            except Exception as e:
                tk.Label(self.content_frame, text=f"Lỗi hiển thị: {e}", fg="white", bg=COLOR_BG_MAIN).pack(pady=20)

        elif text == "Sản phẩm & Kho": 
            try: ProductController(self.content_frame)
            except: pass
        elif text == "Danh mục": 
            try: CategoryManagerPage(self.content_frame).pack(fill="both", expand=True)
            except: pass
        elif text == "Báo cáo": 
            try: ReportManagerPage(self.content_frame).pack(fill="both", expand=True)
            except: pass

    # ... (Các hàm Action, Dashboard, Chat Center giữ nguyên như cũ bên dưới) ...
    def show_dashboard(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()
        self._stop_update = False

        grid_frame = tk.Frame(self.content_frame, bg=COLOR_BG_MAIN)
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure(0, weight=1); grid_frame.grid_columnconfigure(1, weight=1); grid_frame.grid_columnconfigure(2, weight=1)

        c1, self.active_label = self._create_stat_card(grid_frame, "Máy đang bật", "0", "🖥", COLOR_ACCENT_3); c1.grid(row=0, column=0, sticky="nsew")
        c2, self.revenue_label = self._create_stat_card(grid_frame, "Tổng doanh thu", "0", "💵", COLOR_ACCENT_2); c2.grid(row=0, column=1, sticky="nsew")
        c3, self.total_label = self._create_stat_card(grid_frame, "Tổng số máy", "0", "🎲", COLOR_ACCENT_1); c3.grid(row=0, column=2, sticky="nsew")

        notify_frame = tk.Frame(self.content_frame, bg=COLOR_BG_MAIN, pady=10)
        notify_frame.pack(fill="x", padx=10)
        
        tk.Label(notify_frame, text="THÔNG BÁO TỪ MÁY TRẠM", fg="#AAA", bg=COLOR_BG_MAIN, font=("Arial", 10, "bold")).pack(anchor="w")
        
        btns_row = tk.Frame(notify_frame, bg=COLOR_BG_MAIN)
        btns_row.pack(fill="x", pady=5)

        self.btn_notif_chat = tk.Button(btns_row, text="💬 Tin nhắn", bg=COLOR_CARD_BG, fg="white", bd=0, padx=20, pady=10, 
                                        font=("Arial", 11), cursor="hand2", command=self.open_unread_messages)
        self.btn_notif_chat.pack(side="left", padx=5)
        self.dot_chat = tk.Label(self.btn_notif_chat, text="●", fg=COLOR_RED, bg=COLOR_CARD_BG, font=("Arial", 16))

        self.btn_notif_order = tk.Button(btns_row, text="🍔 Đơn hàng mới", bg=COLOR_CARD_BG, fg="white", bd=0, padx=20, pady=10, 
                                         font=("Arial", 11), cursor="hand2", command=self.open_pending_orders)
        self.btn_notif_order.pack(side="left", padx=5)
        self.dot_order = tk.Label(self.btn_notif_order, text="●", fg=COLOR_RED, bg=COLOR_CARD_BG, font=("Arial", 16))

        row2 = tk.Frame(self.content_frame, bg=COLOR_BG_MAIN); row2.pack(fill="both", expand=True, pady=10)
        panel_right = tk.Frame(row2, bg=COLOR_CARD_BG); panel_right.pack(side="left", fill="both", expand=True, padx=10)
        tk.Label(panel_right, text="HOẠT ĐỘNG GẦN ĐÂY", fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, font=self.font_h3).pack(anchor="w", padx=20, pady=15)
        self.recent_log_frame = tk.Frame(panel_right, bg=COLOR_CARD_BG); self.recent_log_frame.pack(fill="both", expand=True)

        self._schedule_fetch()

    def _create_stat_card(self, parent, title, value_var, icon, color_accent):
        wrapper = tk.Frame(parent, bg=COLOR_BG_MAIN); card = tk.Frame(wrapper, bg=COLOR_CARD_BG); card.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Frame(card, bg=color_accent, height=4).pack(fill="x", side="top")
        content = tk.Frame(card, bg=COLOR_CARD_BG); content.pack(fill="both", expand=True, padx=20, pady=20)
        row1 = tk.Frame(content, bg=COLOR_CARD_BG); row1.pack(fill="x")
        tk.Label(row1, text=icon, fg=color_accent, bg=COLOR_CARD_BG, font=("Arial", 22)).pack(side="left")
        tk.Label(row1, text=title.upper(), fg=COLOR_TEXT_GRAY, bg=COLOR_CARD_BG, font=("Helvetica", 10, "bold")).pack(side="left", padx=15)
        lbl_val = tk.Label(content, text="Loading...", fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, font=self.font_big_num, anchor="w"); lbl_val.pack(fill="x", pady=(10, 0))
        return wrapper, lbl_val

    # --- CHAT & NOTIFICATION LOGIC ---
    def check_notifications_loop(self):
        if self.is_logout: return
        try:
            msgs = get_unread_messages()
            if msgs:
                self.dot_chat.place(relx=0.85, rely=0.1)
                self.btn_notif_chat.config(bg="#3E3E4E", text=f"💬 Tin nhắn ({len(msgs)})")
            else:
                self.dot_chat.place_forget()
                self.btn_notif_chat.config(bg=COLOR_CARD_BG, text="💬 Tin nhắn")

            orders = get_pending_orders()
            if orders:
                self.dot_order.place(relx=0.85, rely=0.1)
                self.btn_notif_order.config(bg="#3E3E4E", text=f"🍔 Order ({len(orders)})")
            else:
                self.dot_order.place_forget()
                self.btn_notif_order.config(bg=COLOR_CARD_BG, text="🍔 Order")
        except: pass
        self.after(3000, self.check_notifications_loop)

    def open_unread_messages(self):
        self.chat_window = tk.Toplevel(self)
        self.chat_window.title("TRUNG TÂM TIN NHẮN")
        self.chat_window.geometry("900x600")
        self.chat_window.configure(bg=COLOR_BG_MAIN)

        paned = tk.PanedWindow(self.chat_window, orient=tk.HORIZONTAL, bg=COLOR_BG_MAIN, sashwidth=4)
        paned.pack(fill="both", expand=True)

        left_frame = tk.Frame(paned, bg=COLOR_SIDEBAR, width=250); paned.add(left_frame)
        tk.Label(left_frame, text="DANH SÁCH MÁY", fg="white", bg=COLOR_SIDEBAR, font=("Arial", 10, "bold")).pack(pady=10)
        self.machine_listbox = tk.Listbox(left_frame, bg=COLOR_CARD_BG, fg="white", font=("Arial", 11), bd=0, highlightthickness=0)
        self.machine_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.machine_listbox.bind("<<ListboxSelect>>", self.on_select_chat_machine)

        right_frame = tk.Frame(paned, bg=COLOR_BG_MAIN); paned.add(right_frame)
        self.lbl_chat_target = tk.Label(right_frame, text="Chọn máy để chat...", fg=COLOR_ACCENT_2, bg=COLOR_BG_MAIN, font=("Arial", 14, "bold")); self.lbl_chat_target.pack(pady=10)
        self.txt_chat_history = tk.Text(right_frame, bg=COLOR_CARD_BG, fg="white", font=("Arial", 11), state="disabled", wrap="word", padx=10, pady=10, bd=0)
        self.txt_chat_history.pack(fill="both", expand=True, padx=10)
        self.txt_chat_history.tag_config("admin", foreground=COLOR_ACCENT_3, justify="right")
        self.txt_chat_history.tag_config("client", foreground="white", justify="left")

        input_frame = tk.Frame(right_frame, bg=COLOR_BG_MAIN, height=50); input_frame.pack(fill="x", padx=10, pady=10)
        self.entry_chat_msg = tk.Entry(input_frame, bg="white", fg="black", font=("Arial", 12))
        self.entry_chat_msg.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry_chat_msg.bind("<Return>", self.sv_send_chat)
        tk.Button(input_frame, text="GỬI ➤", bg=COLOR_ACCENT_3, fg="white", font=("Arial", 10, "bold"), command=self.sv_send_chat).pack(side="right", padx=(5,0), ipadx=10, ipady=5)

        self.current_chat_machine = None
        self.load_chat_machines()
        self.chat_loop_active = True
        self.sv_chat_refresh_loop()
        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_close_chat_window)

    def load_chat_machines(self):
        self.machine_listbox.delete(0, tk.END)
        try:
            from database import get_active_chat_users
            users = get_active_chat_users() 
            if not users: users = ["Chưa có tin nhắn"]
            for u in users: self.machine_listbox.insert(tk.END, u)
        except: self.machine_listbox.insert(tk.END, "Lỗi tải danh sách")

    def on_select_chat_machine(self, event):
        selection = self.machine_listbox.curselection()
        if selection:
            self.current_chat_machine = self.machine_listbox.get(selection[0])
            self.lbl_chat_target.config(text=f"Đang chat với: {self.current_chat_machine}")
            self.load_conversation()

    def load_conversation(self):
        if not self.current_chat_machine: return
        from database import get_conversation, mark_message_read
        msgs = get_conversation(self.current_chat_machine)
        self.txt_chat_history.config(state="normal")
        self.txt_chat_history.delete("1.0", tk.END)
        for m in msgs:
            time_str = m['created_at'].strftime("%H:%M")
            if m['sender'] == 'admin':
                self.txt_chat_history.insert(tk.END, f"{m['content']}\n", "admin")
                self.txt_chat_history.insert(tk.END, f"{time_str}\n\n", "admin")
            else:
                self.txt_chat_history.insert(tk.END, f"{m['content']}\n", "client")
                self.txt_chat_history.insert(tk.END, f"{time_str}\n\n", "client")
                if m['is_read'] == 0: mark_message_read(m['id'])
        self.txt_chat_history.see(tk.END)
        self.txt_chat_history.config(state="disabled")

    def sv_send_chat(self, event=None):
        msg = self.entry_chat_msg.get().strip()
        if not msg or not self.current_chat_machine: return
        from database import send_message_v2
        if send_message_v2("admin", self.current_chat_machine, msg):
            self.entry_chat_msg.delete(0, tk.END)
            self.load_conversation()
        else: messagebox.showerror("Lỗi", "Gửi thất bại")

    def sv_chat_refresh_loop(self):
        if hasattr(self, 'chat_loop_active') and self.chat_loop_active:
            if self.current_chat_machine: self.load_conversation()
            self.after(2000, self.sv_chat_refresh_loop)

    def on_close_chat_window(self):
        self.chat_loop_active = False
        self.chat_window.destroy()

    def open_pending_orders(self):
        orders = get_pending_orders()
        if not orders: messagebox.showinfo("Thông báo", "Không có đơn hàng mới!"); return
        top = tk.Toplevel(self); top.title("Đơn hàng chưa phục vụ"); top.geometry("500x400")
        for o in orders:
            f = tk.Frame(top, pady=5, padx=5, bg="#eee"); f.pack(fill="x", pady=2)
            tk.Label(f, text=o['description'], font=("Arial", 11, "bold"), bg="#eee").pack(anchor="w")
            tk.Label(f, text=f"Giá: {o['amount']:,.0f} đ", fg="red", bg="#eee").pack(anchor="w")
            tk.Button(f, text="✅ Đã phục vụ", bg="green", fg="white", command=lambda oid=o['id'], win=top: self._serve_order(oid, win)).pack(anchor="e")

    def _serve_order(self, oid, win):
        complete_order(oid); win.destroy(); self.open_pending_orders()

    def _logout(self):
        if messagebox.askyesno("Xác nhận", "Đăng xuất khỏi hệ thống?"):
            self._stop_update = True; self.is_logout = True; self.destroy()

    def _schedule_fetch(self):
        if self._stop_update: return
        t = threading.Thread(target=self._fetch_and_apply, daemon=True); t.start()

    def _fetch_and_apply(self):
        try:
            data = get_dashboard_data()
            logs = get_transactions(limit=5)
        except: data = {"total_machines": 0, "active_machines": 0, "total_amount": 0}; logs = []
        try: self.after(0, lambda: self._animate_update(int(data.get("active_machines", 0)), int(data.get("total_machines", 0)), int(data.get("total_amount", 0)), logs))
        except: pass
        def schedule_next():
            if not self._stop_update: self.after(self.dashboard_update_interval, self._schedule_fetch)
        try: self.after(0, schedule_next)
        except: pass

    def _animate_update(self, new_active, new_total, new_revenue, logs):
        try:
            if self.active_label.winfo_exists():
                self.active_label.config(text=str(new_active))
                self.total_label.config(text=str(new_total))
                self.revenue_label.config(text=f"{new_revenue:,.0f} đ")
        except: pass
        try:
            if self.recent_log_frame.winfo_exists():
                for w in self.recent_log_frame.winfo_children(): w.destroy()
                if not logs: tk.Label(self.recent_log_frame, text="Chưa có hoạt động nào", fg="#777", bg=COLOR_CARD_BG).pack(pady=10)
                for row in logs:
                    f = tk.Frame(self.recent_log_frame, bg=COLOR_CARD_BG); f.pack(fill="x", padx=20, pady=5)
                    time_str = row['created_at'].strftime("%H:%M") if row.get('created_at') else "--:--"
                    desc = row.get('description', 'Giao dịch'); amt = row.get('amount', 0)
                    tk.Label(f, text=time_str, fg=COLOR_ACCENT_3, bg=COLOR_CARD_BG, font=("Arial", 9, "bold")).pack(side="left")
                    tk.Label(f, text=f"{desc[:30]}...", fg="white", bg=COLOR_CARD_BG, font=("Arial", 9)).pack(side="left", padx=10)
                    tk.Label(f, text=f"+{amt:,.0f}", fg=COLOR_ACCENT_2, bg=COLOR_CARD_BG, font=("Arial", 9, "bold")).pack(side="right")
        except: pass

if __name__ == "__main__":
    app = App()
    app.mainloop()