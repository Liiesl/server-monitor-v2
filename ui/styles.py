"""
UI Stylesheets
"""
from .constants import (
    COLOR_BACKGROUND_DARK, COLOR_BACKGROUND_MEDIUM, COLOR_BACKGROUND_CARD,
    COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY,
    COLOR_TEXT_MUTED, COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_PRESSED,
    COLOR_SUCCESS, COLOR_SUCCESS_HOVER, COLOR_SUCCESS_PRESSED,
    COLOR_ERROR, COLOR_ERROR_DARK, COLOR_ERROR_HOVER, COLOR_ERROR_PRESSED,
    COLOR_INFO, COLOR_SIDEBAR_BG, COLOR_SIDEBAR_HOVER, COLOR_SIDEBAR_SELECTED,
    RADIUS_LARGE, RADIUS_MEDIUM, RADIUS_SMALL, RADIUS_TINY,
    FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_TINY
)


def get_sidebar_style() -> str:
    """Get stylesheet for sidebar widget"""
    return f"""
        QWidget {{
            background-color: {COLOR_SIDEBAR_BG};
        }}
        QPushButton {{
            text-align: left;
            padding: 10px 15px;
            border: none;
            border-radius: {RADIUS_SMALL}px;
            color: {COLOR_TEXT_SECONDARY};
            font-size: {FONT_SIZE_SMALL}px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_SIDEBAR_HOVER};
        }}
        QPushButton:checked {{
            background-color: {COLOR_SIDEBAR_SELECTED};
            color: {COLOR_TEXT_PRIMARY};
        }}
        QLabel {{
            color: {COLOR_TEXT_MUTED};
            font-size: {FONT_SIZE_TINY}px;
        }}
        QFrame {{
            color: {COLOR_BORDER};
        }}
    """


def get_dashboard_style() -> str:
    """Get stylesheet for dashboard view"""
    return f"background-color: {COLOR_BACKGROUND_DARK};"


def get_card_style() -> str:
    """Get stylesheet for stat cards"""
    return f"""
        background-color: {COLOR_BACKGROUND_CARD};
        border-radius: {RADIUS_LARGE}px;
        padding: 20px;
        border: 1px solid {COLOR_BORDER};
    """


def get_primary_button_style() -> str:
    """Get stylesheet for primary action buttons"""
    return f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY};
            color: white;
            padding: 8px 16px;
            border-radius: {RADIUS_SMALL}px;
            font-size: {FONT_SIZE_SMALL}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRIMARY_PRESSED};
        }}
    """


def get_success_button_style() -> str:
    """Get stylesheet for success action buttons"""
    return f"""
        QPushButton {{
            background-color: {COLOR_SUCCESS};
            color: white;
            font-weight: bold;
            padding: 12px 24px;
            border-radius: {RADIUS_MEDIUM}px;
            font-size: {FONT_SIZE_NORMAL}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_SUCCESS_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_SUCCESS_PRESSED};
        }}
    """


def get_error_button_style() -> str:
    """Get stylesheet for error/danger action buttons"""
    return f"""
        QPushButton {{
            background-color: {COLOR_ERROR_DARK};
        }}
        QPushButton:hover {{
            background-color: {COLOR_ERROR_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_ERROR_PRESSED};
        }}
    """


def get_server_detail_style() -> str:
    """Get stylesheet for server detail view"""
    return f"""
        QWidget {{
            background-color: {COLOR_BACKGROUND_DARK};
            color: {COLOR_TEXT_SECONDARY};
        }}
        QLabel {{
            color: {COLOR_TEXT_SECONDARY};
        }}
        QPushButton {{
            background-color: {COLOR_PRIMARY};
            color: white;
            padding: 8px 16px;
            border-radius: {RADIUS_SMALL}px;
            font-size: {FONT_SIZE_SMALL}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRIMARY_PRESSED};
        }}
        QTextEdit {{
            background-color: {COLOR_BACKGROUND_MEDIUM};
            color: {COLOR_TEXT_SECONDARY};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_SMALL}px;
            padding: 10px;
        }}
    """


def get_info_group_style() -> str:
    """Get stylesheet for info group widgets"""
    return f"""
        background-color: {COLOR_BACKGROUND_CARD};
        border-radius: {RADIUS_MEDIUM}px;
        padding: 20px;
        border: 1px solid {COLOR_BORDER};
    """


def get_dialog_style() -> str:
    """Get stylesheet for dialogs"""
    return f"""
        QDialog {{
            background-color: {COLOR_BACKGROUND_DARK};
        }}
        QLabel {{
            color: {COLOR_TEXT_SECONDARY};
            font-size: {FONT_SIZE_SMALL}px;
        }}
        QLineEdit, QSpinBox {{
            background-color: {COLOR_BACKGROUND_MEDIUM};
            color: {COLOR_TEXT_SECONDARY};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_TINY}px;
            padding: 6px;
            font-size: {FONT_SIZE_SMALL}px;
        }}
        QLineEdit:focus, QSpinBox:focus {{
            border: 1px solid {COLOR_PRIMARY};
        }}
        QPushButton {{
            background-color: {COLOR_PRIMARY};
            color: white;
            padding: 8px 16px;
            border-radius: {RADIUS_SMALL}px;
            font-size: {FONT_SIZE_SMALL}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRIMARY_PRESSED};
        }}
    """


def get_label_style(size: str = "normal", color: str = "primary") -> str:
    """Get stylesheet for labels with different sizes and colors"""
    size_map = {
        "title": "28px",
        "large": "24px",
        "medium": "16px",
        "normal": "14px",
        "small": "13px",
        "tiny": "12px"
    }
    
    color_map = {
        "primary": COLOR_TEXT_PRIMARY,
        "secondary": COLOR_TEXT_SECONDARY,
        "tertiary": COLOR_TEXT_TERTIARY,
        "muted": COLOR_TEXT_MUTED,
        "info": COLOR_INFO,
        "success": COLOR_SUCCESS,
        "error": COLOR_ERROR
    }
    
    font_size = size_map.get(size, size_map["normal"])
    text_color = color_map.get(color, color_map["primary"])
    weight = "bold" if size in ["title", "large"] else "normal"
    
    return f"font-size: {font_size}; color: {text_color}; font-weight: {weight};"


def get_input_style() -> str:
    """Get stylesheet for input fields"""
    return f"""
        background-color: {COLOR_BACKGROUND_MEDIUM};
        color: {COLOR_TEXT_SECONDARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_TINY}px;
        padding: 6px;
        font-size: {FONT_SIZE_SMALL}px;
    """


def get_danger_button_style() -> str:
    """Get stylesheet for danger action buttons"""
    return f"""
        QPushButton {{
            background-color: {COLOR_ERROR};
            color: white;
            font-weight: bold;
            padding: 12px 24px;
            border-radius: {RADIUS_MEDIUM}px;
            font-size: {FONT_SIZE_NORMAL}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ERROR_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_ERROR_PRESSED};
        }}
    """


