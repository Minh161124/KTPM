# main.py
import customtkinter as ctk
from page_list_games import GameListPage
from page_install_game import GameInstallPage
from page_home import HomePage  # THÊM DÒNG NÀY

ctk.set_appearance_mode("dark")

class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("G Gaming")
        self.root.geometry("1000x600")
        self.current_page = None
        self.root.after(0, self.show_page, "home")  # MỞ TRANG CHỦ TRƯỚC
        self.root.mainloop()

    def show_page(self, page_name):
        if self.current_page:
            self.current_page.pack_forget()

        if page_name == "home":  # TRANG CHỦ
            self.current_page = ctk.CTkFrame(self.root)
            self.current_page.pack(fill="both", expand=True)
            HomePage(self.current_page, self.show_page)

        elif page_name == "list":  # DANH SÁCH GAME
            self.current_page = ctk.CTkFrame(self.root)
            self.current_page.pack(fill="both", expand=True)
            GameListPage(self.current_page, self.show_page)

        elif page_name == "install":  # CÀI GAME
            self.current_page = ctk.CTkFrame(self.root)
            self.current_page.pack(fill="both", expand=True)
            GameInstallPage(self.current_page, self.show_page)

if __name__ == "__main__":
    App()