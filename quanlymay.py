import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import csv
import time
from datetime import datetime
import os
import json

# --- CHÈN THÊM: KẾT NỐI DATABASE ---
try:
    from database import (
        get_all_machines, update_machine_status, save_log, 
        insert_machine, get_machine_by_name,
        get_weblocklist, add_weblock_domain, remove_weblock_domain
    )
    # Hàm giả lập nếu DB chưa có add_weblog_entry (để tránh lỗi)
    def add_weblog_entry(url, result="allowed", note=""): return False
except ImportError:
    # Fallback (nếu không có DB, chúng ta vẫn vận hành cục bộ với backup file)
    def get_all_machines(): return []
    def update_machine_status(*args, **kwargs): return False
    def save_log(*args, **kwargs): return False
    def insert_machine(*args, **kwargs): return False
    def get_machine_by_name(*args, **kwargs): return None
    def get_weblocklist(): return []
    def add_weblock_domain(domain, note=""): return False
    def remove_weblock_domain(domain): return False
    def add_weblog_entry(url, result="allowed", note=""): return False

# ===== Theme constants =====
COLOR_BG_DARK = "#2a2a2a"
COLOR_BG_HEADER = "#1e1e1e"
COLOR_BG_CELL = "#2a2a2a"
COLOR_BG_INPUT = "#3c3c3c"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_ACCENT = "#00a859"
COLOR_RED = "#e74c3c"
COLOR_YELLOW = "#f39c12"
COLOR_BORDER = "#4a4a4a"

font_default = ('Segoe UI', 10)
font_bold = ('Segoe UI', 10, 'bold')
font_header = ('Segoe UI', 12, 'bold')

# ============================
# CẤU HÌNH MÁY - TỰ ĐẶT TÊN THEO LOẠI
# ============================
machine_setup = [
    ("Tiêu chuẩn", 20, "Màn hình: ASUS TUF Gaming VG249Q1A\nIntel Core i5-11400F\nSamsung 970 EVO Plus 500GB\nChuột: Logitech G102"),
    ("Gaming", 10, "Màn hình: LG 27GP850\nRyzen 5 5600X\nSamsung 980 Pro 1TB\nChuột: Razer DeathAdder"),
    ("Chuyên nghiệp", 5, "Màn hình: Dell U2720Q\nIntel Core i7-12700F\nWD Black SN850 1TB\nChuột: Logitech MX Master"),
    ("Thi đấu", 5, "Màn hình: Zowie XL2546K\nRyzen 7 5800X3D\nSamsung 990 Pro 1TB\nChuột: Zowie EC2")
]

prefix_map = {
    "Tiêu chuẩn": "T",
    "Gaming": "G",
    "Chuyên nghiệp": "C",
    "Thi đấu": "X"
}

# Backup file for local persistence (if DB unreachable)
BACKUP_FILE = "machines_backup.json"

# ---------------------------
# Helper: extract domain naively
# ---------------------------
def extract_domain(url):
    """Return lowercase domain part from URL-like string (naive)."""
    if not url: return ""
    u = url.lower().strip()
    if "://" in u: u = u.split("://", 1)[1]
    u = u.split("/", 1)[0]
    u = u.split(":", 1)[0]
    return u

