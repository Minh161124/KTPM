import tkinter as tk
from tkinter import font as tkFont

class LoginView(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Đăng nhập hệ thống")
        self.geometry("800x650")
        self.configure(bg="black")
        self.resizable(False, False)
        
        # Biến lưu trữ controller để gọi lại
        self.controller = None

        self._setup_ui()

    def set_controller(self, controller):
        self.controller = controller

    def _setup_ui(self):
        label_font = tkFont.Font(family="Arial", size=10, weight="bold")
        entry_font = tkFont.Font(family="Arial", size=12)
        logon_font = tkFont.Font(family="Arial", size=70, weight="bold")
        button_font = tkFont.Font(family="Arial", size=14, weight="bold")

        tk.Label(self, text="LOGIN", font=logon_font, fg="#E63950", bg="black").pack(pady=(160, 50))

        form_frame = tk.Frame(self, bg="black")
        form_frame.pack(pady=0, padx=200)

        # Email
        tk.Label(form_frame, text="EMAIL / PHONE NUMBER:", font=label_font,
                 fg="white", bg="black", anchor="w").pack(fill="x", pady=(0, 5))

        self.email_entry = tk.Entry(form_frame, font=entry_font, bg="#111", fg="white",
                               insertbackground="white", relief="solid", borderwidth=1)
        self.email_entry.pack(fill="x", pady=(0, 20), ipady=5)

        # Password
        tk.Label(form_frame, text="PASSWORD:", font=label_font,
                 fg="white", bg="black", anchor="w").pack(fill="x", pady=(0, 5))

        self.password_entry = tk.Entry(form_frame, font=entry_font, show="*", bg="#111", fg="white",
                                  insertbackground="white", relief="solid", borderwidth=1)
        self.password_entry.pack(fill="x", pady=(0, 10), ipady=5)

        # Options
        options_frame = tk.Frame(form_frame, bg="black")
        options_frame.pack(fill="x", pady=5)
        
        self.save_var = tk.IntVar()
        tk.Checkbutton(options_frame, text="Save password", variable=self.save_var,
                       onvalue=1, offvalue=0, font=label_font, fg="white",
                       bg="black", selectcolor="black").pack(side="left")

        # Button Login
        tk.Button(self, text="LOGIN", font=button_font,
                  fg="white", bg="#D60000", activebackground="#A00000",
                  activeforeground="white", relief="flat", borderwidth=0,
                  pady=5, command=self._on_login_click
                  ).pack(pady=30, ipadx=40, ipady=4)
        
        # Bind phím Enter
        self.bind('<Return>', lambda event: self._on_login_click())

    def _on_login_click(self):
        if self.controller:
            email = self.email_entry.get()
            password = self.password_entry.get()
            self.controller.handle_login(email, password)