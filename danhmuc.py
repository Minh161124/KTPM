import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

# --- IMPORT KẾT NỐI TỪ FILE DATABASE CHUNG ---
try:
    from database import connect_db
except ImportError:
    # Hàm giả lập nếu chạy file này một mình mà thiếu database.py
    def connect_db():
        messagebox.showerror("Lỗi", "Không tìm thấy file database.py!")
        return None

# --- MÀU SẮC GIAO DIỆN (Midnight Blue Theme) ---
COLOR_BG_MAIN = "#1E1E2F"
COLOR_SIDEBAR = "#27293D"
COLOR_CARD_BG = "#27293D"
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_GRAY = "#9A9A9A"
COLOR_ACCENT_1 = "#E14ECA" # Pink
COLOR_ACCENT_2 = "#00F2C3" # Teal
COLOR_ACCENT_3 = "#1D8CF8" # Blue

class CategoryManagerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG_MAIN)
        self.pack(fill="both", expand=True)
        
        self.current_edit_id = None
        
        self._setup_styles()
        self._create_header()
        self._create_ui()
        
        # Tự động tải dữ liệu khi mở
        self.load_data()

    # --- SỬ DỤNG HÀM KẾT NỐI CHUNG ---
    def get_db_connection(self):
        conn = connect_db()
        if not conn:
            messagebox.showerror("Lỗi Database", "Không thể kết nối đến CSDL. Hãy kiểm tra file database.py")
        return conn

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Style cho bảng
        self.style.configure("Treeview", 
                             background=COLOR_CARD_BG, 
                             fieldbackground=COLOR_CARD_BG, 
                             foreground="white", 
                             rowheight=28, borderwidth=0)
        
        self.style.configure("Treeview.Heading", 
                             background="#2E2E3E", 
                             foreground=COLOR_ACCENT_2, 
                             font=("Arial", 10, "bold"), borderwidth=0)
        
        self.style.map("Treeview", 
                       background=[('selected', COLOR_ACCENT_3)], 
                       foreground=[('selected', 'white')])

    def _create_header(self):
        header = tk.Frame(self, bg=COLOR_BG_MAIN)
        header.pack(fill="x", padx=20, pady=15)
        
        tk.Label(header, text="QUẢN LÝ DANH MỤC", font=("Helvetica", 18, "bold"), 
                 bg=COLOR_BG_MAIN, fg="white").pack(side="left")
        
        tk.Button(header, text="🔄 Tải lại", bg=COLOR_SIDEBAR, fg="white", relief="flat", cursor="hand2",
                  command=self.load_data).pack(side="right", padx=5)

    def _create_ui(self):
        # Chia layout: Trái (Form nhập) - Phải (Bảng danh sách)
        main_frame = tk.Frame(self, bg=COLOR_BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- PANEL TRÁI: FORM NHẬP ---
        left_panel = tk.Frame(main_frame, bg=COLOR_CARD_BG, width=320)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="THÔNG TIN DANH MỤC", bg=COLOR_CARD_BG, fg=COLOR_ACCENT_1, 
                 font=("Arial", 12, "bold")).pack(pady=(20, 15))

        # Helper tạo ô nhập
        def create_input(label, var_name):
            tk.Label(left_panel, text=label, bg=COLOR_CARD_BG, fg=COLOR_TEXT_GRAY).pack(anchor="w", padx=15)
            entry = tk.Entry(left_panel, bg="#2E2E3E", fg="white", relief="flat", insertbackground="white")
            entry.pack(fill="x", padx=15, pady=(5, 15), ipady=5)
            return entry

        self.entry_code = create_input("Mã Danh Mục (VD: DOAN, NUOC):", "code")
        self.entry_name = create_input("Tên Hiển Thị (VD: Đồ ăn nhanh):", "name")
        self.entry_desc = create_input("Mô tả thêm:", "desc")

        # Buttons Panel
        btn_frame = tk.Frame(left_panel, bg=COLOR_CARD_BG)
        btn_frame.pack(fill="x", padx=15, pady=20)
        
        self.btn_save = tk.Button(btn_frame, text="💾 LƯU", bg=COLOR_ACCENT_3, fg="white", font=("Arial", 10, "bold"),
                                  relief="flat", cursor="hand2", command=self.save_category)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(btn_frame, text="🧹 MỚI", bg=COLOR_SIDEBAR, fg="white", relief="flat", cursor="hand2",
                  command=self.clear_form).pack(side="right", fill="x", expand=True, padx=(5, 0))

        tk.Label(left_panel, text="* Chuột phải vào bảng để Xóa", bg=COLOR_CARD_BG, fg="#555", font=("Arial", 9, "italic")).pack(side="bottom", pady=20)

        # --- PANEL PHẢI: BẢNG DỮ LIỆU ---
        right_panel = tk.Frame(main_frame, bg=COLOR_CARD_BG)
        right_panel.pack(side="right", fill="both", expand=True)

        cols = ("id", "code", "name", "desc")
        self.tree = ttk.Treeview(right_panel, columns=cols, show="headings", style="Treeview")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Mã DM")
        self.tree.heading("name", text="Tên Danh Mục")
        self.tree.heading("desc", text="Mô tả")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("code", width=100, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("desc", width=300)

        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind sự kiện
        self.tree.bind("<Double-1>", self.on_item_click) # Click đúp để sửa
        self.tree.bind("<Button-3>", self.show_context_menu) # Chuột phải để xóa

    # --- LOGIC XỬ LÝ ---
    def load_data(self):
        # Xóa dữ liệu cũ trên bảng
        for i in self.tree.get_children(): self.tree.delete(i)
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            
            # --- TỰ ĐỘNG TẠO BẢNG NẾU CHƯA CÓ (An toàn) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    description TEXT
                )
            """)
            # ------------------------------------

            cur.execute("SELECT id, code, name, description FROM categories ORDER BY id DESC")
            rows = cur.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
                
        except Error as e:
            messagebox.showerror("Lỗi SQL", str(e))
        finally:
            if conn.is_connected(): conn.close()

    def save_category(self):
        code = self.entry_code.get().strip()
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip()

        if not code or not name:
            messagebox.showwarning("Thiếu thông tin", "Mã và Tên danh mục không được để trống!")
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            if self.current_edit_id:
                # Update
                cur.execute("UPDATE categories SET code=%s, name=%s, description=%s WHERE id=%s", 
                            (code, name, desc, self.current_edit_id))
                msg = "Cập nhật thành công!"
            else:
                # Insert
                cur.execute("INSERT INTO categories (code, name, description) VALUES (%s, %s, %s)", 
                            (code, name, desc))
                msg = "Thêm mới thành công!"
            
            conn.commit()
            messagebox.showinfo("Thông báo", msg)
            self.clear_form()
            self.load_data()
            
        except mysql.connector.IntegrityError:
            messagebox.showerror("Lỗi", f"Mã danh mục '{code}' đã tồn tại! Vui lòng chọn mã khác.")
        except Error as e:
            messagebox.showerror("Lỗi SQL", str(e))
        finally:
            if conn.is_connected(): conn.close()

    def clear_form(self):
        self.entry_code.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.current_edit_id = None
        self.btn_save.config(text="💾 LƯU")
        self.entry_code.config(state="normal") # Mở khóa mã khi thêm mới

    def on_item_click(self, event):
        item = self.tree.selection()
        if not item: return
        vals = self.tree.item(item[0], 'values')
        
        self.current_edit_id = vals[0]
        
        self.entry_code.delete(0, tk.END); self.entry_code.insert(0, vals[1])
        self.entry_name.delete(0, tk.END); self.entry_name.insert(0, vals[2])
        self.entry_desc.delete(0, tk.END); self.entry_desc.insert(0, vals[3])
        
        self.btn_save.config(text="✏️ CẬP NHẬT")
        # Không cho sửa Mã khi đang Edit (để tránh lỗi hệ thống)
        self.entry_code.config(state="disabled") 

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0, bg=COLOR_SIDEBAR, fg="white")
            menu.add_command(label="❌ Xóa danh mục", command=self.delete_category)
            menu.post(event.x_root, event.y_root)

    def delete_category(self):
        item = self.tree.selection()
        if not item: return
        id_del = self.tree.item(item[0], 'values')[0]
        name_del = self.tree.item(item[0], 'values')[2]
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa danh mục '{name_del}'?\n(Các sản phẩm thuộc danh mục này có thể bị ảnh hưởng)"):
            conn = self.get_db_connection()
            if not conn: return
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM categories WHERE id=%s", (id_del,))
                conn.commit()
                messagebox.showinfo("Đã xóa", "Đã xóa danh mục thành công.")
                self.load_data()
                self.clear_form()
            except Error as e:
                messagebox.showerror("Lỗi", str(e))
            finally:
                if conn.is_connected(): conn.close()

if __name__ == "__main__":
    # Test chạy riêng
    root = tk.Tk()
    root.geometry("900x500")
    CategoryManagerPage(root).pack(fill="both", expand=True)
    root.mainloop()