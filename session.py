# session.py
class CurrentUser:
    user_id = None
    username = ""
    full_name = "" 
    role = ""

    @classmethod
    def set_user(cls, u_id, u_name, u_full_name, u_role):
        cls.user_id = u_id
        cls.username = u_name
        cls.full_name = u_full_name
        cls.role = u_role

    @classmethod
    def clear(cls):
        cls.user_id = None
        cls.username = ""
        cls.full_name = ""
        cls.role = ""