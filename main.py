import tkinter as tk
from tkinter import font as tkFont, messagebox
import mysql.connector
from trangchu import App
import database
from openpyxl import Workbook
from tkinter import messagebox
# Đảm bảo bảng database tồn tại
database.create_tables()
# main.py — thêm phần này (requires openpyxl)
from openpyxl import Workbook
from tkinter import messagebox

def export_users_to_excel(filename):
    """
    Xuất toàn bộ bảng users ra file Excel.
    Trả về True nếu thành công, False nếu không có dữ liệu hoặc lỗi.
    """
    try:
        conn = get_connection()
        if not conn:
            return False

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return False

        wb = Workbook()
        ws = wb.active
        ws.title = "Users"

        headers = list(rows[0].keys())
        ws.append(headers)

        for r in rows:
            ws.append([r.get(h) for h in headers])

        wb.save(filename)
        return True
    except Exception as e:
        # bạn có thể gọi messagebox.showerror(...) nếu muốn hiển thị lỗi trong UI
        return False

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",     
            password="",         
            database="btl_ai"    
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Lỗi kết nối CSDL", f"Không thể kết nối MySQL:\n{err}")
        return None

# --- CHUYỂN MÀN HÌNH LOGIN THÀNH CLASS ---
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Đăng nhập hệ thống")
        self.geometry("800x650")
        self.configure(bg="black")
        self.resizable(False, False)
        
        # Biến kiểm tra đăng nhập thành công hay chưa
        self.login_success = False
        self.user_role = ""
        self.user_email = ""

        self._setup_ui()

    def _setup_ui(self):
        label_font = tkFont.Font(family="Arial", size=10, weight="bold")
        entry_font = tkFont.Font(family="Arial", size=12)
        logon_font = tkFont.Font(family="Arial", size=70, weight="bold")
        button_font = tkFont.Font(family="Arial", size=14, weight="bold")

        tk.Label(self, text="LOGIN", font=logon_font, fg="#E63950", bg="black").pack(pady=(160, 50))

        form_frame = tk.Frame(self, bg="black")
        form_frame.pack(pady=0, padx=200)

        # Email
        tk.Label(form_frame, text="GMAIL / PHONE NUMBER:", font=label_font,
                 fg="white", bg="black", anchor="w").pack(fill="x", pady=(0, 5))

        self.email_entry = tk.Entry(form_frame, font=entry_font, bg="#111", fg="white",
                                    insertbackground="white", relief="solid", borderwidth=1)
        self.email_entry.pack(fill="x", pady=(0, 20), ipady=5)

        # Password
        tk.Label(form_frame, text="PASSWORD:", font=label_font,
                 fg="white", bg="black", anchor="w").pack(fill="x", pady=(0, 5))

        self.password_entry = tk.Entry(form_frame, font=entry_font, show="*", bg="#111", fg="white",
                                       insertbackground="white", relief="solid", borderwidth=1)
        self.password_entry.pack(fill="x", pady=(0, 10), ipady=5)
        
        # Bind phím Enter để đăng nhập
        self.password_entry.bind('<Return>', lambda event: self.handle_login())

        # Options
        options_frame = tk.Frame(form_frame, bg="black")
        options_frame.pack(fill="x", pady=5)

        self.save_var = tk.IntVar()
        tk.Checkbutton(options_frame, text="Save password", variable=self.save_var,
                       onvalue=1, offvalue=0, font=label_font, fg="white",
                       bg="black", selectcolor="black").pack(side="left")

        forgot_label = tk.Label(options_frame, text="Forgot password", font=label_font,
                                fg="#8A8AFF", bg="black", cursor="hand2")
        forgot_label.pack(side="right")
        forgot_label.bind("<Button-1>", self.handle_forgot_password)

        # Button
        tk.Button(self, text="LOGIN", font=button_font,
                  fg="white", bg="#D60000", activebackground="#A00000",
                  activeforeground="white", relief="flat", borderwidth=0,
                  pady=5, command=self.handle_login
                  ).pack(pady=30, ipadx=40, ipady=4)

    def handle_forgot_password(self, event):
        messagebox.showinfo("Thông báo", "Chức năng đang được phát triển!", parent=self)

    def handle_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        if email == "" or password == "":
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Email và Mật khẩu!", parent=self)
            return

        conn = get_connection()
        if not conn:
            return 

        cursor = conn.cursor(dictionary=True)
        # Lưu ý: Cần đảm bảo bảng users có cột 'email' và 'password'
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Đăng nhập thành công
            self.login_success = True
            self.user_role = user['role']
            self.user_email = user['email']
            messagebox.showinfo("Thành công", f"Xin chào {user['email']} ({user['role']})", parent=self)
            
            # Chỉ đóng cửa sổ Login, KHÔNG mở App ở đây
            self.destroy()
        else:
            messagebox.showerror("Lỗi", "Email hoặc mật khẩu không đúng!", parent=self)

# --- VÒNG LẶP ĐIỀU KHIỂN CHÍNH ---
if __name__ == "__main__":
    while True:
        # 1. Chạy màn hình Login
        login_app = LoginWindow()
        login_app.mainloop()

        # 2. Kiểm tra kết quả sau khi màn hình Login đóng
        if login_app.login_success:
            # Nếu đăng nhập thành công -> Mở Trang Chủ (App)
            # Bạn có thể truyền thông tin user vào App nếu cần: main_app = App(user_email, user_role)
            main_app = App()
            main_app.mainloop()

            # 3. Kiểm tra lý do Trang Chủ đóng lại
            # Cần đảm bảo class App trong trangchu.py có thuộc tính self.is_logout
            if hasattr(main_app, 'is_logout') and main_app.is_logout:
                # Nếu người dùng bấm Logout -> Lặp lại vòng while -> Mở lại Login
                continue
            else:
                # Nếu người dùng bấm X thoát -> Thoát vòng lặp
                break
        else:
            # Nếu tắt form Login mà chưa đăng nhập -> Thoát luôn
            break
# --- main.py: Export nâng cao (nhiều sheet, style) ---

