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

import  pymysql

def get_db_connection():
    return pymysql.connect(
        host = "localhost",
        user = "root",
        password = "",
        database = "fabrik",
        cursorclass = pymysql.cursors.DictCursor
    )




from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QFormLayout, QPushButton, QMessageBox, QLabel
from PyQt6.QtCore import Qt

from db import get_db_connection


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Настройка основного окна
        self.setWindowTitle("Авторизация")
        self.setFixedSize(200, 200)
        self.setWindowIcon(QIcon("aaa.png"))
        self.setStyleSheet("background-color: #FFFFFF; font-family: Segoe UI")

        layout = QVBoxLayout(self)

        # Создание и настройка логотипа
        logo = QLabel()
        logo.setPixmap(QPixmap("aaa.png").scaled(150, 50, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        # Поля для ввода логина и пароля
        self.login = QLineEdit()
        self.passw = QLineEdit()
        self.passw.setEchoMode(QLineEdit.EchoMode.Password)

        # Форма для полей ввода
        form = QFormLayout()
        form.addRow("Логин:", self.login)
        form.addRow("Пароль:", self.passw)
        layout.addLayout(form)

        # Кнопка входа
        btn = QPushButton("Войти")
        btn.clicked.connect(self.verifi)
        layout.addWidget(btn)

        btn.setStyleSheet("background: #67BA80; color: white; padding: 5px;")

    #Метод для проверки авторизации пользователя
    def verifi(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("select login, password from manager where login = %s and password = %s",
                                (self.login.text(), self.passw.text()))
                    if cur.fetchone():
                        self.accept()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Неправильный логин или пароль, возможно вы не заполнили поля")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных:{e}")











from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QHBoxLayout, QPushButton, QTableWidgetItem, QMessageBox, \
    QLabel
from PyQt6.QtCore import Qt


from add_product import AddProduct
from db import get_db_connection
from ceh import Ceh


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        #Настройка основного окна
        self.setWindowTitle("Главное окно продукции")
        self.setFixedSize(900, 600)
        self.setWindowIcon(QIcon("aaa.png"))
        self.setStyleSheet("background-color: #FFFFFF; font-family: Segoe UI")

        layout = QVBoxLayout(self)

        #Добавление логотипа
        logo = QLabel()
        logo.setPixmap(QPixmap("aaa.png").scaled(150, 50, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        #Создание таблицы для отображения продукции
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Номер продукта", "Название", "Тип продукта", "Артикул", "Мин. цена для партнера", "Тип материала", "Время изготовления"])
        layout.addWidget(self.table)

        btn_la = QHBoxLayout()

        #Создание кнопок для управления
        add_pr = QPushButton("Добавить продукт")
        dlt_pr = QPushButton("Удалить продукт")
        edit_pr = QPushButton("Редактировать продукт")
        ceh = QPushButton("Посмотреть цеха")

        add_pr.clicked.connect(self.add_pr)
        dlt_pr.clicked.connect(self.dlt_pr)
        edit_pr.clicked.connect(self.edit_pr)
        ceh.clicked.connect(self.ceh)

        btn_la.addWidget(add_pr)
        btn_la.addWidget(dlt_pr)
        btn_la.addWidget(edit_pr)
        btn_la.addWidget(ceh)

        add_pr.setStyleSheet("background: #67BA80; color: white; padding: 5px;")
        dlt_pr.setStyleSheet("background: #67BA80; color: white; padding: 5px;")
        edit_pr.setStyleSheet("background: #2196F3; color: white; padding: 5px;")
        ceh.setStyleSheet("background: #67BA80; color: white; padding: 5px;")

        layout.addLayout(btn_la)

        #Загрузка данных в таблицу
        self.load()

    #Метод для редактирования выбранного продукта
    def edit_pr(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите продукт для редактирования")
            return

        product_id = self.table.item(selected_row, 0).text()

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""SELECT * FROM product WHERE id = %s""", (product_id,))
                    product_data = cur.fetchone()

                    if not product_data:
                        QMessageBox.warning(self, "Ошибка", "Продукт не найден")
                        return

                    dialog = AddProduct()
                    dialog.name.setText(product_data['name'])
                    dialog.articul.setText(product_data['articul'])
                    dialog.min.setText(product_data['min_cena'])

                    for i in range(dialog.tip_pr.count()):
                        if dialog.tip_pr.itemData(i) == product_data['tip_product']:
                            dialog.tip_pr.setCurrentIndex(i)
                            break

                    for i in range(dialog.tip_mat.count()):
                        if dialog.tip_mat.itemData(i) == product_data['tip_material']:
                            dialog.tip_mat.setCurrentIndex(i)
                            break

                    for i in range(dialog.ceh.count()):
                        if dialog.ceh.itemData(i) == product_data['ceh_id']:
                            dialog.ceh.setCurrentIndex(i)
                            break

                    if dialog.exec():
                        if dialog.success:
                            name, tip_pr, articul, min_cena, tip_mat, ceh = dialog.get_data()
                            cur.execute("""UPDATE product SET 
                                        name = %s, 
                                        tip_product = %s, 
                                        articul = %s, 
                                        min_cena = %s, 
                                        tip_material = %s, 
                                        ceh_id = %s 
                                        WHERE id = %s""",
                                        (name, tip_pr, articul, min_cena, tip_mat, ceh, product_id))
                            conn.commit()
                            self.load()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных: {e}")

    #Метод для открытия окна управления цехами
    def ceh(self):
        window = Ceh()
        window.exec()

    #Метод загрузки данных о продукции в таблицу
    def load(self):
        self.table.setRowCount(0)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""select p.id, p.name, tp.name_product, p.articul, p.min_cena, m.name_material, c.vremya
                    from product p
                    join tip_product tp on p.tip_product = tp.id
                    join material m on p.tip_material = m.id
                    join ceh c on p.ceh_id = c.id""")
                    for row in cur.fetchall():
                        row_pos = self.table.rowCount()
                        self.table.insertRow(row_pos)
                        self.table.setItem(row_pos, 0, QTableWidgetItem(str(row["id"])))
                        self.table.setItem(row_pos, 1, QTableWidgetItem(row["name"]))
                        self.table.setItem(row_pos, 2, QTableWidgetItem(row["name_product"]))
                        self.table.setItem(row_pos, 3, QTableWidgetItem(row["articul"]))
                        self.table.setItem(row_pos, 4, QTableWidgetItem(row["min_cena"]))
                        self.table.setItem(row_pos, 5, QTableWidgetItem(row["name_material"]))
                        self.table.setItem(row_pos, 6, QTableWidgetItem(row["vremya"]))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных:{e}")

    #Метод для добавления нового продукта
    def add_pr(self):
        dialog = AddProduct()
        if dialog.exec():
            if dialog.success:
                name, tip_pr, articul, min_cena, tip_mat, ceh = dialog.get_data()
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("insert into product(name, tip_product, articul, min_cena, tip_material, ceh_id) values(%s, %s, %s, %s, %s, %s)",
                                        (name, tip_pr, articul, min_cena, tip_mat, ceh))
                            conn.commit()
                            self.load()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных:{e}")

    #Метод для удаления продукта
    def dlt_pr(self):
        scrld = self.table.currentRow()
        if scrld >=0:
            try:
                id = self.table.item(scrld, 0).text()
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("delete from product where id = %s", (id, ))
                        conn.commit()
                        self.load()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных:{e}")








from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QVBoxLayout, QTableWidget, QHBoxLayout, QPushButton, QTableWidgetItem, QMessageBox, \
    QDialog

from add_ceh import AddCeh
from db import get_db_connection


class Ceh(QDialog):
    def __init__(self):
        super().__init__()

        #Настройка основного окна
        self.setWindowTitle("Окно цехов")
        self.setFixedSize(500, 400)
        self.setWindowIcon(QIcon("aaa.png"))
        self.setStyleSheet("background-color: #FFFFFF; font-family: Segoe UI")

        layout = QVBoxLayout(self)

        #Создание таблицы для отображения цехов
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels (["Номер цеха", "Название цеха", "Количество человек", "Время затраченное на реализацию"])
        layout.addWidget(self.table)

        btn_la = QHBoxLayout()

        #Создание кнопок управления
        add_c = QPushButton("Добавить цех")
        dlt_c = QPushButton("Удалить цех")
        edit_c = QPushButton("Редактировать цех")

        add_c.clicked.connect(self.add_c)
        dlt_c.clicked.connect(self.dlt_c)
        edit_c.clicked.connect(self.edit_c)

        add_c.setStyleSheet("background: #67BA80; color: white; padding: 5px;")
        dlt_c.setStyleSheet("background: #67BA80; color: white; padding: 5px;")
        edit_c.setStyleSheet("background: #2196F3; color: white; padding: 5px;")

        btn_la.addWidget(add_c)
        btn_la.addWidget(dlt_c)
        btn_la.addWidget(edit_c)

        layout.addLayout(btn_la)

        #Загрузка данных в таблицу
        self.load()

    #Метод для редактирования выбранного цеха
    def edit_c(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите цех для редактирования")
            return

        ceh_id = self.table.item(selected_row, 0).text()

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""SELECT * FROM ceh WHERE id = %s""", (ceh_id,))
                    ceh_data = cur.fetchone()

                    if not ceh_data:
                        QMessageBox.warning(self, "Ошибка", "Цех не найден")
                        return

                    dialog = AddCeh()
                    dialog.name.setText(ceh_data['name_ceh'])
                    dialog.chelovek.setText(ceh_data['chelovek'])
                    dialog.vremya.setText(ceh_data['vremya'])

                    if dialog.exec():
                        if dialog.success:
                            name, chelovek, vremya = dialog.get_data()
                            cur.execute("""UPDATE ceh SET 
                                        name_ceh = %s, 
                                        chelovek = %s, 
                                        vremya = %s 
                                        WHERE id = %s""",
                                        (name, chelovek, vremya, ceh_id))
                            conn.commit()
                            self.load()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных: {e}")

    #Метод загрузки данных о цехах в таблицу
    def load(self):
        self.table.setRowCount(0)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""select c.id, c.name_ceh, c.chelovek, c.vremya
                    from ceh c""")
                    for row in cur.fetchall():
                        row_pos = self.table.rowCount()
                        self.table.insertRow(row_pos)
                        self.table.setItem(row_pos, 0, QTableWidgetItem(str(row["id"])))
                        self.table.setItem(row_pos, 1, QTableWidgetItem(row["name_ceh"]))
                        self.table.setItem(row_pos, 2, QTableWidgetItem(row["chelovek"]))
                        self.table.setItem(row_pos, 3, QTableWidgetItem(row["vremya"]))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных:{e}")

    #Метод для добавления нового цеха
    def add_c(self):
        dialog = AddCeh()
        if dialog.exec():
            if dialog.success:
                name, chelovek, vremya  = dialog.get_data()
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute ("insert into ceh(name_ceh, chelovek, vremya) values(%s, %s, %s)",
                                        (name, chelovek, vremya))
                            conn.commit()
                            self.load()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных:{e}")

    #Метод для удаления цеха
    def dlt_c(self):
        scrld = self.table.currentRow()
        if scrld >=0:
            try:
                id = self.table.item(scrld, 0).text()
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("delete from ceh where id = %s", (id,))
                        conn.commit()
                        self.load()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка базы данных:{e}")






                

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox


class AddCeh(QDialog):
    def __init__(self):
        super().__init__()

        # Настройка основного окна
        self.setWindowTitle("Добавление цеха")
        self.setFixedSize(500, 500)
        self.setWindowIcon(QIcon("aaa.png"))
        self.setStyleSheet("background-color: #FFFFFF; font-family: Segoe UI")

        layout = QVBoxLayout(self)

        # Создание полей ввода
        self.name = QLineEdit()
        self.chelovek = QLineEdit()
        self.vremya = QLineEdit()

        # Добавление подписей и полей ввода в layout
        layout.addWidget(QLabel("Введите название цеха:"))
        layout.addWidget(self.name)

        layout.addWidget(QLabel("Введите количество человек в цеху:"))
        layout.addWidget(self.chelovek)

        layout.addWidget(QLabel("Введите время на создание в минутах:"))
        layout.addWidget(self.vremya)

        # Создание и настройка кнопки сохранения
        btn = QPushButton("Сохранить")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)
        btn.setStyleSheet("background: #67BA80; color: white; padding: 5px;")

        # Флаг успешного сохранения
        self.success = False

    def save(self):
        # Проверка, что все поля заполнены
        if not self.name.text() or not self.chelovek.text() or not self.vremya.text():
            QMessageBox.critical(self, "Ошибка заполнения полей", "Заполните все поля")
            return

        self.success = True

        self.accept()

    def get_data(self):
        return (
            self.name.text(),
            self.chelovek.text(),
            self.vremya.text()
        )





from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QMessageBox


from db import get_db_connection


class AddProduct(QDialog):
    def __init__(self):
        super().__init__()

        # Настройка основного окна
        self.setWindowTitle("Добавление продукта")
        self.setFixedSize(300, 300)
        self.setWindowIcon(QIcon("aaa.png"))
        self.setStyleSheet("background-color: #FFFFFF; font-family: Segoe UI")

        layout = QVBoxLayout(self)

        # Создание полей ввода и выбора
        self.name = QLineEdit()
        self.tip_pr = QComboBox()
        self.articul = QLineEdit()
        self.min = QLineEdit()
        self.tip_mat = QComboBox()
        self.ceh = QComboBox()

        #Заполнение выпадающих списков
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select id, name_product from tip_product")
                for row in cur.fetchall():
                    self.tip_pr.addItem(row["name_product"], row["id"])

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select id, name_material from material")
                for row in cur.fetchall():
                    self.tip_mat.addItem(row["name_material"], row["id"])

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select id, name_ceh from ceh")
                for row in cur.fetchall():
                    self.ceh.addItem(row["name_ceh"], row["id"])

        # Добавление элементов в layout с подписями
        layout.addWidget(QLabel("Введите название продукта:"))
        layout.addWidget(self.name)

        layout.addWidget(QLabel("Выберите тип родукта:"))
        layout.addWidget(self.tip_pr)

        layout.addWidget(QLabel("Введите артикул:"))
        layout.addWidget(self.articul)

        layout.addWidget(QLabel("Введите минимальную стоимость для партнера:"))
        layout.addWidget(self.min)

        layout.addWidget(QLabel("Выберите тип материала:"))
        layout.addWidget(self.tip_mat)

        layout.addWidget(QLabel("Выберите цех изготовитель:"))
        layout.addWidget(self.ceh)

        # Кнопка сохранения
        btn = QPushButton("Сохранить")
        btn.clicked.connect(self.save)

        btn.setStyleSheet("background: #67BA80; color: white; padding: 5px;")

        layout.addWidget(btn)

        self.success = False

    def save(self):
        # Проверка, что все поля заполнены
        if not self.name.text() or not self.articul.text() or not self.min.text():
            QMessageBox.critical(self, "Ошибка заполнения полей", "Заполните все поля")
            return
        self.success = True
        self.accept()

    def get_data(self):
        return(
            self.name.text(),
            self.tip_pr.currentData(),
            self.articul.text(),
            self.min.text(),
            self.tip_mat.currentData(),
            self.ceh.currentData()
        )








import sys

from PyQt6.QtWidgets import QApplication

from login_dialog import LoginDialog
from main_window import MainWindow

app = QApplication(sys.argv)
login = LoginDialog()
if login.exec():
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



pip install pyinstaller
pyinstaller --onefile --windowed main.py


pip freeze > requirements.txt





# Система управления производством для мебельной фабрики (PyQt6 + MySQL)

## Функционал

### Основные модули
1. Авторизация
   - Вход по логину/паролю
   - Проверка прав доступа


2. Управление цехами
   - Добавление/удаление цехов
   - Редактирование параметров:
     - Название цеха
     - Количество работников
     - Время производства


3. Управление продукцией
   - Каталог изделий
   - Добавление новых продуктов:
     - Название
     - Артикул
     - Тип продукта
     - Материал
     - Цех-изготовитель
   - Редактирование и удаление


4. Работа с БД
   - Хранение данных:
     - Цехи
     - Продукция
     - Материалы
     - Пользователи


## Быстрый старт
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python main.py





# Перейдите в папку проекта

git init

git add .

git commit -m "приложение"

git remote add origin https://github.com/YaroslavSilyanov/prob

git push -u origin main

# Если ветка называется master:
git push -u origin master



