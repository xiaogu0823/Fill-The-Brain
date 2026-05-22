import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLayout, QWidget


BASE_WIDTH = 1920
BASE_HEIGHT = 1080
MIN_SCALE = 0.75
MAX_SCALE = 1.35


def enable_high_dpi():
    """在 QApplication 创建前启用高 DPI 支持。"""
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def get_scale_factor(app=None):
    app = app or QApplication.instance()
    if app and app.primaryScreen():
        geometry = app.primaryScreen().availableGeometry()
        width = max(geometry.width(), 1)
        height = max(geometry.height(), 1)
    else:
        desktop = QApplication.desktop()
        geometry = desktop.availableGeometry() if desktop else None
        width = max(geometry.width(), 1) if geometry else BASE_WIDTH
        height = max(geometry.height(), 1) if geometry else BASE_HEIGHT

    scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
    return max(MIN_SCALE, min(scale, MAX_SCALE))


def scale_value(value, scale):
    return max(1, int(round(value * scale)))


def scale_stylesheet(stylesheet, scale):
    if not stylesheet or abs(scale - 1.0) < 0.01:
        return stylesheet

    def replace_px(match):
        value = float(match.group(1))
        return f"{scale_value(value, scale)}px"

    return re.sub(r"(\d+(?:\.\d+)?)px", replace_px, stylesheet)


def _scale_font(widget, scale):
    font = widget.font()
    if not font:
        return

    pixel_size = font.pixelSize()
    if pixel_size > 0:
        font.setPixelSize(scale_value(pixel_size, scale))
        widget.setFont(font)
        return

    point_size = font.pointSizeF()
    if point_size > 0:
        font.setPointSizeF(max(1.0, point_size * scale))
        widget.setFont(font)


def _scale_widget_size(widget, scale):
    min_size = widget.minimumSize()
    max_size = widget.maximumSize()

    has_fixed_size = (
        min_size.width() > 0
        and min_size.height() > 0
        and min_size == max_size
        and max_size.width() < 16777215
        and max_size.height() < 16777215
    )
    if has_fixed_size:
        widget.setFixedSize(
            scale_value(min_size.width(), scale),
            scale_value(min_size.height(), scale),
        )
        return

    if min_size.width() > 0 or min_size.height() > 0:
        widget.setMinimumSize(
            scale_value(min_size.width(), scale) if min_size.width() > 0 else 0,
            scale_value(min_size.height(), scale) if min_size.height() > 0 else 0,
        )

    if max_size.width() < 16777215 or max_size.height() < 16777215:
        widget.setMaximumSize(
            scale_value(max_size.width(), scale) if max_size.width() < 16777215 else max_size.width(),
            scale_value(max_size.height(), scale) if max_size.height() < 16777215 else max_size.height(),
        )


def _scale_layout(layout, scale):
    margins = layout.contentsMargins()
    layout.setContentsMargins(
        scale_value(margins.left(), scale),
        scale_value(margins.top(), scale),
        scale_value(margins.right(), scale),
        scale_value(margins.bottom(), scale),
    )

    if layout.spacing() >= 0:
        layout.setSpacing(scale_value(layout.spacing(), scale))


def apply_window_scaling(window, scale=None):
    """对窗口及其子控件做一次性缩放，适配不同分辨率。"""
    if window.property("_adaptive_scaled"):
        return

    scale = scale or get_scale_factor()
    widgets = [window] + window.findChildren(QWidget)
    for widget in widgets:
        _scale_font(widget, scale)
        _scale_widget_size(widget, scale)
        stylesheet = widget.styleSheet()
        if stylesheet:
            widget.setStyleSheet(scale_stylesheet(stylesheet, scale))

    for layout in window.findChildren(QLayout):
        _scale_layout(layout, scale)

    window.setProperty("_adaptive_scaled", True)
