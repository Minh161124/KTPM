from tkinter import messagebox
from view.cus_home import CustomerView
from model.cus_home_model import CustomerModel

PRICE_PER_HOUR = 5000 

class CustomerController:
    def __init__(self, member_data):
        self.member_data = member_data
        self.model = CustomerModel()
        self.view = CustomerView()
        self.view.set_controller(self)
        self.last_msg_id = 0

        self.total_seconds = 0
        self.is_running = True
        self.full_menu = [] 
        
        self.init_data()
        self.start_timer() 
        self.poll_chat()

    def run(self):
        self.view.mainloop()

    def init_data(self):
        # 1. Load Info
        self.refresh_member_info()

        # 2. Load Menu từ Database
        self.full_menu = self.model.get_menu_from_db()
        self.view.render_menu(self.full_menu)
        
        # 3. Load History
        self.load_history()

    def refresh_member_info(self):
        info = self.model.get_member_info(self.member_data['id'])
        if info:
            self.member_data = info
            balance = float(info['balance'])
            # Chỉ reset timer nếu đây là lần đầu hoặc cần đồng bộ lại
            if self.total_seconds == 0: 
                self.total_seconds = int((balance / PRICE_PER_HOUR) * 3600)
            self.update_view_labels(balance)

    def start_timer(self):
        if self.is_running and self.total_seconds > 0:
            self.total_seconds -= 1
            current_balance = (self.total_seconds / 3600) * PRICE_PER_HOUR
            self.update_view_labels(current_balance)
            
            # Sync DB mỗi 60s
            if self.total_seconds % 60 == 0:
                self.model.update_balance_only(self.member_data['id'], current_balance)

            self.view.after(1000, self.start_timer)
        elif self.total_seconds <= 0:
            self.handle_out_of_time()

    def update_view_labels(self, balance):
        m, s = divmod(self.total_seconds, 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02}:{m:02}:{s:02}"
        
        self.view.update_info(
            name=self.member_data['ho_ten'],
            group=self.member_data['group_name'],
            balance=int(balance),
            time_str=time_str
        )

    def filter_menu(self, category_code):
        if category_code == "ALL":
            self.view.render_menu(self.full_menu)
        else:
            # Lọc list theo ma_dm
            filtered = [item for item in self.full_menu if item['ma_dm'] == category_code]
            self.view.render_menu(filtered)

    def handle_order(self, item):
        confirm = messagebox.askyesno("Xác nhận", f"Bạn muốn gọi món:\n{item['ten_sp']}\nGiá: {item['gia']:,} đ?")
        if confirm:
            current_balance = (self.total_seconds / 3600) * PRICE_PER_HOUR

            result = self.model.order_service(self.member_data['id'], item['id'], item['ten_sp'], item['gia'])
            
            if result == "SUCCESS":
                messagebox.showinfo("Thành công", "Đã gọi món thành công! Chúc ngon miệng.")
                deducted_seconds = int((item['gia'] / PRICE_PER_HOUR) * 3600)
                self.total_seconds -= deducted_seconds
                self.full_menu = self.model.get_menu_from_db()
                self.filter_menu(self.view.filter_var.get()) 
                self.load_history() 

                sys_msg = f"Đã gọi món: {item['ten_sp']} ({item['gia']:,} đ)"
                self.model.send_chat_message(self.member_data['id'], sys_msg, 'SYSTEM')
                
            elif result == "NOT_ENOUGH_MONEY":
                messagebox.showerror("Thất bại", "Số dư không đủ để gọi món này!")
            elif result == "OUT_OF_STOCK":
                messagebox.showerror("Xin lỗi", "Món này vừa hết hàng!")
            else:
                messagebox.showerror("Lỗi", "Lỗi hệ thống, vui lòng thử lại.")

    def load_history(self):

        current_member_id = self.member_data['id']
        history = self.model.get_transaction_history(current_member_id)
        self.view.update_history_table(history)

    def handle_change_password(self):
        new_pass = self.view.ask_password_change()
        if new_pass:
            if len(new_pass) < 6:
                messagebox.showwarning("Yếu", "Mật khẩu phải dài hơn 6 ký tự")
                return
            
            success = self.model.change_password(self.member_data['id'], new_pass)
            if success:
                messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!")
            else:
                messagebox.showerror("Lỗi", "Không thể đổi mật khẩu lúc này.")

    def handle_out_of_time(self):
        self.is_running = False
        self.model.update_balance_only(self.member_data['id'], 0)
        self.view.update_info(self.member_data['ho_ten'], self.member_data['group_name'], 0, "00:00:00")
        messagebox.showwarning("Hết giờ", "Tài khoản của bạn đã hết tiền!")
        self.view.destroy()

    def handle_logout(self):
        confirm = messagebox.askyesno("Đăng xuất", "Bạn muốn đăng xuất?")
        if confirm:
            self.is_running = False
            final_balance = (self.total_seconds / 3600) * PRICE_PER_HOUR
            self.model.update_balance_only(self.member_data['id'], final_balance)
            self.view.destroy()

    def poll_chat(self):
        """Định kỳ kiểm tra tin nhắn mới mỗi 2 giây"""
        if not self.is_running: return

        new_msgs = self.model.get_new_messages(self.member_data['id'], self.last_msg_id)
        if new_msgs:
            for msg in new_msgs:
                self.view.append_message(msg['sender_type'], msg['message'])
                self.last_msg_id = max(self.last_msg_id, msg['id'])

        self.view.after(2000, self.poll_chat)

    def send_message(self):
        """Gửi tin nhắn từ Client"""
        msg = self.view.msg_entry.get().strip()
        if msg:
            success = self.model.send_chat_message(self.member_data['id'], msg, 'CLIENT')
            if success:
                self.view.clear_message_entry()