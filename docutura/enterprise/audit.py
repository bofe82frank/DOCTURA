"""
Audit logging system for DocTura Desktop.

Provides enterprise-grade tracking of all conversions.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from docutura.core.models import ConversionResult, DocumentMetadata, ValidationReport


class AuditLogger:
    """Manages audit logs for document conversions."""

    def __init__(self, log_dir: Path):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for storing audit logs
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = log_dir / "audit_index.jsonl"

    def log_conversion(
        self,
        result: ConversionResult,
        user_metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Log a conversion operation.

        Args:
            result: Conversion result
            user_metadata: Optional user/machine metadata

        Returns:
            Path to log file
        """
        # Generate log ID
        timestamp = datetime.now()
        log_id = self._generate_log_id(result.input_file, timestamp)

        # Create log entry
        log_entry = {
            "log_id": log_id,
            "timestamp": timestamp.isoformat(),
            "input_file": {
                "path": str(result.input_file),
                "name": result.input_file.name,
                "hash": result.metadata.input_file_hash,
            },
            "output_files": [
                {"path": str(f), "name": f.name, "hash": self._compute_file_hash(f)}
                for f in result.output_files
            ],
            "plugin": {
                "id": result.metadata.plugin_id,
                "version": result.metadata.plugin_version,
                "confidence": result.metadata.plugin_confidence,
            },
            "extraction": {
                "mode": result.metadata.extraction_mode,
                "excel_layout": result.metadata.excel_layout_mode,
                "word_orientation": result.metadata.word_orientation,
                "output_formats": result.metadata.output_formats,
                "theme": result.metadata.theme,
            },
            "validation": {
                "status": result.validation_report.overall_status.value,
                "tables_validated": result.validation_report.tables_validated,
                "tables_passed": result.validation_report.tables_passed,
                "tables_with_warnings": result.validation_report.tables_with_warnings,
                "tables_failed": result.validation_report.tables_failed,
                "issues_count": len(result.validation_report.issues),
            },
            "performance": {
                "processing_time_seconds": result.processing_time_seconds,
            },
            "success": result.success,
            "error_message": result.error_message,
        }

        # Add user metadata if provided
        if user_metadata:
            log_entry["user_metadata"] = user_metadata

        # Write detailed log file
        log_file = self.log_dir / f"{log_id}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)

        # Append to index
        self._append_to_index(log_entry)

        return log_file

    def _generate_log_id(self, input_file: Path, timestamp: datetime) -> str:
        """Generate unique log ID."""
        base = f"{input_file.name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        # Add short hash for uniqueness
        hash_val = hashlib.md5(f"{input_file}_{timestamp}".encode()).hexdigest()[:8]
        return f"{base}_{hash_val}"

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file."""
        sha256 = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return "error"

    def _append_to_index(self, log_entry: Dict[str, Any]) -> None:
        """Append log entry to index file (JSONL format)."""
        # Create summary for index
        index_entry = {
            "log_id": log_entry["log_id"],
            "timestamp": log_entry["timestamp"],
            "input_file": log_entry["input_file"]["name"],
            "output_formats": log_entry["extraction"]["output_formats"],
            "validation_status": log_entry["validation"]["status"],
            "success": log_entry["success"],
        }

        with open(self.index_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(index_entry) + "\n")

    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of log entries (most recent first)
        """
        if not self.index_file.exists():
            return []

        entries = []
        with open(self.index_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        # Return most recent entries
        return list(reversed(entries[-limit:]))

    def search_logs(
        self,
        input_file_name: Optional[str] = None,
        validation_status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs.

        Args:
            input_file_name: Filter by input file name
            validation_status: Filter by validation status
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Matching log entries
        """
        if not self.index_file.exists():
            return []

        results = []

        with open(self.index_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                entry = json.loads(line)

                # Apply filters
                if input_file_name and input_file_name not in entry["input_file"]:
                    continue

                if validation_status and entry["validation_status"] != validation_status:
                    continue

                entry_time = datetime.fromisoformat(entry["timestamp"])

                if start_date and entry_time < start_date:
                    continue

                if end_date and entry_time > end_date:
                    continue

                results.append(entry)

        return results
