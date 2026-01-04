"""
Main window for DocTura Desktop.

Provides file selection, configuration, and conversion interface.
"""

import platform
import subprocess
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from docutura.core.controller import ConversionController
from docutura.core.models import (
    ConversionResult,
    ExcelLayoutMode,
    ExtractionMode,
    ExtractionOptions,
    OutputFormat,
    WordOrientation,
)
from docutura.core.themes import ThemeType, get_qt_stylesheet, get_theme


class ConversionWorker(QThread):
    """Background worker for document conversion."""

    progress = Signal(str)  # Progress message
    finished = Signal(object)  # ConversionResult
    error = Signal(str)  # Error message

    def __init__(self, controller: ConversionController, input_file: Path, options: ExtractionOptions):
        super().__init__()
        self.controller = controller
        self.input_file = input_file
        self.options = options

    def run(self):
        """Run conversion in background."""
        try:
            self.progress.emit(f"Processing {self.input_file.name}...")
            result = self.controller.convert_document(self.input_file, self.options)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, controller: ConversionController):
        super().__init__()

        self.controller = controller
        self.selected_files: List[Path] = []
        self.current_worker: Optional[ConversionWorker] = None
        self.current_theme = ThemeType.CORPORATE

        self.setWindowTitle("DocTura Desktop - Document Intelligence")
        self.setMinimumSize(900, 700)

        # Apply default theme
        self._apply_theme(self.current_theme)

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("DocTura Desktop")
        header.setProperty("heading", True)
        main_layout.addWidget(header)

        subtitle = QLabel(
            "Generic, offline-first document intelligence - Convert PDFs, DOCX, and images to Excel, Word, CSV"
        )
        subtitle.setProperty("subheading", True)
        main_layout.addWidget(subtitle)

        # File Selection Group
        file_group = self._create_file_selection_group()
        main_layout.addWidget(file_group)

        # Output Settings Group
        output_group = self._create_output_settings_group()
        main_layout.addWidget(output_group)

        # Excel Layout Group
        excel_group = self._create_excel_layout_group()
        main_layout.addWidget(excel_group)

        # Theme Selection
        theme_group = self._create_theme_group()
        main_layout.addWidget(theme_group)

        # Convert Button
        self.convert_btn = QPushButton("Convert Documents")
        self.convert_btn.setProperty("accent", True)
        self.convert_btn.setMinimumHeight(50)
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setEnabled(False)
        main_layout.addWidget(self.convert_btn)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Log Output
        log_label = QLabel("Processing Log:")
        log_label.setProperty("subheading", True)
        main_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        main_layout.addWidget(self.log_output)

        main_layout.addStretch()

    def _create_file_selection_group(self) -> QGroupBox:
        """Create file selection group."""
        group = QGroupBox("File Selection")
        layout = QVBoxLayout()

        # File list
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(120)
        layout.addWidget(self.file_list)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Files")
        add_btn.clicked.connect(self._add_files)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.setProperty("secondary", True)
        remove_btn.clicked.connect(self._remove_selected_files)
        btn_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setProperty("secondary", True)
        clear_btn.clicked.connect(self._clear_files)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        group.setLayout(layout)

        return group

    def _create_output_settings_group(self) -> QGroupBox:
        """Create output settings group."""
        group = QGroupBox("Output Settings")
        layout = QVBoxLayout()

        # Output formats
        formats_label = QLabel("Output Formats:")
        layout.addWidget(formats_label)

        formats_layout = QHBoxLayout()
        self.xlsx_check = QCheckBox("Excel (XLSX)")
        self.xlsx_check.setChecked(True)
        formats_layout.addWidget(self.xlsx_check)

        self.docx_check = QCheckBox("Word (DOCX)")
        formats_layout.addWidget(self.docx_check)

        self.csv_check = QCheckBox("CSV")
        formats_layout.addWidget(self.csv_check)

        formats_layout.addStretch()
        layout.addLayout(formats_layout)

        # Word orientation
        word_label = QLabel("Word Orientation:")
        layout.addWidget(word_label)

        word_layout = QHBoxLayout()
        self.portrait_radio = QRadioButton("Portrait")
        self.portrait_radio.setChecked(True)
        word_layout.addWidget(self.portrait_radio)

        self.landscape_radio = QRadioButton("Landscape")
        word_layout.addWidget(self.landscape_radio)

        word_layout.addStretch()
        layout.addLayout(word_layout)

        group.setLayout(layout)
        return group

    def _create_excel_layout_group(self) -> QGroupBox:
        """Create Excel layout options group."""
        group = QGroupBox("Excel Layout Options")
        layout = QVBoxLayout()

        label = QLabel("Logical Tables Layout:")
        layout.addWidget(label)

        self.excel_layout_combo = QComboBox()
        self.excel_layout_combo.addItem("Each table → separate worksheet", ExcelLayoutMode.SEPARATE_SHEETS)
        self.excel_layout_combo.addItem("All tables → single sheet (vertical)", ExcelLayoutMode.SINGLE_SHEET_VERTICAL)
        self.excel_layout_combo.addItem("All tables → single sheet (horizontal)", ExcelLayoutMode.SINGLE_SHEET_HORIZONTAL)
        layout.addWidget(self.excel_layout_combo)

        group.setLayout(layout)
        return group

    def _create_theme_group(self) -> QGroupBox:
        """Create theme selection group."""
        group = QGroupBox("Theme")
        layout = QHBoxLayout()

        self.corporate_radio = QRadioButton("Corporate Theme")
        self.corporate_radio.setChecked(True)
        self.corporate_radio.toggled.connect(lambda: self._change_theme(ThemeType.CORPORATE))
        layout.addWidget(self.corporate_radio)

        self.indigenous_radio = QRadioButton("Indigenous Theme")
        self.indigenous_radio.toggled.connect(lambda: self._change_theme(ThemeType.INDIGENOUS))
        layout.addWidget(self.indigenous_radio)

        layout.addStretch()

        group.setLayout(layout)
        return group

    def _add_files(self):
        """Add files to conversion list."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Documents (*.pdf *.docx *.doc *.png *.jpg *.jpeg)")

        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            for file_path in files:
                path = Path(file_path)
                if path not in self.selected_files:
                    self.selected_files.append(path)
                    self.file_list.addItem(path.name)

        self.convert_btn.setEnabled(len(self.selected_files) > 0)

    def _remove_selected_files(self):
        """Remove selected files from list."""
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            del self.selected_files[row]

        self.convert_btn.setEnabled(len(self.selected_files) > 0)

    def _clear_files(self):
        """Clear all files."""
        self.file_list.clear()
        self.selected_files.clear()
        self.convert_btn.setEnabled(False)

    def _change_theme(self, theme_type: ThemeType):
        """Change application theme."""
        if self.corporate_radio.isChecked():
            self.current_theme = ThemeType.CORPORATE
        else:
            self.current_theme = ThemeType.INDIGENOUS

        self._apply_theme(self.current_theme)

    def _apply_theme(self, theme_type: ThemeType):
        """Apply theme to application."""
        theme = get_theme(theme_type)
        stylesheet = get_qt_stylesheet(theme)
        self.setStyleSheet(stylesheet)

    def _get_extraction_options(self) -> ExtractionOptions:
        """Build extraction options from UI."""
        # Output formats
        formats = []
        if self.xlsx_check.isChecked():
            formats.append(OutputFormat.XLSX)
        if self.docx_check.isChecked():
            formats.append(OutputFormat.DOCX)
        if self.csv_check.isChecked():
            formats.append(OutputFormat.CSV)

        # Word orientation
        word_orientation = (
            WordOrientation.PORTRAIT
            if self.portrait_radio.isChecked()
            else WordOrientation.LANDSCAPE
        )

        # Excel layout
        excel_layout = self.excel_layout_combo.currentData()

        return ExtractionOptions(
            mode=ExtractionMode.HYBRID,
            output_formats=formats,
            excel_layout=excel_layout,
            word_orientation=word_orientation,
            theme=self.current_theme.value,
        )

    def _start_conversion(self):
        """Start document conversion."""
        if not self.selected_files:
            return

        # Disable UI during conversion
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.selected_files))
        self.progress_bar.setValue(0)

        # Get options
        self.conversion_options = self._get_extraction_options()

        # Process first file
        self.current_file_index = 0
        self._process_next_file()

    def _process_next_file(self):
        """Process next file in queue."""
        if self.current_file_index >= len(self.selected_files):
            # All files processed
            self._conversion_complete()
            return

        input_file = self.selected_files[self.current_file_index]

        # Start worker
        self.current_worker = ConversionWorker(
            self.controller, input_file, self.conversion_options
        )
        self.current_worker.progress.connect(self._on_progress)
        self.current_worker.finished.connect(self._on_file_complete)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()

    def _on_progress(self, message: str):
        """Handle progress update."""
        self.log_output.append(message)

    def _on_file_complete(self, result: ConversionResult):
        """Handle file conversion complete."""
        self.progress_bar.setValue(self.current_file_index + 1)

        if result.success:
            self.log_output.append(f"✓ {result.input_file.name}: {result.get_summary()}")

            # Show validation status
            if result.validation_report.overall_status.value != "passed":
                self.log_output.append(
                    f"  ⚠ Validation: {result.validation_report.overall_status.value.upper()} "
                    f"({len(result.validation_report.issues)} issues)"
                )
        else:
            self.log_output.append(f"✗ {result.input_file.name}: {result.error_message}")

        # Process next file
        self.current_file_index += 1
        self._process_next_file()

    def _on_error(self, error_message: str):
        """Handle conversion error."""
        self.log_output.append(f"ERROR: {error_message}")
        self.current_file_index += 1
        self._process_next_file()

    def _conversion_complete(self):
        """Handle all conversions complete."""
        self.log_output.append("\n=== Conversion Complete ===")

        # Re-enable UI
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Show completion message with option to open output folder
        msg = QMessageBox(self)
        msg.setWindowTitle("Conversion Complete")
        msg.setText(f"Successfully processed {len(self.selected_files)} document(s).")
        msg.setInformativeText("Would you like to open the output folder?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)

        if msg.exec() == QMessageBox.Yes:
            self._open_output_folder()

    def _open_output_folder(self):
        """Open output folder in file explorer."""
        output_dir = self.controller.output_dir

        if platform.system() == "Windows":
            subprocess.run(["explorer", str(output_dir)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(output_dir)])
        else:  # Linux
            subprocess.run(["xdg-open", str(output_dir)])
