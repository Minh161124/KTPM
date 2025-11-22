# controller/cust_contr.py
import tkinter as tk
from tkinter import messagebox
from model.cust_model import CustomerModel
from view.cust_view_list import CustomerListPage
from view.cust_add import CustomerForm, TopUpDialog

class CustomerController:
    def __init__(self, main_frame):
        self.model = CustomerModel()
        self.view_form = None 
        self.view_list = CustomerListPage(main_frame, self)
        self.view_list.pack(fill='both', expand=True)
        self.view_list.trigger_refresh()

    def refresh_customers(self, search, limit, page):
        data, total = self.model.fetch_customers(search, limit, page)
        self.view_list.update_display(data, total)

    def show_add_form(self):
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift(); return
        self.view_form = CustomerForm(self.view_list, self)
        self.view_list.wait_window(self.view_form)

    def show_edit_form(self, customer_id):
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift(); return
        
        data = self.model.get_customer_by_id(customer_id)
        if data:
            self.view_form = CustomerForm(self.view_list, self, customer_id)
            self.view_form.load_data(data)
            self.view_list.wait_window(self.view_form)

    def show_topup_dialog(self, row_data):
        # row_data: list values from table row
        TopUpDialog(self.view_list, self, row_data)

    def save_customer(self, data, customer_id):
        success, message = self.model.save_customer(data, customer_id)
        if success:
            messagebox.showinfo("Thành công", message)
            if self.view_form: self.view_form.destroy()
            self.view_list.trigger_refresh()
        else:
            messagebox.showerror("Lỗi", message)

    def process_top_up(self, customer_id, amount, dialog_ref):
        success, msg = self.model.top_up_money(customer_id, amount)
        if success:
            messagebox.showinfo("Thành công", f"Đã nạp {amount:,.0f}đ vào tài khoản.\n{msg}")
            dialog_ref.destroy()
            self.view_list.trigger_refresh()
        else:
            messagebox.showerror("Thất bại", msg)

    def delete_customer(self, customer_id):
        if self.model.delete_customer(customer_id):
            messagebox.showinfo("Đã xóa", "Xóa hội viên thành công.")
            self.view_list.trigger_refresh()
        else:
            messagebox.showerror("Lỗi", "Không thể xóa hội viên này.")