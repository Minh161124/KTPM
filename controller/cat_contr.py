import tkinter as tk
from tkinter import messagebox
from model.cat_model import CategoryModel      
from view.cat_add import CategoryForm        
from view.cat_view_list import CategoryListPage 

 
class CategoryController:
    def __init__(self, main_frame):
        self.model = CategoryModel()
        self.view_form = None
        self.view_list = CategoryListPage(main_frame, self)
        self.view_list.pack(fill='both', expand=True)
        self.view_list.trigger_refresh()

    def refresh_categories(self, search, limit, page):
        """Xử lý yêu cầu làm mới từ view_list"""
        try:
            data, total_records = self.model.fetch_categories(search, limit, page)
            self.view_list.update_display(data, total_records)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách danh mục: {e}")

    def show_add_form(self):
        """Hiển thị form thêm mới"""
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift()
            return
            
        self.view_form = CategoryForm(self.view_list, self)
        self.view_list.wait_window(self.view_form)

    def show_edit_form(self, category_id):
        """Hiển thị form chỉnh sửa"""
        if self.view_form and self.view_form.winfo_exists():
            self.view_form.lift()
            return
            
        category_data = self.model.get_category_by_id(category_id)
        if not category_data:
            messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu danh mục.")
            return

        self.view_form = CategoryForm(self.view_list, self, category_id)
        self.view_form.load_data(category_data)
        self.view_list.wait_window(self.view_form)

    def save_category(self, data, category_id):
        """Xử lý yêu cầu lưu từ view_form"""
        
        success, message = self.model.save_category(data, category_id)
        
        if success:
            if self.view_form:
                self.view_form.show_info_and_close(message)
            self.view_list.trigger_refresh()
        else:
            if self.view_form:
                self.view_form.show_error(message) 

    def delete_category(self, category_id):
        """Xử lý yêu cầu xóa từ view_list"""
        success = self.model.delete_category(category_id)
        if success:
            messagebox.showinfo("Thành công", "Đã xóa danh mục.")
            self.view_list.trigger_refresh()
        else:
            messagebox.showerror("Thất bại", "Không thể xóa danh mục.\nCó thể danh mục này đang được sản phẩm sử dụng.")