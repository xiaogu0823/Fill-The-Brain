from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from utils.dialog_utils import show_styled_message_box
from utils.i18n import get_language_manager
from utils.ui_scaling import apply_window_scaling


class ProductSelectionDialog(QDialog):
    def __init__(self, available_products, parent=None):
        super().__init__(parent)
        self.available_products = available_products
        self.language_manager = get_language_manager()
        self.use_manual_input = True
        self.selected_product = ""
        self.empty_choice_text = self.language_manager.tr("no_products_available")
        self._loading_combobox = False
        self.manual_input_touched = False
        self.combo_selection_touched = False
        self.setup_ui()
        self.language_manager.language_changed.connect(self.apply_translations)
        self.apply_translations()

    def setup_ui(self):
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        self.title_label = QLabel()
        layout.addWidget(self.title_label)

        self.group_box = QGroupBox()
        group_layout = QVBoxLayout()

        manual_layout = QVBoxLayout()
        self.manual_label = QLabel()
        manual_layout.addWidget(self.manual_label)
        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.on_manual_input_changed)
        manual_layout.addWidget(self.line_edit)
        group_layout.addLayout(manual_layout)

        combo_layout = QVBoxLayout()
        self.combo_label = QLabel()
        combo_layout.addWidget(self.combo_label)
        self.combo_box = QComboBox()
        self._loading_combobox = True
        if self.available_products:
            self.combo_box.addItems(self.available_products)
            self.combo_box.setCurrentIndex(0)
            self.use_manual_input = False
        else:
            self.combo_box.addItem(self.empty_choice_text)
            self.combo_box.setEnabled(False)
            self.use_manual_input = True
        self._loading_combobox = False
        self.combo_box.currentTextChanged.connect(self.on_combobox_changed)
        combo_layout.addWidget(self.combo_box)
        group_layout.addLayout(combo_layout)

        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton()
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.ok_button.setDefault(True)
        self.cancel_button = QPushButton()
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.update_input_states()
        apply_window_scaling(self)

    def apply_translations(self):
        tr = self.language_manager.tr
        self.empty_choice_text = tr("no_products_available")
        self.setWindowTitle(tr("select_next_product_title"))
        self.title_label.setText(tr("select_next_product_label"))
        self.group_box.setTitle(tr("selection_mode_group"))
        self.manual_label.setText(tr("enter_new_product_label"))
        self.line_edit.setPlaceholderText(tr("type_product_name_placeholder"))
        self.combo_label.setText(tr("choose_existing_products_label"))
        self.ok_button.setText(tr("confirm_button"))
        self.cancel_button.setText(tr("cancel_button"))

        if not self.available_products:
            self.combo_box.blockSignals(True)
            self.combo_box.clear()
            self.combo_box.addItem(self.empty_choice_text)
            self.combo_box.blockSignals(False)

    def on_manual_input_changed(self, text):
        if text.strip():
            self.manual_input_touched = True
            self.use_manual_input = True
            self.update_input_states()

    def on_combobox_changed(self, text):
        if self._loading_combobox:
            return
        if text.strip() and text != self.empty_choice_text:
            self.combo_selection_touched = True
            self.use_manual_input = False
            self.update_input_states()

    def update_input_states(self):
        combo_style = """
            QComboBox {
                background-color: #f7fbff;
                color: #1f2937;
                border: 2px solid #667eea;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #1f2937;
                selection-background-color: #667eea;
                selection-color: #ffffff;
            }
        """
        line_style = """
            QLineEdit {
                background-color: #f7fbff;
                color: #1f2937;
                border: 2px solid #667eea;
                border-radius: 6px;
                padding: 6px 10px;
            }
        """
        self.line_edit.setStyleSheet(line_style)
        self.combo_box.setStyleSheet(combo_style)

    def validate_and_accept(self):
        manual_input = self.line_edit.text().strip()
        selected_value = self.combo_box.currentText().strip()
        if (
            manual_input
            and selected_value
            and selected_value != self.empty_choice_text
            and self.manual_input_touched
            and self.combo_selection_touched
        ):
            show_styled_message_box(
                self,
                QMessageBox.Warning,
                self.language_manager.tr("selection_conflict_title"),
                self.language_manager.tr("login_selection_conflict_text"),
            )
            return

        if self.use_manual_input:
            product_name = manual_input
        else:
            product_name = selected_value

        if not product_name or product_name == self.empty_choice_text:
            show_styled_message_box(
                self,
                QMessageBox.Warning,
                self.language_manager.tr("input_error_title"),
                self.language_manager.tr("valid_product_name_required"),
            )
            return

        if self.parent() and hasattr(self.parent(), "product_tests"):
            for test in self.parent().product_tests:
                if test.get("product_name") == product_name:
                    reply = show_styled_message_box(
                        self,
                        QMessageBox.Warning,
                        self.language_manager.tr("existing_product_title"),
                        self.language_manager.tr(
                            "existing_product_message",
                            product_name=product_name,
                        ),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        return
                    break

        self.selected_product = product_name
        self.accept()

    def get_selected_product(self):
        return self.selected_product
