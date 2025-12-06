# revenue_manager.py
# Module: Quản lý Thu Chi (Cyber Style)
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

# Import Database
try:
    from database import (
        create_transaction_table, get_transactions, add_transaction_db, 
        delete_transaction_db, get_financial_summary
    )
except ImportError:
    # Mock data
    def create_transaction_table(): pass
    def get_transactions(limit=100): 
        return [
            {'id': 1, 'type': 'thu', 'category': 'Tiền giờ', 'amount': 500000, 'description': 'Ca sáng', 'created_at': '2023-10-27 12:00'},
            {'id': 2, 'type': 'chi', 'category': 'Nhập hàng', 'amount': 1200000, 'description': 'Nước ngọt, Mì tôm', 'created_at': '2023-10-27 14:00'},
            {'id': 3, 'type': 'thu', 'category': 'Dịch vụ', 'amount': 300000, 'description': 'Bán thẻ nạp', 'created_at': '2023-10-27 15:30'},
        ]
    def add_transaction_db(*args): pass
    def delete_transaction_db(*args): pass
    def get_financial_summary(): return {"total_in": 800000, "total_out": 1200000, "balance": -400000}

# --- Theme ---
COLOR_BG_DARK     = "#1e1e1e"
COLOR_BG_CARD     = "#2d2d2d"
COLOR_ACCENT      = "#00ff88"  # Xanh lá (Thu)
COLOR_RED         = "#ff4757"  # Đỏ (Chi)
COLOR_TEXT_MAIN   = "#ffffff"
COLOR_TEXT_SUB    = "#b0b0b0"
FONT_HEADER = ('Segoe UI', 16, 'bold')
FONT_VAL    = ('Segoe UI', 24, 'bold')
FONT_BODY   = ('Segoe UI', 10)

# ==========================================
# COMPONENT: STAT CARD
# ==========================================
class StatCard(tk.Frame):
    def __init__(self, parent, title, value, color, icon):
        super().__init__(parent, bg=COLOR_BG_CARD, padx=20, pady=15)
        self.configure(highlightbackground=color, highlightthickness=1)
        
        tk.Label(self, text=icon, bg=COLOR_BG_CARD, fg=color, font=("Arial", 24)).pack(side='left', padx=(0, 15))
        
        content = tk.Frame(self, bg=COLOR_BG_CARD)
        content.pack(side='left', fill='x')
        
        tk.Label(content, text=title.upper(), bg=COLOR_BG_CARD, fg=COLOR_TEXT_SUB, font=("Segoe UI", 9, "bold")).pack(anchor='w')
        self.lbl_val = tk.Label(content, text=value, bg=COLOR_BG_CARD, fg="white", font=FONT_VAL)
        self.lbl_val.pack(anchor='w')

    def update_value(self, new_val):
        self.lbl_val.config(text=new_val)

# ==========================================
# MAIN PAGE
# ==========================================
class RevenueManagerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG_DARK)
        create_transaction_table()
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 1. HEADER & STATS
        top_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        top_frame.pack(fill='x', padx=30, pady=20)
        
        tk.Label(top_frame, text="QUẢN LÝ THU CHI", font=FONT_HEADER, bg=COLOR_BG_DARK, fg="white").pack(anchor='w', pady=(0, 15))

        stats_grid = tk.Frame(top_frame, bg=COLOR_BG_DARK)
        stats_grid.pack(fill='x')
        
        self.card_in = StatCard(stats_grid, "Tổng Thu", "0 đ", COLOR_ACCENT, "💰")
        self.card_in.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.card_out = StatCard(stats_grid, "Tổng Chi", "0 đ", COLOR_RED, "💸")
        self.card_out.pack(side='left', fill='x', expand=True, padx=10)
        
        self.card_bal = StatCard(stats_grid, "Lợi Nhuận", "0 đ", "#2196F3", "📊")
        self.card_bal.pack(side='left', fill='x', expand=True, padx=(10, 0))

        # 2. TOOLBAR
        toolbar = tk.Frame(self, bg=COLOR_BG_DARK)
        toolbar.pack(fill='x', padx=30, pady=10)

        btn_style = {"font": ('Segoe UI', 10, 'bold'), "bd": 0, "padx": 20, "pady": 8, "cursor": "hand2"}
        
        tk.Button(toolbar, text="+ THU TIỀN", bg=COLOR_ACCENT, fg="black", command=lambda: self._open_editor('thu'), **btn_style).pack(side='left', padx=(0, 10))
        tk.Button(toolbar, text="- CHI TIỀN", bg=COLOR_RED, fg="white", command=lambda: self._open_editor('chi'), **btn_style).pack(side='left')
        
        tk.Button(toolbar, text="↻ Tải lại", bg="#444", fg="white", font=('Segoe UI', 10), bd=0, padx=15, pady=8, 
                  command=self._load_data).pack(side='right')

        # 3. DATA TABLE (TREEVIEW)
        table_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        table_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#252525", fieldbackground="#252525", foreground="white", rowheight=35, borderwidth=0, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", background="#333", foreground="white", font=('Segoe UI', 10, 'bold'), relief="flat")
        style.map("Treeview", background=[('selected', '#444')])

        cols = ("id", "time", "type", "cat", "desc", "amount")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="#")
        self.tree.heading("time", text="Thời gian")
        self.tree.heading("type", text="Loại")
        self.tree.heading("cat", text="Danh mục")
        self.tree.heading("desc", text="Mô tả")
        self.tree.heading("amount", text="Số tiền (VNĐ)")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("time", width=150, anchor="center")
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("cat", width=150)
        self.tree.column("desc", width=250)
        self.tree.column("amount", width=150, anchor="e")

        # Tags color
        self.tree.tag_configure('thu', foreground=COLOR_ACCENT)
        self.tree.tag_configure('chi', foreground=COLOR_RED)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        # Right click menu
        self.tree.bind("<Button-3>", self._show_menu)

    def _load_data(self):
        # Clear
        for i in self.tree.get_children(): self.tree.delete(i)
        
        # Load Stats
        summary = get_financial_summary()
        self.card_in.update_value(f"{summary['total_in']:,.0f} đ")
        self.card_out.update_value(f"{summary['total_out']:,.0f} đ")
        self.card_bal.update_value(f"{summary['balance']:,.0f} đ")
        
        # Load Table
        rows = get_transactions(limit=50)
        for r in rows:
            tag = 'thu' if r['type'] == 'thu' else 'chi'
            type_str = "THU" if r['type'] == 'thu' else "CHI"
            amt_str = f"{r['amount']:,.0f}"
            if r['type'] == 'thu': amt_str = f"+ {amt_str}"
            else: amt_str = f"- {amt_str}"
            
            self.tree.insert("", "end", values=(r['id'], r['created_at'], type_str, r['category'], r['description'], amt_str), tags=(tag,))

    def _open_editor(self, trans_type):
        TransactionEditor(self, trans_type)

    def _show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            m = tk.Menu(self, tearoff=0, bg="#333", fg="white")
            m.add_command(label="Xóa giao dịch", command=self._delete_item, foreground=COLOR_RED)
            m.tk_popup(event.x_root, event.y_root)

    def _delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        val = self.tree.item(sel[0], 'values')
        if messagebox.askyesno("Xóa", "Bạn chắc chắn muốn xóa giao dịch này?"):
            delete_transaction_db(val[0])
            self._load_data()

