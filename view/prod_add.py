import tkinter as tk
from tkinter import ttk, messagebox

# --- Giả lập config.py (Màu sắc từ hình ảnh) ---
COLOR_BG = "#4E4E4E"
COLOR_BG_LIGHT = "#5A5A5A"
COLOR_ENTRY_BG = "#555555"
COLOR_TEXT_LIGHT = "#FFFFFF"
COLOR_PLACEHOLDER = "#AAAAAA"
COLOR_GREEN = "#4CAF50"
COLOR_RED = "#F44336"
font_default = ("Arial", 10)
font_bold = ("Arial", 10, "bold")
# --- Kết thúc giả lập ---


class ProductForm(tk.Toplevel):
    def __init__(self, parent, controller, category_list, product_id=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.product_id = product_id
        self.category_lookup = dict(category_list)

        self.COLOR_BG = COLOR_BG
        self.COLOR_ENTRY_BG = COLOR_ENTRY_BG
        self.COLOR_TEXT_LIGHT = COLOR_TEXT_LIGHT
        self.COLOR_PLACEHOLDER = COLOR_PLACEHOLDER
        self.COLOR_GREEN = COLOR_GREEN
        self.COLOR_RED = COLOR_RED

        self.font_default = font_default
        self.font_bold = font_bold

        if self.product_id:
            self.title("Chỉnh sửa sản phẩm")
        else:
            self.title("Thêm sản phẩm mới")

        self.product_data = None
        self.config(bg=self.COLOR_BG)
        self.geometry("400x450")
        self.grab_set()
        self.resizable(False, False)

        # Style cho Combobox
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure(
            "TCombobox",
            fieldbackground=self.COLOR_ENTRY_BG,
            background=self.COLOR_ENTRY_BG,
            foreground=self.COLOR_TEXT_LIGHT,
            arrowcolor=self.COLOR_TEXT_LIGHT,
            selectbackground=self.COLOR_ENTRY_BG,
            selectforeground=self.COLOR_TEXT_LIGHT,
        )

        # Placeholder cho Entries
        self.placeholders = {
            "Tên sản phẩm": "Nhập tên sản phẩm",
            "Mã DM": "Nhập mã danh mục",   # Chỉ dùng cho combobox
            "Mã vạch": "Nhập mã vạch",
            "Giá": "Nhập giá",
            "Số lượng": "Nhập số lượng"
        }

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=self.COLOR_BG)
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)

        fields = ["Mã SP", "Tên sản phẩm", "Mã DM", "Tên DM", "Mã vạch", "Giá", "Số lượng"]
        self.entries = {}

        row_count = 0
        for field in fields:

            if field == "Mã SP" and self.product_id is None:
                continue

            label = tk.Label(
                main_frame, text=f"{field}:", bg=self.COLOR_BG,
                fg=self.COLOR_TEXT_LIGHT, font=self.font_default
            )
            label.grid(row=row_count, column=0, sticky="w", pady=10)

            # --- Combobox cho Mã DM ---
            if field == "Mã DM":
                cb = ttk.Combobox(main_frame, font=self.font_default, width=30, style="TCombobox")
                cb["values"] = list(self.category_lookup.keys())
                cb.grid(row=row_count, column=1, sticky="w", pady=10, ipady=5)
                self.entries[field] = cb

                # Placeholder cho Combobox
                cb.set(self.placeholders["Mã DM"])
                cb.config(foreground=self.COLOR_PLACEHOLDER)

                cb.bind("<<ComboboxSelected>>", self._on_category_select)
                cb.bind("<FocusOut>", self._on_category_select)
                cb.bind("<Return>", self._on_category_select)

            # --- Tên DM (readonly) ---
            elif field == "Tên DM":
                self.ten_dm_display = tk.Entry(
                    main_frame, font=self.font_default, width=32,
                    bg=self.COLOR_ENTRY_BG, fg=self.COLOR_PLACEHOLDER,
                    relief="flat", state="disabled",
                    disabledbackground=self.COLOR_ENTRY_BG,
                    disabledforeground=self.COLOR_PLACEHOLDER
                )
                self.ten_dm_display.grid(row=row_count, column=1, sticky="w", pady=10, ipady=5)

            # --- Giá có đơn vị ---
            elif field == "Giá":
                price_container = tk.Frame(main_frame, bg=self.COLOR_ENTRY_BG)
                entry = tk.Entry(
                    price_container, font=self.font_default,
                    width=25, bg=self.COLOR_ENTRY_BG,
                    fg=self.COLOR_TEXT_LIGHT, relief="flat",
                    insertbackground=self.COLOR_TEXT_LIGHT
                )
                self.entries[field] = entry
                unit = tk.Label(price_container, text="VND", bg=self.COLOR_ENTRY_BG,
                                fg=self.COLOR_PLACEHOLDER, font=self.font_default)

                entry.pack(side="left", fill="x", expand=True, padx=(5, 0), ipady=5)
                unit.pack(side="right", padx=5)

                price_container.grid(row=row_count, column=1, sticky="w", pady=10)

            # --- Entry bình thường ---
            else:
                entry = tk.Entry(
                    main_frame, font=self.font_default, width=32,
                    bg=self.COLOR_ENTRY_BG, fg=self.COLOR_TEXT_LIGHT,
                    relief="flat", insertbackground=self.COLOR_TEXT_LIGHT
                )
                entry.grid(row=row_count, column=1, sticky="w", pady=10, ipady=5)
                self.entries[field] = entry

            # Disable mã SP
            if field == "Mã SP":
                entry.config(state="disabled", fg=self.COLOR_PLACEHOLDER)

            # Placeholder cho Entry (KHÔNG áp dụng cho combobox)
            if field in self.placeholders and field != "Mã DM":
                self.add_placeholder(self.entries[field], self.placeholders[field])

            row_count += 1

        # Buttons
        save_text = "Thêm +" if self.product_id is None else "Cập nhật"

        btn_save = tk.Button(
            main_frame, text=save_text, bg=self.COLOR_GREEN, fg=self.COLOR_TEXT_LIGHT,
            font=self.font_bold, width=12, relief="flat", command=self.on_save
        )
        btn_save.grid(row=row_count, column=1, sticky="e", pady=20)

        btn_cancel = tk.Button(
            main_frame, text="Hủy", bg=self.COLOR_RED, fg=self.COLOR_TEXT_LIGHT,
            font=self.font_bold, width=12, relief="flat", command=self.destroy
        )
        btn_cancel.grid(row=row_count, column=0, sticky="w", pady=20)

    def _on_category_select(self, event=None):
        try:
            cb = self.entries["Mã DM"]
            value = cb.get()

            cb.config(foreground=self.COLOR_TEXT_LIGHT)

            ten_dm = self.category_lookup.get(value, "")

            self.ten_dm_display.config(state="normal")
            self.ten_dm_display.delete(0, "end")

            if ten_dm:
                self.ten_dm_display.insert(0, ten_dm)
                self.ten_dm_display.config(fg=self.COLOR_TEXT_LIGHT)
            else:
                self.ten_dm_display.insert(0, "--- Không tìm thấy ---")
                self.ten_dm_display.config(fg=self.COLOR_RED)

            self.ten_dm_display.config(state="disabled")

        except Exception as e:
            print("Lỗi chọn danh mục:", e)

    def add_placeholder(self, entry, placeholder):
        entry.insert(0, placeholder)
        entry.config(fg=self.COLOR_PLACEHOLDER)

        entry.bind("<FocusIn>", lambda e: self._focus_in(entry, placeholder))
        entry.bind("<FocusOut>", lambda e: self._focus_out(entry, placeholder))

    def _focus_in(self, entry, placeholder):
        if entry.get() == placeholder and entry.cget("fg") == self.COLOR_PLACEHOLDER:
            entry.delete(0, "end")
            entry.config(fg=self.COLOR_TEXT_LIGHT)

    def _focus_out(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=self.COLOR_PLACEHOLDER)

    def load_data(self, product_data):
        self.product_data = product_data

        if "Mã SP" in self.entries:
            self.load_entry_data(self.entries["Mã SP"], "ma_sp")

        self.load_entry_data(self.entries["Tên sản phẩm"], "ten_sp")
        self.load_entry_data(self.entries["Mã DM"], "ma_dm")
        self.load_entry_data(self.entries["Mã vạch"], "ma_vach")
        self.load_entry_data(self.entries["Giá"], "gia")
        self.load_entry_data(self.entries["Số lượng"], "so_luong")

        self._on_category_select()

    def load_entry_data(self, entry, key):
        value = self.product_data.get(key, "")

        entry.delete(0, "end")
        entry.insert(0, str(value))
        entry.config(fg=self.COLOR_TEXT_LIGHT)

    def on_save(self):
        data = {}
        for field, entry in self.entries.items():

            if field == "Mã DM":
                if entry.get() == self.placeholders["Mã DM"]:
                    data[field] = ""
                else:
                    data[field] = entry.get()
                continue

            placeholder = self.placeholders.get(field, "")
            if entry.get() == placeholder and entry.cget("fg") == self.COLOR_PLACEHOLDER:
                data[field] = ""
            else:
                data[field] = entry.get()

        final_data = {
            "ten_sp": data.get("Tên sản phẩm", ""),
            "ma_dm": data.get("Mã DM", ""),
            "ma_vach": data.get("Mã vạch", ""),
            "gia": data.get("Giá", ""),
            "so_luong": data.get("Số lượng", "")
        }

        self.controller.save_product(final_data, self.product_id)

    def show_error(self, message):
        messagebox.showerror("Lỗi", message, parent=self)

    def show_info_and_close(self, message):
        messagebox.showinfo("Thành công", message, parent=self.parent)
        self.destroy()
