import tkinter as tk
from tkinter import ttk
import datetime
import random

# ============================================================================
# --- 1. CONFIG & THEME (ĐỒNG BỘ VỚI TRANG CHỦ) ---
# ============================================================================
COLOR_BG_MAIN   = "#1E1E2F"      # Nền chính
COLOR_CARD_BG   = "#27293D"      # Nền card
COLOR_TEXT_WHITE= "#FFFFFF"
COLOR_TEXT_GRAY = "#9A9A9A"
COLOR_ACCENT_1  = "#E14ECA"      # Tím hồng
COLOR_ACCENT_2  = "#00F2C3"      # Xanh ngọc
COLOR_ACCENT_3  = "#1D8CF8"      # Xanh dương
COLOR_RED       = "#FF6B6B"      # Đỏ

FONT_HEADER = ("Segoe UI", 18, "bold")
FONT_TITLE  = ("Segoe UI", 12, "bold")
FONT_VAL    = ("Segoe UI", 24, "bold")
FONT_NORM   = ("Segoe UI", 10)

# ============================================================================
# --- 2. MOCK DATA & DATABASE CONNECTION ---
# ============================================================================
try:
    from database import get_revenue_stats, get_machine_usage_stats, get_general_report
except ImportError:
    # --- MOCK DATA NẾU KHÔNG CÓ DB ---
    def get_general_report():
        # Trả về: [Tổng thu, Tổng chi, Lợi nhuận, Số khách]
        return [15000000, 5000000, 10000000, 125]

    def get_machine_usage_stats(): 
        # Giả lập Top 5 máy
        return [
            {'machine_name': 'MAY-05', 'total_minutes': 1200},
            {'machine_name': 'VIP-01', 'total_minutes': 950},
            {'machine_name': 'MAY-02', 'total_minutes': 800},
            {'machine_name': 'MAY-10', 'total_minutes': 600},
            {'machine_name': 'MAY-01', 'total_minutes': 300}
        ]

    def get_revenue_stats(days=7): 
        # Giả lập doanh thu 7 ngày gần nhất
        data = {}
        today = datetime.date.today()
        for i in range(days):
            d = today - datetime.timedelta(days=6-i) # Từ quá khứ đến hiện tại
            date_str = d.strftime("%d/%m")
            data[date_str] = random.randint(500000, 3000000) # Doanh thu ngẫu nhiên
        return data

# ============================================================================
# --- 3. UI COMPONENTS ---
# ============================================================================

class StatCard(tk.Frame):
    """Thẻ thống kê nhỏ (Revenue, Profit, etc.)"""
    def __init__(self, parent, title, value, icon, color):
        super().__init__(parent, bg=COLOR_CARD_BG, highlightbackground=color, highlightthickness=1)
        self.pack_propagate(False)
        
        # Icon & Title
        row1 = tk.Frame(self, bg=COLOR_CARD_BG)
        row1.pack(fill='x', padx=15, pady=(15, 5))
        tk.Label(row1, text=icon, fg=color, bg=COLOR_CARD_BG, font=("Arial", 18)).pack(side='left')
        tk.Label(row1, text=title.upper(), fg=COLOR_TEXT_GRAY, bg=COLOR_CARD_BG, font=("Arial", 10, "bold")).pack(side='left', padx=10)
        
        # Value
        self.lbl_value = tk.Label(self, text=value, fg="white", bg=COLOR_CARD_BG, font=FONT_VAL, anchor='w')
        self.lbl_value.pack(fill='x', padx=15, pady=(0, 15))

