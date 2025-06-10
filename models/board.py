class Column:
    def __init__(self, name):
        self.name = name
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def remove_task(self, task):
        self.tasks.remove(task)


class KanbanBoard:
    def __init__(self):
        self.columns = {
            "To Do": Column("To Do"),
            "In Progress": Column("In Progress"),
            "Done": Column("Done"),
        }
