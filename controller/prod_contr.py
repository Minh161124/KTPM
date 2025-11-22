
import tkinter as tk
from tkinter import messagebox
from model.prod_model import ProductModel     
from view.prod_add import ProductForm        
from view.prod_view_list import ProductListPage 
from model.cat_model import CategoryModel

 

class ProductController:
    def __init__(self, main_frame):
        self.model = ProductModel()
        self.cat_model_lookup = CategoryModel()
        self.view_form = None 
        self.view_list = ProductListPage(main_frame, self)
        self.view_list.pack(fill='both', expand=True)
      
        self.view_list.trigger_refresh()

    def refresh_products(self, search, limit, page):
        """Xử lý yêu cầu làm mới từ view_list"""
        try:
            data, total_records = self.model.fetch_products(search, limit, page)
            self.view_list.update_display(data, total_records)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách sản phẩm: {e}")

    def show_add_form(self):
        """Hiển thị form thêm mới"""
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift()
            return
            
        category_list = self.cat_model_lookup.get_all_categories_for_lookup()
        self.view_form = ProductForm(self.view_list, self, category_list)
        self.view_list.wait_window(self.view_form)

    def show_edit_form(self, product_id):
        """Hiển thị form chỉnh sửa"""
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift()
            return
            
        product_data = self.model.get_product_by_id(product_id)
        if not product_data:
            messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu sản phẩm.")
            return

        category_list = self.cat_model_lookup.get_all_categories_for_lookup()
        self.view_form = ProductForm(self.view_list, self, category_list, product_id)
        self.view_form.load_data(product_data)
        self.view_list.wait_window(self.view_form)

    def save_product(self, data, product_id):
        """Xử lý yêu cầu lưu từ view_form"""
        
        success, message = self.model.save_product(data, product_id)
        
        if success:
            if self.view_form:
                self.view_form.show_info_and_close(message)
            self.view_list.trigger_refresh()
        else:
            if self.view_form:
                self.view_form.show_error(message)

    def delete_product(self, product_id):
        """Xử lý yêu cầu xóa từ view_list"""
        success = self.model.delete_product(product_id)
        if success:
            messagebox.showinfo("Thành công", "Đã xóa sản phẩm.")
            self.view_list.trigger_refresh()
        else:
            messagebox.showerror("Thất bại", "Không thể xóa sản phẩm.")