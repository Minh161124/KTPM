# view/report_view.py
import tkinter as tk
from tkinter import ttk, messagebox
# Giả định config.py tồn tại và có các hằng số màu sắc, font chữ
from config import * 
from datetime import datetime, timedelta

# Import thư viện vẽ biểu đồ
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Tùy chỉnh matplotlib cho giao diện tối (nếu cần)
plt.style.use('dark_background')
plt.rc('axes', edgecolor=COLOR_BORDER)
plt.rc('figure', facecolor=COLOR_BG_DARK)
plt.rc('text', color=COLOR_TEXT_LIGHT)
plt.rc('xtick', color=COLOR_TEXT_LIGHT)
plt.rc('ytick', color=COLOR_TEXT_LIGHT)


class ReportView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_DARK)
        self.controller = controller

        # --- 1. Header ---
        header_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        header_frame.pack(fill='x')
        tk.Label(header_frame, text="Trang chủ/ Báo cáo & Thống kê",  
                 fg=COLOR_TEXT_LIGHT, bg=COLOR_BG_DARK, font=font_header).pack(side='left')
        
        title_bar = tk.Frame(self, bg=COLOR_ACCENT)
        title_bar.pack(fill='x', pady=(10, 5))
        tk.Label(title_bar, text="Bảng điều khiển Thống kê", font=font_bold,  
                 bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=10, pady=5)

        # --- 2. Khung Bộ lọc (Filter) ---
        filter_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        filter_frame.pack(fill='x', pady=5, padx=10)

        # Ngày bắt đầu
        tk.Label(filter_frame, text="Từ ngày:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=(0, 5))
        self.start_date_entry = tk.Entry(filter_frame, width=12, font=font_default, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, relief='flat')
        self.start_date_entry.pack(side='left')
        
        # Ngày kết thúc
        tk.Label(filter_frame, text="Đến ngày:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=(10, 5))
        self.end_date_entry = tk.Entry(filter_frame, width=12, font=font_default, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_LIGHT, relief='flat')
        self.end_date_entry.pack(side='left')

        # Loại báo cáo
        tk.Label(filter_frame, text="Loại:", bg=COLOR_BG_DARK, fg=COLOR_TEXT_LIGHT).pack(side='left', padx=(10, 5))
        self.report_type_cb = ttk.Combobox(filter_frame, width=20, font=font_default, state="readonly")
        self.report_type_cb['values'] = ('Doanh thu theo ngày', 'Top Dịch vụ (Sắp ra mắt)')
        self.report_type_cb.current(0)
        self.report_type_cb.pack(side='left')
        
        # Nút Lọc
        tk.Button(filter_frame, text="📊 Xem Báo Cáo", bg=COLOR_ACCENT, fg=COLOR_TEXT_LIGHT,
                   font=font_bold, relief='flat', activebackground="#007a3c",
                   cursor="hand2", command=self._on_generate_report).pack(side='right', padx=5, ipady=2)

        # Nút lọc nhanh
        tk.Button(filter_frame, text="Hôm nay", bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT,
                   font=font_default, relief='flat',
                   cursor="hand2", command=lambda: self._set_quick_filter('today')).pack(side='right', padx=5)
        tk.Button(filter_frame, text="7 ngày qua", bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT,
                   font=font_default, relief='flat',
                   cursor="hand2", command=lambda: self._set_quick_filter('week')).pack(side='right', padx=5)

        kpi_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        kpi_frame.pack(fill='x', pady=10, padx=10, ipady=10)
        kpi_frame.grid_columnconfigure((0,1,2), weight=1) # 3 cột bằng nhau

        kpi_revenue_card, self.kpi_revenue = self._create_kpi_card(kpi_frame, "TỔNG DOANH THU", "0 VNĐ", COLOR_BLUE)
        kpi_revenue_card.grid(row=0, column=0, padx=10, sticky='ew') # <-- Grid cái THẺ
        
        kpi_hours_card, self.kpi_hours = self._create_kpi_card(kpi_frame, "TỔNG GIỜ SỬ DỤNG", "0 giờ", COLOR_YELLOW)
        kpi_hours_card.grid(row=0, column=1, padx=10, sticky='ew') # <-- Grid cái THẺ
        
        kpi_users_card, self.kpi_users = self._create_kpi_card(kpi_frame, "TỔNG KHÁCH", "0 người", COLOR_RED)
        kpi_users_card.grid(row=0, column=2, padx=10, sticky='ew') # <-- Grid cái THẺ

        # --- 4. Khung Hiển thị (Biểu đồ và Bảng) ---
        display_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        display_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Khung Biểu đồ (bên trái)
        self.chart_frame = tk.Frame(display_frame, bg=COLOR_BG_CELL)
        self.chart_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        tk.Label(self.chart_frame, text="Nơi hiển thị biểu đồ", bg=COLOR_BG_CELL, fg=COLOR_TEXT_DISABLED).pack(pady=20)

        self.table_frame = tk.Frame(display_frame, bg=COLOR_BG_CELL, width=300) 
        self.table_frame.pack(side='right', fill='y', expand=False)
        
        # Tiêu đề bảng
        tk.Label(self.table_frame, text="Chi tiết dữ liệu", font=font_bold, bg=COLOR_BG_HEADER, fg=COLOR_TEXT_LIGHT).pack(fill='x', pady=(0, 1))
        # Cây Treeview
        columns = ('col1', 'col2')
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=15)
        self.tree.heading('col1', text='Ngày')
        self.tree.heading('col2', text='Doanh Thu')
        self.tree.column('col1', width=120, anchor='w')
        self.tree.column('col2', width=180, anchor='e')
        self.tree.pack(fill='both', expand=True)

        # Set giá trị mặc định cho ngày
        self._set_quick_filter('today')
        # Tự động tải báo cáo lần đầu
        self.after(100, self._on_generate_report)


    def _create_kpi_card(self, parent, title, value, title_color):
        """Hàm trợ giúp tạo thẻ KPI"""
        frame = tk.Frame(parent, bg=COLOR_BG_CELL, relief='solid', bd=1, highlightbackground=title_color, highlightthickness=1)
        
        lbl_title = tk.Label(frame, text=title, font=font_bold, bg=title_color, fg=COLOR_TEXT_LIGHT)
        lbl_title.pack(fill='x', pady=(0, 1)) # pack bên trong thẻ
        
        lbl_value = tk.Label(frame, text=value, font=font_header, bg=COLOR_BG_CELL, fg=COLOR_TEXT_LIGHT, height=2)
        lbl_value.pack(pady=10) # pack bên trong thẻ
        
        # Trả về (cái_thẻ, nhãn_giá_trị)
        return frame, lbl_value

    def _set_quick_filter(self, period):
        """Đặt giá trị cho ô lọc ngày"""
        today = datetime.now()
        start_date = today
        
        if period == 'week':
            start_date = today - timedelta(days=6) # 7 ngày bao gồm hôm nay

        str_start = start_date.strftime("%Y-%m-%d")
        str_end = today.strftime("%Y-%m-%d") + " 23:59:59"

        self.start_date_entry.delete(0, 'end')
        self.start_date_entry.insert(0, str_start)
        self.end_date_entry.delete(0, 'end')
        self.end_date_entry.insert(0, str_end)

    def _on_generate_report(self):
        """Lấy tham số và yêu cầu Controller xử lý"""
        params = {
            "start_date": self.start_date_entry.get(),
            "end_date": self.end_date_entry.get(),
            "report_type": self.report_type_cb.get()
        }
        
        # Gọi controller
        self.controller.handle_generate_report(params)

    # --- Các hàm cập nhật giao diện (do Controller gọi) ---

    def update_kpis(self, kpi_data):
        """Cập nhật 3 thẻ KPI"""
        revenue_text = f"{kpi_data.get('revenue', 0):,.0f} VNĐ"
        hours_text = f"{kpi_data.get('hours', 0):,.1f} giờ"
        users_text = f"{kpi_data.get('users', 0):,} người"
        
        self.kpi_revenue.config(text=revenue_text)
        self.kpi_hours.config(text=hours_text)
        self.kpi_users.config(text=users_text)

    def update_chart(self, chart_data, report_type):
        """Vẽ lại biểu đồ"""
        # Xóa biểu đồ cũ
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        if not chart_data:
            tk.Label(self.chart_frame, text="Không có dữ liệu để vẽ biểu đồ", 
                     bg=COLOR_BG_CELL, fg=COLOR_TEXT_DISABLED).pack(pady=20)
            return

        fig = plt.Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        if report_type == 'Doanh thu theo ngày':

            dates = [item[0].strftime('%d/%m') if isinstance(item[0], datetime) else item[0] for item in chart_data]
            revenues = [item[1] for item in chart_data]

            ax.bar(dates, revenues, color=COLOR_ACCENT)
            ax.set_title('Biểu đồ Doanh thu theo ngày', color=COLOR_TEXT_LIGHT)
            ax.set_ylabel('Doanh thu (VNĐ)', color=COLOR_TEXT_LIGHT)
            fig.autofmt_xdate() 

        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_table(self, chart_data, report_type):
        """Cập nhật bảng dữ liệu chi tiết"""
        # Xóa dữ liệu cũ
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        if report_type == 'Doanh thu theo ngày':
            self.tree.heading('col1', text='Ngày')
            self.tree.heading('col2', text='Doanh Thu')
            
            if chart_data:
                for row in chart_data:
                    date_str = row[0].strftime('%Y-%m-%d') if isinstance(row[0], datetime) else row[0]
                    revenue_str = f"{row[1]:,.0f} VNĐ"
                    self.tree.insert("", "end", values=(date_str, revenue_str))

        # elif report_type == 'Top Dịch vụ':
        #     self.tree.heading('col1', text='Tên Dịch Vụ')
        #     self.tree.heading('col2', text='Số Lượng Bán')
        #     ... (code insert dữ liệu dịch vụ) ...

    def show_error(self, message):
        messagebox.showerror("Lỗi", message)