# ---------------------------
# MAIN CLASS
# ---------------------------
class MachineManagerPage(tk.Frame):
    BLACKLIST_FILE = "weblocklist.txt"

    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG_DARK)
        # in-memory logs
        self.logs = []
        self._log_id_counter = 1

        # machines init
        self.machines = []
        db_machines = []
        try:
            db_machines = get_all_machines() or []
        except Exception as e:
            print("DEBUG: get_all_machines error:", e)
            db_machines = []

        if db_machines:
            # Assume db_machines is a list of dicts with required fields
            self.machines = db_machines
        else:
            # Try load backup if DB empty/unavailable
            backup = self._load_backup()
            if backup:
                self.machines = backup
            else:
                # create defaults
                counter = {"Tiêu chuẩn": 0, "Gaming": 0, "Chuyên nghiệp": 0, "Thi đấu": 0}
                for category, count, spec in machine_setup:
                    prefix = prefix_map.get(category, "M")
                    for i in range(count):
                        counter[category] += 1
                        name = f"{prefix}{counter[category]:02d}"
                        m = {
                            "name": name,
                            "state": "off",
                            "category": category,
                            "spec": spec,
                            "started_at": "--/--",
                            "used": "00:00:00",
                            "amount": 0,
                            "paused": False,
                            "pause_start": None,
                            "acc_paused_seconds": 0,
                            "custom_price": None
                        }
                        self.machines.append(m)
                        try:
                            insert_machine(name, category, spec, "off")
                        except Exception:
                            pass

        self.pricing = {"Tiêu chuẩn":100, "Gaming":150, "Chuyên nghiệp":200, "Thi đấu":250}
        self.selected_index = 0
        self.current_filter = "Tất cả"
        self.running_timers = {}

        # --- Web log / control state ---
        self.weblog = []  # each: {'time','url','domain','result','note'}
        self.weblog_enabled = False
        self.web_block_enabled = False
        # load blacklist from DB (fallback to file)
        self.weblocklist = self._load_blacklist()

        # build UI
        self._build_ui()

        # --- KHỞI PHỤC TIMER ---
        for idx, m in enumerate(self.machines):
            if m.get('state') == 'on' and m.get('started_at') and m.get('started_at') != '--/--':
                try:
                    datetime.strptime(m['started_at'], "%Y-%m-%d %H:%M:%S")
                    self._tick_time(idx)
                except Exception:
                    print(f"DEBUG: invalid started_at for {m['name']}: {m.get('started_at')}")
                    m['state'] = 'off'

        if self.machines:
            self.update_info(self.selected_index)

        # Bind destroy to persist state backup
        self.bind('<Destroy>', lambda e: self._save_backup())

    # ---------------------------
    # Backup persistence (local JSON)
    # ---------------------------
    def _load_backup(self):
        try:
            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list): return data
        except Exception as e:
            print('load backup error:', e)
        return None

    def _save_backup(self):
        try:
            with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.machines, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print('save backup error:', e)

    # ---------------------------
    # BLACKLIST persistence
    # ---------------------------
    def _load_blacklist(self):
        try:
            domains = get_weblocklist()
            if domains:
                return sorted(set([d.strip().lower() for d in domains if d and d.strip()]))
        except Exception as e:
            print("load blacklist from db error:", e)
        try:
            if os.path.exists(self.BLACKLIST_FILE):
                with open(self.BLACKLIST_FILE, "r", encoding="utf-8") as f:
                    lines = [l.strip().lower() for l in f.readlines() if l.strip()]
                    return sorted(set(lines))
        except Exception as e:
            print("load blacklist file fallback error:", e)
        return []

    def _save_blacklist_to_file(self):
        try:
            for d in sorted(set(self.weblocklist)):
                try: add_weblock_domain(d, note="saved_from_ui")
                except Exception: pass
        except Exception as e:
            print("persist blacklist to db error:", e)

        try:
            with open(self.BLACKLIST_FILE, "w", encoding="utf-8") as f:
                for d in sorted(set(self.weblocklist)): f.write(d + "\n")
        except Exception as e:
            print("save blacklist file error:", e)

        try: messagebox.showinfo("Đã lưu", "Danh sách chặn đã được lưu (DB + file backup).")
        except Exception: pass

    # ---------------------------
    # UI BUILD
    # ---------------------------
    def _build_ui(self):
        style = ttk.Style(self)
        try: style.theme_use('clam')
        except Exception: pass

        style.configure('Treeview', background=COLOR_BG_CELL, fieldbackground=COLOR_BG_INPUT, foreground=COLOR_TEXT_LIGHT, rowheight=26, font=font_default)
        style.configure('Treeview.Heading', background=COLOR_BG_HEADER, foreground=COLOR_TEXT_LIGHT, font=font_bold)
        style.map('Treeview', background=[('selected', COLOR_ACCENT)], foreground=[('selected', COLOR_TEXT_LIGHT)])

        toolbar = tk.Frame(self, bg=COLOR_BG_HEADER, padx=8, pady=6)
        toolbar.pack(fill='x')
        toolbar_buttons = [
            ('⚙', 'Cài đặt', None), ('📁', 'Máy trạm', None), ('💳', 'Tài khoản', None), ('📝', 'Nhật ký', None),
            ('🌐', 'Mở website', self._open_website_dialog), ('🗂', 'Nhật ký Website', self.open_weblog_window),
            ('🔒', 'Khống chế Website', self.open_web_control_dialog)
        ]
        for ico, text, cmd in toolbar_buttons:
            b = tk.Button(toolbar, text=f"{ico}  {text}", bg=COLOR_BG_HEADER, fg=COLOR_TEXT_LIGHT, font=font_default, relief='flat', activebackground=COLOR_BG_HEADER, command=cmd, cursor="hand2")
            b.pack(side='left', padx=(6,4))

        spacer = tk.Frame(toolbar, bg=COLOR_BG_HEADER)
        spacer.pack(side='left', expand=True)
        self.server_status = tk.Label(toolbar, text='Server: ■ Stopped', bg=COLOR_BG_HEADER, fg=COLOR_TEXT_LIGHT, font=('Segoe UI',9))
        self.server_status.pack(side='right', padx=6)
        self.weblog_status = tk.Label(toolbar, text='WebLog: disabled', bg=COLOR_BG_HEADER, fg=COLOR_TEXT_LIGHT, font=('Segoe UI',9))
        self.weblog_status.pack(side='right', padx=6)
        self.webblock_status = tk.Label(toolbar, text='Block: off', bg=COLOR_BG_HEADER, fg=COLOR_TEXT_LIGHT, font=('Segoe UI',9))
        self.webblock_status.pack(side='right', padx=6)

        action_row = tk.Frame(self, bg=COLOR_BG_CELL, pady=8)
        action_row.pack(fill='x')
        tk.Label(action_row, text="Tìm:", bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT, font=font_default).pack(side='left', padx=(12,4))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(action_row, textvariable=self.search_var, width=30, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, insertbackground=COLOR_TEXT_LIGHT, relief='flat', bd=1)
        search_entry.pack(side='left', padx=(0,8))
        tk.Button(action_row, text='Tìm', bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, relief='flat', command=self._do_search, cursor="hand2").pack(side='left')
        
        tk.Label(action_row, text='  Lọc:', bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=(8,0))
        self.filter_var = tk.StringVar(value='Tất cả')
        cb = ttk.Combobox(action_row, textvariable=self.filter_var, values=['Tất cả'] + list(self.pricing.keys()), state='readonly', width=18)
        cb.pack(side='left', padx=6)
        cb.bind('<<ComboboxSelected>>', lambda e: self.apply_filter(self.filter_var.get()))
        
        right_actions = tk.Frame(action_row, bg=COLOR_BG_CELL)
        right_actions.pack(side='right', padx=12)
        tk.Button(right_actions, text='Chỉnh giá', bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, relief='flat', command=self._open_pricing_dialog, cursor="hand2").pack(side='left', padx=6)
        tk.Button(right_actions, text='Export logs', bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, relief='flat', command=self.export_logs, cursor="hand2").pack(side='left', padx=6)
        tk.Button(right_actions, text='Reset hệ thống', bg=COLOR_RED, fg=COLOR_TEXT_LIGHT, relief='flat', command=self.reset_system, cursor="hand2").pack(side='left')

        sep = ttk.Separator(self, orient='horizontal')
        sep.pack(fill='x')

        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=12, pady=12)
        left = tk.Frame(paned, bg=COLOR_BG_DARK)
        paned.add(left, weight=3)

        columns = ("name","status","user","combo","start","used","remain","amount","date","group","note")
        self.tree = ttk.Treeview(left, columns=columns, show='headings', selectmode='browse')
        headings = {"name":"Tên máy","status":"Tình trạng","user":"Tên người dùng","combo":"COMBO","start":"Bắt đầu","used":"Đã dùng","remain":"Còn lại","amount":"Số tiền","date":"Ngày","group":"Nhóm máy","note":"Ghi chú"}
        widths = {"name":90, "status":130, "user":150, "combo":70, "start":160, "used":90, "remain":90, "amount":110, "date":90, "group":100, "note":140}
        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths.get(c,80), anchor='center')

        vsb = ttk.Scrollbar(left, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(left, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        self.tree.pack(side='top', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        self._row_colors = { 'off':COLOR_BG_CELL, 'on':'#213445', 'maint':'#3b2a2a', 'lost':'#2b0d0d' }

        self.context_menu = tk.Menu(self, tearoff=0, bg=COLOR_BG_HEADER, fg=COLOR_TEXT_LIGHT)
        self.context_menu.add_command(label="Bật/Tắt", command=lambda: self.toggle_power(self.selected_index))
        self.context_menu.add_command(label="Bảo trì/Bỏ", command=lambda: self.toggle_maint(self.selected_index))
        self.context_menu.add_command(label="Tạm dừng/Resume", command=lambda: self.toggle_pause(self.selected_index))
        self.context_menu.add_command(label="Chuyển máy", command=lambda: self.open_move_dialog(self.selected_index))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Chỉnh sửa thông tin", command=lambda: self.open_edit_dialog(self.selected_index))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Thanh toán", command=lambda: self.pay_machine(self.selected_index))

        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<Button-3>', self._on_tree_right_click)
        self.tree.bind('<Double-1>', self._on_tree_double_click)

        right = tk.Frame(paned, bg=COLOR_BG_DARK, width=420)
        paned.add(right, weight=0)
        right.pack_propagate(False)
        
        header = tk.Label(right, text='THÔNG TIN MÁY', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_header)
        header.pack(anchor='nw', pady=(12,6), padx=12)

        content = tk.Frame(right, bg=COLOR_BG_DARK)
        content.pack(fill='both', expand=True, padx=12, pady=(0,12))

        spec_frame = tk.Frame(content, bg=COLOR_BG_DARK)
        spec_frame.pack(side='left', fill='both', expand=True)

        self.spec_text = tk.Text(spec_frame, wrap='word', height=20, width=40, bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT, bd=0, font=font_default, relief='flat', insertbackground=COLOR_TEXT_LIGHT)
        self.spec_text.pack(side='left', fill='both', expand=True)
        self.spec_text.insert('1.0', '')
        self.spec_text.config(state='disabled')

        spec_vsb = ttk.Scrollbar(spec_frame, orient='vertical', command=self.spec_text.yview)
        spec_vsb.pack(side='right', fill='y')
        self.spec_text.configure(yscrollcommand=spec_vsb.set)

        info_col = tk.Frame(content, bg=COLOR_BG_DARK, width=220)
        info_col.pack(side='right', anchor='n', padx=(12,0), fill='y')
        info_col.pack_propagate(False)

        tk.Label(info_col, text='Trạng thái:', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, anchor='w', font=font_bold).pack(fill='x', pady=(6,2))
        self.lbl_status = tk.Label(info_col, text='', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, anchor='w', font=font_default)
        self.lbl_status.pack(fill='x', pady=(0,6))

        tk.Label(info_col, text='Thời gian bắt đầu:', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, anchor='w', font=font_bold).pack(fill='x', pady=(6,2))
        self.lbl_start = tk.Label(info_col, text='', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, anchor='w', font=font_default)
        self.lbl_start.pack(fill='x', pady=(0,6))

        tk.Label(info_col, text='Đã dùng:', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, anchor='w', font=font_bold).pack(fill='x', pady=(6,2))
        self.lbl_used = tk.Label(info_col, text='', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, anchor='w', font=font_default)
        self.lbl_used.pack(fill='x', pady=(0,6))

        tk.Label(info_col, text='Tạm tính (VND):', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, anchor='w', font=font_bold).pack(fill='x', pady=(6,2))
        self.lbl_amount = tk.Label(info_col, text='', bg=COLOR_BG_DARK, fg=COLOR_ACCENT, anchor='w', font=font_bold)
        self.lbl_amount.pack(fill='x', pady=(0,6))

        legend = tk.Frame(right, bg=COLOR_BG_DARK)
        legend.pack(side='bottom', fill='x', pady=12, padx=12)
        for text, col in [("Mất kết nối", COLOR_RED),("Đang sử dụng","#4ea8ff"),("Sẵn sàng",COLOR_ACCENT)]:
            spot = tk.Canvas(legend, width=14, height=14, bg=COLOR_BG_DARK, highlightthickness=0)
            spot.create_rectangle(0,0,14,14, fill=col, outline=col)
            spot.pack(side='left', padx=(6,4))
            tk.Label(legend, text=text, bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT, font=font_default).pack(side='left', padx=(0,8))

        self._populate_tree()
        self._refresh_weblog_status_labels()

    # ---------------------------
    # WebLog & WebControl features
    # ---------------------------
    def _refresh_weblog_status_labels(self):
        self.weblog_status.config(text=f"WebLog: {'enabled' if self.weblog_enabled else 'disabled'}")
        self.webblock_status.config(text=f"Block: {'on' if self.web_block_enabled else 'off'}")

    def log_weblog_entry(self, url, result, note=""):
        entry = { "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "url": url, "domain": extract_domain(url), "result": result, "note": note }
        self.weblog.append(entry)
        return entry

    def open_website(self, url):
        if not url: return
        domain = extract_domain(url)
        blocked = False
        blocked_domain = None
        for bd in self.weblocklist:
            if domain == bd or domain.endswith("." + bd):
                blocked = True; blocked_domain = bd; break

        entry = self.log_weblog_entry(url, "blocked" if blocked else "allowed", note=(f"blocked by rule '{blocked_domain}'" if blocked else ""))
        try: add_weblog_entry(url, entry['result'], entry['note'])
        except Exception as e: print("Cannot write weblog to DB:", e)

        if self.web_block_enabled and blocked:
            messagebox.showwarning("Bị chặn", f"Truy cập {url} đã bị chặn bởi quy tắc khống chế.")
            return False
        else:
            messagebox.showinfo("Mở website", f"Giả lập mở {url} — (allowed).")
            return True

    def _open_website_dialog(self):
        url = simpledialog.askstring("Mở website", "Nhập URL hoặc domain (ví dụ: https://youtube.com hoặc youtube.com):")
        if not url: return
        if not self.weblog_enabled:
            if messagebox.askyesno("Ghi nhật ký", "Nhật ký website đang tắt. Bạn có muốn bật nhật ký cho lần thử này không?"):
                self.weblog_enabled = True; self._refresh_weblog_status_labels()
        self.open_website(url)
        if self.weblog_enabled:
            try:
                if hasattr(self, "_weblog_tree"): self._weblog_tree_insert(self.weblog[-1])
            except: pass

    def open_weblog_window(self):
        dlg = tk.Toplevel(self)
        dlg.title("Nhật ký Website")
        dlg.geometry("820x420")
        top = tk.Frame(dlg, bg=COLOR_BG_DARK)
        top.pack(fill='x', padx=6, pady=6)
        self.weblog_enabled_var = tk.BooleanVar(value=self.weblog_enabled)
        ttk.Checkbutton(top, text="Bật ghi nhật ký", variable=self.weblog_enabled_var, command=lambda: self._toggle_weblog(dlg)).pack(side='left')
        ttk.Button(top, text="Export WebLog CSV", command=self.export_weblog).pack(side='right')

        columns = ("time","url","domain","result","note")
        tree = ttk.Treeview(dlg, columns=columns, show='headings')
        for c in columns:
            tree.heading(c, text=c.capitalize())
            tree.column(c, width=150 if c!="note" else 220, anchor='w')
        vsb = ttk.Scrollbar(dlg, orient='vertical', command=tree.yview)
        tree.configure(yscroll=vsb.set)
        tree.pack(fill='both', expand=True, side='left')
        vsb.pack(side='right', fill='y')
        self._weblog_tree = tree
        for e in self.weblog:
            tree.insert('', 'end', values=(e['time'], e['url'], e['domain'], e['result'], e['note']))

    def _weblog_tree_insert(self, entry):
        if hasattr(self, "_weblog_tree") and self._weblog_tree.winfo_exists():
            self._weblog_tree.insert('', 'end', values=(entry['time'], entry['url'], entry['domain'], entry['result'], entry['note']))

    def _toggle_weblog(self, dlg=None):
        self.weblog_enabled = bool(self.weblog_enabled_var.get())
        self._refresh_weblog_status_labels()

    def export_weblog(self):
        if not self.weblog:
            messagebox.showinfo("Export WebLog", "Không có dữ liệu nhật ký website để xuất.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path: return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["time","url","domain","result","note"])
                for e in self.weblog: writer.writerow([e['time'], e['url'], e['domain'], e['result'], e['note']])
            messagebox.showinfo("Export WebLog", f"Đã xuất {len(self.weblog)} dòng ra {path}")
        except Exception as ex:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {ex}")

    def open_web_control_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Khống chế Website (Blacklist)")
        dlg.geometry("480x420")
        top = tk.Frame(dlg, bg=COLOR_BG_DARK)
        top.pack(fill='x', padx=8, pady=8)
        self.web_block_var = tk.BooleanVar(value=self.web_block_enabled)
        ttk.Checkbutton(top, text="Bật chế độ chặn (Block)", variable=self.web_block_var, command=self._toggle_block_mode).pack(side='left')
        ttk.Button(top, text="Lưu danh sách", command=self._save_blacklist_to_file).pack(side='right')

        frm = tk.Frame(dlg, bg=COLOR_BG_DARK)
        frm.pack(fill='both', expand=True, padx=8, pady=6)
        lb = tk.Listbox(frm, activestyle='none', bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT)
        lb.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(frm, orient='vertical', command=lb.yview)
        lb.configure(yscroll=sb.set)
        sb.pack(side='left', fill='y', padx=(4,0))

        for d in self.weblocklist: lb.insert('end', d)

        ctrl = tk.Frame(dlg, bg=COLOR_BG_DARK)
        ctrl.pack(fill='x', padx=8, pady=6)
        self.new_domain_var = tk.StringVar()
        tk.Entry(ctrl, textvariable=self.new_domain_var, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT).pack(side='left', fill='x', expand=True, padx=(0,6))
        def add_domain():
            v = self.new_domain_var.get().strip().lower()
            if not v: return
            v = v.split("://")[-1].split("/",1)[0].split(":",1)[0]
            if v in self.weblocklist:
                messagebox.showinfo("Đã có", "Domain đã có trong danh sách.")
                return
            ok = False
            try: ok = add_weblock_domain(v, note="added_from_ui")
            except Exception as e: print("add_weblock_domain error:", e)
            self.weblocklist.append(v)
            self.weblocklist = sorted(set(self.weblocklist))
            lb.insert('end', v); self.new_domain_var.set("")
            if ok: messagebox.showinfo("Đã thêm", f"Đã thêm '{v}' vào danh sách chặn (CSDL).")
            else: messagebox.showwarning("Lưu ý", f"Đã thêm '{v}' cục bộ (DB không kết nối).")

        tk.Button(ctrl, text="Thêm", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, command=add_domain).pack(side='left', padx=(0,6))
        def remove_selected():
            sel = lb.curselection()
            if not sel: return
            idx = sel[0]; domain = lb.get(idx)
            if not messagebox.askyesno("Xóa", f"Xóa '{domain}' khỏi danh sách chặn?"): return
            ok = False
            try: ok = remove_weblock_domain(domain)
            except Exception as e: print("remove_weblock_domain error:", e)
            lb.delete(idx)
            try: self.weblocklist.remove(domain)
            except ValueError: pass
            self._save_blacklist_to_file()
            if ok: messagebox.showinfo("Đã xóa", f"Đã xóa '{domain}' khỏi CSDL.")
            else: messagebox.showwarning("Lưu ý", f"Đã xóa '{domain}' cục bộ (DB không kết nối).")

        tk.Button(ctrl, text="Xóa", bg=COLOR_RED, fg=COLOR_TEXT_LIGHT, command=remove_selected).pack(side='left')
        tk.Label(dlg, text="Ghi chú: thêm domain như 'facebook.com' để chặn facebook và tất cả subdomain.", anchor='w', justify='left', bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).pack(fill='x', padx=8, pady=(4,8))

    def _toggle_block_mode(self):
        self.web_block_enabled = bool(self.web_block_var.get())
        self._refresh_weblog_status_labels()

    # ---------------------------
    # Existing machine UI logic
    # ---------------------------
    def _populate_tree(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for idx, m in enumerate(self.machines):
            if self.current_filter != 'Tất cả' and m['category'] != self.current_filter: continue
            values = (m['name'], self._format_state(m['state'], m.get('paused')), "", "", m['started_at'], m['used'], "", f"{m['amount']}", datetime.now().strftime('%d-%b'), "Mặc định", "")
            self.tree.insert('', 'end', iid=str(idx), values=values)
            color = self._row_colors.get(m['state'], COLOR_BG_CELL)
            try:
                self.tree.tag_configure(str(idx), background=color, foreground=COLOR_TEXT_LIGHT)
                self.tree.item(str(idx), tags=(str(idx),))
            except Exception: pass

    def _format_state(self, state, paused=False):
        text = {"on":"Đang sử dụng","off":"Chưa bật","maint":"Bảo trì", 'lost':'Mất kết nối'}.get(state, state)
        if paused: text += " (Tạm dừng)"
        return text

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        self.selected_index = idx
        self.update_info(idx)

    def _on_tree_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.selected_index = int(iid)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            except: pass
            finally: self.context_menu.grab_release()

    def _on_tree_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            idx = int(iid)
            self.toggle_power(idx)

    def _tick_time(self, idx):
        m = self.machines[idx]
        if m.get("state") != "on" or m.get('paused'): return
        try:
            start = datetime.strptime(m['started_at'], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delta = now - start
            total_sec = int(delta.total_seconds()) - int(m.get("acc_paused_seconds", 0) or 0)
            if total_sec < 0: total_sec = 0
            h, rem = divmod(total_sec, 3600)
            mi, s = divmod(rem, 60)
            m['used'] = f"{h:02d}:{mi:02d}:{s:02d}"
            mins = total_sec / 60
            price = self.pricing.get(m["category"], 100)
            m["amount"] = int(mins * price)
            if self.selected_index == idx: self.update_info(idx)
            self._update_tree_row(idx, m)
            if self.winfo_exists():
                self.running_timers[idx] = self.after(1000, lambda: self._tick_time(idx))
        except Exception as e: print("_tick_time error:", e)

    def _update_tree_row(self, idx, m):
        if not self.tree.exists(str(idx)): return
        vals = list(self.tree.item(str(idx), 'values'))
        vals[1] = self._format_state(m['state'], m.get('paused'))
        vals[4] = m['started_at']
        vals[5] = m['used']
        vals[7] = f"{m['amount']}"
        self.tree.item(str(idx), values=vals)
        color = self._row_colors.get(m['state'], COLOR_BG_CELL)
        try:
            self.tree.tag_configure(str(idx), background=color, foreground=COLOR_TEXT_LIGHT)
            self.tree.item(str(idx), tags=(str(idx),))
        except Exception: pass

    def select_machine(self, idx):
        self.selected_index = idx
        if self.tree.exists(str(idx)):
            self.tree.selection_set(str(idx))
        self.update_info(idx)

    def update_info(self, idx):
        m = self.machines[idx]
        self.spec_text.config(state='normal')
        self.spec_text.delete('1.0', 'end')
        spec_lines = f"Cấu hình {m['name']}:\n{m['spec']}"
        self.spec_text.insert('1.0', spec_lines)
        self.spec_text.config(state='disabled')
        state_text = {"on":"Đang bật","off":"Chưa bật","maint":"Bảo trì"}.get(m["state"], m["state"])
        if m.get("paused"): state_text += " (Tạm dừng)"
        self.lbl_status.config(text=state_text)
        self.lbl_start.config(text=m['started_at'])
        self.lbl_used.config(text=m['used'])
        try: self.lbl_amount.config(text=f"{m['amount']:,} VND")
        except Exception: self.lbl_amount.config(text=str(m.get('amount',0)) + ' VND')

    def toggle_power(self, idx):
        m = self.machines[idx]
        if m.get("state") == "maint":
            messagebox.showwarning("Thông báo", "Máy đang bảo trì, không thể bật/tắt.")
            return
        if m.get("state") == "on":
            m["state"] = "off"
            if idx in self.running_timers:
                try: self.after_cancel(self.running_timers[idx])
                except Exception: pass
                del self.running_timers[idx]
        else:
            m["state"] = "on"
            m["paused"] = False; m["pause_start"] = None; m["acc_paused_seconds"] = 0
            m["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            m["used"] = "00:00:00"; m["amount"] = 0
            if self.winfo_exists():
                self.running_timers[idx] = self.after(1000, lambda: self._tick_time(idx))

        # --- [UPDATE DB] ---
        try: update_machine_status(m['name'], m['state'], m['started_at'], m['used'], m['amount'])
        except Exception as e: print('update_machine_status error:', e)
        
        self._save_backup()
        self._update_tree_row(idx, m)
        self.update_info(idx)

    def toggle_maint(self, idx):
        m = self.machines[idx]
        if m.get("state") == "on":
            messagebox.showinfo("Lưu ý", "Máy đang bật, hãy tắt trước khi bảo trì.")
            return
        m["state"] = "off" if m.get("state") == "maint" else "maint"
        try: update_machine_status(m['name'], m['state'], m['started_at'], m['used'], m['amount'])
        except Exception as e: print('update_machine_status error:', e)
        self._save_backup()
        self._update_tree_row(idx, m)
        self.update_info(idx)

    def toggle_pause(self, idx):
        m = self.machines[idx]
        if m.get("state") != "on":
            messagebox.showinfo("Thông báo", "Chỉ có thể pause khi máy đang bật.")
            return
        if not m.get("paused"):
            m["paused"] = True; m["pause_start"] = time.time()
            if idx in self.running_timers:
                try: self.after_cancel(self.running_timers[idx])
                except Exception: pass
                del self.running_timers[idx]
        else:
            paused_seconds = int(time.time() - (m.get("pause_start") or time.time()))
            m["acc_paused_seconds"] = int(m.get("acc_paused_seconds", 0) or 0) + paused_seconds
            m["pause_start"] = None; m["paused"] = False
            if self.winfo_exists():
                self.running_timers[idx] = self.after(1000, lambda: self._tick_time(idx))
        try: update_machine_status(m['name'], m['state'], m['started_at'], m['used'], m['amount'])
        except Exception as e: print('update_machine_status error:', e)
        self._save_backup()
        self._update_tree_row(idx, m)
        self.update_info(idx)

    def pay_machine(self, idx):
        m = self.machines[idx]
        if m.get("state") != "on" and m.get("amount",0) == 0:
            messagebox.showinfo("Thanh toán", "Không có gì để thanh toán.")
            return
        confirm = messagebox.askyesno("Thanh toán", f"Đã thanh toán cho {m['name']} số tiền {m['amount']:,} VND. Xác nhận?")
        if not confirm: return

        start = m["started_at"] if m.get("started_at") != "--/--" else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_per_min = m.get("custom_price") if m.get("custom_price") else self.pricing.get(m["category"], 100)
        minutes = m.get("amount",0) / price_per_min if price_per_min else 0

        log = { "id": self._log_id_counter, "machine_name": m["name"], "category": m["category"],
                "start_time": start, "end_time": end, "minutes": round(minutes, 2), "amount": m["amount"] }
        self._log_id_counter += 1
        self.logs.append(log)
        messagebox.showinfo("Thành công", f"✅ Thanh toán thành công cho {m['name']}\nSố tiền: {m['amount']:,} VND")

        # --- [SAVE LOG & UPDATE DB] ---
        try: save_log(m["name"], m["category"], start, end, minutes, m["amount"])
        except Exception as e: print('save_log error:', e)

        if idx in self.running_timers:
            try: self.after_cancel(self.running_timers[idx])
            except Exception: pass
            del self.running_timers[idx]

        m["used"] = "00:00:00"; m["amount"] = 0; m["state"] = "off"; m["started_at"] = "--/--"
        m["paused"] = False; m["pause_start"] = None; m["acc_paused_seconds"] = 0

        try: update_machine_status(m['name'], 'off', '--/--', '00:00:00', 0)
        except Exception as e: print('update_machine_status error:', e)

        self._save_backup()
        self._update_tree_row(idx, m)
        self.update_info(idx)

    def apply_filter(self, category):
        self.current_filter = category
        self._populate_tree()

    def _do_search(self):
        q = (self.search_var.get() or "").strip().lower()
        self._populate_tree()
        if q:
            for idx, m in enumerate(self.machines):
                if q in m['name'].lower() or q in m['category'].lower() or q in m['state'].lower():
                    if self.tree.exists(str(idx)):
                        self.tree.selection_set(str(idx)); self.tree.see(str(idx)); self.update_info(idx)
                    break

    def _open_pricing_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Chỉnh giá theo category")
        dlg.configure(bg=COLOR_BG_DARK)
        entries = {}
        r = 0
        for cat, price in self.pricing.items():
            tk.Label(dlg, text=cat, bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).grid(row=r, column=0, padx=8, pady=6, sticky="w")
            v = tk.StringVar(value=str(price))
            tk.Entry(dlg, textvariable=v, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT).grid(row=r, column=1, padx=8, pady=6)
            entries[cat] = v; r += 1
        def save_prices():
            for cat, var in entries.items():
                try: p = int(var.get()); self.pricing[cat] = p
                except: messagebox.showerror("Lỗi", f"Giá cho {cat} không hợp lệ."); return
            messagebox.showinfo("OK", "Đã cập nhật giá."); dlg.destroy()
        tk.Button(dlg, text="Lưu", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, command=save_prices).grid(row=r, column=0, columnspan=2, pady=8)

    def open_edit_dialog(self, idx):
        m = self.machines[idx]
        dlg = tk.Toplevel(self)
        dlg.title(f"Chỉnh sửa {m['name']}")
        dlg.configure(bg=COLOR_BG_DARK)
        tk.Label(dlg, text="Tên máy:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).grid(row=0,column=0,sticky="w",padx=8,pady=6)
        name_v = tk.StringVar(value=m['name'])
        tk.Entry(dlg, textvariable=name_v, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT).grid(row=0,column=1,padx=8,pady=6)
        tk.Label(dlg, text="Category:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).grid(row=1,column=0,sticky="w",padx=8,pady=6)
        cat_v = tk.StringVar(value=m['category'])
        tk.Entry(dlg, textvariable=cat_v, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT).grid(row=1,column=1,padx=8,pady=6)
        tk.Label(dlg, text="Spec:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).grid(row=2,column=0,sticky="w",padx=8,pady=6)
        spec_v = tk.StringVar(value=m['spec'])
        tk.Entry(dlg, textvariable=spec_v, width=50, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT).grid(row=2,column=1,padx=8,pady=6)
        tk.Label(dlg, text="Giá / phút tùy máy:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).grid(row=3,column=0,columnspan=2,sticky="w",padx=8,pady=6)
        custom_v = tk.StringVar(value=str(m.get("custom_price") or ""))
        tk.Entry(dlg, textvariable=custom_v, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT).grid(row=4,column=1,padx=8,pady=6)
        def save_edit():
            newname = name_v.get().strip()
            if not newname: messagebox.showerror("Lỗi", "Tên không được để trống."); return
            m['name'] = newname; m['category'] = cat_v.get().strip(); m['spec'] = spec_v.get()
            try: cp = int(custom_v.get()) if custom_v.get().strip() else None
            except: messagebox.showerror("Lỗi", "Giá không hợp lệ."); return
            m['custom_price'] = cp
            messagebox.showinfo("OK", "Đã lưu thông tin máy."); dlg.destroy()
            self._populate_tree(); self.update_info(idx)
            try: update_machine_status(m['name'], m['state'], m['started_at'], m['used'], m['amount'])
            except Exception as e: print('update_machine_status error:', e)
            self._save_backup()
        tk.Button(dlg, text="Lưu", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT, command=save_edit).grid(row=5, column=0, columnspan=2, pady=8)

    def open_move_dialog(self, idx):
        m = self.machines[idx]
        target = simpledialog.askstring("Chuyển máy", "Nhập tên máy muốn chuyển sang (ví dụ T05, G10):")
        if not target: return
        target = target.strip().upper()
        target_idx = None
        for i, mc in enumerate(self.machines):
            if mc['name'].upper() == target: target_idx = i; break
        if target_idx is None: messagebox.showerror("Lỗi", f"Không tìm thấy máy '{target}'."); return
        if target_idx == idx: messagebox.showinfo("Thông báo", "Máy đích phải khác máy hiện tại."); return
        m2 = self.machines[target_idx]
        if m2.get("state") == "on": messagebox.showwarning("Lỗi", "Máy đích đang bật – không thể chuyển."); return
        if m2.get("state") == "maint": messagebox.showwarning("Lỗi", "Máy đích đang bảo trì – không thể chuyển."); return
        if not messagebox.askyesno("Xác nhận", f"Chuyển phiên sử dụng từ {m['name']} sang {m2['name']}?"): return
        
        m2["state"] = m["state"]; m2["started_at"] = m["started_at"]; m2["used"] = m["used"]; m2["amount"] = m["amount"]
        m2["paused"] = m["paused"]; m2["pause_start"] = m["pause_start"]; m2["acc_paused_seconds"] = m["acc_paused_seconds"]
        m2["custom_price"] = m["custom_price"]
        
        m["state"] = "off"; m["started_at"] = "--/--"; m["used"] = "00:00:00"; m["amount"] = 0
        m["paused"] = False; m["pause_start"] = None; m["acc_paused_seconds"] = 0
        
        if idx in self.running_timers:
            try: self.after_cancel(self.running_timers[idx])
            except Exception: pass
            del self.running_timers[idx]
        if m2["state"] == "on":
            if self.winfo_exists(): self.running_timers[target_idx] = self.after(1000, lambda: self._tick_time(target_idx))

        try:
            update_machine_status(m['name'], 'off', '--/--', '00:00:00', 0)
            update_machine_status(m2['name'], 'on', m2['started_at'], m2['used'], m2['amount'])
        except Exception as e: print('update_machine_status error:', e)
        
        self._save_backup()
        self._populate_tree()
        self.update_info(target_idx); self.selected_index = target_idx
        messagebox.showinfo("Hoàn tất", f"Đã chuyển sang {m2['name']}.")

    def export_logs(self):
        if not self.logs: messagebox.showinfo("Export", "Không có dữ liệu log để xuất."); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path: return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id","machine_name","category","start_time","end_time","minutes","amount"])
            for item in self.logs:
                writer.writerow([item["id"], item["machine_name"], item["category"], item["start_time"], item["end_time"], item["minutes"], item["amount"]])
        messagebox.showinfo("Export", f"Đã xuất {len(self.logs)} dòng ra {path}")

    def reset_system(self):
        if not messagebox.askyesno("Xác nhận", "Bạn muốn reset hệ thống? (xóa logs và đặt tất cả máy về OFF)"): return
        for idx in list(self.running_timers.keys()):
            try: self.after_cancel(self.running_timers[idx])
            except Exception: pass
        self.running_timers.clear(); self.logs.clear(); self._log_id_counter = 1
        for m in self.machines:
            m["state"] = "off"; m["started_at"] = "--/--"; m["used"] = "00:00:00"; m["amount"] = 0
            m["paused"] = False; m["pause_start"] = None; m["acc_paused_seconds"] = 0
            try: update_machine_status(m['name'], 'off', '--/--', '00:00:00', 0)
            except Exception as e: print('update_machine_status error:', e)
        self._save_backup(); self._populate_tree(); self.update_info(0)
        messagebox.showinfo("Đã reset", "Hệ thống đã được reset. Tất cả máy ở trạng thái tắt.")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Machine Manager - Full Version")
    root.geometry("1280x820")
    app = MachineManagerPage(root)
    app.pack(fill="both", expand=True)
    root.mainloop()