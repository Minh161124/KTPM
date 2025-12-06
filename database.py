# database.py - FULL VERSION (Đã khôi phục đầy đủ code cũ + Fix lỗi Dashboard)
import mysql.connector
from mysql.connector import Error
import bcrypt
import time
from datetime import datetime
from contextlib import contextmanager

# --- CẤU HÌNH KẾT NỐI ---
DB_CONF = dict(
    host="localhost",
    user="root",
    password="",  # <-- Điền mật khẩu ở đây
    database="btl_ai",
    charset="utf8mb4"
)

def connect_db():
    try:
        conn = mysql.connector.connect(
            host=DB_CONF['host'],
            user=DB_CONF['user'],
            password=DB_CONF['password'],
            database=DB_CONF['database'],
            charset=DB_CONF.get('charset','utf8mb4')
        )
        if conn and conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Lỗi kết nối MySQL: {e}")
    return None

@contextmanager
def get_cursor(dictionary=False):
    conn = connect_db()
    if not conn:
        yield None, None
        return
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cur
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

# ---------- Helper: kiểm tra và thêm cột không phá hủy ----------
def add_column_if_missing(table, column_def):
    colname = column_def.strip().split()[0]
    with get_cursor() as (conn, cur):
        if not conn: return False
        try:
            cur.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """, (DB_CONF['database'], table, colname))
            if cur.fetchone()[0] == 0:
                sql = f"ALTER TABLE `{table}` ADD COLUMN {column_def}"
                cur.execute(sql)
                conn.commit()
                print(f"Added column {colname} to {table}")
            return True
        except Exception as e:
            print("WARN add_column_if_missing:", e)
            return False
# ... (Phần đầu file giữ nguyên) ...

# ---------- CREATE / ENSURE TABLES (non-destructive) ----------
def create_tables():
    with get_cursor() as (conn, cur):
        if not conn:
            print("Không thể tạo bảng do lỗi kết nối.")
            return
        try:
            # ... (Các lệnh cur.execute tạo bảng machines, users, logs CŨ GIỮ NGUYÊN) ...

            # =================================================================
            # --- [THÊM MỚI] TẠO BẢNG DANH MỤC & SẢN PHẨM ---
            # =================================================================
            
            # 1. Bảng Danh Mục
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    description TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 2. Bảng Sản Phẩm
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    category_id INT,
                    barcode VARCHAR(50),
                    price DECIMAL(15, 0) DEFAULT 0,
                    qty INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # =================================================================

            conn.commit()
            
            # ... (Phần add_column_if_missing phía dưới giữ nguyên) ...
            
            print(" -> Đã cập nhật cấu trúc Database (bao gồm Sản phẩm & Danh mục).")
        except Exception as e:
            print("ERROR create_tables:", e)

# ... (Phần còn lại của file giữ nguyên) ...
# ---------- CREATE / ENSURE TABLES (non-destructive) ----------
def create_tables():
    with get_cursor() as (conn, cur):
        if not conn:
            print("Không thể tạo bảng do lỗi kết nối.")
            return
        try:
            # Tạo các bảng dựa trên schema cũ (giữ nguyên)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) UNIQUE,
                    category VARCHAR(50),
                    spec TEXT,
                    state VARCHAR(20) DEFAULT 'off',
                    started_at VARCHAR(50),
                    used VARCHAR(20),
                    amount DOUBLE,
                    paused BOOLEAN DEFAULT FALSE,
                    acc_paused_seconds INT DEFAULT 0,
                    custom_price INT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_name VARCHAR(50),
                    category VARCHAR(50),
                    start_time VARCHAR(50),
                    end_time VARCHAR(50),
                    minutes DOUBLE,
                    amount DOUBLE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE,
                    email VARCHAR(150),
                    password VARCHAR(255),
                    password_hash VARCHAR(255),
                    role VARCHAR(20) DEFAULT 'admin',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weblocklist (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    domain VARCHAR(255) UNIQUE,
                    note VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weblog (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    time_stamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    url TEXT,
                    domain VARCHAR(255),
                    result VARCHAR(50),
                    note TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    category VARCHAR(100),
                    version VARCHAR(50),
                    path TEXT,
                    image TEXT,
                    blocked BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS gamelog (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100),
                    pc_name VARCHAR(20),
                    game_name VARCHAR(150),
                    start_time DATETIME,
                    end_time DATETIME,
                    play_minutes DOUBLE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type VARCHAR(20) NOT NULL,
                    category VARCHAR(100),
                    amount DOUBLE NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS shifts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    start_time VARCHAR(20),
                    end_time VARCHAR(20),
                    employee_name VARCHAR(100),
                    note TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    created_by VARCHAR(100) DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key VARCHAR(50) PRIMARY KEY,
                    setting_value TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()

            # --- Add non-destructive "modern" helper columns if missing ---
            add_column_if_missing('machines', "started_at_dt DATETIME NULL")
            add_column_if_missing('machines', "used_seconds INT DEFAULT 0")
            add_column_if_missing('machines', "amount_decimal DECIMAL(14,2) NULL")
            add_column_if_missing('users', "password_hash VARCHAR(255) NULL")
            add_column_if_missing('logs', "amount_decimal DECIMAL(14,2) NULL")
            add_column_if_missing('transactions', "amount_decimal DECIMAL(14,2) NULL")
            # Add helpful column for shifts
            add_column_if_missing('shifts', "closed_at DATETIME NULL")
            # done
            print(" -> Cấu trúc Database (non-destructive) đã sẵn sàng.")
        except Exception as e:
            print("ERROR create_tables:", e)

# ---------- SHIFTS (QUẢN LÝ CA TRỰC) ----------
def create_tables():
    with get_cursor() as (conn, cur):
        if not conn:
            print("Không thể tạo bảng do lỗi kết nối.")
            return
        try:
            # ... (Các lệnh tạo bảng machines, logs, users... cũ giữ nguyên) ...

            # ========================================================
            # --- THÊM ĐOẠN NÀY VÀO TRONG HÀM create_tables ---
            # ========================================================
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(150) NOT NULL,
                    account VARCHAR(100),
                    gender VARCHAR(20),
                    phone VARCHAR(50),
                    role VARCHAR(50),
                    salary DECIMAL(15, 2) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            # ========================================================

            conn.commit()
            
            # ... (Phần add_column_if_missing cũ giữ nguyên) ...
            
            print(" -> Cấu trúc Database (bao gồm employees) đã sẵn sàng.")
        except Exception as e:
            print("ERROR create_tables:", e)

def get_all_shifts():
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id, name, start_time, end_time, employee_name, note, status, created_by, created_at, closed_at
            FROM shifts
            ORDER BY id DESC
        """)
        rows = cur.fetchall() or []
        out = []
        for r in rows:
            s = r.get('start_time') or ""
            e = r.get('end_time') or ""
            def norm(t):
                if t is None: return ""
                t = str(t)
                if ":" in t:
                    parts = t.split(":")
                    if len(parts) >= 2:
                        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
                return t
            r['start_time'] = norm(s)
            r['end_time'] = norm(e)
            out.append(r)
        return out
    except Exception as e:
        print("ERROR get_all_shifts:", e)
        return []
    finally:
        cur.close(); conn.close()

