"""
Smart naming engine for DocTura Desktop.

Generates intelligent output file names based on document metadata.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from docutura.core.models import DocumentMetadata, OutputFormat


class SmartNamingEngine:
    """Generates smart output file names."""

    def __init__(self):
        pass

    def generate_output_name(
        self,
        input_file: Path,
        metadata: Optional[DocumentMetadata],
        output_format: OutputFormat,
        suffix: str = "",
    ) -> str:
        """
        Generate smart output file name.

        Args:
            input_file: Input file path
            metadata: Document metadata
            output_format: Output format
            suffix: Optional suffix (e.g., "_combined")

        Returns:
            Output file name (without directory)
        """
        parts = []

        # Use metadata if available
        if metadata:
            # Add subject/code if available
            if metadata.subject_or_code:
                parts.append(self._sanitize(metadata.subject_or_code))

            # Add reporting period if available
            if metadata.reporting_period:
                parts.append(metadata.reporting_period)

            # Add plugin hint
            if metadata.plugin_id:
                if "waec" in metadata.plugin_id.lower():
                    parts.append("WAEC")
                elif "staff" in metadata.plugin_id.lower():
                    parts.append("Staff_List")

        # If no metadata, use input file name (without extension)
        if not parts:
            parts.append(input_file.stem)

        # Add suffix if provided
        if suffix:
            parts.append(suffix)

        # Join parts with underscores
        base_name = "_".join(parts)

        # Clean up
        base_name = self._sanitize(base_name)

        # Add extension
        return f"{base_name}.{output_format.value}"

    def generate_directory_name(
        self, input_file: Path, metadata: Optional[DocumentMetadata]
    ) -> str:
        """
        Generate output directory name.

        Args:
            input_file: Input file path
            metadata: Document metadata

        Returns:
            Directory name
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if metadata and metadata.subject_or_code:
            base = self._sanitize(metadata.subject_or_code)
        else:
            base = input_file.stem

        return f"{base}_{timestamp}"

    @staticmethod
    def _sanitize(name: str) -> str:
        """
        Sanitize file name.

        Args:
            name: Name to sanitize

        Returns:
            Sanitized name
        """
        # Remove or replace invalid characters
        name = re.sub(r'[<>:"/\\|?*]', "", name)

        # Replace spaces and multiple underscores
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"_+", "_", name)

        # Trim underscores
        name = name.strip("_")

        # Limit length
        if len(name) > 100:
            name = name[:100]

        return name
