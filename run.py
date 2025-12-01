from controller.login_cus_contr import LoginController
from model.login_model import create_tables

if __name__ == "__main__":
    create_tables()
    app = LoginController()
    app.run()