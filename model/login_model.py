import mysql.connector
from mysql.connector import Error

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

def check_login(username, password):
    conn = connect_db()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM employees WHERE tai_khoan = %s AND mat_khau = %s"
        
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Lỗi query: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_connection():
    """Hàm chung để kết nối CSDL"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="btl_ai"
        )
        return conn
    except Error as err:
        print(f"Lỗi kết nối: {err}")
        return None

def create_tables():
    """Tạo cấu trúc bảng nếu chưa có"""
    conn = get_connection()
    if not conn:
        print("Không thể kết nối để tạo bảng.")
        return

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100) UNIQUE,
            password VARCHAR(100),
            role VARCHAR(50) DEFAULT 'nhanvien'
        )
    """)

    cursor.execute("SELECT * FROM users WHERE email = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password, role) VALUES ('admin', '123', 'admin')")
        print("-> Đã tạo tài khoản admin/123")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maytinh (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50),
            category VARCHAR(50),
            trangthai VARCHAR(50) DEFAULT 'Trống',
            amount DOUBLE DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            machine_name VARCHAR(50),
            amount DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Kiểm tra cấu trúc CSDL hoàn tất.")
