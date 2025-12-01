from tkinter import messagebox
from view.login_view import LoginView
from model.login_model import check_login, check_login_member 
from trangchu import App 
from view.cus_home import CustomerView 
from controller.cus_home_contr import CustomerController
from session import CurrentUser

class LoginController:
    def __init__(self):
        self.view = LoginView()
        self.view.set_controller(self)

    def run(self):
        self.view.mainloop()

    def handle_login(self, username, password, role):
        if not username or not password:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Tài khoản và Mật khẩu!")
            return

        # --- TRƯỜNG HỢP: NHÂN VIÊN ---
        if role == "employee":
            user = check_login(username, password)
            if user:
                u_id = user.get('id')
                u_tk = user.get('tai_khoan')
                u_ten = user.get('ho_ten')    
                u_role = user.get('chuc_vu')   

                CurrentUser.set_user(u_id, u_tk, u_ten, u_role)
                messagebox.showinfo("Thành công", f"Xin chào Nhân viên: {u_ten}!")
                
                self.view.destroy()
                dashboard = App(user_role=u_role, user_email=u_ten)
                dashboard.mainloop()
            else:
                messagebox.showerror("Lỗi", "Tài khoản nhân viên hoặc mật khẩu không đúng!")

        elif role == "customer":
            member = check_login_member(username, password)
            if member:
                if member.get('status') == 0:
                     messagebox.showwarning("Thông báo", "Tài khoản đã bị khóa!")
                     return

                messagebox.showinfo("Thành công", f"Xin chào: {member.get('ho_ten')}")
                
                self.view.destroy()
                
                # Gọi Controller của khách hàng (theo mô hình MVC)
                client_app = CustomerController(member_data=member)
                client_app.run()
            else:
                messagebox.showerror("Lỗi", "Sai tài khoản/mật khẩu hội viên!")