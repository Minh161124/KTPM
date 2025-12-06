# cybercafelauncher.py
# FIX LỖI: Thiếu thư viện 'sys' gây lỗi khi bấm nút CHƠI
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os, threading, time, subprocess, sys  # <--- ĐÃ THÊM sys VÀO ĐÂY
from typing import Optional

# --- KẾT NỐI DATABASE ---
try:
    from database import (
        create_tables, get_all_games, add_game_db, update_game_db, 
        delete_game_db, toggle_block_db, queue_install_game # Thêm hàm queue
    )
except ImportError:
    # Fallback nếu chạy file này 1 mình mà ko có db
    def create_tables(): pass
    def get_all_games(): return []
    def add_game_db(*args): pass
    def update_game_db(*args): pass
    def delete_game_db(*args): pass
    def toggle_block_db(*args): pass
    def queue_install_game(*args): pass

# --- Cấu hình & Theme ---
COLOR_BG_DARK     = "#1e1e1e"       
COLOR_BG_CARD     = "#2d2d2d"       
COLOR_BG_HOVER    = "#383838"       
COLOR_ACCENT      = "#00ff88"       
COLOR_ACCENT_DARK = "#00cc6a"       
COLOR_TEXT_MAIN   = "#ffffff"
COLOR_TEXT_SUB    = "#b0b0b0"
COLOR_RED         = "#ff4757"
COLOR_WARNING     = "#ffa502"

FONT_MAIN   = ('Segoe UI', 10)
FONT_BOLD   = ('Segoe UI', 10, 'bold')
FONT_TITLE  = ('Segoe UI', 11, 'bold')
FONT_HEADER = ('Segoe UI', 14, 'bold')

# Pillow Check
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# --- Image Cache System ---
_IMG_CACHE = {}

def load_image_smart(path_str: str, size=(220, 120)):
    if not path_str: return None
    if not PIL_AVAILABLE: return None
    
    key = f"{path_str}|{size}"
    if key in _IMG_CACHE: return _IMG_CACHE[key]

    real_path = path_str
    if not os.path.exists(real_path):
        base = os.path.basename(path_str)
        for folder in ["", "images", "assets", "img"]:
            check = os.path.join(os.getcwd(), folder, base)
            if os.path.exists(check): real_path = check; break
    
    if not os.path.exists(real_path): return None

    try:
        img = Image.open(real_path)
        img_ratio = img.width / img.height
        target_ratio = size[0] / size[1]
        
        if img_ratio > target_ratio:
            new_width = int(target_ratio * img.height)
            left = (img.width - new_width) / 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) / 2
            img = img.crop((0, top, img.width, top + new_height))
            
        img = img.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        _IMG_CACHE[key] = photo
        return photo
    except Exception:
        return None

# ==========================================
# 2. UI COMPONENTS: CUSTOM CARD
# ==========================================