def add_shift_db(name, s, e, emp, note, created_by=None):
    conn = connect_db()
    if not conn: return None
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO shifts (name, start_time, end_time, employee_name, note, status, created_by)
            VALUES (%s, %s, %s, %s, %s, 'active', %s)
        """, (name, s, e, emp, note, created_by))
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print("ERROR add_shift_db:", e)
        try: conn.rollback()
        except: pass
        return None
    finally:
        cur.close(); conn.close()

def update_shift_db(id, name, s, e, emp, note):
    conn = connect_db()
    if not conn: return 0
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE shifts
            SET name=%s, start_time=%s, end_time=%s, employee_name=%s, note=%s
            WHERE id=%s
        """, (name, s, e, emp, note, id))
        conn.commit()
        return cur.rowcount
    except Exception as e:
        print("ERROR update_shift_db:", e)
        try: conn.rollback()
        except: pass
        return 0
    finally:
        cur.close(); conn.close()

def delete_shift_db(id):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM shifts WHERE id=%s", (id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print("ERROR delete_shift_db:", e)
        try: conn.rollback()
        except: pass
        return False
    finally:
        cur.close(); conn.close()

def close_shift_db(id):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("UPDATE shifts SET status='closed' WHERE id=%s", (id,))
        try:
            cur.execute("SHOW COLUMNS FROM shifts LIKE 'closed_at'")
            if cur.fetchone():
                cur.execute("UPDATE shifts SET closed_at=%s WHERE id=%s", (datetime.now(), id))
        except:
            pass
        conn.commit()
        return True
    except Exception as e:
        print("ERROR close_shift_db:", e)
        try: conn.rollback()
        except: pass
        return False
    finally:
        cur.close(); conn.close()

# ---------- AUTH ----------
def check_login(username_or_email, password):
    conn = connect_db()
    if not conn: return None
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM users WHERE username=%s OR email=%s LIMIT 1", (username_or_email, username_or_email))
        user = cur.fetchone()
    finally:
        cur.close(); conn.close()
    if not user: return None
    stored_hash = user.get('password_hash') or user.get('password') or ""
    if not user.get('password_hash') and user.get('password'):
        return None
    try:
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            user.pop('password', None)
            user.pop('password_hash', None)
            return user
    except Exception:
        return None
    return None

# ---------- GAME MANAGEMENT ----------
def get_all_games():
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM games ORDER BY id DESC")
        rows = cur.fetchall()
        return rows
    except Error as e:
        print("Lỗi lấy danh sách game:", e)
        return []
    finally:
        cur.close(); conn.close()

def add_game_db(name, category, version, path, image):
    conn = connect_db();
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO games (name, category, version, path, image, blocked) 
                       VALUES (%s, %s, %s, %s, %s, 0)""", (name, category, version, path, image))
        conn.commit(); return True
    except Exception as e:
        print("ERROR add_game_db:", e); return False
    finally:
        cur.close(); conn.close()

def update_game_db(id, name, category, version, path, image):
    conn = connect_db();
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("""UPDATE games SET name=%s, category=%s, version=%s, path=%s, image=%s WHERE id=%s""",
                    (name, category, version, path, image, id))
        conn.commit(); return True
    except Exception as e:
        print("ERROR update_game_db:", e); return False
    finally:
        cur.close(); conn.close()

def delete_game_db(id):
    conn = connect_db();
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM games WHERE id=%s", (id,))
        conn.commit(); return True
    except Exception as e:
        print("ERROR delete_game_db:", e); return False
    finally:
        cur.close(); conn.close()

def toggle_block_db(id, current_status):
    conn = connect_db();
    if not conn: return False
    cur = conn.cursor()
    try:
        new_status = 0 if current_status == 1 else 1
        cur.execute("UPDATE games SET blocked=%s WHERE id=%s", (new_status, id))
        conn.commit(); return True
    except Exception as e:
        print("ERROR toggle_block_db:", e); return False
    finally:
        cur.close(); conn.close()

# ---------- MACHINES ----------
def get_all_machines():
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM machines ORDER BY id")
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print("ERROR get_all_machines:", e); return []
    finally:
        cur.close(); conn.close()

def insert_machine(name, category, spec, state):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM machines WHERE name = %s", (name,))
        if cur.fetchone(): return False
        cur.execute("""
            INSERT INTO machines (name, category, spec, state, started_at, used, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, category, spec, state, "--/--", "00:00:00", 0))
        conn.commit(); return True
    except Exception as e:
        print("ERROR insert_machine:", e); return False
    finally:
        cur.close(); conn.close()

