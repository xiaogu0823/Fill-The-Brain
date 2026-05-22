from PyQt5.QtWidgets import QMessageBox

from utils.i18n import get_language_manager


PURPLE_MESSAGE_BOX_STYLESHEET = """
QMessageBox {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #667eea, stop:1 #764ba2);
    border: 2px solid #5d6dde;
    border-radius: 16px;
}
QMessageBox QLabel {
    min-width: 520px;
    color: white;
    font-size: 20px;
    padding: 6px 2px;
    background: transparent;
}
QMessageBox QPushButton {
    min-width: 150px;
    min-height: 52px;
    padding: 8px 18px;
    font-size: 18px;
    font-weight: bold;
    border: none;
    border-radius: 12px;
    background-color: white;
    color: #5a6fd8;
}
QMessageBox QPushButton:hover {
    background-color: #eef2ff;
}
"""


def show_styled_message_box(
    parent,
    icon,
    title,
    text,
    buttons=QMessageBox.Ok,
    default_button=QMessageBox.NoButton,
):
    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setStandardButtons(buttons)
    if default_button != QMessageBox.NoButton:
        msg_box.setDefaultButton(default_button)
    msg_box.setStyleSheet(PURPLE_MESSAGE_BOX_STYLESHEET)
    get_language_manager().localize_message_box_buttons(msg_box)
    return msg_box.exec_()
