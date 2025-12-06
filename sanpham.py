import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

# --- IMPORT MODULE DATABASE ---
# Đảm bảo bạn đã thêm hàm get_all_categories vào database.py như hướng dẫn trước
try:
    from database import get_all_products, add_product_db, update_product_db, delete_product_db, generate_next_product_code, get_all_categories
except ImportError:
    # Dummy function phòng hờ lỗi
    def get_all_products(k=""): return []
    def get_all_categories(): return [{"name": "Mặc định"}]
    def generate_next_product_code(): return "SP001"

# --- MÀU SẮC GIAO DIỆN ---
COLOR_BG_MAIN = "#1E1E2F"
COLOR_SIDEBAR = "#27293D"
COLOR_CARD_BG = "#27293D"
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_GRAY = "#9A9A9A"
COLOR_ACCENT_1 = "#E14ECA"
COLOR_ACCENT_2 = "#00F2C3"
COLOR_ACCENT_3 = "#1D8CF8"

class ProductController(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG_MAIN)
        self.pack(fill="both", expand=True)
        self.current_edit_code = None 

        self._setup_styles()
        self._create_header()
        self._create_toolbar()
        self._create_table()
        
        self.load_data()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Custom.Treeview", 
                             background=COLOR_CARD_BG, fieldbackground=COLOR_CARD_BG, 
                             foreground="white", rowheight=30, borderwidth=0)
        self.style.configure("Custom.Treeview.Heading", 
                             background="#2E2E3E", foreground=COLOR_ACCENT_3, 
                             font=("Arial", 10, "bold"), borderwidth=0)
        self.style.map("Custom.Treeview", 
                       background=[('selected', COLOR_ACCENT_3)], 
                       foreground=[('selected', 'white')])

    def _create_header(self):
        header = tk.Frame(self, bg=COLOR_BG_MAIN)
        header.pack(fill="x", padx=20, pady=(10, 0))
        tk.Label(header, text="KHO & SẢN PHẨM", font=("Helvetica", 18, "bold"), 
                 bg=COLOR_BG_MAIN, fg="white").pack(side="left")

    def _create_toolbar(self):
        toolbar = tk.Frame(self, bg=COLOR_BG_MAIN)
        toolbar.pack(fill="x", padx=20, pady=20)

        tk.Label(toolbar, text="Tìm kiếm:", bg=COLOR_BG_MAIN, fg=COLOR_TEXT_GRAY).pack(side="left", padx=(0, 10))
        self.entry_search = tk.Entry(toolbar, bg=COLOR_CARD_BG, fg="white", insertbackground="white", width=30, relief="flat")
        self.entry_search.pack(side="left", ipady=4)
        self.entry_search.bind("<KeyRelease>", self.on_search)

        btn_add = tk.Button(toolbar, text="+ Thêm Mới", bg=COLOR_ACCENT_2, fg="black", font=("Arial", 10, "bold"),
                            relief="flat", cursor="hand2", padx=15, pady=5, command=self.open_add_dialog)
        btn_add.pack(side="right")

        btn_refresh = tk.Button(toolbar, text="🔄 Tải lại", bg=COLOR_SIDEBAR, fg="white", 
                                relief="flat", cursor="hand2", padx=15, pady=5, command=self.load_data)
        btn_refresh.pack(side="right", padx=10)

    def _create_table(self):
        container = tk.Frame(self, bg=COLOR_CARD_BG)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cols = ("code", "name", "category", "price_in", "price_out", "stock")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", style="Custom.Treeview")
        
        headers = ["Mã SP", "Tên Sản Phẩm", "Danh Mục", "Giá Nhập", "Giá Bán", "Tồn Kho"]
        widths = [80, 250, 120, 120, 120, 100]
        
        for col, h, w in zip(cols, headers, widths):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=w, anchor="center" if col != "name" else "w")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def load_data(self, event=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        keyword = self.entry_search.get()
        
        # Gọi hàm từ database.py
        data = get_all_products(keyword)
        
        for row in data:
            self.tree.insert("", "end", values=(
                row['code'], row['name'], row['category'], 
                f"{int(row['price_in']):,}", f"{int(row['price_out']):,}", row['stock']
            ))

    def on_search(self, event):
        self.load_data()

    # --- DIALOG ---
    def open_add_dialog(self):
        self.current_edit_code = None
        next_code = generate_next_product_code()
        self._show_input_dialog("Thêm Sản Phẩm Mới", default_code=next_code)

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        vals = self.tree.item(item[0], 'values')
        
        data = {
            "code": vals[0], "name": vals[1], "category": vals[2],
            "price_in": vals[3].replace(",", ""), "price_out": vals[4].replace(",", ""), "stock": vals[5]
        }
        self.current_edit_code = data['code']
        self._show_input_dialog("Cập Nhật Sản Phẩm", data=data)

    def _show_input_dialog(self, title, data=None, default_code=""):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("400x550")
        dialog.configure(bg=COLOR_BG_MAIN)
        dialog.transient(self)
        dialog.grab_set()

        def create_field(lbl, val="", readonly=False):
            f = tk.Frame(dialog, bg=COLOR_BG_MAIN); f.pack(fill="x", padx=20, pady=10)
            tk.Label(f, text=lbl, bg=COLOR_BG_MAIN, fg=COLOR_TEXT_GRAY).pack(anchor="w")
            e = tk.Entry(f, bg=COLOR_SIDEBAR, fg="white", relief="flat")
            e.pack(fill="x", ipady=5, pady=(5,0))
            if val: e.insert(0, str(val))
            if readonly: e.config(state="readonly")
            return e

        code_val = data['code'] if data else default_code
        e_code = create_field("Mã SP (Tự động)", code_val, True)
        e_name = create_field("Tên sản phẩm", data['name'] if data else "")

        # --- [LIÊN KẾT DANH MỤC TẠI ĐÂY] ---
        f_cat = tk.Frame(dialog, bg=COLOR_BG_MAIN); f_cat.pack(fill="x", padx=20, pady=10)
        tk.Label(f_cat, text="Danh mục", bg=COLOR_BG_MAIN, fg=COLOR_TEXT_GRAY).pack(anchor="w")
        
        # 1. Lấy dữ liệu từ Database
        db_categories = get_all_categories() # Trả về list các dict: [{'name': 'A'}, {'name': 'B'}]
        # 2. Chỉ lấy tên để đưa vào combobox
        cat_values = [c['name'] for c in db_categories] if db_categories else ["Chưa có danh mục"]
        
        e_cat = ttk.Combobox(f_cat, values=cat_values, state="readonly")
        e_cat.pack(fill="x", ipady=5, pady=(5,0))
        
        # Chọn giá trị mặc định
        if data and data['category'] in cat_values:
            e_cat.set(data['category'])
        elif cat_values:
            e_cat.current(0)
        # -----------------------------------

        e_pin = create_field("Giá nhập", data['price_in'] if data else "0")
        e_pout = create_field("Giá bán", data['price_out'] if data else "0")
        e_stock = create_field("Tồn kho", data['stock'] if data else "0")

        def save():
            try:
                name = e_name.get()
                cat = e_cat.get()
                pin = float(e_pin.get()); pout = float(e_pout.get()); stk = int(e_stock.get())
                
                if not name: return messagebox.showerror("Lỗi", "Tên không được trống", parent=dialog)

                if self.current_edit_code:
                    res, msg = update_product_db(self.current_edit_code, name, cat, pin, pout, stk)
                else:
                    res, msg = add_product_db(e_code.get(), name, cat, pin, pout, stk)
                
                if res:
                    messagebox.showinfo("Thành công", msg, parent=dialog)
                    self.load_data()
                    dialog.destroy()
                else:
                    messagebox.showerror("Lỗi", msg, parent=dialog)
            except ValueError:
                messagebox.showerror("Lỗi", "Giá/Số lượng phải là số", parent=dialog)

        tk.Button(dialog, text="LƯU DỮ LIỆU", bg=COLOR_ACCENT_3, fg="white", font=("Arial", 11, "bold"),
                  relief="flat", command=save).pack(fill="x", padx=20, pady=30, ipady=8)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0, bg=COLOR_SIDEBAR, fg="white")
            menu.add_command(label="❌ Xóa", command=self.delete_product)
            menu.post(event.x_root, event.y_root)

    def delete_product(self):
        item = self.tree.selection()
        if not item: return
        vals = self.tree.item(item[0], 'values')
        if messagebox.askyesno("Xác nhận", f"Xóa '{vals[1]}'?"):
            if delete_product_db(vals[0]):
                messagebox.showinfo("Đã xóa", f"Đã xóa {vals[0]}")
                self.load_data()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x600")
    ProductController(root).pack(fill="both", expand=True)
    root.mainloop()