# --- [MODIFIED] UPDATE MACHINE STATUS (Fix reset data khi OFF) ---
def update_machine_status(name, state, started_at=None, used=None, amount=0):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        # Nếu trạng thái là OFF -> Reset thời gian và số tiền
        if state.lower() == 'off':
            cur.execute("""
                UPDATE machines SET state=%s, started_at='--/--', used='00:00:00', amount=0, amount_decimal=0, used_seconds=0
                WHERE name=%s
            """, (state, name))
        else:
            # Nếu ON hoặc MAINTENANCE -> Cập nhật trạng thái và thời gian (nếu có)
            sql = "UPDATE machines SET state=%s"
            params = [state]
            if started_at:
                sql += ", started_at=%s"
                params.append(started_at)
            
            # Nếu có truyền vào used và amount thì cập nhật luôn (phòng trường hợp update định kỳ)
            if used:
                sql += ", used=%s"
                params.append(used)
            if amount:
                sql += ", amount=%s"
                params.append(amount)
                
            sql += " WHERE name=%s"
            params.append(name)
            cur.execute(sql, tuple(params))
            
        conn.commit()
        return True
    except Exception as e:
        print("ERROR update_machine_status:", e)
        return False
    finally:
        cur.close(); conn.close()

def get_machine_by_name(name):
    conn = connect_db()
    if not conn: return None
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM machines WHERE name=%s", (name,))
        return cur.fetchone()
    except Exception as e:
        print("ERROR get_machine_by_name:", e)
        return None
    finally:
        cur.close(); conn.close()

def save_log(machine_name, category, start_time, end_time, minutes, amount):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO logs (machine_name, category, start_time, end_time, minutes, amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (machine_name, category, start_time, end_time, minutes, amount))
        try:
            cur.execute("SHOW COLUMNS FROM logs LIKE 'amount_decimal'")
            if cur.fetchone():
                cur.execute("UPDATE logs SET amount_decimal=%s WHERE id=LAST_INSERT_ID()", (round(float(amount or 0),2),))
        except:
            pass
        conn.commit()
        return True
    except Exception as e:
        print("ERROR save_log:", e)
        return False
    finally:
        cur.close(); conn.close()

# ---------- WEBBLOCK ----------
def get_weblocklist():
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor()
    try:
        cur.execute("SELECT domain FROM weblocklist ORDER BY domain")
        rows = cur.fetchall()
        return [r[0] for r in rows]
    except Exception as e:
        print("ERROR get_weblocklist:", e)
        return []
    finally:
        cur.close(); conn.close()

def add_weblock_domain(domain, note=""):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("INSERT IGNORE INTO weblocklist (domain, note) VALUES (%s, %s)", (domain, note))
        conn.commit()
        return cur.rowcount > 0
    except:
        return False
    finally:
        cur.close(); conn.close()

def remove_weblock_domain(domain):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM weblocklist WHERE domain=%s", (domain,))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        return False
    finally:
        cur.close(); conn.close()

# ---------- DASHBOARD (ĐÃ FIX LOGIC) ----------
def get_dashboard_data():
    """
    Lấy dữ liệu tổng quan cho Dashboard.
    Fix: Đếm đúng trạng thái 'on'/'ON' và tính tiền từ Transactions để cập nhật nhanh.
    """
    conn = connect_db()
    if not conn:
        return {"total_machines": 0, "active_machines": 0, "total_amount": 0, "total_minutes": 0}
    cur = conn.cursor(dictionary=True)
    try:
        # 1. Tổng máy
        cur.execute("SELECT COUNT(*) AS total FROM machines")
        total = cur.fetchone()['total'] or 0

        # 2. Máy đang bật (Check case-insensitive)
        cur.execute("SELECT COUNT(*) AS active FROM machines WHERE LOWER(state) = 'on'")
        active = cur.fetchone()['active'] or 0

        # 3. Tổng doanh thu (Lấy từ bảng transactions)
        cur.execute("SELECT SUM(amount) as total_rev FROM transactions WHERE type='thu'")
        rev = cur.fetchone()['total_rev'] or 0

        return {
            "total_machines": total,
            "active_machines": active,
            "total_amount": float(rev),
            "total_minutes": 0 # Có thể update sau nếu cần
        }
    except Exception as e:
        print("ERROR get_dashboard_data:", e)
        return {"total_machines": 0, "active_machines": 0, "total_amount": 0, "total_minutes": 0}
    finally:
        cur.close(); conn.close()

# ---------- TRANSACTIONS ----------
def create_transaction_table():
    create_tables()

def get_transactions(limit=100):
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()
    except:
        return []
    finally:
        cur.close(); conn.close()

def add_transaction_db(type_, category, amount, description):
    conn = connect_db(); cur = conn.cursor()
    if not conn: return False
    try:
        cur.execute("INSERT INTO transactions (type, category, amount, description) VALUES (%s,%s,%s,%s)",
                    (type_, category, amount, description))
        try:
            cur.execute("UPDATE transactions SET amount_decimal=%s WHERE id=LAST_INSERT_ID()", (round(float(amount or 0),2),))
        except:
            pass
        conn.commit(); return True
    except Exception as e:
        print("ERROR add_transaction_db:", e); return False
    finally:
        cur.close(); conn.close()

def delete_transaction_db(id):
    conn = connect_db(); cur = conn.cursor()
    if not conn: return False
    try:
        cur.execute("DELETE FROM transactions WHERE id=%s", (id,))
        conn.commit(); return True
    except Exception as e:
        print("ERROR delete_transaction_db:", e); return False
    finally:
        cur.close(); conn.close()

