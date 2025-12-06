import tkinter as tk
from tkinter import ttk, messagebox

# Kết nối Database
try:
    from database import get_setting, save_setting, change_admin_password
except ImportError:
    def get_setting(k, d=""): return d
    def save_setting(k, v): print(f"Saved {k}: {v}")
    def change_admin_password(p): return True

# --- Theme ---
COLOR_BG      = "#121212"
COLOR_CARD    = "#1E1E1E"
COLOR_HOVER   = "#252525"
COLOR_ACCENT  = "#00E676"
COLOR_TEXT    = "#FFFFFF"
COLOR_SUB     = "#888888"

FONT_HEADER = ('Segoe UI', 20, 'bold')
FONT_TITLE  = ('Segoe UI', 12, 'bold')
FONT_DESC   = ('Segoe UI', 9)

# ==========================================
# CUSTOM: SETTING TILE (Thẻ cài đặt)
# ==========================================
class SettingTile(tk.Frame):
    def __init__(self, parent, icon, title, desc, command):
        super().__init__(parent, bg=COLOR_CARD, cursor="hand2", 
                         highlightbackground="#333", highlightthickness=1)
        self.command = command
        self.configure(width=250, height=160)
        self.pack_propagate(False)

        # Icon
        tk.Label(self, text=icon, font=("Segoe UI Emoji", 32), bg=COLOR_CARD, fg=COLOR_ACCENT).pack(pady=(25, 10))
        
        # Title
        tk.Label(self, text=title, font=FONT_TITLE, bg=COLOR_CARD, fg="white").pack()
        
        # Desc
        tk.Label(self, text=desc, font=FONT_DESC, bg=COLOR_CARD, fg=COLOR_SUB, wraplength=220).pack(pady=(5, 0))

        # Events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: command())
        
        for child in self.winfo_children():
            child.bind("<Enter>", self._on_enter)
            child.bind("<Button-1>", lambda e: command())

    def _on_enter(self, event):
        self.configure(bg=COLOR_HOVER, highlightbackground=COLOR_ACCENT)
        for child in self.winfo_children(): child.configure(bg=COLOR_HOVER)

    def _on_leave(self, event):
        self.configure(bg=COLOR_CARD, highlightbackground="#333")
        for child in self.winfo_children(): child.configure(bg=COLOR_CARD)

# ==========================================
# CUSTOM: MODERN ENTRY
# ==========================================
class ModernEntry(tk.Frame):
    def __init__(self, parent, label, is_pass=False):
        super().__init__(parent, bg=COLOR_BG)
        self.var = tk.StringVar()
        tk.Label(self, text=label, fg=COLOR_SUB, bg=COLOR_BG, font=("Segoe UI", 10)).pack(anchor='w')
        self.entry = tk.Entry(self, textvariable=self.var, bg="#222", fg="white", 
                              bd=0, insertbackground="white", font=("Segoe UI", 11), show="*" if is_pass else "")
        self.entry.pack(fill='x', ipady=5, pady=(2,0))
        tk.Frame(self, bg=COLOR_ACCENT, height=1).pack(fill='x')
    
    def get(self): return self.var.get()
    def set(self, val): self.var.set(val)

