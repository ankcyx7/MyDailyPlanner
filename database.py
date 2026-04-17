import sqlite3


class PlannerDB:
    def __init__(self, db_name="planner.db"):
        """
        初始化数据库连接。
        如果 planner.db 文件不存在，sqlite3 会自动在当前目录帮你建一个。
        """
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        """
        【内部方法】建表操作。
        我们使用 context manager (with 语句)，这样代码执行完会自动关闭连接，防止文件被锁死。
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # 这里的字段完全按照我们之前在 PRD 里敲定的结构来设计
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time_period TEXT NOT NULL,
                    content TEXT NOT NULL,
                    is_completed INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    # ==========================
    # 下面是提供给 UI 层调用的四个接口 (增删改查)
    # ==========================

    def add_task(self, date_str, time_period, content):
        """【增】添加一条新任务"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # 使用 ? 作为占位符可以有效防止 SQL 注入攻击，这是行业标准写法
            cursor.execute(
                "INSERT INTO tasks (date, time_period, content, is_completed) VALUES (?, ?, ?, 0)",
                (date_str, time_period, content)
            )
            conn.commit()

    def get_tasks_by_date(self, date_str):
        """【查】获取某一天的所有任务"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, time_period, content, is_completed FROM tasks WHERE date = ?",
                (date_str,)
            )
            # fetchall() 会返回一个列表，列表里每个元素是一个元组 (id, time_period, content, is_completed)
            return cursor.fetchall()

    def toggle_task_status(self, task_id, is_completed):
        """【改】切换任务的完成状态 (划掉 / 取消划掉)"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET is_completed = ? WHERE id = ?",
                (is_completed, task_id)
            )
            conn.commit()

    def delete_task(self, task_id):
        """【删】彻底删除一条任务 (用于手抖打错字的情况)"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()


# ==========================================
# 本地测试代码：只有直接运行当前文件时才会执行
# ==========================================
if __name__ == "__main__":
    # 实例化我们的数据库对象
    db = PlannerDB()

    # 模拟写入几条今天的数据
    today = "2026-04-18"
    db.add_task(today, "morning", "吃一顿丰盛的早餐")
    db.add_task(today, "afternoon", "学习 PyCharm 的基本用法")
    db.add_task(today, "evening", "出去跑个步")

    # 把刚才写入的数据查出来打印看看
    print(f"--- {today} 的任务清单 ---")
    tasks = db.get_tasks_by_date(today)
    for task in tasks:
        print(f"ID: {task[0]} | 时段: {task[1]} | 内容: {task[2]} | 是否完成: {'是' if task[3] else '否'}")