def get_financial_summary():
    conn = connect_db()
    if not conn:
        return {"total_in": 0, "total_out": 0, "balance": 0}
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT SUM(CASE WHEN amount_decimal IS NOT NULL THEN amount_decimal ELSE amount END) as total FROM transactions WHERE type='thu'")
        res_in = cur.fetchone()['total'] or 0
        cur.execute("SELECT SUM(CASE WHEN amount_decimal IS NOT NULL THEN amount_decimal ELSE amount END) as total FROM transactions WHERE type='chi'")
        res_out = cur.fetchone()['total'] or 0
        return {"total_in": float(res_in), "total_out": float(res_out), "balance": float(res_in - res_out)}
    except Exception as e:
        print("ERROR get_financial_summary:", e)
        return {"total_in": 0, "total_out": 0, "balance": 0}
    finally:
        cur.close(); conn.close()

# ---------- REPORT HELPERS ----------
def get_revenue_stats(days=30):
    conn = connect_db()
    if not conn: return {}
    cur = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT DATE(created_at) as date, SUM(CASE WHEN amount_decimal IS NOT NULL THEN amount_decimal ELSE amount END) as total 
            FROM transactions 
            WHERE type='thu' AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """
        cur.execute(query, (days,))
        rows = cur.fetchall()
        return {str(r['date']): float(r['total'] or 0) for r in rows}
    except Exception as e:
        print("ERROR get_revenue_stats:", e)
        return {}
    finally:
        cur.close(); conn.close()

def get_machine_usage_stats():
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT machine_name, COUNT(*) as sessions, SUM(minutes) as total_minutes 
            FROM logs 
            GROUP BY machine_name 
            ORDER BY total_minutes DESC 
            LIMIT 5
        """)
        return cur.fetchall()
    except:
        return []
    finally:
        cur.close(); conn.close()

def get_general_report():
    conn = connect_db()
    if not conn: return [0,0,0,0]
    cur = conn.cursor()
    try:
        cur.execute("SELECT SUM(CASE WHEN amount_decimal IS NOT NULL THEN amount_decimal ELSE amount END) FROM transactions WHERE type='thu'")
        total_in = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(CASE WHEN amount_decimal IS NOT NULL THEN amount_decimal ELSE amount END) FROM transactions WHERE type='chi'")
        total_out = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM users"); total_users = cur.fetchone()[0] or 0
        return [float(total_in), float(total_out), float(total_in - total_out), total_users]
    except Exception as e:
        print("ERROR get_general_report:", e)
        return [0,0,0,0]
    finally:
        cur.close(); conn.close()

# ---------- SETTINGS ----------
def create_settings_table():
    with get_cursor() as (conn, cur):
        if not conn: return
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key VARCHAR(50) PRIMARY KEY,
                    setting_value TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            cur.execute("SELECT COUNT(*) FROM settings")
            if cur.fetchone()[0] == 0:
                defaults = [
                    ('shop_name', 'G Gaming Center'),
                    ('address', 'Hà Nội, Việt Nam'),
                    ('phone', '0123456789'),
                    ('price_standard', '5000'),
                    ('price_gaming', '8000'),
                    ('price_pro', '10000'),
                    ('price_competition', '15000')
                ]
                cur.executemany("INSERT INTO settings (setting_key, setting_value) VALUES (%s,%s)", defaults)
                conn.commit()
        except Exception as e:
            print("ERROR create_settings_table:", e)

def get_setting(key, default=""):
    conn = connect_db()
    if not conn: return default
    cur = conn.cursor()
    try:
        cur.execute("SELECT setting_value FROM settings WHERE setting_key=%s", (key,))
        res = cur.fetchone()
        return res[0] if res else default
    finally:
        cur.close(); conn.close()

