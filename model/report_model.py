# model/report_model.py
from .db_connector import Database
from mysql.connector import Error

class ReportModel:
    def __init__(self):
        self.db_connector = Database()

    def get_kpi_summary(self, start_date, end_date):
        conn = self.db_connector.connect()
        if not conn:
            return {'revenue': 0, 'hours': 0, 'users': 0}

        cursor = conn.cursor()
        kpi_data = {'revenue': 0, 'hours': 0, 'users': 0}

        try:
            # 1. Tổng doanh thu
            query_revenue = """
                SELECT SUM(tong_tien) 
                FROM lich_su_su_dung 
                WHERE thoi_gian_ket_thuc BETWEEN %s AND %s
            """
            cursor.execute(query_revenue, (start_date, end_date))
            result = cursor.fetchone()
            kpi_data['revenue'] = result[0] if result[0] else 0

            # 2. Tổng giờ sử dụng
            query_hours = """
                SELECT SUM(TIMESTAMPDIFF(MINUTE, thoi_gian_bat_dau, thoi_gian_ket_thuc)) / 60
                FROM lich_su_su_dung 
                WHERE thoi_gian_ket_thuc BETWEEN %s AND %s
            """
            cursor.execute(query_hours, (start_date, end_date))
            result = cursor.fetchone()
            kpi_data['hours'] = result[0] if result[0] else 0

            # 3. Tổng khách (DISTINCT khách trong bảng customers)
            query_users = """
                SELECT COUNT(DISTINCT c.ma_kh)
                FROM customers c
                JOIN lich_su_su_dung l ON c.ma_kh = l.ma_khach_hang
                WHERE l.thoi_gian_ket_thuc BETWEEN %s AND %s
            """
            cursor.execute(query_users, (start_date, end_date))
            result = cursor.fetchone()
            kpi_data['users'] = result[0] if result[0] else 0

        except Error as e:
            print(f"Lỗi khi lấy KPI: {e}")
        finally:
            cursor.close()
            self.db_connector.disconnect()

        return kpi_data

    def get_daily_revenue(self, start_date, end_date):
        conn = self.db_connector.connect()
        if not conn:
            return []

        cursor = conn.cursor()
        results = []

        try:
            query = """
                SELECT DATE(thoi_gian_ket_thuc) AS Ngay, SUM(tong_tien) AS DoanhThu
                FROM lich_su_su_dung
                WHERE thoi_gian_ket_thuc BETWEEN %s AND %s
                GROUP BY Ngay
                ORDER BY Ngay ASC
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

        except Error as e:
            print(f"Lỗi khi lấy doanh thu theo ngày: {e}")
        finally:
            cursor.close()
            self.db_connector.disconnect()

        return results