class RevenueChart(tk.Canvas):
    """Biểu đồ cột đơn giản vẽ bằng Canvas"""
    def __init__(self, parent, width=600, height=300):
        super().__init__(parent, width=width, height=height, bg=COLOR_CARD_BG, highlightthickness=0)
        self.W, self.H = width, height
        
    def draw(self, data_dict):
        self.delete("all")
        if not data_dict:
            self.create_text(self.W/2, self.H/2, text="Không có dữ liệu", fill="white")
            return

        dates = list(data_dict.keys())
        values = list(data_dict.values())
        max_val = max(values) if values else 1
        
        # Cấu hình vẽ
        margin_left = 50
        margin_bottom = 30
        graph_w = self.W - margin_left - 20
        graph_h = self.H - margin_bottom - 20
        
        bar_width = graph_w / len(values) * 0.6
        spacing = graph_w / len(values)

        # Vẽ trục
        self.create_line(margin_left, 10, margin_left, self.H - margin_bottom, fill="#555", width=2) # Y axis
        self.create_line(margin_left, self.H - margin_bottom, self.W, self.H - margin_bottom, fill="#555", width=2) # X axis

        for i, (d_str, val) in enumerate(zip(dates, values)):
            x0 = margin_left + i * spacing + (spacing - bar_width) / 2
            x1 = x0 + bar_width
            
            # Chiều cao cột
            bar_h = (val / max_val) * graph_h
            y0 = self.H - margin_bottom
            y1 = y0 - bar_h
            
            # Vẽ cột
            color = COLOR_ACCENT_3 if i < len(values)-1 else COLOR_ACCENT_2 # Cột cuối khác màu
            self.create_rectangle(x0, y1, x1, y0, fill=color, outline="")
            
            # Text giá trị (Triệu/Ngàn)
            val_text = f"{val/1000000:.1f}M" if val > 1000000 else f"{val/1000:.0f}K"
            self.create_text((x0+x1)/2, y1 - 10, text=val_text, fill="white", font=("Arial", 8))
            
            # Text ngày
            self.create_text((x0+x1)/2, y0 + 15, text=d_str, fill=COLOR_TEXT_GRAY, font=("Arial", 9))

