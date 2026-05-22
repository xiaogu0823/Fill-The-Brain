from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont
from PyQt5.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from utils.i18n import get_language_manager


class ComprehensiveScoreTable(QWidget):
    """Table widget for the product-level emotional scores."""

    product_name_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_manager = get_language_manager()
        self.product_scores = {}
        self.setup_ui()
        self.language_manager.language_changed.connect(self.apply_translations)
        self.apply_translations()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 22, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.title_label)

        self.table_widget = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table_widget)

        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.stats_label)

    def apply_translations(self):
        self.title_label.setText(self.language_manager.tr("score_table_title"))
        self.setup_headers()
        if not self.product_scores:
            self.stats_label.setText(self.language_manager.tr("score_table_count", count=0))
        else:
            self.populate_table()

    def setup_table(self):
        self.table_widget.setFont(QFont("Microsoft YaHei", 20))
        self.table_widget.setColumnCount(4)
        self.setup_headers()

        header_font = QFont("Microsoft YaHei", 20, QFont.Bold)
        self.table_widget.horizontalHeader().setFont(header_font)
        self.table_widget.horizontalHeader().setVisible(True)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSortingEnabled(False)
        self.table_widget.cellClicked.connect(self.on_cell_clicked)

        self.table_widget.verticalHeader().setDefaultSectionSize(60)
        self.table_widget.horizontalHeader().setMinimumHeight(50)

        header = self.table_widget.horizontalHeader()
        self.table_widget.setColumnWidth(0, 150)
        self.table_widget.setColumnWidth(1, 150)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_widget.setColumnWidth(2, 250)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_widget.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #ddd;
                border: 1px solid #ddd;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
        """
        )
        self._apply_header_tooltip()

    def setup_headers(self):
        headers = [
            self.language_manager.tr("score_table_header_order"),
            self.language_manager.tr("score_table_header_product"),
            self.language_manager.tr("score_table_header_index"),
            self.language_manager.tr("score_table_header_summary"),
        ]
        self.table_widget.setHorizontalHeaderLabels(headers)
        self._apply_header_tooltip()

    def _apply_header_tooltip(self):
        header_item = self.table_widget.horizontalHeaderItem(1)
        if header_item:
            header_item.setToolTip(self.language_manager.tr("score_table_tooltip"))

    def update_product_data(self, product_tests):
        try:
            if not product_tests:
                self.clear_table()
                return

            self.process_product_tests(product_tests.get("products", {}))
            self.sort_products_by_original_order()
            self.populate_table()
        except Exception as exc:
            print(f"Failed to update product data: {exc}")

    def process_product_tests(self, product_tests):
        self.product_scores.clear()
        for product_index, product_data in product_tests.items():
            self.product_scores[product_index] = {
                "product_name": product_data.get("product_name", f"Product_{product_index}"),
                "comprehensive_score": product_data.get("comprehensive_score", 0),
                "dominant_emotions": product_data.get("primary_emotion_reaction", "Pending"),
                "original_index": product_index,
            }

    def sort_products_by_original_order(self):
        if not self.product_scores:
            return
        for order, (product_id, product_data) in enumerate(self.product_scores.items(), 1):
            product_data["rank"] = order
            self.product_scores[product_id] = product_data

    def populate_table(self):
        try:
            self.table_widget.setRowCount(0)
            if not self.product_scores:
                self.stats_label.setText(self.language_manager.tr("score_table_no_data"))
                return

            self.table_widget.setRowCount(len(self.product_scores))
            for row, (_, product_data) in enumerate(self.product_scores.items()):
                self.populate_table_row(row, product_data)

            product_count = len(self.product_scores)
            self.stats_label.setText(self.language_manager.tr("score_table_count", count=product_count))
            self.adjust_column_widths()
        except Exception as exc:
            print(f"Failed to populate the table: {exc}")

    def adjust_column_widths(self):
        self.table_widget.resizeColumnToContents(0)
        self.table_widget.resizeColumnToContents(1)

        col0_width = self.table_widget.columnWidth(0)
        col1_width = self.table_widget.columnWidth(1)
        if col0_width < 100:
            self.table_widget.setColumnWidth(0, 100)
        if col1_width < 150:
            self.table_widget.setColumnWidth(1, 150)

        max_width = 300
        if col0_width > max_width:
            self.table_widget.setColumnWidth(0, max_width)
        if col1_width > max_width:
            self.table_widget.setColumnWidth(1, max_width)

    def populate_table_row(self, row, product_data):
        try:
            rank_item = QTableWidgetItem(str(product_data.get("rank", row + 1)))
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setFlags(rank_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 0, rank_item)

            name = product_data.get("product_name", f"Product_{row + 1}")
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 1, name_item)

            comp_score = product_data.get("comprehensive_score", 0)
            if comp_score > 0:
                score_item = QTableWidgetItem(f"{comp_score:.1f}")
                score_item.setForeground(self.get_score_color(comp_score))
            else:
                score_item = QTableWidgetItem("--")
            score_item.setTextAlignment(Qt.AlignCenter)
            score_item.setFlags(score_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 2, score_item)

            dominant_emotions = product_data.get("dominant_emotions", "Pending")
            emotion_description = (
                dominant_emotions
                if dominant_emotions != "Pending"
                else "No significant emotional fluctuation"
            )
            emotion_description = self.language_manager.translate_emotion_text(emotion_description)
            emotion_item = QTableWidgetItem(emotion_description)
            emotion_item.setTextAlignment(Qt.AlignCenter)
            emotion_item.setFlags(emotion_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 3, emotion_item)
        except Exception as exc:
            print(f"Failed to populate table row {row}: {exc}")

    def get_score_color(self, score):
        if score >= 80:
            return QBrush(QColor(0, 128, 0))
        if score >= 60:
            return QBrush(QColor(255, 165, 0))
        return QBrush(QColor(255, 0, 0))

    def clear_table(self):
        self.table_widget.setRowCount(0)
        self.stats_label.setText(self.language_manager.tr("score_table_count", count=0))
        self.product_scores.clear()

    def update_scores(self, new_scores):
        for product_id, score_data in new_scores.items():
            if product_id in self.product_scores:
                self.product_scores[product_id].update(score_data)
        self.populate_table()

    def on_cell_clicked(self, row, column):
        if column != 1:
            return
        product_item = self.table_widget.item(row, 1)
        if product_item:
            self.product_name_clicked.emit(product_item.text())
