class Task:
    def __init__(self, title, description="", due_date=None, priority="Mittel"):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
