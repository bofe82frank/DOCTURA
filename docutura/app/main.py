"""
Main GUI application for DocTura Desktop.

PySide6-based desktop interface.
"""

import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication

from docutura.app.windows.main_window import MainWindow
from docutura.core.controller import ConversionController
from docutura.plugins.base import PluginRegistry
from docutura.plugins.staff_list import InternationalStaffListPlugin
from docutura.plugins.waec_marksdist import WAECMarksDistributionPlugin


def initialize_plugins() -> PluginRegistry:
    """Initialize and register all plugins."""
    registry = PluginRegistry()

    # Register built-in plugins
    registry.register(WAECMarksDistributionPlugin())
    registry.register(InternationalStaffListPlugin())

    return registry


def get_default_paths() -> tuple:
    """Get default output and audit directories."""
    home = Path.home()

    output_dir = home / "Documents" / "DocTura" / "Output"
    audit_dir = home / "Documents" / "DocTura" / "Audit"

    return output_dir, audit_dir


def main():
    """Main entry point for DocTura Desktop."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("DocTura Desktop")
    app.setOrganizationName("DocTura")
    app.setOrganizationDomain("doctura.dev")

    # Initialize plugin registry
    plugin_registry = initialize_plugins()

    # Get default paths
    output_dir, audit_dir = get_default_paths()

    # Create conversion controller
    controller = ConversionController(
        plugin_registry=plugin_registry, output_dir=output_dir, audit_dir=audit_dir
    )

    # Create and show main window
    window = MainWindow(controller)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