# ==========================================
# EDITOR POPUP
# ==========================================
class TransactionEditor(tk.Toplevel):
    def __init__(self, parent_page, trans_type):
        super().__init__(parent_page)
        self.parent_page = parent_page
        self.trans_type = trans_type
        
        title_text = "THÊM KHOẢN THU" if trans_type == 'thu' else "THÊM KHOẢN CHI"
        color = COLOR_ACCENT if trans_type == 'thu' else COLOR_RED
        
        self.title(title_text)
        self.geometry("400x400")
        self.configure(bg="#252525")
        self.transient(parent_page.winfo_toplevel())
        self.grab_set()
        try: self.geometry(f"+{parent_page.winfo_rootx() + 150}+{parent_page.winfo_rooty() + 80}")
        except: pass

        # UI
        tk.Label(self, text=title_text, font=("Segoe UI", 16, "bold"), bg="#252525", fg=color).pack(pady=20)
        f = tk.Frame(self, bg="#252525", padx=30); f.pack(fill='both', expand=True)
        
        def entry(lbl, r, is_combo=False, vals=[]):
            tk.Label(f, text=lbl, bg="#252525", fg="#AAA", font=FONT_BODY).grid(row=r, column=0, sticky='w', pady=8)
            if is_combo:
                e = ttk.Combobox(f, values=vals, font=FONT_BODY, state="readonly")
            else:
                e = tk.Entry(f, bg="#333", fg="white", insertbackground="white", relief="flat", font=FONT_BODY)
            e.grid(row=r, column=1, sticky='ew', ipady=5, padx=10)
            return e

        cats = ["Tiền giờ", "Dịch vụ", "Thẻ nạp", "Khác"] if trans_type == 'thu' else ["Nhập hàng", "Tiền điện/nước", "Lương NV", "Bảo trì", "Khác"]
        self.e_cat = entry("Danh mục:", 0, True, cats)
        self.e_cat.current(0)
        
        self.e_amount = entry("Số tiền (VNĐ):", 1)
        self.e_desc = entry("Mô tả:", 2)
        
        f.grid_columnconfigure(1, weight=1)
        
        tk.Button(self, text="XÁC NHẬN", bg=color, fg="black", font=("Segoe UI", 11, "bold"), bd=0, pady=8,
                  command=self._save).pack(fill='x', padx=30, pady=30)

    def _save(self):
        try:
            amt = int(self.e_amount.get())
            cat = self.e_cat.get()
            desc = self.e_desc.get()
            if amt <= 0: raise ValueError
            
            add_transaction_db(self.trans_type, cat, amt, desc)
            self.parent_page._load_data()
            self.destroy()
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền không hợp lệ!")

if __name__ == "__main__":
    root = tk.Tk(); root.geometry("1000x600"); root.configure(bg="#1e1e1e")
    RevenueManagerPage(root).pack(fill='both', expand=True)
    root.mainloop()