# ============================================================================
# --- 4. MAIN PAGE CLASS ---
# ============================================================================
class ReportManagerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG_MAIN)
        
        # Header
        header = tk.Frame(self, bg=COLOR_BG_MAIN)
        header.pack(fill='x', padx=30, pady=20)
        tk.Label(header, text="BÁO CÁO & THỐNG KÊ", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_MAIN, font=FONT_HEADER).pack(side='left')
        
        tk.Button(header, text="↻ Làm mới", bg=COLOR_CARD_BG, fg="white", bd=0, 
                  font=("Arial", 10), padx=15, pady=5, cursor="hand2",
                  command=self.load_data).pack(side='right')

        # Content Area
        self.content = tk.Frame(self, bg=COLOR_BG_MAIN)
        self.content.pack(fill='both', expand=True, padx=30)

        # 1. Cards Section (Top)
        self.card_frame = tk.Frame(self.content, bg=COLOR_BG_MAIN)
        self.card_frame.pack(fill='x', pady=(0, 20))
        
        self.card_rev = StatCard(self.card_frame, "Doanh Thu", "0 đ", "💰", COLOR_ACCENT_2)
        self.card_rev.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.card_exp = StatCard(self.card_frame, "Chi Phí", "0 đ", "💸", COLOR_RED)
        self.card_exp.pack(side='left', fill='x', expand=True, padx=10)
        
        self.card_prf = StatCard(self.card_frame, "Lợi Nhuận", "0 đ", "📈", COLOR_ACCENT_3)
        self.card_prf.pack(side='left', fill='x', expand=True, padx=10)
        
        self.card_usr = StatCard(self.card_frame, "Khách Mới", "0", "👥", "#FFC107")
        self.card_usr.pack(side='left', fill='x', expand=True, padx=(10, 0))

        # 2. Charts Section (Bottom)
        bottom_frame = tk.Frame(self.content, bg=COLOR_BG_MAIN)
        bottom_frame.pack(fill='both', expand=True)

        # Left: Chart
        chart_container = tk.Frame(bottom_frame, bg=COLOR_CARD_BG, padx=20, pady=20)
        chart_container.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(chart_container, text="BIỂU ĐỒ DOANH THU (7 NGÀY)", fg="white", bg=COLOR_CARD_BG, font=FONT_TITLE).pack(anchor='w', pady=(0, 10))
        self.chart = RevenueChart(chart_container, height=350)
        self.chart.pack(fill='both', expand=True)

        # Right: Top Machines
        list_container = tk.Frame(bottom_frame, bg=COLOR_CARD_BG, width=350, padx=20, pady=20)
        list_container.pack(side='right', fill='y', padx=(10, 0))
        list_container.pack_propagate(False) # Cố định chiều rộng

        tk.Label(list_container, text="TOP MÁY HOẠT ĐỘNG", fg="white", bg=COLOR_CARD_BG, font=FONT_TITLE).pack(anchor='w', pady=(0, 15))
        
        self.machine_list_frame = tk.Frame(list_container, bg=COLOR_CARD_BG)
        self.machine_list_frame.pack(fill='both', expand=True)

        # Load Data Init
        self.load_data()

    def load_data(self):
        # 1. Update Cards
        try:
            # Stats: [Thu, Chi, Lợi nhuận, Khách]
            stats = get_general_report() 
            self.card_rev.lbl_value.config(text=f"{stats[0]:,.0f} đ")
            self.card_exp.lbl_value.config(text=f"{stats[1]:,.0f} đ")
            self.card_prf.lbl_value.config(text=f"{stats[2]:,.0f} đ")
            self.card_usr.lbl_value.config(text=f"{stats[3]}")
        except: pass

        # 2. Draw Chart
        try:
            rev_data = get_revenue_stats(7)
            self.chart.draw(rev_data)
        except: pass

        # 3. Draw Top Machines
        for w in self.machine_list_frame.winfo_children(): w.destroy()
        try:
            top_machines = get_machine_usage_stats()
            max_minutes = max([m['total_minutes'] for m in top_machines]) if top_machines else 1000

            for m in top_machines:
                row = tk.Frame(self.machine_list_frame, bg=COLOR_CARD_BG)
                row.pack(fill='x', pady=8)
                
                # Header row: Tên máy + Số phút
                info = tk.Frame(row, bg=COLOR_CARD_BG)
                info.pack(fill='x')
                tk.Label(info, text=m['machine_name'], fg=COLOR_ACCENT_1, bg=COLOR_CARD_BG, font=("Arial", 10, "bold")).pack(side='left')
                tk.Label(info, text=f"{int(m['total_minutes']/60)}h {int(m['total_minutes']%60)}p", fg="white", bg=COLOR_CARD_BG, font=("Arial", 9)).pack(side='right')
                
                # Progress Bar (Giả lập)
                pct = m['total_minutes'] / max_minutes
                bar_bg = tk.Frame(row, bg="#444", height=6)
                bar_bg.pack(fill='x', pady=(5,0))
                
                # Trick: Dùng place để vẽ thanh màu trên nền xám
                # Lưu ý: Tkinter Frame width trong pack/fill đôi khi cần update_idletasks, 
                # nhưng ở đây ta dùng Canvas hoặc Frame lồng sẽ phức tạp. 
                # Cách đơn giản nhất cho thanh bar tĩnh:
                
                bar_canvas = tk.Canvas(row, height=6, bg="#444", highlightthickness=0)
                bar_canvas.pack(fill='x')
                bar_canvas.create_rectangle(0, 0, 300 * pct, 6, fill=COLOR_ACCENT_2, width=0) # 300 là ước lượng width, thực tế sẽ resize theo frame
                
                # Cập nhật lại width thực tế khi vẽ xong (nâng cao) - ở đây để đơn giản ta vẽ cố định hoặc tương đối
        except: 
            tk.Label(self.machine_list_frame, text="Chưa có dữ liệu", fg="gray", bg=COLOR_CARD_BG).pack()

# ============================================================================
# --- TEST RUN (CHẠY ĐỘC LẬP) ---
# ============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1100x700")
    root.configure(bg=COLOR_BG_MAIN)
    ReportManagerPage(root).pack(fill='both', expand=True)
    root.mainloop()