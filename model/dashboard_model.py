import mysql.connector
from mysql.connector import Error

# Hàm kết nối (Nên tách ra dùng chung, nhưng để tiện thì mình viết lại ở đây)
def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="btl_ai"
        )
        if conn and conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Lỗi kết nối MySQL: {e}")
    return None

def get_dashboard_data():
    """Lấy dữ liệu thống kê cho Dashboard"""
    conn = connect_db()
    # Giá trị mặc định nếu không kết nối được
    default_data = {
        "active": 0, 
        "revenue": 0, 
        "maintenance": 0,
        "total_machines": 0
    }

    if not conn:
        return default_data

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Số máy đang bật (giả sử trạng thái khác 'Trống')
        cursor.execute("SELECT COUNT(*) AS active FROM maytinh WHERE trangthai != 'Trống'")
        active = cursor.fetchone()['active']

        # 2. Tổng doanh thu (từ bảng logs hoặc hoadon)
        cursor.execute("SELECT COALESCE(SUM(amount), 0) AS revenue FROM logs")
        revenue = cursor.fetchone()['revenue']

        # 3. Số máy bảo trì
        cursor.execute("SELECT COUNT(*) AS maintenance FROM maytinh WHERE trangthai = 'Bảo trì'")
        maintenance = cursor.fetchone()['maintenance']

        return {
            "active": active,
            "revenue": revenue,
            "maintenance": maintenance
        }
    except Error as e:
        print(f"Lỗi lấy dữ liệu dashboard: {e}")
        return default_data
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()