def save_setting(key, value):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value=%s
        """, (key, value, value))
        conn.commit(); return True
    except Exception as e:
        print("ERROR save_setting:", e); return False
    finally:
        cur.close(); conn.close()

def change_admin_password(new_pass):
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("UPDATE users SET password_hash=%s WHERE username='admin'", (hashed,))
        conn.commit(); return True
    except Exception as e:
        print("ERROR change_admin_password:", e); return False
    finally:
        cur.close(); conn.close()
# --- THÊM VÀO CUỐI FILE database.py ---

# ---------- MEMBER MANAGEMENT (QUẢN LÝ HỘI VIÊN) ----------
# ---------- MEMBER MANAGEMENT (QUẢN LÝ HỘI VIÊN) ----------
def get_all_members():
    conn = connect_db(); cur = conn.cursor(dictionary=True)
    if not conn: return []
    try:
        cur.execute("SELECT * FROM members ORDER BY id DESC")
        return cur.fetchall()
    finally: cur.close(); conn.close()

def add_member(username, password, balance):
    conn = connect_db(); cur = conn.cursor()
    if not conn: return False
    try:
        # Kiểm tra trùng tên
        cur.execute("SELECT id FROM members WHERE username=%s", (username,))
        if cur.fetchone(): return False
        
        cur.execute("INSERT INTO members (username, password, balance) VALUES (%s, %s, %s)", (username, password, balance))
        conn.commit()
        return True
    except: return False
    finally: cur.close(); conn.close()

def update_member(id, username, password, balance):
    """Cập nhật thông tin. Nếu password rỗng thì giữ nguyên pass cũ."""
    conn = connect_db(); cur = conn.cursor()
    if not conn: return False
    try:
        if password: 
            # Nếu có nhập pass mới -> Cập nhật tất cả
            cur.execute("UPDATE members SET username=%s, password=%s, balance=%s WHERE id=%s", (username, password, balance, id))
        else:
            # Nếu để trống pass -> Chỉ cập nhật user và tiền
            cur.execute("UPDATE members SET username=%s, balance=%s WHERE id=%s", (username, balance, id))
        conn.commit()
        return True
    except: return False
    finally: cur.close(); conn.close()

def delete_member(id):
    conn = connect_db(); cur = conn.cursor()
    if not conn: return False
    try:
        cur.execute("DELETE FROM members WHERE id=%s", (id,))
        conn.commit()
        return True
    except: return False
    finally: cur.close(); conn.close()

def top_up_member(id, amount):
    """Nạp tiền nhanh"""
    conn = connect_db(); cur = conn.cursor()
    if not conn: return False
    try:
        cur.execute("UPDATE members SET balance = balance + %s WHERE id=%s", (amount, id))
        conn.commit()
        return True
    except: return False
    finally: cur.close(); conn.close()

def login_member(username, password):
    """Hàm này dùng cho Client App đăng nhập"""
    conn = connect_db(); cur = conn.cursor(dictionary=True)
    if not conn: return None
    try:
        cur.execute("SELECT * FROM members WHERE username=%s AND password=%s", (username, password))
        return cur.fetchone()
    finally: cur.close(); conn.close()
    # =========================================================
# --- EMPLOYEE MANAGEMENT (QUẢN LÝ NHÂN VIÊN - MySQL) ---
# =========================================================

def get_employees_paginated(search="", role="Tất cả", limit=10, page=1):
    """
    Lấy danh sách nhân viên có phân trang và tìm kiếm.
    Trả về: (danh sách_bản_ghi, tổng_số_bản_ghi)
    """
    conn = connect_db()
    if not conn: return [], 0
    cur = conn.cursor(dictionary=False) # Để False để trả về tuple cho dễ hiển thị lên Treeview
    try:
        offset = (page - 1) * limit
        
        # 1. Xây dựng câu query cơ bản
        sql_where = " WHERE (name LIKE %s OR code LIKE %s) "
        params = [f"%{search}%", f"%{search}%"]
        
        if role and role != "Tất cả" and role != "Tất cả chức vụ":
            sql_where += " AND role = %s "
            params.append(role)
            
        # 2. Đếm tổng số bản ghi (để tính số trang)
        cur.execute(f"SELECT COUNT(*) FROM employees {sql_where}", tuple(params))
        total_records = cur.fetchone()[0]
        
        # 3. Lấy dữ liệu chi tiết
        sql_data = f"SELECT id, code, name, account, gender, phone, role, salary FROM employees {sql_where} ORDER BY id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(sql_data, tuple(params))
        rows = cur.fetchall()
        
        # Format lại tiền lương cho đẹp (nếu cần xử lý tại đây, hoặc để UI xử lý)
        formatted_rows = []
        for r in rows:
            r_list = list(r)
            # r[7] là salary, ép kiểu float để tránh lỗi Decimal của MySQL
            if r[7] is not None:
                r_list[7] = f"{float(r[7]):,.0f}"
            formatted_rows.append(tuple(r_list))
            
        return formatted_rows, total_records
        
    except Exception as e:
        print("ERROR get_employees_paginated:", e)
        return [], 0
    finally:
        cur.close(); conn.close()

def add_employee_db(data):
    """
    Thêm nhân viên mới.
    data: (code, name, account, gender, phone, role, salary)
    """
    conn = connect_db()
    if not conn: return False, "Lỗi kết nối CSDL"
    cur = conn.cursor()
    try:
        # Kiểm tra trùng mã
        cur.execute("SELECT id FROM employees WHERE code = %s", (data[0],))
        if cur.fetchone():
            return False, f"Mã nhân viên '{data[0]}' đã tồn tại!"

        sql = """
            INSERT INTO employees (code, name, account, gender, phone, role, salary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, data)
        conn.commit()
        return True, "Thêm nhân viên thành công!"
    except Exception as e:
        print("ERROR add_employee_db:", e)
        return False, str(e)
    finally:
        cur.close(); conn.close()

# =============================================================================
# --- MODULE QUẢN LÝ NHÂN VIÊN (EMPLOYEE MANAGEMENT) ---
# =============================================================================

def get_employees_paginated(search="", role="Tất cả", limit=10, page=1):
    """
    Lấy danh sách nhân viên: Tìm kiếm + Lọc chức vụ + Phân trang
    """
    conn = connect_db()
    if not conn: return [], 0
    cur = conn.cursor() # Trả về tuple để hiển thị lên UI nhanh hơn
    try:
        offset = (page - 1) * limit
        
        # 1. Tạo câu điều kiện WHERE
        sql_where = " WHERE (name LIKE %s OR code LIKE %s) "
        params = [f"%{search}%", f"%{search}%"]
        
        if role and role not in ["Tất cả", "Tất cả chức vụ"]:
            sql_where += " AND role = %s "
            params.append(role)
            
        # 2. Đếm tổng số bản ghi (để tính số trang)
        cur.execute(f"SELECT COUNT(*) FROM employees {sql_where}", tuple(params))
        total_records = cur.fetchone()[0]
        
        # 3. Lấy dữ liệu phân trang
        # Lấy các cột: id, code, name, account, gender, phone, role, salary
        sql_data = f"""
            SELECT id, code, name, account, gender, phone, role, salary 
            FROM employees 
            {sql_where} 
            ORDER BY id DESC 
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cur.execute(sql_data, tuple(params))
        rows = cur.fetchall()
        
        # Xử lý format tiền tệ (Decimal -> Float/String) để tránh lỗi UI
        formatted_rows = []
        for row in rows:
            r_list = list(row)
            # row[7] là salary. Nếu có giá trị thì format đẹp, ko thì để 0
            if r_list[7] is not None:
                r_list[7] = f"{float(r_list[7]):,.0f}"
            else:
                r_list[7] = "0"
            formatted_rows.append(tuple(r_list))
            
        return formatted_rows, total_records
        
    except Exception as e:
        print("ERROR get_employees_paginated:", e)
        return [], 0
    finally:
        if cur: cur.close()
        if conn: conn.close()

def add_employee_db(data):
    """
    Thêm nhân viên mới.
    data = (code, name, account, gender, phone, role, salary)
    """
    conn = connect_db()
    if not conn: return False, "Lỗi kết nối database"
    cur = conn.cursor()
    try:
        # 1. Check trùng mã nhân viên
        cur.execute("SELECT id FROM employees WHERE code = %s", (data[0],))
        if cur.fetchone():
            return False, f"Mã nhân viên '{data[0]}' đã tồn tại!"

        # 2. Thêm mới
        sql = """
            INSERT INTO employees (code, name, account, gender, phone, role, salary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, data)
        conn.commit()
        return True, "Thêm nhân viên thành công!"
    except Exception as e:
        print("ERROR add_employee_db:", e)
        return False, str(e)
    finally:
        if cur: cur.close()
        if conn: conn.close()

