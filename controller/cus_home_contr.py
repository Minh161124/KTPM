from tkinter import messagebox
from view.cus_home import CustomerView
from model.cus_home_model import CustomerModel

PRICE_PER_HOUR = 5000  # 5000 VND / giờ

class CustomerController:
    def __init__(self, member_data):
        self.member_data = member_data
        self.model = CustomerModel()
        self.view = CustomerView()
        self.view.set_controller(self)
        
        # Biến lưu trữ thời gian thực
        self.total_seconds = 0
        self.is_running = True
        
        self.init_data()
        self.start_timer() # Bắt đầu đếm ngược ngay khi chạy

    def run(self):
        self.view.mainloop()

    def init_data(self):
        # 1. Lấy thông tin mới nhất
        info = self.model.get_member_info(self.member_data['id'])
        if info:
            self.member_data = info
            balance = float(info['balance'])
            
            # 2. Quy đổi Tiền -> Tổng số giây
            # Công thức: (Tiền / Giá 1 giờ) * 3600 giây
            self.total_seconds = int((balance / PRICE_PER_HOUR) * 3600)
            
            self.update_view_labels(balance)

        # Load menu
        menu = self.model.get_menu()
        self.view.render_menu(menu)

    def start_timer(self):
        """Hàm đếm ngược chạy mỗi 1 giây"""
        if self.is_running and self.total_seconds > 0:
            # 1. Trừ 1 giây
            self.total_seconds -= 1
            
            # 2. Tính lại tiền hiện tại dựa trên số giây còn lại
            # Công thức: (Giây / 3600) * Giá 1 giờ
            current_balance = (self.total_seconds / 3600) * PRICE_PER_HOUR
            
            # 3. Cập nhật giao diện
            self.update_view_labels(current_balance)
            
            # 4. Cập nhật vào CSDL (Tùy chọn: Để tránh lag, ta có thể chỉ update mỗi 1 phút)
            # Ở đây mình update mỗi 60 giây (khi số giây chia hết cho 60) để tối ưu
            if self.total_seconds % 60 == 0:
                self.model.update_balance_only(self.member_data['id'], current_balance)

            # 5. Hẹn giờ chạy lại hàm này sau 1000ms (1 giây)
            self.view.after(1000, self.start_timer)
            
        elif self.total_seconds <= 0:
            self.handle_out_of_time()

    def update_view_labels(self, balance):
        """Hàm phụ để format hiển thị"""
        # Format Giờ:Phút:Giây
        m, s = divmod(self.total_seconds, 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02}:{m:02}:{s:02}"
        
        self.view.update_info(
            name=self.member_data['ho_ten'],
            group=self.member_data['group_name'],
            balance=int(balance), # Hiển thị số nguyên cho đẹp
            time_str=time_str
        )

    def handle_out_of_time(self):
        """Xử lý khi hết giờ"""
        self.is_running = False
        self.model.update_balance_only(self.member_data['id'], 0) # Set tiền về 0
        self.view.update_info(self.member_data['ho_ten'], self.member_data['group_name'], 0, "00:00:00")
        messagebox.showwarning("Hết giờ", "Tài khoản của bạn đã hết tiền. Vui lòng nạp thêm!")
        self.view.destroy() # Hoặc khóa màn hình

    def handle_order(self, item):
        confirm = messagebox.askyesno("Xác nhận", f"Bạn muốn gọi {item['name']} ({item['price']:,}đ)?")
        if confirm:
            # Check nhanh xem đủ tiền không (tính theo giây hiện tại)
            current_balance = (self.total_seconds / 3600) * PRICE_PER_HOUR
            
            if current_balance >= item['price']:
                success = self.model.order_service(self.member_data['id'], item['name'], item['price'])
                if success:
                    messagebox.showinfo("Thành công", "Đã gọi món! Tiền và giờ chơi đã được trừ.")
                    # Trừ thẳng số giây tương ứng với giá tiền món ăn
                    deducted_seconds = int((item['price'] / PRICE_PER_HOUR) * 3600)
                    self.total_seconds -= deducted_seconds
                    
                    # Cập nhật ngay lập tức
                    new_balance = current_balance - item['price']
                    self.update_view_labels(new_balance)
            else:
                messagebox.showerror("Thất bại", "Số dư không đủ!")

    def handle_logout(self):
        confirm = messagebox.askyesno("Đăng xuất", "Bạn muốn đăng xuất và lưu số dư?")
        if confirm:
            self.is_running = False
            # Lưu số tiền chính xác còn lại vào DB trước khi thoát
            final_balance = (self.total_seconds / 3600) * PRICE_PER_HOUR
            self.model.update_balance_only(self.member_data['id'], final_balance)
            self.view.destroy()