# ==========================================
# MAIN PAGE
# ==========================================
class SettingsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG)
        
        # Container chính
        self.container = tk.Frame(self, bg=COLOR_BG)
        self.container.pack(fill='both', expand=True, padx=40, pady=30)
        
        self.current_frame = None
        self._show_home()

    # --- NAVIGATION ---
    def _clear_view(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = tk.Frame(self.container, bg=COLOR_BG)
        self.current_frame.pack(fill='both', expand=True)

    def _show_home(self):
        self._clear_view()
        
        # Header
        tk.Label(self.current_frame, text="HỆ THỐNG", font=FONT_HEADER, bg=COLOR_BG, fg="white").pack(anchor='w', pady=(0, 30))

        # Grid
        grid = tk.Frame(self.current_frame, bg=COLOR_BG)
        grid.pack(fill='both', expand=True)

        # Các thẻ (Tiles)
        tiles = [
            ("🏢", "Thông tin Quán", "Tên, địa chỉ, hotline, wifi...", self._view_info),
            ("💰", "Bảng Giá", "Cấu hình giá tiền cho từng loại máy", self._view_price),
            ("🔒", "Bảo Mật", "Đổi mật khẩu Admin, phân quyền", self._view_security),
            ("⚙️", "Hệ Thống", "Sao lưu, âm thanh, thông báo", self._view_system),
        ]

        r, c = 0, 0
        for icon, title, desc, cmd in tiles:
            tile = SettingTile(grid, icon, title, desc, cmd)
            tile.grid(row=r, column=c, padx=15, pady=15)
            c += 1
            if c > 1: # 2 cột
                c = 0
                r += 1

    def _create_detail_header(self, title):
        h = tk.Frame(self.current_frame, bg=COLOR_BG)
        h.pack(fill='x', pady=(0, 20))
        
        # Nút Back
        btn_back = tk.Button(h, text="← Quay lại", bg=COLOR_BG, fg=COLOR_ACCENT, bd=0, 
                             font=("Segoe UI", 11, "bold"), cursor="hand2", 
                             activebackground=COLOR_BG, activeforeground="white",
                             command=self._show_home)
        btn_back.pack(side='left')
        
        tk.Label(h, text="|", fg="#444", bg=COLOR_BG).pack(side='left', padx=10)
        tk.Label(h, text=title, font=FONT_TITLE, fg="white", bg=COLOR_BG).pack(side='left')

    # --- SUB PAGES ---
    def _view_info(self):
        self._clear_view()
        self._create_detail_header("THÔNG TIN QUÁN")
        
        f = tk.Frame(self.current_frame, bg=COLOR_BG, padx=50)
        f.pack(fill='x')

        self.inp_name = ModernEntry(f, "Tên quán nét")
        self.inp_name.pack(fill='x', pady=10)
        self.inp_name.set(get_setting('shop_name', 'G Gaming'))

        self.inp_addr = ModernEntry(f, "Địa chỉ")
        self.inp_addr.pack(fill='x', pady=10)
        self.inp_addr.set(get_setting('address', ''))

        self.inp_wifi = ModernEntry(f, "Wifi Password")
        self.inp_wifi.pack(fill='x', pady=10)
        self.inp_wifi.set(get_setting('wifi_pass', ''))

        tk.Button(f, text="LƯU THÔNG TIN", bg=COLOR_ACCENT, fg="black", font=("Segoe UI", 10, "bold"), 
                  pady=8, bd=0, width=20, command=self._save_info).pack(anchor='w', pady=20)

    def _save_info(self):
        save_setting('shop_name', self.inp_name.get())
        save_setting('address', self.inp_addr.get())
        save_setting('wifi_pass', self.inp_wifi.get())
        messagebox.showinfo("Lưu", "Đã cập nhật thông tin quán.")
        self._show_home()

    def _view_price(self):
        self._clear_view()
        self._create_detail_header("CẤU HÌNH GIÁ (VNĐ/Giờ)")
        
        f = tk.Frame(self.current_frame, bg=COLOR_BG, padx=50)
        f.pack(fill='x')

        self.prices = {}
        cats = ["Tiêu chuẩn", "Gaming", "Chuyên nghiệp", "Thi đấu"]
        keys = ["price_standard", "price_gaming", "price_pro", "price_competition"]
        defaults = ["5000", "8000", "10000", "15000"]

        for i, cat in enumerate(cats):
            p = ModernEntry(f, f"Giá máy {cat}")
            p.pack(fill='x', pady=10)
            p.set(get_setting(keys[i], defaults[i]))
            self.prices[keys[i]] = p
        
        tk.Button(f, text="CẬP NHẬT GIÁ", bg=COLOR_ACCENT, fg="black", font=("Segoe UI", 10, "bold"), 
                  pady=8, bd=0, width=20, command=self._save_price).pack(anchor='w', pady=20)

    def _save_price(self):
        for k, v in self.prices.items():
            save_setting(k, v.get())
        messagebox.showinfo("Lưu", "Đã cập nhật bảng giá mới.")
        self._show_home()

    def _view_security(self):
        self._clear_view()
        self._create_detail_header("BẢO MẬT TÀI KHOẢN")
        
        f = tk.Frame(self.current_frame, bg=COLOR_BG, padx=50)
        f.pack(fill='x')

        self.inp_new = ModernEntry(f, "Mật khẩu mới", is_pass=True)
        self.inp_new.pack(fill='x', pady=10)

        self.inp_confirm = ModernEntry(f, "Nhập lại mật khẩu", is_pass=True)
        self.inp_confirm.pack(fill='x', pady=10)

        tk.Button(f, text="ĐỔI MẬT KHẨU", bg="#ff5252", fg="white", font=("Segoe UI", 10, "bold"), 
                  pady=8, bd=0, width=20, command=self._save_security).pack(anchor='w', pady=20)

    def _save_security(self):
        p1 = self.inp_new.get()
        p2 = self.inp_confirm.get()
        if not p1: return messagebox.showerror("Lỗi", "Mật khẩu trống")
        if p1 != p2: return messagebox.showerror("Lỗi", "Mật khẩu không khớp")
        if change_admin_password(p1):
            messagebox.showinfo("Thành công", "Đã đổi mật khẩu Admin.")
            self._show_home()
        else:
            messagebox.showerror("Lỗi", "Lỗi Database.")

    def _view_system(self):
        self._clear_view()
        self._create_detail_header("HỆ THỐNG")
        
        f = tk.Frame(self.current_frame, bg=COLOR_BG, padx=50)
        f.pack(fill='x')

        tk.Label(f, text="Tính năng này đang phát triển...", fg="#777", bg=COLOR_BG).pack(pady=20)
        tk.Button(f, text="Quay về", bg="#333", fg="white", bd=0, command=self._show_home).pack()

if __name__ == "__main__":
    root = tk.Tk(); root.geometry("900x600"); root.configure(bg=COLOR_BG)
    SettingsPage(root).pack(fill='both', expand=True)
    root.mainloop()