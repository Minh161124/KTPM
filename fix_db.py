import mysql.connector

# CẤU HÌNH KẾT NỐI (Nếu XAMPP có pass thì điền vào password="")
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  
    'database': 'btl_ai'
}

try:
    print("--- BẮT ĐẦU SỬA LỖI DATABASE ---")
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    
    # 1. Tạo bảng members (Khách hàng)
    print(">> Đang tạo bảng 'members'...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(50) NOT NULL,
            balance DOUBLE DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # 2. Tạo bảng transactions (Giao dịch) nếu thiếu
    print(">> Đang tạo bảng 'transactions'...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type VARCHAR(20),
            category VARCHAR(100),
            amount DOUBLE,
            amount_decimal DECIMAL(14,2),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 3. Thêm tài khoản mẫu để test
    print(">> Đang thêm tài khoản mẫu (khach01)...")
    try:
        cur.execute("INSERT INTO members (username, password, balance) VALUES ('khach01', '123', 50000)")
    except:
        print("   (Tài khoản mẫu đã tồn tại, bỏ qua)")

    conn.commit()
    cur.close()
    conn.close()
    print("\n✅ THÀNH CÔNG! ĐÃ TẠO BẢNG XONG.")
    print("👉 HÃY CHẠY LẠI FILE main.py NGAY.")

except Exception as e:
    print(f"\n❌ LỖI: {e}")
    print("Hãy chắc chắn bạn đã bật XAMPP (MySQL)!")

input("\nẤn Enter để thoát...")