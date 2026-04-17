import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class CloudPlannerDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    # --- 登录相关接口 ---
    def sign_up(self, email, password):
        """注册新用户"""
        return self.supabase.auth.sign_up({"email": email, "password": password})

    def sign_in(self, email, password):
        """邮箱登录"""
        return self.supabase.auth.sign_in_with_password({"email": email, "password": password})

    # --- 数据操作接口 ---
    def add_task(self, user_id, date_str, time_period, content):
        data = {
            "user_id": user_id,
            "date": date_str,
            "time_period": time_period,
            "content": content,
            "is_completed": False
        }
        return self.supabase.table("tasks").insert(data).execute()

    def get_tasks(self, user_id, date_str):
        return self.supabase.table("tasks") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("date", date_str) \
            .execute()

    def update_task(self, task_id, is_completed):
        return self.supabase.table("tasks") \
            .update({"is_completed": is_completed}) \
            .eq("id", task_id) \
            .execute()

    def delete_task(self, task_id):
        return self.supabase.table("tasks").delete().eq("id", task_id).execute()

