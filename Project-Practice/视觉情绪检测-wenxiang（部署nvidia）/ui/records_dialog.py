import pandas as pd
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
)

from utils.dialog_utils import show_styled_message_box
from utils.i18n import get_language_manager
from utils.ui_scaling import apply_window_scaling


class TestRecordsViewerDialog(QDialog):
    """Record query, filtering, and export dialog."""

    def __init__(self, record_logger, parent=None):
        super().__init__(parent)
        self.record_logger = record_logger
        self.language_manager = get_language_manager()
        self.current_df = pd.DataFrame()
        self.resize(1180, 720)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setup_ui()
        self.language_manager.language_changed.connect(self.apply_translations)
        self.apply_translations()
        self.run_query()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.filter_group = QGroupBox()
        filter_layout = QHBoxLayout(self.filter_group)

        self.person_id_edit = QLineEdit()
        filter_layout.addWidget(self.person_id_edit)

        self.product_name_edit = QLineEdit()
        filter_layout.addWidget(self.product_name_edit)

        self.enable_date_filter = QCheckBox()
        filter_layout.addWidget(self.enable_date_filter)

        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setEnabled(False)
        self.date_edit.setStyleSheet(
            """
            QDateEdit {
                background-color: #f7fbff;
                color: #1f2937;
                border: 1px solid #94a3b8;
                border-radius: 6px;
                padding: 6px 8px;
            }
            QDateEdit::drop-down {
                width: 24px;
                border-left: 1px solid #cbd5e1;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #eff6ff;
                background-color: #ffffff;
                color: #1f2937;
            }
            QCalendarWidget QToolButton {
                color: #1f2937;
                background-color: #e2e8f0;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #1f2937;
                background-color: #ffffff;
                selection-background-color: #667eea;
                selection-color: white;
            }
        """
        )
        self.enable_date_filter.toggled.connect(self.date_edit.setEnabled)
        filter_layout.addWidget(self.date_edit)

        self.query_button = QPushButton()
        self.query_button.clicked.connect(self.run_query)
        filter_layout.addWidget(self.query_button)

        self.reset_button = QPushButton()
        self.reset_button.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_button)

        layout.addWidget(self.filter_group)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.table_widget = QTableWidget()
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(False)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()
        self.export_button = QPushButton()
        self.export_button.clicked.connect(self.export_current_records)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()

        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        apply_window_scaling(self)

    def apply_translations(self):
        tr = self.language_manager.tr
        self.setWindowTitle(tr("records_center_title"))
        self.filter_group.setTitle(tr("filters_group"))
        self.person_id_edit.setPlaceholderText(tr("participant_id"))
        self.product_name_edit.setPlaceholderText(tr("product_name"))
        self.enable_date_filter.setText(tr("filter_by_test_date"))
        self.query_button.setText(tr("search_button"))
        self.reset_button.setText(tr("reset_button"))
        self.export_button.setText(tr("export_results_button"))
        self.close_button.setText(tr("close"))
        if not self.current_df.empty or self.table_widget.columnCount() > 0:
            self.populate_table(self.current_df)

    def reset_filters(self):
        self.person_id_edit.clear()
        self.product_name_edit.clear()
        self.enable_date_filter.setChecked(False)
        self.date_edit.setDate(QDate.currentDate())
        self.run_query()

    def run_query(self):
        try:
            test_date = self.date_edit.date().toString("yyyy-MM-dd") if self.enable_date_filter.isChecked() else ""
            self.current_df = self.record_logger.filter_records(
                person_id=self.person_id_edit.text().strip(),
                product_name=self.product_name_edit.text().strip(),
                test_date=test_date,
            )
            self.populate_table(self.current_df)
            self.info_label.setText(
                f"{self.language_manager.tr('record_file_info', file_path=self.record_logger.file_path)}\n"
                f"{self.language_manager.tr('current_result_count', count=len(self.current_df))}"
            )
        except Exception as exc:
            show_styled_message_box(
                self,
                QMessageBox.Critical,
                self.language_manager.tr("query_failed_title"),
                self.language_manager.tr("query_failed_message", error=exc),
            )

    def populate_table(self, df):
        self.table_widget.clear()
        if df.empty:
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(len(self.record_logger.FIELDNAMES))
            self.table_widget.setHorizontalHeaderLabels(
                self.language_manager.get_record_headers(self.record_logger.FIELDNAMES)
            )
            return

        self.table_widget.setRowCount(len(df))
        self.table_widget.setColumnCount(len(df.columns))
        headers = self.language_manager.get_record_headers([str(col) for col in df.columns])
        self.table_widget.setHorizontalHeaderLabels(headers)
        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iat[row, col]
                text = "" if pd.isna(value) else str(value)
                if str(df.columns[col]) == "Composite Index" and text:
                    try:
                        text = f"{float(text):.1f}"
                    except (TypeError, ValueError):
                        pass
                if str(df.columns[col]) == "Emotional Response":
                    text = self.language_manager.translate_emotion_text(text)
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table_widget.setItem(row, col, item)
        self.table_widget.resizeColumnsToContents()

    def export_current_records(self):
        try:
            if self.current_df.empty:
                show_styled_message_box(
                    self,
                    QMessageBox.Information,
                    self.language_manager.tr("notice_title"),
                    self.language_manager.tr("no_records_to_export"),
                )
                return
            export_path = self.record_logger.export_records(self.current_df)
            show_styled_message_box(
                self,
                QMessageBox.Information,
                self.language_manager.tr("export_complete_title"),
                self.language_manager.tr("export_complete_message", path=export_path),
            )
        except Exception as exc:
            show_styled_message_box(
                self,
                QMessageBox.Critical,
                self.language_manager.tr("export_failed_title"),
                self.language_manager.tr("export_failed_message", error=exc),
            )