def update_employee_db(emp_id, data):
    """
    Cập nhật thông tin nhân viên.
    data = (code, name, account, gender, phone, role, salary)
    """
    conn = connect_db()
    if not conn: return False, "Lỗi kết nối database"
    cur = conn.cursor()
    try:
        # MySQL update query
        sql = """
            UPDATE employees 
            SET code=%s, name=%s, account=%s, gender=%s, phone=%s, role=%s, salary=%s
            WHERE id=%s
        """
        # Nối emp_id vào cuối tuple data để khớp với %s cuối cùng
        params = data + (emp_id,)
        
        cur.execute(sql, params)
        conn.commit()
        return True, "Cập nhật thành công!"
    except Exception as e:
        print("ERROR update_employee_db:", e)
        return False, str(e)
    finally:
        if cur: cur.close()
        if conn: conn.close()

def delete_employee_db(emp_id):
    """Xóa nhân viên theo ID"""
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
        conn.commit()
        return True
    except Exception as e:
        print("ERROR delete_employee_db:", e)
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()
        # ------------------ PRODUCTS & CATEGORIES (ADD-ON) ------------------
# -------------------------------------------------------------------
# =============================================================================
# --- MODULE QUẢN LÝ SẢN PHẨM & KHO (PRODUCTS - Add-on) ---
# =============================================================================

def get_all_products(keyword=""):
    """
    Lấy danh sách sản phẩm.
    Hỗ trợ tìm kiếm theo Tên hoặc Mã SP.
    """
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor(dictionary=True)
    try:
        # Kiểm tra xem bảng có tồn tại cột price_in không (để tránh lỗi nếu dùng cấu trúc cũ)
        cur.execute("SHOW COLUMNS FROM products LIKE 'price_in'")
        has_price_in = cur.fetchone()

        if keyword:
            sql = "SELECT * FROM products WHERE name LIKE %s OR code LIKE %s ORDER BY id DESC"
            params = (f"%{keyword}%", f"%{keyword}%")
            cur.execute(sql, params)
        else:
            cur.execute("SELECT * FROM products ORDER BY id DESC")
        
        rows = cur.fetchall()
        
        # Chuẩn hóa dữ liệu trả về để tránh lỗi None
        results = []
        for r in rows:
            # Nếu dùng cấu trúc cũ (chỉ có price), map nó sang price_out
            p_in = r.get('price_in', 0) if has_price_in else 0
            p_out = r.get('price_out') if has_price_in else r.get('price', 0)
            qty = r.get('stock') if 'stock' in r else r.get('qty', 0)
            
            r['price_in'] = float(p_in or 0)
            r['price_out'] = float(p_out or 0)
            r['stock'] = int(qty or 0)
            results.append(r)
            
        return results
    except Exception as e:
        print("ERROR get_all_products:", e)
        return []
    finally:
        cur.close(); conn.close()

