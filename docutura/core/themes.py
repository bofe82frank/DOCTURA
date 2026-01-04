"""
Theme system for DocTura Desktop.

Provides Corporate and Indigenous themes with defined color palettes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


@dataclass(frozen=True)
class ColorPalette:
    """Color palette definition for a theme."""

    # Core colors
    primary: str
    secondary: str
    accent: str
    highlight: str = ""  # Optional highlight accent

    # Background colors
    background: str = "#FFFFFF"
    surface: str = "#FFFFFF"

    # Text colors
    text_primary: str = "#000000"
    text_secondary: str = "#666666"

    # Status colors
    success: str = "#1F7A1F"
    warning: str = "#D97706"
    error: str = "#9B1C1C"


class ThemeType(str, Enum):
    """Available theme types."""

    CORPORATE = "corporate"
    INDIGENOUS = "indigenous"


class Theme:
    """Theme definition with colors and usage rules."""

    def __init__(
        self,
        name: str,
        description: str,
        palette: ColorPalette,
        button_primary_color: str,
        button_accent_color: str,
        header_color: str,
        table_background: str,
    ):
        self.name = name
        self.description = description
        self.palette = palette
        self.button_primary_color = button_primary_color
        self.button_accent_color = button_accent_color
        self.header_color = header_color
        self.table_background = table_background

    def get_stylesheet_variables(self) -> Dict[str, str]:
        """Get theme variables for Qt stylesheet."""
        return {
            "primary": self.palette.primary,
            "secondary": self.palette.secondary,
            "accent": self.palette.accent,
            "highlight": self.palette.highlight or self.palette.accent,
            "background": self.palette.background,
            "surface": self.palette.surface,
            "text_primary": self.palette.text_primary,
            "text_secondary": self.palette.text_secondary,
            "success": self.palette.success,
            "warning": self.palette.warning,
            "error": self.palette.error,
            "button_primary": self.button_primary_color,
            "button_accent": self.button_accent_color,
            "header": self.header_color,
            "table_bg": self.table_background,
        }


# Corporate Theme Definition
CORPORATE_PALETTE = ColorPalette(
    primary="#0B1F3B",  # Deep Navy Blue
    secondary="#4A5568",  # Slate Grey
    accent="#C9A227",  # Gold
    background="#F7F9FC",  # Off-White
    surface="#FFFFFF",  # White
    text_primary="#1A202C",  # Charcoal
    text_secondary="#6B7280",  # Muted Grey
    success="#1F7A1F",  # Deep Green
    warning="#D97706",  # Amber
    error="#9B1C1C",  # Dark Red
)

CORPORATE_THEME = Theme(
    name="Corporate",
    description="For enterprise, government, and professional environments where neutrality, clarity, and authority matter.",
    palette=CORPORATE_PALETTE,
    button_primary_color=CORPORATE_PALETTE.primary,  # Navy Blue
    button_accent_color=CORPORATE_PALETTE.accent,  # Gold
    header_color=CORPORATE_PALETTE.primary,  # Navy Blue
    table_background=CORPORATE_PALETTE.surface,  # White
)


# Indigenous Theme Definition
INDIGENOUS_PALETTE = ColorPalette(
    primary="#5A3E2B",  # Earth Brown
    secondary="#1E5631",  # Forest Green
    accent="#C05621",  # Burnt Orange
    highlight="#D69E2E",  # Ochre Yellow
    background="#FAF3E0",  # Warm Sand
    surface="#FFF8ED",  # Light Clay
    text_primary="#2D1B12",  # Dark Umber
    text_secondary="#6B705C",  # Olive Grey
    success="#2F855A",  # Deep Green
    warning="#B7791F",  # Earth Amber
    error="#9C4221",  # Clay Red
)

INDIGENOUS_THEME = Theme(
    name="Indigenous",
    description="To reflect African identity, heritage, and grounded authenticity without sacrificing usability or professionalism.",
    palette=INDIGENOUS_PALETTE,
    button_primary_color=INDIGENOUS_PALETTE.secondary,  # Forest Green
    button_accent_color=INDIGENOUS_PALETTE.accent,  # Burnt Orange
    header_color=INDIGENOUS_PALETTE.primary,  # Earth Brown
    table_background=INDIGENOUS_PALETTE.background,  # Warm Sand
)


# Theme registry
THEMES: Dict[ThemeType, Theme] = {
    ThemeType.CORPORATE: CORPORATE_THEME,
    ThemeType.INDIGENOUS: INDIGENOUS_THEME,
}


def get_theme(theme_type: ThemeType) -> Theme:
    """Get theme by type."""
    return THEMES[theme_type]


def get_qt_stylesheet(theme: Theme) -> str:
    """
    Generate Qt stylesheet from theme.

    Args:
        theme: Theme to apply

    Returns:
        Qt stylesheet string
    """
    vars = theme.get_stylesheet_variables()

    stylesheet = f"""
    /* DocTura Desktop - {theme.name} Theme */

    QMainWindow {{
        background-color: {vars['background']};
    }}

    QWidget {{
        background-color: {vars['background']};
        color: {vars['text_primary']};
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 10pt;
    }}

    /* Headers */
    QLabel[heading="true"] {{
        color: {vars['header']};
        font-size: 14pt;
        font-weight: bold;
        padding: 10px 0px;
    }}

    QLabel[subheading="true"] {{
        color: {vars['text_primary']};
        font-size: 11pt;
        font-weight: 600;
        padding: 5px 0px;
    }}

    /* Primary Buttons */
    QPushButton {{
        background-color: {vars['button_primary']};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 600;
        min-width: 100px;
    }}

    QPushButton:hover {{
        background-color: {vars['secondary']};
    }}

    QPushButton:pressed {{
        background-color: {vars['text_secondary']};
    }}

    QPushButton:disabled {{
        background-color: {vars['text_secondary']};
        color: #CCCCCC;
    }}

    /* Accent Buttons */
    QPushButton[accent="true"] {{
        background-color: {vars['button_accent']};
        color: white;
    }}

    QPushButton[accent="true"]:hover {{
        background-color: {vars['highlight']};
    }}

    /* Secondary Buttons */
    QPushButton[secondary="true"] {{
        background-color: {vars['surface']};
        color: {vars['primary']};
        border: 2px solid {vars['primary']};
    }}

    QPushButton[secondary="true"]:hover {{
        background-color: {vars['primary']};
        color: white;
    }}

    /* Input Fields */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
        background-color: {vars['surface']};
        border: 1px solid {vars['text_secondary']};
        border-radius: 4px;
        padding: 8px;
        color: {vars['text_primary']};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
        border: 2px solid {vars['primary']};
    }}

    /* Group Boxes */
    QGroupBox {{
        background-color: {vars['surface']};
        border: 1px solid {vars['text_secondary']};
        border-radius: 6px;
        margin-top: 10px;
        padding: 15px;
        font-weight: 600;
    }}

    QGroupBox::title {{
        color: {vars['header']};
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}

    /* Tables */
    QTableWidget, QTableView {{
        background-color: {vars['table_bg']};
        alternate-background-color: {vars['surface']};
        gridline-color: {vars['text_secondary']};
        border: 1px solid {vars['text_secondary']};
        border-radius: 4px;
    }}

    QTableWidget::item, QTableView::item {{
        padding: 5px;
    }}

    QHeaderView::section {{
        background-color: {vars['primary']};
        color: white;
        padding: 8px;
        border: none;
        font-weight: 600;
    }}

    /* Progress Bar */
    QProgressBar {{
        border: 1px solid {vars['text_secondary']};
        border-radius: 4px;
        text-align: center;
        background-color: {vars['surface']};
        color: {vars['text_primary']};
    }}

    QProgressBar::chunk {{
        background-color: {vars['success']};
        border-radius: 3px;
    }}

    /* Status Messages */
    QLabel[status="success"] {{
        color: {vars['success']};
        font-weight: 600;
    }}

    QLabel[status="warning"] {{
        color: {vars['warning']};
        font-weight: 600;
    }}

    QLabel[status="error"] {{
        color: {vars['error']};
        font-weight: 600;
    }}

    /* Checkboxes and Radio Buttons */
    QCheckBox, QRadioButton {{
        color: {vars['text_primary']};
        spacing: 8px;
    }}

    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {vars['primary']};
        border-radius: 3px;
        background-color: {vars['surface']};
    }}

    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {vars['primary']};
    }}

    /* Scroll Bars */
    QScrollBar:vertical {{
        background-color: {vars['background']};
        width: 12px;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {vars['text_secondary']};
        border-radius: 6px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {vars['primary']};
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {vars['text_secondary']};
        border-radius: 4px;
        background-color: {vars['surface']};
    }}

    QTabBar::tab {{
        background-color: {vars['background']};
        color: {vars['text_primary']};
        padding: 10px 20px;
        border: 1px solid {vars['text_secondary']};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}

    QTabBar::tab:selected {{
        background-color: {vars['primary']};
        color: white;
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {vars['highlight']};
    }}
    """

    return stylesheet
