import flet as ft
from datetime import datetime, timedelta
from database_cloud import CloudPlannerDB  # 【关键】改用云端数据库
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


# ==========================================
# UI 组件：任务行（适配云端数据结构）
# ==========================================
class TaskRow(ft.Container):
    def __init__(self, task_id, content, is_completed, delete_cb, status_cb):
        super().__init__()
        self.task_id = task_id
        self.delete_cb = delete_cb
        self.status_cb = status_cb

        self.checkbox = ft.Checkbox(
            value=is_completed,  # 云端传回的是布尔值
            on_change=self.toggle_status,
            fill_color=ft.Colors.BLUE_600
        )
        self.task_text = ft.Text(
            value=content, size=15, expand=True, weight=ft.FontWeight.W_500,
            spans=[ft.TextSpan(style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH))] if is_completed else [],
            color=ft.Colors.GREY_400 if is_completed else ft.Colors.BLACK87
        )
        self.delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_ROUNDED, icon_color=ft.Colors.RED_300,
            on_click=self.delete_clicked, opacity=0.7
        )

        self.bgcolor = ft.Colors.WHITE if not is_completed else ft.Colors.GREY_50
        self.border_radius = 12
        self.padding = ft.Padding.symmetric(horizontal=10, vertical=5)
        self.margin = ft.Margin.only(bottom=10)
        self.shadow = ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.Colors.BLACK12, offset=ft.Offset(0, 4))
        self.animate = ft.Animation(300, "easeOut")
        self.content = ft.Row([self.checkbox, self.task_text, self.delete_btn])

    def toggle_status(self, e):
        is_done = self.checkbox.value
        # 视觉更新
        self.task_text.spans = [
            ft.TextSpan(style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH))] if is_done else []
        self.task_text.color = ft.Colors.GREY_400 if is_done else ft.Colors.BLACK87
        self.bgcolor = ft.Colors.GREY_50 if is_done else ft.Colors.WHITE
        self.update()
        # 云端同步
        self.status_cb(self.task_id, is_done)

    def delete_clicked(self, e):
        self.delete_cb(self)


# ==========================================
# 主程序逻辑
# ==========================================
def main(page: ft.Page):
    page.title = "Cloud Planner"
    page.window.width = 400
    page.window.height = 800
    page.bgcolor = "#F7F9FC"
    page.theme_mode = ft.ThemeMode.LIGHT

    db = CloudPlannerDB()
    user_session = None  # 存储当前登录的用户信息
    current_date_obj = datetime.now()

    # --- UI 引用声明 ---
    main_view = ft.Column(visible=False, expand=True)  # 主手账本界面
    login_view = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)  # 登录界面

    # ================= 1. 登录逻辑 =================
    email_input = ft.TextField(label="电子邮箱", border_radius=15)
    pw_input = ft.TextField(label="密码", password=True, can_reveal_password=True, border_radius=15)
    login_msg = ft.Text(color=ft.Colors.RED_400)

    def handle_login(e):
        try:
            res = db.sign_in(email_input.value, pw_input.value)
            nonlocal user_session
            user_session = res.user
            show_planner()
        except Exception as err:
            login_msg.value = "登录失败: 账号或密码错误"
            page.update()

    def handle_register(e):
        try:
            db.sign_up(email_input.value, pw_input.value)
            login_msg.value = "注册成功！请查收邮箱验证邮件后登录。"
            login_msg.color = ft.Colors.GREEN_600
            page.update()
        except Exception as err:
            login_msg.value = f"注册失败: {err}"
            page.update()

    login_view.controls = [
        ft.Container(height=100),
        ft.Icon(ft.Icons.CLOUD_DONE_ROUNDED, size=80, color=ft.Colors.BLUE_600),
        ft.Text("我的云端手账", size=28, weight=ft.FontWeight.W_800),
        ft.Text("数据实时同步，永不丢失", color=ft.Colors.GREY_600),
        ft.Container(height=30),
        email_input,
        pw_input,
        login_msg,
        ft.Container(height=10),
        ft.ElevatedButton("立即登录", on_click=handle_login, width=300, height=50,
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))),
        ft.TextButton("还没有账号？点此注册", on_click=handle_register),
    ]

    # ================= 2. 手账本逻辑 (迁移至云端) =================
    date_display = ft.Container(
        content=ft.Text(value="", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        bgcolor=ft.Colors.BLUE_50, padding=ft.Padding.symmetric(horizontal=20, vertical=8), border_radius=20
    )

    def refresh_data():
        date_str = current_date_obj.strftime("%Y-%m-%d")
        date_display.content.value = date_str

        # 清空 UI 容器
        for section in [morning_list, afternoon_list, evening_list]:
            section.controls.clear()

        # 从云端抓取
        res = db.get_tasks(user_session.id, date_str)
        for t in res.data:
            row = TaskRow(
                task_id=t['id'], content=t['content'], is_completed=t['is_completed'],
                delete_cb=lambda r, p=t['time_period']: delete_task_cloud(r, p),
                status_cb=lambda tid, stat: db.update_task(tid, stat)
            )
            get_list_by_period(t['time_period']).controls.append(row)
        page.update()

    def add_task_cloud(period_id, input_field, target_list):
        if input_field.value.strip():
            db.add_task(user_session.id, current_date_obj.strftime("%Y-%m-%d"), period_id, input_field.value)
            input_field.value = ""
            refresh_data()

    def delete_task_cloud(task_row, period_id):
        db.delete_task(task_row.task_id)
        refresh_data()

    def get_list_by_period(p):
        return {"morning": morning_list, "afternoon": afternoon_list, "evening": evening_list}[p]

    # --- 区块定义 ---
    def create_section(title, icon, pid):
        input_f = ft.TextField(hint_text="记点什么...", expand=True, height=45, border_radius=25,
                               bgcolor=ft.Colors.BLUE_GREY_50, border_color=ft.Colors.TRANSPARENT)
        l_view = ft.Column()
        return ft.Column([
            ft.Text(f"{icon} {title}", size=18, weight=ft.FontWeight.BOLD),
            l_view,
            ft.Row([input_f, ft.IconButton(ft.Icons.ADD_CIRCLE_ROUNDED, icon_color=ft.Colors.BLUE_600,
                                           on_click=lambda e: add_task_cloud(pid, input_f, l_view))])
        ]), l_view

    sec_m, morning_list = create_section("上午", "🌅", "morning")
    sec_a, afternoon_list = create_section("下午", "☕", "afternoon")
    sec_e, evening_list = create_section("晚上", "🌙", "evening")

    main_view.controls = [
        ft.Row([ft.Text("My Cloud Planner", size=24, weight=ft.FontWeight.W_800)],
               alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: change_date(-1)),
            date_display,
            ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=lambda _: change_date(1)),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        sec_m, sec_a, sec_e,
        ft.ElevatedButton("退出登录", icon=ft.Icons.LOGOUT, on_click=lambda _: page.window_destroy())
    ]

    def change_date(delta):
        nonlocal current_date_obj
        current_date_obj += timedelta(days=delta)
        refresh_data()

    def show_planner():
        login_view.visible = False
        main_view.visible = True
        refresh_data()
        page.update()

    page.add(login_view, main_view)


def change_date(delta):
    pass  # 逻辑已在 main 内部处理


ft.run(main)