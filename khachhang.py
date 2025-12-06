import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Cố gắng import database, nếu lỗi thì không crash chương trình
try:
    import database as db
except ImportError:
    db = None

# --- MÀU SẮC GIAO DIỆN ---
COLOR_BG = "#1E1E2F"
COLOR_CARD = "#27293D"
COLOR_TEXT = "#FFFFFF"
COLOR_ACCENT = "#00F2C3" 
COLOR_BTN = "#1D8CF8"    
COLOR_DANGER = "#FF6B6B" 

class CustomerManagerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG)
        
        # --- 1. HEADER ---
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", pady=(10, 20))
        tk.Label(header, text="QUẢN LÝ KHÁCH HÀNG", fg=COLOR_TEXT, bg=COLOR_BG, 
                 font=("Segoe UI", 24, "bold")).pack(side="left", padx=20)

        # --- 2. TOOLBAR ---
        toolbar = tk.Frame(self, bg=COLOR_CARD, padx=10, pady=10)
        toolbar.pack(fill="x", padx=20)

        # Ô tìm kiếm
        tk.Label(toolbar, text="Tìm tên:", fg="#aaa", bg=COLOR_CARD, font=("Arial", 11)).pack(side="left")
        self.entry_search = tk.Entry(toolbar, bg="#1E1E2F", fg="white", insertbackground="white", font=("Arial", 11), relief="flat")
        self.entry_search.pack(side="left", padx=10, ipady=3)
        # Bắt sự kiện Enter để tìm
        self.entry_search.bind('<Return>', lambda e: self.load_data())
        
        tk.Button(toolbar, text="🔍 Tìm kiếm", bg=COLOR_BTN, fg="white", font=("Arial", 10, "bold"), relief="flat",
                  command=self.load_data).pack(side="left")

        # Các nút chức năng
        tk.Button(toolbar, text="🗑 Xóa", bg=COLOR_DANGER, fg="white", font=("Arial", 10, "bold"), relief="flat",
                  command=self.delete_member).pack(side="right", padx=5)
        
        tk.Button(toolbar, text="✏️ Sửa", bg="#34495E", fg="white", font=("Arial", 10, "bold"), relief="flat",
                  command=self.open_edit_dialog).pack(side="right", padx=5)

        tk.Button(toolbar, text="💵 Nạp Tiền", bg="#F1C40F", fg="black", font=("Arial", 10, "bold"), relief="flat",
                  command=self.top_up).pack(side="right", padx=5)

        tk.Button(toolbar, text="➕ Thêm Mới", bg=COLOR_ACCENT, fg="#0f172a", font=("Arial", 10, "bold"), relief="flat",
                  command=self.open_add_dialog).pack(side="right", padx=5)

        # --- 3. DANH SÁCH (TABLE) ---
        table_frame = tk.Frame(self, bg=COLOR_BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLOR_CARD, foreground="white", fieldbackground=COLOR_CARD, rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background="#1a1a2e", foreground="white", font=("Arial", 11, "bold"))
        style.map("Treeview", background=[('selected', COLOR_BTN)])

        columns = ("id", "username", "password", "balance", "created_at")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Tài khoản")
        self.tree.heading("password", text="Mật khẩu")
        self.tree.heading("balance", text="Số dư (VNĐ)")
        self.tree.heading("created_at", text="Ngày tạo")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("username", width=150)
        self.tree.column("password", width=100, anchor="center")
        self.tree.column("balance", width=150, anchor="e")
        self.tree.column("created_at", width=150, anchor="center")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Load dữ liệu
        self.load_data()

    # --- LOGIC XỬ LÝ ---
    def load_data(self):
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        keyword = self.entry_search.get().lower().strip()
        
        members = []
        if db:
            try:
                # Gọi hàm lấy danh sách từ database.py
                members = db.get_all_members()
            except Exception as e:
                print(f"Lỗi load data: {e}")
                # Không crash app, chỉ in lỗi ra console
        
        for m in members:
            # Lọc tìm kiếm
            if keyword and keyword not in m['username'].lower():
                continue
            
            self.tree.insert("", "end", values=(
                m['id'],
                m['username'],
                "******", 
                f"{m['balance']:,.0f}",
                m['created_at']
            ))

    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn khách hàng trong danh sách.")
            return None
        return self.tree.item(sel[0])['values']

    def open_add_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Thêm Hội Viên")
        dlg.geometry("350x300")
        dlg.configure(bg=COLOR_CARD)
        
        tk.Label(dlg, text="Tên đăng nhập:", fg="white", bg=COLOR_CARD).pack(anchor="w", padx=20, pady=(20,5))
        e_user = tk.Entry(dlg, font=("Arial", 11)); e_user.pack(fill="x", padx=20)
        
        tk.Label(dlg, text="Mật khẩu:", fg="white", bg=COLOR_CARD).pack(anchor="w", padx=20, pady=(10,5))
        e_pass = tk.Entry(dlg, show="*", font=("Arial", 11)); e_pass.pack(fill="x", padx=20)
        
        tk.Label(dlg, text="Tiền nạp ban đầu:", fg="white", bg=COLOR_CARD).pack(anchor="w", padx=20, pady=(10,5))
        e_bal = tk.Entry(dlg, font=("Arial", 11)); e_bal.insert(0, "0"); e_bal.pack(fill="x", padx=20)
        
        def save():
            u, p = e_user.get().strip(), e_pass.get().strip()
            try: b = float(e_bal.get())
            except: messagebox.showerror("Lỗi", "Tiền phải là số", parent=dlg); return
            
            if not u or not p: messagebox.showerror("Lỗi", "Thiếu thông tin", parent=dlg); return
            
            if db and db.add_member(u, p, b):
                messagebox.showinfo("OK", f"Đã thêm {u}", parent=dlg)
                self.load_data()
                dlg.destroy()
            else:
                messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại hoặc lỗi DB", parent=dlg)

        tk.Button(dlg, text="LƯU LẠI", bg=COLOR_ACCENT, fg="#0f172a", font=("Arial", 10, "bold"), command=save).pack(pady=20)

    def top_up(self):
        item = self.get_selected()
        if not item: return
        
        amount = simpledialog.askfloat("Nạp tiền", f"Nhập số tiền nạp cho {item[1]}:", minvalue=1000)
        if amount:
            if db and db.top_up_member(item[0], amount):
                try: db.add_transaction_db("thu", "Nạp tài khoản", amount, f"Nạp cho {item[1]}")
                except: pass
                messagebox.showinfo("Thành công", f"Đã nạp {amount:,.0f} đ cho {item[1]}")
                self.load_data()
            else:
                messagebox.showerror("Lỗi", "Lỗi kết nối CSDL")

    def open_edit_dialog(self):
        item = self.get_selected()
        if not item: return
        id_mem, old_user = item[0], item[1]
        
        dlg = tk.Toplevel(self)
        dlg.title(f"Sửa {old_user}")
        dlg.geometry("350x300")
        dlg.configure(bg=COLOR_CARD)
        
        tk.Label(dlg, text="Tên đăng nhập:", fg="white", bg=COLOR_CARD).pack(anchor="w", padx=20, pady=5)
        e_user = tk.Entry(dlg, font=("Arial", 11)); e_user.insert(0, old_user); e_user.pack(fill="x", padx=20)
        
        tk.Label(dlg, text="Mật khẩu mới (để trống nếu không đổi):", fg="white", bg=COLOR_CARD).pack(anchor="w", padx=20, pady=5)
        e_pass = tk.Entry(dlg, font=("Arial", 11)); e_pass.pack(fill="x", padx=20)
        
        tk.Label(dlg, text="Số dư:", fg="white", bg=COLOR_CARD).pack(anchor="w", padx=20, pady=5)
        e_bal = tk.Entry(dlg, font=("Arial", 11)); e_bal.insert(0, str(item[3]).replace(",", "")); e_bal.pack(fill="x", padx=20)
        
        def save():
            if db and db.update_member(id_mem, e_user.get(), e_pass.get(), float(e_bal.get())):
                self.load_data(); dlg.destroy(); messagebox.showinfo("OK", "Đã cập nhật")
            else:
                messagebox.showerror("Lỗi", "Cập nhật thất bại", parent=dlg)
        
        tk.Button(dlg, text="CẬP NHẬT", bg=COLOR_BTN, fg="white", font=("Arial", 10, "bold"), command=save).pack(pady=20)

    def delete_member(self):
        item = self.get_selected()
        if item and messagebox.askyesno("Xóa", f"Xóa tài khoản '{item[1]}'?"):
            if db and db.delete_member(item[0]):
                self.load_data()
                messagebox.showinfo("Đã xóa", "Thành công.")
            else:
                messagebox.showerror("Lỗi", "Xóa thất bại.")
