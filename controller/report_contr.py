# controller/report_controller.py
from model.report_model import ReportModel
from view.report_view import ReportView
from datetime import datetime

class ReportController:
    def __init__(self, main_frame):
        self.model = ReportModel()
        # Khởi tạo View và truyền chính nó (controller) vào View
        self.view = ReportView(main_frame, self)
        # Hiển thị View
        self.view.pack(fill='both', expand=True)

    def handle_generate_report(self, params):
        """
        Xử lý logic khi người dùng bấm nút 'Xem Báo Cáo'
        """
        try:
            # 1. Lấy và chuẩn hóa tham số
            start_date_str = params.get('start_date')
            end_date_str = params.get('end_date')
            report_type = params.get('report_type')

            # Validate ngày (đơn giản)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            # Thêm 23:59:59 cho ngày kết thúc để bao gồm cả ngày đó
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S') \
                if len(end_date_str) > 10 \
                else datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

        except ValueError as e:
            self.view.show_error(f"Định dạng ngày không hợp lệ. Yêu cầu: YYYY-MM-DD\nLỗi: {e}")
            return

        # 2. Gọi Model để lấy dữ liệu
        
        # Luôn lấy KPI
        kpi_data = self.model.get_kpi_summary(start_date, end_date)
        
        chart_data = []
        if report_type == 'Doanh thu theo ngày':
            chart_data = self.model.get_daily_revenue(start_date, end_date)
        
        # (Thêm logic cho các loại báo cáo khác ở đây)
        # elif report_type == 'Top Dịch vụ':
        #     chart_data = self.model.get_top_services(start_date, end_date)

        # 3. Cập nhật View với dữ liệu mới
        self.view.update_kpis(kpi_data)
        self.view.update_chart(chart_data, report_type)
        self.view.update_table(chart_data, report_type)