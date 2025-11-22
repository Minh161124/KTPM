import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from model.shift_model import ShiftCreateModel
from view.shift_view import ShiftCreateView
from view.shift_add_item import ShiftAddItemForm
from session import CurrentUser

class ShiftCreateController:
    def __init__(self, main_frame):
        self.model = ShiftCreateModel()
        self.view = ShiftCreateView(main_frame, self)
        self.view.pack(fill='both', expand=True)
        
        self.current_shift_id = None
        
        # --- FIX 1: LOAD MENU TỪ SQL ---
        self.menu_items = self.model.get_menu_from_db()
        self.view.render_menu_items(self.menu_items)
        
        # Dữ liệu tính toán
        self.sum_products = 0
        self.sum_additions = 0
        self.sum_expenses = 0
        
        # --- FIX 2: KIỂM TRA CA CŨ (Để không bị reset khi đổi tab) ---
        self.check_existing_open_shift()

    def check_existing_open_shift(self):
        """Kiểm tra DB xem có ca nào chưa đóng không, nếu có thì load lại ngay"""
        existing_id = self.model.get_open_shift()
        if existing_id:
            self.current_shift_id = existing_id
            # Cập nhật giao diện sang trạng thái "Đang trong ca"
            self.view.update_status(True, str(self.current_shift_id))
            # Load lại bảng dữ liệu
            self.refresh_data()
        else:
            self.view.update_status(False, "")

    # ... (Các hàm format tiền giữ nguyên) ...
    def _format_currency(self, value):
        return f"{int(value):,}"

    def _parse_currency(self, value):
        try:
            return int(str(value).replace(',', '').replace('.', ''))
        except:
            return 0

    def create_shift(self):
        if self.current_shift_id: return

        shift_type = self.view.combo_ca.get()
        nhan_vien = CurrentUser.full_name if CurrentUser.full_name else "Admin (Unknown)"
        
        now_str = datetime.now().strftime("%Y-%m-%d")
        # Logic giờ đơn giản, bạn có thể giữ nguyên logic cũ của bạn
        tu_gio = f"{now_str} 06:00:00"
        den_gio = f"{now_str} 14:00:00"
        
        if "Chiều" in shift_type:
            tu_gio = f"{now_str} 14:00:00"
            den_gio = f"{now_str} 22:00:00"
        elif "Đêm" in shift_type:
            tu_gio = f"{now_str} 22:00:00"
            den_gio = f"{now_str} 06:00:00" 

        new_id = self.model.create_new_shift(tu_gio, den_gio, nhan_vien)
        if new_id:
            self.current_shift_id = new_id
            messagebox.showinfo("Thành công", f"Đã mở ca #{new_id}")
            self.view.update_status(True, str(new_id))
            self.refresh_data()
        else:
            messagebox.showerror("Lỗi", "Không thể tạo ca. Kiểm tra kết nối DB.")

    def refresh_data(self):
        if not self.current_shift_id: return

        # Lấy dữ liệu từ Model
        products, expenses, additions = self.model.get_shift_summary_data(self.current_shift_id)

        # Xóa bảng cũ
        self.view.clear_tree()

        self.sum_products = 0
        self.sum_expenses = 0
        self.sum_additions = 0

        # Fill Sản phẩm (products: id, san_pham, don_vi, khach, gia, thanh_tien)
        for p in products:
            row_total = p[5]
            self.sum_products += row_total
            # Hiển thị lên TreeView
            self.view.insert_tree_row(p[0], "Bán hàng", p[1], p[3], p[4], row_total, "product")

        # Fill Phụ thu
        for a in additions:
            self.sum_additions += a[3]
            self.view.insert_tree_row(a[0], "Phụ thu", a[1], 1, a[3], a[3], "addition")

        # Fill Chi phí
        for e in expenses:
            self.sum_expenses += e[3]
            self.view.insert_tree_row(e[0], "Chi phí", e[1], 1, e[3], e[3], "expense")

        # Update Labels Tổng
        self.view.lbl_doanh_thu.config(text=self._format_currency(self.sum_products))
        self.view.lbl_thu_khac.config(text=self._format_currency(self.sum_additions))
        self.view.lbl_chi_phi.config(text=self._format_currency(self.sum_expenses))
        
        must_have = (self.sum_products + self.sum_additions) - self.sum_expenses
        self.view.lbl_can_co.config(text=self._format_currency(must_have))
        
        self.update_summary_calc()

    def add_product_quick(self, item_data):
        """Xử lý khi bấm nút trên Menu (Fix 3: gọi hàm update mới trong model)"""
        if not self.current_shift_id:
            messagebox.showwarning("Chưa có ca", "Vui lòng BẮT ĐẦU CA trước khi bán hàng.")
            return

        qty = 1
        total = item_data['price'] * qty
        
        # Gọi hàm model mới (đã có logic cộng dồn)
        success, msg = self.model.add_shift_product(
            self.current_shift_id,
            item_data['name'],
            item_data['unit'],
            qty,
            item_data['price'],
            total
        )
        
        if success:
            self.refresh_data() # Load lại bảng để thấy số lượng tăng lên
        else:
            messagebox.showerror("Lỗi", msg)

    # ... (Các hàm show_add_form, save_manual_item, delete... giữ nguyên như bài trước) ...
    def show_add_form(self, table_type):
        if not self.current_shift_id:
             messagebox.showerror("Lỗi", "Vui lòng tạo ca trực trước.")
             return
        ShiftAddItemForm(
            parent=self.view.winfo_toplevel(), 
            controller=self, 
            table_type=table_type,
            on_save_callback=self.save_manual_item
        )

    def save_manual_item(self, table_type, data_tuple, item_id=None):
        success, msg = self.model.save_item(self.current_shift_id, table_type, data_tuple, item_id)
        if success:
            self.refresh_data()
        else:
            messagebox.showerror("Lỗi", msg)

    def on_tree_double_click(self, event):
        if not self.current_shift_id: return
        selected_item = self.view.tree.selection()
        if not selected_item: return
        
        vals = self.view.tree.item(selected_item, "values")
        item_id = vals[0]
        item_type_str = vals[1]
        
        if messagebox.askyesno("Xác nhận", "Bạn muốn xóa dòng này?"):
            if item_type_str == "Bán hàng":
                self.model.delete_shift_product(item_id)
            elif item_type_str == "Chi phí":
                self.model.delete_item('expenses', item_id)
            elif item_type_str == "Phụ thu":
                self.model.delete_item('additions', item_id)
            self.refresh_data()

    def update_summary_calc(self, event=None):
        try:
            real_cash = self._parse_currency(self.view.entry_thuc_dem.get())
            must_have = (self.sum_products + self.sum_additions) - self.sum_expenses
            diff = real_cash - must_have
            txt_color = "#2ed573" if diff >= 0 else "#ff4757"
            self.view.lbl_chenh_lech.config(text=f"Chênh lệch: {diff:,}", fg=txt_color)
        except: pass

    def close_shift(self):
        if not self.current_shift_id:
            return

        # 1. Tính toán số tiền hệ thống (Phải có)
        # Công thức: (Tiền hàng + Phụ thu) - Chi phí
        must_have = (self.sum_products + self.sum_additions) - self.sum_expenses
        
        # 2. Lấy số tiền thực tế nhân viên nhập (Thực đếm)
        try:
            real_cash = self._parse_currency(self.view.entry_thuc_dem.get())
        except:
            real_cash = 0
        
        # 3. Tính chênh lệch
        diff = real_cash - must_have
        diff_str = f"{diff:,}" if diff < 0 else f"+{diff:,}"

        # 4. Thông báo xác nhận
        msg = (
            f"XÁC NHẬN CHỐT CA #{self.current_shift_id}?\n"
            f"--------------------------------\n"
            f"- Hệ thống tính: \t{must_have:,} VNĐ\n"
            f"- Thực tế đếm: \t{real_cash:,} VNĐ\n"
            f"- Chênh lệch: \t{diff_str} VNĐ\n"
            f"--------------------------------\n"
            "Dữ liệu sẽ được lưu vào báo cáo và không thể sửa đổi."
        )

        if messagebox.askyesno("Xác nhận chốt ca", msg):
            # 5. GỌI MODEL ĐỂ LƯU VÀO SQL (Truyền đủ 4 tham số)
            success, message = self.model.close_current_shift(
                self.current_shift_id, 
                must_have,   # tong_he_thong
                real_cash,   # thuc_te
                diff         # chenh_lech
            )
            
            if success:
                messagebox.showinfo("Thành công", message)
                self._reset_ui_after_close() # Hàm phụ để reset giao diện (xem bên dưới)
            else:
                messagebox.showerror("Lỗi", message)

    def _reset_ui_after_close(self):
        """Hàm phụ để xóa trắng màn hình sau khi chốt"""
        self.current_shift_id = None
        self.view.update_status(False, "") 
        self.view.clear_tree()
        self.view.entry_thuc_dem.delete(0, 'end')
        self.view.entry_thuc_dem.insert(0, "0")
        
        # Reset biến tổng
        self.sum_products = 0
        self.sum_additions = 0
        self.sum_expenses = 0
        
        # Reset Labels
        self.view.lbl_doanh_thu.config(text="0")
        self.view.lbl_thu_khac.config(text="0")
        self.view.lbl_chi_phi.config(text="0")
        self.view.lbl_can_co.config(text="0")
        self.view.lbl_chenh_lech.config(text="Chênh lệch: 0", fg="#ffffff")