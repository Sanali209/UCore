class TaskService:
    def __init__(self):
        self._tasks = []

    def add_task(self, description: str):
        self._tasks.append({"description": description, "completed": False})

    def list_tasks(self):
        return [
            {"index": i, "description": t["description"], "completed": t["completed"]}
            for i, t in enumerate(self._tasks)
        ]

    def complete_task(self, index: int):
        if 0 <= index < len(self._tasks):
            self._tasks[index]["completed"] = True
            return True
        return False