class GameCard(tk.Frame):
    def __init__(self, parent, game_data, app_instance):
        super().__init__(parent, bg=COLOR_BG_CARD, bd=0, cursor="hand2")
        self.game = game_data
        self.app = app_instance
        self.pack_propagate(False)
        self.configure(width=240, height=200)

        # 1. Ảnh bìa
        self.img_frame = tk.Label(self, bg="#000000", bd=0)
        self.img_frame.place(x=0, y=0, width=240, height=135)
        photo = load_image_smart(game_data.get("image") or game_data.get("path"), size=(240, 135))
        if photo:
            self.img_frame.config(image=photo)
            self.img_frame.image = photo
        else:
            self.img_frame.config(text=game_data.get("name")[:2].upper(), fg="#555", font=("Arial", 30, "bold"))

        # 2. Thông tin
        self.info_frame = tk.Frame(self, bg=COLOR_BG_CARD, height=65)
        self.info_frame.place(x=0, y=135, width=240, height=65)

        self.lbl_name = tk.Label(self.info_frame, text=game_data.get("name"), font=FONT_TITLE, 
                                 bg=COLOR_BG_CARD, fg=COLOR_TEXT_MAIN, anchor='w')
        self.lbl_name.place(x=10, y=5, width=220)

        cat_ver = f"{game_data.get('category', 'Game')} | {game_data.get('version', '')}"
        self.lbl_sub = tk.Label(self.info_frame, text=cat_ver, font=('Segoe UI', 8), 
                                bg=COLOR_BG_CARD, fg=COLOR_TEXT_SUB, anchor='w')
        self.lbl_sub.place(x=10, y=30, width=150)

        self.btn_play = tk.Button(self.info_frame, text="CHƠI", bg=COLOR_BG_CARD, fg=COLOR_ACCENT,
                                  font=('Segoe UI', 9, 'bold'), bd=1, relief="solid",
                                  activebackground=COLOR_ACCENT, activeforeground="black",
                                  command=self._on_play_click)
        self.btn_play.configure(highlightbackground=COLOR_ACCENT, highlightthickness=1)
        self.btn_play.place(x=170, y=30, width=60, height=25)

        if int(game_data.get("blocked", 0)):
            self.overlay_f = tk.Frame(self, bg="black")
            self.overlay_f.place(x=0, y=0, width=240, height=200)
            self.overlay_f.wait_visibility()
            self.overlay_f.wm_attributes("-alpha", 0.7)
            tk.Label(self.overlay_f, text="ĐANG BẢO TRÌ", fg=COLOR_RED, bg="black", font=FONT_HEADER).pack(expand=True)

        # Events
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)
        self.img_frame.bind("<Button-1>", self._on_play_click)
        self.lbl_name.bind("<Button-1>", self._on_play_click)
        
        self.bind("<Button-3>", self._show_context_menu)
        self.img_frame.bind("<Button-3>", self._show_context_menu)

    def _on_hover(self, e):
        self.configure(bg=COLOR_BG_HOVER)
        self.info_frame.configure(bg=COLOR_BG_HOVER)
        self.lbl_name.configure(bg=COLOR_BG_HOVER, fg=COLOR_ACCENT)
        self.lbl_sub.configure(bg=COLOR_BG_HOVER)
        self.btn_play.configure(bg=COLOR_ACCENT, fg="black")

    def _on_leave(self, e):
        self.configure(bg=COLOR_BG_CARD)
        self.info_frame.configure(bg=COLOR_BG_CARD)
        self.lbl_name.configure(bg=COLOR_BG_CARD, fg=COLOR_TEXT_MAIN)
        self.lbl_sub.configure(bg=COLOR_BG_CARD)
        self.btn_play.configure(bg=COLOR_BG_CARD, fg=COLOR_ACCENT)

    def _on_play_click(self, e=None):
        if int(self.game.get("blocked", 0)):
            messagebox.showwarning("Thông báo", "Game này đang bảo trì, vui lòng chọn game khác!")
            return
        path = self.game.get("path", "")
        if not path:
            messagebox.showinfo("Chưa cài đặt", f"Game '{self.game['name']}' chưa có đường dẫn chạy (Path).")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, path])
            self.app.show_toast(f"Đang khởi động {self.game['name']}...")
        except Exception as ex:
            messagebox.showerror("Lỗi khởi động", f"Không thể chạy file:\n{path}\n\nLỗi: {ex}")

    def _show_context_menu(self, e):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Cập nhật / Sửa", command=lambda: self.app.open_editor(self.game))
        m.add_command(label="Cài đặt lại", command=lambda: self.app.open_installer(self.game))
        m.add_separator()
        state = "Bỏ chặn" if int(self.game.get("blocked", 0)) else "Chặn (Bảo trì)"
        m.add_command(label=state, command=lambda: self.app.toggle_block(self.game))
        m.add_command(label="Xóa khỏi menu", command=lambda: self.app.delete_game(self.game), foreground="red")
        m.tk_popup(e.x_root, e.y_root)

# ==========================================
# 3. MAIN PAGE (DẠNG FRAME ĐỂ NHÚNG)
# ==========================================

class GameManagerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#0E0E0E") 
        
        try: create_tables() 
        except Exception as e: print(f"Lỗi tạo bảng CSDL: {e}")

        self._games = []
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        toolbar = tk.Frame(self, bg=COLOR_BG_DARK)
        toolbar.pack(fill='x', padx=20, pady=10)
        
        lbl_title = tk.Label(toolbar, text="DANH SÁCH TRÒ CHƠI", font=FONT_HEADER, bg=COLOR_BG_DARK, fg="white")
        lbl_title.pack(side='left')

        search_frame = tk.Frame(toolbar, bg="#333", padx=2, pady=2)
        search_frame.pack(side='left', padx=40)
        tk.Label(search_frame, text="🔍", bg="#333", fg="#888").pack(side='left', padx=5)
        self.entry_search = tk.Entry(search_frame, textvariable=self.search_var, width=30, 
                                     font=FONT_MAIN, bg="#333", fg="white", bd=0, insertbackground="white")
        self.entry_search.pack(side='left', ipady=5)

        btn_style = {"bg": "#333", "fg": "white", "bd": 0, "padx": 15, "pady": 5, "activebackground": "#444"}
        fr_btns = tk.Frame(toolbar, bg=COLOR_BG_DARK)
        fr_btns.pack(side='right')
        
        tk.Button(fr_btns, text="+ Thêm Game", command=self._add_new_game, **btn_style).pack(side='left', padx=5)
        tk.Button(fr_btns, text="⚙ Trình Cài Đặt", command=lambda: self.open_installer(None), **btn_style).pack(side='left', padx=5)
        tk.Button(fr_btns, text="↻ Làm mới", command=self._load_data, **btn_style).pack(side='left', padx=5)

        self.canvas = tk.Canvas(self, bg=COLOR_BG_DARK, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG_DARK)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=20)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_resize)
        self.scrollable_frame.bind('<Enter>', lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.scrollable_frame.bind('<Leave>', lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_resize(self, event):
        width = event.width
        card_w = 240
        pad_x = 20
        columns = max(1, width // (card_w + pad_x))
        self._render_grid(columns)

    def _render_grid(self, columns):
        for widget in self.scrollable_frame.winfo_children():
            widget.grid_forget()
        
        # Xóa sạch để vẽ lại
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
            
        current_games = self._filtered_games if hasattr(self, '_filtered_games') else self._games
        
        row = 0
        col = 0
        for i, game in enumerate(current_games):
            card = GameCard(self.scrollable_frame, game, self)
            card.grid(row=row, column=col, padx=10, pady=15)
            col += 1
            if col >= columns:
                col = 0
                row += 1

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _load_data(self):
        self._games = get_all_games()
        self._filtered_games = self._games
        self.update_idletasks()
        w = self.canvas.winfo_width()
        if w > 1:
            self._on_resize(type('obj', (object,), {'width': w}))

    def _on_search_change(self, *args):
        query = self.search_var.get().lower().strip()
        if not query:
            self._filtered_games = self._games
        else:
            self._filtered_games = [
                g for g in self._games 
                if query in g['name'].lower() or query in g.get('category','').lower()
            ]
        w = self.canvas.winfo_width()
        self._render_grid(max(1, w // 260))

    def show_toast(self, message):
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.configure(bg=COLOR_ACCENT)
        w, h = 300, 40
        x = self.winfo_rootx() + self.winfo_width() - w - 30
        y = self.winfo_rooty() + self.winfo_height() - h - 50
        top.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(top, text=message, bg=COLOR_ACCENT, fg="black", font=FONT_BOLD).pack(expand=True)
        top.after(3000, top.destroy)

    def open_editor(self, game):
        dlg = GameEditor(self, game)
        self.wait_window(dlg)
        self._load_data()

    def _add_new_game(self):
        self.open_editor(None)

    def delete_game(self, game):
        if messagebox.askyesno("Xác nhận", f"Xóa game {game['name']} khỏi danh sách?"):
            try:
                delete_game_db(game['id'])
                self.after(100, self._load_data) 
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")

    def toggle_block(self, game):
        try:
            toggle_block_db(game['id'], int(game.get('blocked', 0)))
            self.after(100, self._load_data)
        except Exception as e:
            print(f"Lỗi toggle: {e}")

    def open_installer(self, game):
        dlg = InstallerWindow(self, selected_game=game)
        self.wait_window(dlg)
        self._load_data()

# ==========================================
# 4. CLASS EDITOR & INSTALLER (UPDATED)
# ==========================================
class GameEditor(tk.Toplevel):
    def __init__(self, parent, game: Optional[dict]=None):
        super().__init__(parent)
        self.title("Quản lý thông tin Game")
        self.configure(bg=COLOR_BG_DARK)
        self.geometry("550x400")
        self.game_editing = game
        
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        
        self._build_ui(game)

    def _build_ui(self, game):
        frm = tk.Frame(self, bg=COLOR_BG_DARK, padx=20, pady=20)
        frm.pack(fill='both', expand=True)
        
        def entry_row(label, row):
            tk.Label(frm, text=label, bg=COLOR_BG_DARK, fg="white").grid(row=row, column=0, sticky='w', pady=5)
            e = tk.Entry(frm, bg="#333", fg="white", insertbackground="white")
            e.grid(row=row, column=1, sticky='ew', padx=10)
            return e

        self.e_name = entry_row("Tên Game:", 0)
        tk.Label(frm, text="Thể loại:", bg=COLOR_BG_DARK, fg="white").grid(row=1, column=0, sticky='w', pady=5)
        CATEGORIES = ["MOBA", "FPS (Bắn súng)", "Battle Royale", "MMORPG", "Sports (Thể thao)", "Strategy", "Racing", "Fighting", "Simulator", "Khác"]
        self.e_cat = ttk.Combobox(frm, values=CATEGORIES, state="readonly", font=('Segoe UI', 10))
        self.e_cat.grid(row=1, column=1, sticky='ew', padx=10)

        self.e_ver = entry_row("Phiên bản:", 2)
        tk.Label(frm, text="Đường dẫn (.exe):", bg=COLOR_BG_DARK, fg="white").grid(row=3, column=0, sticky='w', pady=5)
        fr_path = tk.Frame(frm, bg=COLOR_BG_DARK); fr_path.grid(row=3, column=1, sticky='ew', padx=10)
        self.e_path = tk.Entry(fr_path, bg="#333", fg="white", insertbackground="white"); self.e_path.pack(side='left', fill='x', expand=True)
        tk.Button(fr_path, text="...", command=self._browse_exe, bg="#444", fg="white", bd=0).pack(side='right', padx=(5,0))

        tk.Label(frm, text="Ảnh (File):", bg=COLOR_BG_DARK, fg="white").grid(row=4, column=0, sticky='w', pady=5)
        fr_img = tk.Frame(frm, bg=COLOR_BG_DARK); fr_img.grid(row=4, column=1, sticky='ew', padx=10)
        self.e_img = tk.Entry(fr_img, bg="#333", fg="white", insertbackground="white"); self.e_img.pack(side='left', fill='x', expand=True)
        tk.Button(fr_img, text="...", command=self._browse_img, bg="#444", fg="white", bd=0).pack(side='right', padx=(5,0))

        frm.grid_columnconfigure(1, weight=1)
        btn_save = tk.Button(self, text="LƯU THÔNG TIN", bg=COLOR_ACCENT, fg="black", font=FONT_BOLD, command=self._save)
        btn_save.pack(pady=15, ipadx=20)

        if game:
            self.e_name.insert(0, game.get('name', ''))
            self.e_cat.set(game.get('category', ''))
            self.e_ver.insert(0, game.get('version', ''))
            self.e_path.insert(0, game.get('path', ''))
            self.e_img.insert(0, game.get('image', ''))
        else:
            self.e_cat.current(0)

    def _browse_exe(self):
        f = filedialog.askopenfilename(title="Chọn file chạy game", filetypes=[("Executable", "*.exe"), ("All", "*.*")])
        if f: self.e_path.delete(0, tk.END); self.e_path.insert(0, f); self.lift(); self.focus_force()

    def _browse_img(self):
        f = filedialog.askopenfilename(title="Chọn ảnh bìa", filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")])
        if f: self.e_img.delete(0, tk.END); self.e_img.insert(0, f); self.lift(); self.focus_force()

    def _save(self):
        name = self.e_name.get().strip()
        if not name: messagebox.showwarning("Thiếu thông tin", "Tên game không được để trống!", parent=self); return
        cat = self.e_cat.get(); ver = self.e_ver.get(); path = self.e_path.get(); img = self.e_img.get()

        if self.game_editing: update_game_db(self.game_editing['id'], name, cat, ver, path, img)
        else: add_game_db(name, cat, ver, path, img)
        self.destroy()

# --- [CẬP NHẬT] INSTALLER WINDOW (Chọn Máy + Game) ---
class InstallerWindow(tk.Toplevel):
    def __init__(self, parent, selected_game: Optional[dict]=None):
        super().__init__(parent)
        self.title("DEPLOY GAME SYSTEM - SERVER")
        self.geometry("600x450")
        self.configure(bg=COLOR_BG_DARK)
        self.transient(parent)
        self.grab_set()

        # Header
        tk.Label(self, text="TRÌNH CÀI ĐẶT GAME TỪ XA", bg=COLOR_BG_DARK, fg=COLOR_ACCENT, font=FONT_HEADER).pack(pady=15)

        # Chọn Game
        f1 = tk.Frame(self, bg=COLOR_BG_DARK); f1.pack(fill='x', padx=20)
        tk.Label(f1, text="Chọn Game:", bg=COLOR_BG_DARK, fg="white", width=15, anchor='w').pack(side='left')
        
        self.cbo_game = ttk.Combobox(f1, state="readonly", font=FONT_MAIN, width=40)
        self.cbo_game.pack(side='left', fill='x', expand=True)
        
        # Load danh sách game
        games = get_all_games()
        game_names = [g['name'] for g in games]
        self.cbo_game['values'] = game_names
        if selected_game: self.cbo_game.set(selected_game['name'])
        elif game_names: self.cbo_game.current(0)

        # Chọn Máy
        f2 = tk.Frame(self, bg=COLOR_BG_DARK); f2.pack(fill='x', padx=20, pady=10)
        tk.Label(f2, text="Chọn Máy Trạm:", bg=COLOR_BG_DARK, fg="white", width=15, anchor='w').pack(side='left')
        
        self.cbo_machine = ttk.Combobox(f2, state="readonly", font=FONT_MAIN, width=40)
        self.cbo_machine.pack(side='left', fill='x', expand=True)
        # Load danh sách máy (Giả lập hoặc lấy từ DB)
        # Để test, bạn có thể hardcode hoặc lấy từ get_all_machines()
        self.cbo_machine['values'] = ["Tất cả máy", "MAY01", "MAY02", "MAY03", "MAY04", "MAY05"]
        self.cbo_machine.current(1) # Mặc định MAY01

        # Progress Area
        self.progress_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        self.progress_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.lbl_status = tk.Label(self.progress_frame, text="Sẵn sàng deploy...", bg=COLOR_BG_DARK, fg="#888")
        self.lbl_status.pack(pady=5)
        
        self.pbar = ttk.Progressbar(self.progress_frame, mode='determinate', length=500)
        self.pbar.pack(pady=5)

        # Button
        btn = tk.Button(self, text="🚀 GỬI LỆNH CÀI ĐẶT", bg=COLOR_ACCENT, fg="black", font=FONT_BOLD, 
                        command=self._start_deploy, padx=20, pady=10)
        btn.pack(pady=20)

    def _start_deploy(self):
        game = self.cbo_game.get()
        machine = self.cbo_machine.get()
        
        if not game or not machine:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Game và Máy trạm!")
            return

        # Import hàm queue mới
        try:
            from database import queue_install_game
            
            if machine == "Tất cả máy":
                # Demo gửi cho MAY01 -> MAY05
                for i in range(1, 6):
                    queue_install_game(f"MAY0{i}", game)
            else:
                queue_install_game(machine, game)
                
            messagebox.showinfo("Thành công", f"Đã gửi lệnh cài đặt '{game}' xuống {machine}.\nMáy trạm sẽ tự động tải về.")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))