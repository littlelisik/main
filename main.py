import sys

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QTableWidgetItem, QAbstractItemView

from front_py.autoriz import Ui_Autoriz
from front_py.user import Ui_User
from front_py.create_mession import Ui_create_mission
from front_py.admin import Ui_Admin

from database import select, update

class AutorizationWindow(QMainWindow, Ui_Autoriz):
    """
    Окно авторизации пользователей
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Авторизация")
        self.user_id = None
        self.log_but.clicked.connect(self.autoriz)
        self.set_icon()

    def set_icon(self):
        """
        Загружает иконку приложения.
        """
        try:
            pixmap = QPixmap("icon/icon.png")
            if not pixmap.isNull():
                self.icon.setPixmap(pixmap)
                self.icon.setScaledContents(True)
        except Exception as e:
            print(f"Ошибка загрузки иконки: {e}")

    def autoriz(self):
        login = self.log_edit.text().strip()
        password = self.pass_edit.text().strip()

        try:
            query = """SELECT id, role FROM users 
                       WHERE login = %s AND password = %s"""
            result = select(query, (login, password))
            result = result[0]

            if result:
                user_id, role = result
                if role == "user":
                    self.open_user_window(user_id)
                elif role == "admin":
                    self.open_admin_window()
                else:
                    QMessageBox.warning(self, "Ошибка", "У вас нет доступа")
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при авторизации: {e}")

    def open_user_window(self, user_id):
        self.user_window = UserWindow(self, user_id)
        self.user_window.show()
        self.hide()

    def open_admin_window(self):
        self.admin_window = AdminWindow(self)
        self.admin_window.show()
        self.hide()

class UserWindow(QMainWindow, Ui_User):
    """
    Окно обычного пользователя
    """
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.setupUi(self)
        self.user_id = user_id
        self.setWindowTitle("Окно пользователя")
        self.out_but.clicked.connect(self.open_autoriz_window)

    def open_autoriz_window(self):
        self.autoriz_window = AutorizationWindow(self)
        self.autoriz_window.show()
        self.hide()

class CreateMissionWindow(QMainWindow, Ui_create_mission):
    """
    Окно создания нового поручения
    """
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Создание нового поручения")

class AdminWindow(QMainWindow, Ui_Admin):
    """
    Окно администратора
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Окно Администратора")
        # Разрешаем редактирование таблицы
        self.users_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.out_but.clicked.connect(self.open_autoriz_window)
        self.delete_but.clicked.connect(self.delete_user)
        self.create_but.clicked.connect(self.create_new_user)
        self.edit_but.clicked.connect(self.edit_user_data)
        self.output_to_user_table()
        self.output_to_combobox()

    def output_to_user_table(self):
        try:
            result = select(''' SELECT u.login, u.role, u.email, d.name_dep FROM users u
                               JOIN department d ON u.id_department = d.id''')
            if not result:
                QMessageBox.information(self, "Информация", "Нет данных для отображения")
                return

            column_headers = ['Логин', 'Роль', 'Почта', 'Отдел']
            self.users_tableWidget.setColumnCount(len(column_headers))  # Устанавливаем количество столбцов
            self.users_tableWidget.setHorizontalHeaderLabels(column_headers)  # Устанавливаем заголовки

            # Устанавливаем количество строк
            self.users_tableWidget.setRowCount(len(result))

            # Заполняем таблицу данными
            for row_num, row_data in enumerate(result):
                for col_num, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))  # Преобразуем данные в строку
                    self.users_tableWidget.setItem(row_num, col_num, item)
        except:
            QMessageBox.warning(self, "Ошибка", "Ошибка при выводе данных")

    def output_to_combobox(self):
        """Заполняет комбо-боксы ролями и отделами из БД"""
        try:
            # Заполняем роли
            if not self.role_comboBox.count():
                result = select("SELECT role FROM users GROUP BY role")
                self.role_comboBox.addItems(role[0] for role in result)

            # Заполняем отделы
            if not self.department_comboBox.count():
                result = select("SELECT name_dep FROM department")
                self.department_comboBox.addItems(name[0] for name in result)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные, {str(e)}")

    def edit_user_data(self):
        """Сохраняет изменения только для выбранного пользователя"""
        selected_row = self.users_tableWidget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для редактирования")
            return
        try:
            login = self.users_tableWidget.item(selected_row, 0).text()
            new_role = self.users_tableWidget.item(selected_row, 1).text()
            new_email = self.users_tableWidget.item(selected_row, 2).text()
            new_department_name = self.users_tableWidget.item(selected_row, 3).text()

            result = select("SELECT id FROM department WHERE name_dep = %s", [new_department_name])
            department_id = result[0][0]

            if not department_id:
                QMessageBox.warning(self, "Ошибка", f"Отдел '{new_department_name}' не найден!")
                return
            update("""
                UPDATE users 
                SET role = %s, email = %s, id_department = %s 
                WHERE login = %s
            """, [new_role, new_email, department_id[0], login])
            QMessageBox.information(self, "Успех", "Изменения сохранены")
            print(f"Updating: {login}, {new_role}, {new_email}, {department_id}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")
        finally:
            self.output_to_user_table()


    def delete_user(self):
        """Удаляет выбранного пользователя из БД и обновляет таблицу"""
        selected_row = self.users_tableWidget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления")
            return

        login = self.users_tableWidget.item(selected_row, 0).text()

        try:
            update("DELETE FROM users WHERE login = %s", (login,))
            QMessageBox.information(self, "Успех", "Пользователь удален")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
        finally:
            self.output_to_user_table()  # Обновляем таблицу

    def create_new_user(self):
        """Создает нового пользователя в БД"""
        try:
            # Получаем данные из полей ввода
            login = self.log_edit.text().strip()
            password = self.pass_edit.text().strip()
            email = self.email_edit.text().strip()
            role = self.role_comboBox.currentText()
            department_name = self.department_comboBox.currentText()

            if not all([login, password, email, role, department_name]):
                return QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены")

            department_id = select("SELECT id from department WHERE name_dep = %s", [department_name])[0][0]

            result = select("SELECT 1 FROM users WHERE login = %s", (login,))
            if result:
                return QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует")

            # Создание нового пользователя
            update(
                "INSERT INTO users (login, password, email, role, id_department) VALUES (%s, %s, %s, %s, %s)",
                (login, password, email, role, department_id))
            # Очистка полей
            self.log_edit.clear()
            self.pass_edit.clear()
            self.email_edit.clear()
            QMessageBox.information(self, "Успех", "Пользователь успешно создан")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании пользователя: {str(e)}")
        finally:
            self.output_to_user_table()

    def open_autoriz_window(self):
        self.parent().show()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutorizationWindow()
    window.show()
    sys.exit(app.exec())


import pymysql

def connect_to_database():
    try:
        db = pymysql.connect(
            host = "localhost",
            user = "root",
            password = "",
            database = "db_doc_2"
    )
        print("Подключение установлено!")
        return db
    except:
        print("Не удалось подключиться!")
        return None

connection = connect_to_database()

def select(query, args=None):
    cursor = connection.cursor()
    try:
        print(query, args)
        cursor.execute(query, args)
        return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        raise e
    finally:
        cursor.close()

def update(query, args=None):
    cursor = connection.cursor()
    try:
        print(query, args)
        cursor.execute(query, args)
        connection.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        connection.rollback()
        raise e
    finally:
        cursor.close()



