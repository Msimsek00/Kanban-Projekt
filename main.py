import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QListWidgetItem, QDialog, QVBoxLayout,
    QLabel, QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox,
    QTimeEdit, QComboBox, QDateEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime, QDate
from PyQt5.QtGui import QColor, QTextCharFormat, QBrush
from PyQt5 import uic
from fpdf import FPDF


class Task:
    def __init__(self, title, description="", priority="Mittel", due_date=None, reminder_time=None):
        self.title = title
        self.description = description
        self.priority = priority
        self.due_date = due_date  # QDate
        self.reminder_time = reminder_time  # QTime


class TaskDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neue Aufgabe")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()
        self.title_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.priority_input = QComboBox()
        self.priority_input.addItems(["Niedrig", "Mittel", "Hoch"])
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm")
        self.time_input.setTime(QTime.currentTime())

        layout.addWidget(QLabel("Titel:"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("Beschreibung:"))
        layout.addWidget(self.desc_input)
        layout.addWidget(QLabel("Priorität:"))
        layout.addWidget(self.priority_input)
        layout.addWidget(QLabel("Fälligkeitsdatum:"))
        layout.addWidget(self.date_input)
        layout.addWidget(QLabel("Erinnerung (Uhrzeit):"))
        layout.addWidget(self.time_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_task(self):
        return Task(
            self.title_input.text(),
            self.desc_input.toPlainText(),
            self.priority_input.currentText(),
            self.date_input.date(),
            self.time_input.time()
        )


class KanbanApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("kanban.ui", self)

        self.darkmode = False
        self.reminder_timers = []
        self.task_dates = set()

        for widget in [self.listtodo, self.listinprogress, self.listdone]:
            widget.setDragEnabled(True)
            widget.setAcceptDrops(True)
            widget.setDragDropMode(widget.InternalMove)
            widget.setDefaultDropAction(Qt.MoveAction)
            widget.setContextMenuPolicy(Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(self.open_context_menu)

        self.pushButtonaddtot.clicked.connect(lambda: self.add_task(self.listtodo))
        self.btnaddinprogress.clicked.connect(lambda: self.add_task(self.listinprogress))
        self.pushButtondone.clicked.connect(lambda: self.add_task(self.listdone))
        self.pushButtonexportpdf.clicked.connect(self.export_to_pdf)
        self.pushButtondarkmode.clicked.connect(self.toggle_darkmode)
        self.calendarWidget.selectionChanged.connect(self.show_tasks_for_selected_date)

    def add_task(self, list_widget):
        dialog = TaskDialog()
        if dialog.exec_():
            task = dialog.get_task()
            item = self.create_task_item(task)
            list_widget.addItem(item)
            self.setup_reminder(task)
            self.mark_date_on_calendar(task.due_date)

    def create_task_item(self, task):
        item = QListWidgetItem(
            f"{task.title}\n{task.description}\nPriorität: {task.priority}\nFällig: {task.due_date.toString('dd.MM.yyyy')}"
        )
        item.setData(Qt.UserRole, task)
        self.set_item_color(item, task.priority)
        return item

    def set_item_color(self, item, priority):
        colors = {
            "Hoch": Qt.red,
            "Mittel": Qt.yellow,
            "Niedrig": Qt.green
        }
        item.setBackground(colors.get(priority, Qt.white))

    def setup_reminder(self, task):
        datetime = QDateTime(task.due_date, task.reminder_time)
        now = QDateTime.currentDateTime()
        if datetime > now:
            ms_until = now.msecsTo(datetime)
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.show_reminder(task))
            timer.start(ms_until)
            self.reminder_timers.append(timer)

    def show_reminder(self, task):
        QMessageBox.information(self, "Erinnerung", f"🔔 Aufgabe fällig: {task.title}")

    def export_to_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Als PDF speichern", "", "PDF-Dateien (*.pdf)")
        if not filename:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for title, widget in [("To Do", self.listtodo), ("In Progress", self.listinprogress), ("Done", self.listdone)]:
            pdf.set_font("Arial", 'B', size=14)
            pdf.cell(200, 10, title, ln=True)
            pdf.set_font("Arial", size=12)
            for i in range(widget.count()):
                item = widget.item(i)
                task = item.data(Qt.UserRole)
                text = f"{task.title} ({task.priority}) – Fällig: {task.due_date.toString('dd.MM.yyyy')}"
                pdf.multi_cell(0, 10, text)
                if task.description:
                    pdf.set_font("Arial", 'I', 11)
                    pdf.multi_cell(0, 10, f"→ {task.description}")
                    pdf.set_font("Arial", size=12)
            pdf.ln()

        pdf.output(filename)
        QMessageBox.information(self, "Exportiert", f"PDF gespeichert:\n{filename}")

    def show_tasks_for_selected_date(self):
        selected_date = self.calendarWidget.selectedDate()
        matching_tasks = []

        for widget in [self.listtodo, self.listinprogress, self.listdone]:
            for i in range(widget.count()):
                item = widget.item(i)
                task = item.data(Qt.UserRole)
                if task.due_date == selected_date:
                    matching_tasks.append(f"• {task.title} ({task.priority})")

        if matching_tasks:
            QMessageBox.information(
                self,
                f"Aufgaben am {selected_date.toString('dd.MM.yyyy')}",
                "\n".join(matching_tasks)
            )
        else:
            QMessageBox.information(
                self,
                f"Keine Aufgaben am {selected_date.toString('dd.MM.yyyy')}",
                "An diesem Tag gibt es keine Aufgaben mit Fälligkeit."
            )

    def mark_date_on_calendar(self, date: QDate):
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor("orange")))
        self.calendarWidget.setDateTextFormat(date, fmt)

    def open_context_menu(self, position):
        sender_list = self.sender()
        item = sender_list.itemAt(position)
        if not item:
            return

        menu = QMessageBox()
        menu.setWindowTitle("Aktion auswählen")
        menu.setText(f"Was möchtest du mit '{item.text().splitlines()[0]}' machen?")
        edit_button = menu.addButton("Bearbeiten", QMessageBox.AcceptRole)
        delete_button = menu.addButton("Löschen", QMessageBox.DestructiveRole)
        cancel_button = menu.addButton("Abbrechen", QMessageBox.RejectRole)
        menu.exec_()

        if menu.clickedButton() == edit_button:
            self.edit_task(item, sender_list)
        elif menu.clickedButton() == delete_button:
            sender_list.takeItem(sender_list.row(item))

    def edit_task(self, item, list_widget):
        old_task = item.data(Qt.UserRole)
        dialog = TaskDialog()
        dialog.title_input.setText(old_task.title)
        dialog.desc_input.setPlainText(old_task.description)
        dialog.priority_input.setCurrentText(old_task.priority)
        dialog.date_input.setDate(old_task.due_date)
        dialog.time_input.setTime(old_task.reminder_time)

        if dialog.exec_():
            new_task = dialog.get_task()
            new_item = self.create_task_item(new_task)
            list_widget.takeItem(list_widget.row(item))
            list_widget.addItem(new_item)
            self.setup_reminder(new_task)
            self.mark_date_on_calendar(new_task.due_date)

    def toggle_darkmode(self):
        if not self.darkmode:
            dark_stylesheet = """
            QMainWindow { background-color: #2b2b2b; color: white; }
            QLabel, QPushButton, QListWidget, QLineEdit, QTextEdit, QComboBox, QCalendarWidget {
                background-color: #3c3f41;
                color: white;
                border: 1px solid #555;
            }
            QListWidget::item:selected {
                background-color: #505050;
            }
            """
            self.setStyleSheet(dark_stylesheet)
            self.darkmode = True
        else:
            self.setStyleSheet("")
            self.darkmode = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KanbanApp()
    window.setWindowTitle("📅 Kanban mit Kalender, Erinnerungen & Darkmode")
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec_())
