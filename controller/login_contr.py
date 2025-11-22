from tkinter import messagebox
from view.login_view import LoginView
from model.login_model import check_login
from trangchu import App 
from session import CurrentUser

class LoginController:
    def __init__(self):
        self.view = LoginView()
        self.view.set_controller(self)

    def run(self):
        self.view.mainloop()

    def handle_login(self, username, password):

        if not username or not password:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Tài khoản và Mật khẩu!")
            return

        user = check_login(username, password)

        if user:

            u_id = user.get('id')
            u_tk = user.get('tai_khoan')
            u_ten = user.get('ho_ten')    
            u_role = user.get('chuc_vu')   

            CurrentUser.set_user(u_id, u_tk, u_ten, u_role)
            
            messagebox.showinfo("Thành công", f"Xin chào {u_ten}!\nChức vụ: {u_role}")

            self.view.destroy()

            dashboard = App(user_role=u_role, user_email=u_ten)
            dashboard.mainloop()
        else:
            messagebox.showerror("Lỗi", "Tài khoản hoặc mật khẩu không đúng!")