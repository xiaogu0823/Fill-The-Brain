import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QDialog,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QHBoxLayout,
)

from camera.camera_manager import CameraManager
from emo_process.video_calibration_worker import GlobalAnalysisManager
from ui.combine_window import ProjectsTestWindow
from ui.login_window import LoginWindow
from utils.dialog_utils import show_styled_message_box
from utils.i18n import get_language_manager
from utils.logger import get_logger
from utils.signal_manager import SignalManager
from utils.ui_scaling import enable_high_dpi


class WindowController:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.language_manager = get_language_manager()
        enable_high_dpi()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.logger.info("Window controller initialized.")

        self.is_shutting_down = False
        self.window_signals = SignalManager()
        self.app.aboutToQuit.connect(self.shutdown)

        self.login_window = None
        self.test_window = None
        self.camera_manager = None

        self.current_person_id = ""
        self.current_product_name = ""
        self.calibration_guide_shown = False

        self.emotion_model_path = "/home/nvidia/workspace/wenxiang/weights/mv3_fp.engine"
        self.face_model_path = "/home/nvidia/workspace/wenxiang/weights/yolov11n-face.engine"
        self.emonet_path = "/home/nvidia/workspace/wenxiang/weights/emonet_v1.engine"
        self.calibration_guide_image_path = Path("/home/nvidia/workspace/wenxiang/calibration_guide.png")

        self.analysis_manager = GlobalAnalysisManager()
        self.analysis_manager.init_analyzer(
            self.emotion_model_path,
            self.face_model_path,
            self.emonet_path,
        )

    def minimize_active_window(self):
        window = self.app.activeWindow() or self.test_window or self.login_window
        if window:
            window.showMinimized()

    def request_app_exit(self):
        if self.is_shutting_down:
            return
        self.logger.info("Received ESC exit request.")
        self.shutdown()
        self.app.quit()

    def shutdown(self):
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        for window_name in ("test_window", "login_window"):
            window = getattr(self, window_name, None)
            if window:
                try:
                    window.close()
                except Exception as exc:
                    self.logger.warning(f"Failed to close {window_name}: {exc}")
                finally:
                    setattr(self, window_name, None)

        self.window_signals.disconnect_all()

        if self.camera_manager:
            try:
                self.camera_manager.release()
            except Exception as exc:
                self.logger.warning(f"Failed to release camera resources: {exc}")

    def show_login(self):
        if self.login_window:
            self.login_window.close()

        self.camera_manager = CameraManager()
        self.login_window = LoginWindow()
        self.login_window.minimize_requested.connect(self.minimize_active_window)
        self.login_window.close_requested.connect(self.request_app_exit)
        self.window_signals.connect(self.login_window.login_success, self.on_login_success)
        self.login_window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.login_window.showFullScreen()
        self.logger.info("Login window displayed in full-screen mode.")

    def on_login_success(self, person_id, product_name):
        self.current_person_id = person_id
        self.current_product_name = product_name
        self.calibration_guide_shown = False

        if self.login_window:
            self.login_window.close()
            self.login_window = None

        self.show_test()

    def set_calibration_guide_image_path(self, image_path):
        self.calibration_guide_image_path = Path(image_path)

    def show_test(self):
        try:
            if self.test_window:
                self.test_window.close()

            self.test_window = ProjectsTestWindow(
                self.current_person_id,
                self.current_product_name,
                self.analysis_manager,
                self.camera_manager,
            )
            self.test_window.minimize_requested.connect(self.minimize_active_window)
            self.test_window.close_requested.connect(self.request_app_exit)
            self.window_signals.connect(self.test_window.test_complete, self.on_test_complete)
            self.test_window.showFullScreen()
            self.show_calibration_guide_if_available()
            self.logger.info(
                "ProjectsTestWindow created for person_id=%s, product=%s",
                self.current_person_id,
                self.current_product_name,
            )
        except Exception as exc:
            self.logger.error(f"Failed to create the test window: {exc}")
            show_styled_message_box(
                None,
                QMessageBox.Critical,
                self.language_manager.tr("error_title"),
                self.language_manager.tr("failed_launch_test_window"),
            )

    def on_test_complete(self):
        show_styled_message_box(
            self.test_window,
            QMessageBox.Information,
            self.language_manager.tr("workflow_complete_title"),
            self.language_manager.tr(
                "workflow_complete_message",
                person_id=self.current_person_id,
                product_name=self.current_product_name,
            ),
        )

        if self.test_window:
            self.test_window.close()
            self.test_window = None

        self.show_login()

    def show_calibration_guide_if_available(self):
        if self.calibration_guide_shown or not self.test_window:
            return
        if not self.calibration_guide_image_path.exists():
            return

        dialog = QDialog(self.test_window)
        dialog.setWindowTitle("Calibration Guide")
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #5a6fd8;
                border-radius: 16px;
            }
            QLabel {
                color: white;
                font-size: 18px;
                background: transparent;
            }
            QPushButton {
                background-color: white;
                color: #4c5bc6;
                border: none;
                border-radius: 10px;
                min-width: 180px;
                min-height: 48px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eef2ff;
            }
            QToolButton {
                background-color: rgba(255, 255, 255, 0.18);
                color: white;
                border: none;
                border-radius: 10px;
                min-width: 42px;
                min-height: 42px;
                font-size: 20px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.28);
            }
            """
        )
        dialog.resize(960, 820)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        close_button = QToolButton(dialog)
        close_button.setText("x")
        close_button.clicked.connect(dialog.reject)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        image_label = QLabel(dialog)
        image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(str(self.calibration_guide_image_path))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(860, 660, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        layout.addWidget(image_label)

        confirm_button = QPushButton("我已知晓", dialog)
        confirm_button.clicked.connect(dialog.accept)
        layout.addWidget(confirm_button, alignment=Qt.AlignCenter)

        self.calibration_guide_shown = True
        dialog.exec_()

    def run(self):
        self.show_login()
        sys.exit(self.app.exec_())
