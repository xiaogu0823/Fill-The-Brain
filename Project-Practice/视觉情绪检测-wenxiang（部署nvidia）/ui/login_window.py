import os

from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPushButton, QToolButton

import config.settings as config
from utils.dialog_utils import show_styled_message_box
from utils.i18n import get_language_manager
from utils.ui_scaling import apply_window_scaling


class LoginWindow(QMainWindow):
    login_success = pyqtSignal(str, str)
    minimize_requested = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.showMinimized()
        self.load_ui_file("main_window.ui")
        apply_window_scaling(self)

        self.setGeometry(0, 0, 0, 0)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        self.language_manager = get_language_manager()
        self.use_manual_input = None
        self.recorded_ids = set()
        self.records_file = "recorded_ids.txt"
        self._loading_combobox = False
        self.manual_input_touched = False
        self.combo_selection_touched = False

        self.setup_toolbar_buttons()
        self.setup_connections()
        self.load_combobox_from_file()
        self.load_recorded_ids()
        self.update_input_states()
        self.language_manager.language_changed.connect(self.apply_translations)
        self.apply_translations()

    def load_ui_file(self, ui_filename):
        ui_path = config.UI_FILES_DIR / ui_filename
        if not ui_path.exists():
            raise FileNotFoundError(f"UI file not found: {ui_path}")
        uic.loadUi(str(ui_path), self)

    def setup_toolbar_buttons(self):
        self.language_button = QPushButton(self)
        self.language_button.setFixedSize(110, 54)
        self.language_button.setCursor(Qt.PointingHandCursor)
        self.language_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.95);
                color: #374151;
                border: 2px solid rgba(102, 126, 234, 0.35);
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #ffffff;
                border-color: #667eea;
            }
            """
        )
        self.language_button.clicked.connect(self.language_manager.toggle_language)
        self.language_button.raise_()

        self.minimize_button = QToolButton(self)
        self.minimize_button.setText("-")
        self.minimize_button.setFixedSize(54, 54)
        self.minimize_button.setCursor(Qt.PointingHandCursor)
        self.minimize_button.setStyleSheet(
            """
            QToolButton {
                background-color: rgba(255, 255, 255, 0.95);
                color: #334155;
                border: 2px solid rgba(102, 126, 234, 0.25);
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #ffffff;
                border-color: #667eea;
            }
            """
        )
        self.minimize_button.clicked.connect(self.minimize_requested.emit)
        self.minimize_button.raise_()

        self.close_button = QToolButton(self)
        self.close_button.setText("x")
        self.close_button.setFixedSize(54, 54)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet(
            """
            QToolButton {
                background-color: rgba(239, 68, 68, 0.92);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 22px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: rgba(220, 38, 38, 0.96);
            }
            """
        )
        self.close_button.clicked.connect(self.close_requested.emit)
        self.close_button.raise_()

    def setup_connections(self):
        self.pushButton.clicked.connect(self.on_login_clicked)
        self.id_lineEdit.returnPressed.connect(self.on_login_clicked)
        self.name_lineEdit.returnPressed.connect(self.on_login_clicked)
        self.name_lineEdit.textChanged.connect(self.on_manual_input_changed)
        self.select_comboBox.currentTextChanged.connect(self.on_combobox_changed)
        self.id_lineEdit.editingFinished.connect(self.check_id_duplicate)

    def apply_translations(self):
        tr = self.language_manager.tr
        self.setWindowTitle(tr("login_window_title"))
        self.main_title.setText(tr("login_main_title"))
        self.id_label.setText(tr("login_id_label"))
        self.id_lineEdit.setPlaceholderText(tr("login_id_placeholder"))
        self.name_label.setText(tr("login_name_label"))
        self.name_lineEdit.setPlaceholderText(tr("login_name_placeholder"))
        self.label.setText(tr("login_optional_products"))
        self.pushButton.setText(tr("login_button"))
        self.language_button.setText(self.language_manager.get_language_button_text())
        self.language_button.setToolTip(self.language_manager.get_language_button_tooltip())
        self.position_language_button()

    def position_language_button(self):
        if not hasattr(self, "language_button"):
            return
        margin = 24
        close_x = max(margin, self.width() - self.close_button.width() - margin)
        minimize_x = close_x - self.minimize_button.width() - 12
        language_x = margin
        y = margin
        self.language_button.move(language_x, y)
        self.language_button.raise_()
        self.minimize_button.move(minimize_x, y)
        self.minimize_button.raise_()
        self.close_button.move(close_x, y)
        self.close_button.raise_()

    def on_manual_input_changed(self, text):
        if text.strip():
            self.manual_input_touched = True
            self.use_manual_input = True
            self.update_input_states()

    def on_combobox_changed(self):
        current_text = self.select_comboBox.currentText().strip()
        if self._loading_combobox:
            return
        if current_text:
            self.combo_selection_touched = True
            self.use_manual_input = False
            self.update_input_states()

    def update_input_states(self):
        combo_style = """
            QComboBox {
                background-color: #f0f8ff;
                color: #1f2937;
            }
        """
        manual_style = ""
        self.select_comboBox.setStyleSheet(combo_style if self.use_manual_input is False else manual_style)
        self.name_lineEdit.setStyleSheet(manual_style)

    def on_login_clicked(self):
        person_id = self.id_lineEdit.text().strip()
        manual_input = self.name_lineEdit.text().strip()
        combobox_selection = self.select_comboBox.currentText().strip()
        is_duplicate_id = person_id in self.recorded_ids

        if manual_input and combobox_selection and self.manual_input_touched and self.combo_selection_touched:
            QMessageBox.warning(
                self,
                self.language_manager.tr("selection_conflict_title"),
                self.language_manager.tr("login_selection_conflict_text"),
            )
            return

        if manual_input:
            product_name = manual_input
            self.use_manual_input = True
        elif combobox_selection:
            product_name = combobox_selection
            self.use_manual_input = False
        else:
            show_styled_message_box(
                self,
                QMessageBox.Warning,
                self.language_manager.tr("input_error_title"),
                self.language_manager.tr("enter_or_choose_product_name"),
            )
            return

        if not person_id:
            show_styled_message_box(
                self,
                QMessageBox.Warning,
                self.language_manager.tr("input_error_title"),
                self.language_manager.tr("enter_participant_id"),
            )
            return

        if is_duplicate_id:
            reply = show_styled_message_box(
                self,
                QMessageBox.Warning,
                self.language_manager.tr("duplicate_id_title"),
                self.language_manager.tr("duplicate_id_confirm", person_id=person_id),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                self.id_lineEdit.setFocus()
                self.id_lineEdit.selectAll()
                return
        else:
            self.save_record_id(person_id)

        mode = "manual input" if self.use_manual_input else "existing product selection"
        print(
            f"Login info - mode: {mode}, participant_id: {person_id}, "
            f"product_name: {product_name}"
        )
        self.login_success.emit(person_id, product_name)

    def load_recorded_ids(self):
        try:
            if not os.path.exists(self.records_file):
                return

            with open(self.records_file, "r", encoding="utf-8") as file:
                for line in file:
                    person_id = line.strip()
                    if person_id:
                        self.recorded_ids.add(person_id)
        except Exception as exc:
            print(f"Failed to load recorded IDs: {exc}")
            self.recorded_ids = set()

    def save_record_id(self, person_id):
        try:
            if person_id in self.recorded_ids:
                return

            with open(self.records_file, "a", encoding="utf-8") as file:
                file.write(person_id + "\n")
            self.recorded_ids.add(person_id)
            print(f"Recorded ID: {person_id}")
        except Exception as exc:
            print(f"Failed to save recorded ID: {exc}")
            show_styled_message_box(
                self,
                QMessageBox.Warning,
                self.language_manager.tr("save_error_title"),
                self.language_manager.tr("save_record_failed", error=exc),
            )

    def check_id_duplicate(self):
        person_id = self.id_lineEdit.text().strip()
        if person_id and person_id in self.recorded_ids:
            show_styled_message_box(
                self,
                QMessageBox.Warning,
                self.language_manager.tr("duplicate_id_title"),
                self.language_manager.tr("duplicate_id_notice", person_id=person_id),
            )

    def load_combobox_from_file(self):
        file_path = "ui/options.txt"
        try:
            self._loading_combobox = True
            with open(file_path, "r", encoding="utf-8") as file:
                options_list = [line.strip() for line in file if line.strip()]

            self.select_comboBox.clear()
            self.select_comboBox.addItems(options_list)

            if options_list:
                self.select_comboBox.setCurrentIndex(0)
                self.use_manual_input = False
            else:
                self.select_comboBox.setCurrentIndex(-1)
                self.use_manual_input = None
            self.combo_selection_touched = False

            print(f"Loaded {len(options_list)} product options from '{file_path}'.")
        except FileNotFoundError:
            show_styled_message_box(
                self,
                QMessageBox.Critical,
                self.language_manager.tr("file_error_title"),
                self.language_manager.tr("cannot_find_file", file_path=file_path),
            )
        except Exception as exc:
            show_styled_message_box(
                self,
                QMessageBox.Critical,
                self.language_manager.tr("error_title"),
                self.language_manager.tr("read_file_failed", error=exc),
            )
        finally:
            self._loading_combobox = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_language_button()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