def add_product_db(code, name, category, price_in, price_out, stock):
    """Thêm sản phẩm mới"""
    conn = connect_db()
    if not conn: return False, "Lỗi kết nối"
    cur = conn.cursor()
    try:
        # Kiểm tra trùng mã
        cur.execute("SELECT id FROM products WHERE code=%s", (code,))
        if cur.fetchone():
            return False, f"Mã sản phẩm {code} đã tồn tại!"

        # Insert (Hỗ trợ cấu trúc bảng bạn đã tạo trong SQL)
        sql = """
            INSERT INTO products (code, name, category, price_in, price_out, stock) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, (code, name, category, price_in, price_out, stock))
        conn.commit()
        return True, "Thêm thành công"
    except Exception as e:
        print("ERROR add_product_db:", e)
        # Fallback: Nếu bảng dùng cấu trúc cũ (price, qty)
        try:
            cur.execute("""
                INSERT INTO products (code, name, category, price, qty) 
                VALUES (%s, %s, %s, %s, %s)
            """, (code, name, category, price_out, stock))
            conn.commit()
            return True, "Thêm thành công (Cấu trúc cũ)"
        except:
            return False, str(e)
    finally:
        cur.close(); conn.close()

def update_product_db(code, name, category, price_in, price_out, stock):
    """Cập nhật sản phẩm theo Mã (code)"""
    conn = connect_db()
    if not conn: return False, "Lỗi kết nối"
    cur = conn.cursor()
    try:
        sql = """
            UPDATE products 
            SET name=%s, category=%s, price_in=%s, price_out=%s, stock=%s 
            WHERE code=%s
        """
        cur.execute(sql, (name, category, price_in, price_out, stock, code))
        conn.commit()
        return True, "Cập nhật thành công"
    except Exception as e:
        print("ERROR update_product_db:", e)
        return False, str(e)
    finally:
        cur.close(); conn.close()

def delete_product_db(code):
    """Xóa sản phẩm theo Mã"""
    conn = connect_db()
    if not conn: return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE code=%s", (code,))
        conn.commit()
        return True
    except Exception as e:
        print("ERROR delete_product_db:", e)
        return False
    finally:
        cur.close(); conn.close()

def get_product_by_code(code):
    """Lấy chi tiết 1 sản phẩm"""
    conn = connect_db()
    if not conn: return None
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM products WHERE code=%s", (code,))
        return cur.fetchone()
    finally:
        cur.close(); conn.close()

def generate_next_product_code():
    """Tự động tạo mã SP tiếp theo (VD: SP031)"""
    conn = connect_db()
    if not conn: return "SP001"
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM products ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            next_id = row[0] + 1
            return f"SP{next_id:03d}"
        return "SP001"
    except:
        return "SP001"
    finally:
        cur.close(); conn.close()

# =============================================================================
# --- MODULE QUẢN LÝ DANH MỤC (CATEGORIES - Add-on) ---
# =============================================================================

def get_all_categories():
    conn = connect_db()
    if not conn: return []
    cur = conn.cursor(dictionary=True)
    try:
        # Kiểm tra bảng categories có tồn tại không
        try:
            cur.execute("SELECT * FROM categories ORDER BY id DESC")
            return cur.fetchall()
        except:
            # Nếu chưa có bảng categories, trả về danh sách cứng để không lỗi app
            return [
                {"name": "Đồ ăn"}, {"name": "Nước uống"}, 
                {"name": "Thẻ Game"}, {"name": "Thẻ ĐT"}, 
                {"name": "Combo"}, {"name": "Khác"}
            ]
    finally:
        cur.close(); conn.close()
        # =============================================================================
# --- ADD-ON: CHAT SYSTEM & NOTIFICATIONS ---
# =============================================================================

# 1. Cập nhật bảng transactions (Thêm cột 'status' nếu chưa có)
def migrate_db_updates():
    with get_cursor() as (conn, cur):
        if not conn: return
        try:
            # Thêm cột status cho bảng transactions để biết đơn hàng đã phục vụ chưa
            add_column_if_missing("transactions", "status VARCHAR(20) DEFAULT 'pending'")
            
            # Tạo bảng Messages (Tin nhắn)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender VARCHAR(50),
                    content TEXT,
                    is_read INT DEFAULT 0,  -- 0: Chưa đọc, 1: Đã đọc
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            print(" -> DB Updated: Added Messages table & Transaction status.")
        except Exception as e:
            print("Migrate Error:", e)

# Chạy cập nhật DB ngay khi import
migrate_db_updates()

# --- HÀM XỬ LÝ CHAT ---
def send_message(sender, content):
    """Gửi tin nhắn mới"""
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO messages (sender, content, is_read) VALUES (%s, %s, 0)", (sender, content))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def get_unread_messages():
    """Lấy tin nhắn chưa đọc cho Admin"""
    conn = connect_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM messages WHERE is_read = 0 ORDER BY created_at DESC")
        return cur.fetchall()
    finally: conn.close()

def mark_message_read(msg_id):
    """Đánh dấu đã đọc"""
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE messages SET is_read = 1 WHERE id=%s", (msg_id,))
        conn.commit()
    finally: conn.close()

# --- HÀM XỬ LÝ ORDER (PENDING) ---
def get_pending_orders():
    """Lấy danh sách đơn hàng chưa phục vụ"""
    conn = connect_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM transactions WHERE type='thu' AND category='Dịch vụ' AND status='pending' ORDER BY created_at DESC")
        return cur.fetchall()
    finally: conn.close()

def complete_order(trans_id):
    """Đánh dấu đơn hàng đã xong"""
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE transactions SET status = 'completed' WHERE id=%s", (trans_id,))
        conn.commit()
    finally: conn.close()
    # =============================================================================
# --- [CHAT SYSTEM V2] - HỖ TRỢ CHAT 2 CHIỀU ---
# =============================================================================

def upgrade_chat_db():
    """Tự động thêm cột receiver nếu chưa có"""
    add_column_if_missing("messages", "receiver VARCHAR(50) DEFAULT 'admin'")

# Chạy ngay khi khởi động
upgrade_chat_db()

def send_message_v2(sender, receiver, content):
    """Gửi tin nhắn (có chỉ định người nhận)"""
    conn = connect_db(); cur = conn.cursor()
    try:
        # is_read = 0 (chưa đọc)
        sql = "INSERT INTO messages (sender, receiver, content, is_read) VALUES (%s, %s, %s, 0)"
        cur.execute(sql, (sender, receiver, content))
        conn.commit()
        return True
    except Exception as e:
        print("Chat Error:", e)
        return False
    finally: conn.close()

def get_conversation(machine_name):
    """Lấy toàn bộ lịch sử chat giữa Admin và Máy trạm cụ thể"""
    conn = connect_db(); cur = conn.cursor(dictionary=True)
    try:
        # Lấy tin nhắn chiều đi (Admin -> Máy) VÀ chiều về (Máy -> Admin)
        sql = """
            SELECT * FROM messages 
            WHERE (sender = %s AND receiver = 'admin') 
               OR (sender = 'admin' AND receiver = %s)
            ORDER BY created_at ASC
        """
        cur.execute(sql, (machine_name, machine_name))
        return cur.fetchall()
    finally: conn.close()

def get_active_chat_users():
    """Lấy danh sách các máy đã từng nhắn tin để hiển thị bên Admin"""
    conn = connect_db(); cur = conn.cursor()
    try:
        # Lấy danh sách sender khác 'admin'
        cur.execute("SELECT DISTINCT sender FROM messages WHERE sender != 'admin'")
        return [r[0] for r in cur.fetchall()]
    finally: conn.close()
# ---------- INIT ----------
create_transaction_table()# =============================================================================
# --- [GAME INSTALLER SYSTEM] - HỆ THỐNG CÀI ĐẶT GAME TỪ XA ---
# =============================================================================

# --- DÁN VÀO CUỐI FILE database.py ---

def upgrade_installer_db():
    with get_cursor() as (conn, cur):
        if not conn: return
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS install_queue (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_name VARCHAR(50),
                    game_name VARCHAR(150),
                    status VARCHAR(20) DEFAULT 'pending',
                    progress INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except Exception as e: print("Installer DB Error:", e)

# Chạy hàm này ngay khi import
upgrade_installer_db()

def queue_install_game(machine_name, game_name):
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO install_queue (machine_name, game_name, status, progress) VALUES (%s, %s, 'pending', 0)", 
                    (machine_name, game_name))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def get_install_tasks(machine_name):
    conn = connect_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM install_queue WHERE machine_name=%s AND status='pending'", (machine_name,))
        return cur.fetchall()
    finally: conn.close()

def update_install_progress(task_id, status, progress):
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE install_queue SET status=%s, progress=%s WHERE id=%s", (status, progress, task_id))
        conn.commit()
    finally: conn.close()
# --- Thêm vào cuối file database.py ---

# --- Thêm vào cuối file database.py ---

# =============================================================
# --- PHẦN LOGIC CHATBOT AI (Thêm vào cuối file database.py) ---
# =============================================================

# --- Thay thế hàm cũ trong database.py bằng hàm này ---

def get_ai_response_from_db(user_msg):
    """
    Phiên bản V2: Tính điểm độ phù hợp (Scoring Match)
    Giúp Bot chọn câu trả lời sát nghĩa nhất thay vì câu đầu tiên tìm thấy.
    """
    msg = user_msg.lower()
    default_ans = "Dạ em chưa hiểu rõ ý này. Anh/chị thử hỏi ngắn gọn hơn xem sao ạ?"
    
    try:
        conn = connect_db()
        if not conn: return "Lỗi kết nối Server."

        cursor = conn.cursor(dictionary=True)
        # Lấy toàn bộ dữ liệu
        cursor.execute("SELECT keywords, response FROM chatbot_data")
        rules = cursor.fetchall()
        conn.close()

        best_response = None
        highest_score = 0

        # --- LOGIC TÍNH ĐIỂM ---
        for row in rules:
            # Tách từ khóa: "liên minh, lol, garena" -> ['liên minh', 'lol', 'garena']
            keywords = [k.strip().lower() for k in row['keywords'].split(',')]
            
            current_score = 0
            # Đếm xem có bao nhiêu từ khóa xuất hiện trong tin nhắn của khách
            for key in keywords:
                if key in msg:
                    # Từ khóa dài (trên 2 ký tự) được cộng nhiều điểm hơn để ưu tiên độ chính xác
                    # Ví dụ: "giới thiệu" (2 từ) giá trị hơn "lol" (1 từ)
                    if len(key.split()) > 1:
                        current_score += 2
                    else:
                        current_score += 1
            
            # Nếu điểm câu này cao hơn câu trước đó -> Chọn câu này
            if current_score > highest_score:
                highest_score = current_score
                best_response = row['response']

        # Nếu tìm được câu trả lời có điểm > 0
        if best_response:
            return best_response
            
        # Fallback: Nếu không tìm thấy trong DB, gợi ý web
        if any(x in msg for x in ["lên đồ", "build", "combo", "cách chơi"]):
            return "Dữ liệu chi tiết đang cập nhật. Anh/chị tham khảo trên u.gg hoặc op.gg giúp em nhé!"

    except Exception as e:
        print(f"Lỗi Bot: {e}")
        return "Bot đang bảo trì."

    return default_ans
def create_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",        # User mặc định XAMPP
            password="",        # Pass mặc định XAMPP để trống
            database="btl_ai"   # <--- ĐÃ SỬA TÊN DB CỦA BẠN
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối database: {err}")
        return None

# ... (Các hàm xử lý nhân viên cũ của bạn: add_employee, update... để ở giữa này) ...


# =============================================================================
# 2. CÁC HÀM XỬ LÝ CA TRỰC (THÊM VÀO CUỐI FILE)
# =============================================================================

def get_all_employees_for_shift():
    """Lấy TẤT CẢ nhân sự (không phân biệt chức vụ) để xếp ca"""
    try:
        conn = create_connection()
        if conn is None: return []
        
        cursor = conn.cursor()
        # Lấy thêm cột 'role' để hiển thị chức vụ trong dropdown
        sql = "SELECT id, code, name, role FROM employees ORDER BY name ASC" 
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print("Lỗi lấy danh sách xếp ca:", e)
        return []

def add_shift_db(emp_id, date, shift_name, note=""):
    try:
        conn = create_connection()
        if conn is None: return False, "Lỗi kết nối"

        cursor = conn.cursor()
        sql = "INSERT INTO shifts (employee_id, shift_date, shift_name, note) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (emp_id, date, shift_name, note))
        conn.commit()
        conn.close()
        return True, "Thêm ca trực thành công!"
    except Exception as e:
        return False, f"Lỗi: {e}"

# --- FILE: database.py ---

# ... (Các hàm khác giữ nguyên)

def get_all_shifts():
    """Lấy danh sách ca trực, format ngày thành dd/mm/yyyy"""
    try:
        conn = create_connection()
        if conn is None: return []

        cursor = conn.cursor()
        # SỬ DỤNG DATE_FORMAT ĐỂ CHUYỂN NGÀY SANG ĐỊNH DẠNG VIỆT NAM NGAY TRONG SQL
        sql = """
            SELECT s.id, e.code, e.name, e.role, 
                   DATE_FORMAT(s.shift_date, '%d/%m/%Y') as vn_date, 
                   s.shift_name, s.note 
            FROM shifts s
            JOIN employees e ON s.employee_id = e.id
            ORDER BY s.shift_date DESC
        """
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print("Lỗi get_shifts:", e)
        return []
    except Exception as e:
        print("Lỗi get_shifts:", e)
        return []

def delete_shift_db(shift_id):
    try:
        conn = create_connection()
        if conn is None: return False
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shifts WHERE id = %s", (shift_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False
create_settings_table()
create_tables()

if __name__ == "__main__":
    print("\n--- DATABASE FULL LOADED ---")
    print("Done.")