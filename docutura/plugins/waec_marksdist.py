"""
WAEC Marks Distribution Plugin.

Handles WAEC TASS/CASS statistical distribution reports with score-domain segmentation.
"""

import re
from typing import Any, Dict, List, Optional

from docutura.core.models import DocumentMetadata, ScoreDomain, SegmentationStrategy
from docutura.plugins.base import DocumentPlugin, PluginDetectionResult


class WAECMarksDistributionPlugin(DocumentPlugin):
    """Plugin for WAEC marks distribution reports."""

    def get_plugin_id(self) -> str:
        return "waec_marksdist"

    def get_version(self) -> str:
        return "1.0.0"

    def detect(
        self,
        tables_data: List[Dict[str, Any]],
        page_texts: List[str],
        context: Dict[str, Any],
    ) -> PluginDetectionResult:
        """
        Detect if document is a WAEC marks distribution report.

        Looks for:
        - "TASS" or "CASS" keywords
        - Statistical distribution tables (Score, Frequency, Percent, Cumulative)
        - Score ranges like 0-19, 15-40
        """
        confidence = 0.0
        metadata = {}

        # Join all page texts
        full_text = " ".join(page_texts).upper()

        # Check for WAEC indicators
        waec_indicators = ["WAEC", "WEST AFRICAN EXAMINATIONS COUNCIL", "TASS", "CASS"]
        indicator_matches = sum(1 for ind in waec_indicators if ind in full_text)

        if indicator_matches > 0:
            confidence += 0.3 * min(indicator_matches, 2)

        # Check for statistical distribution headers
        distribution_keywords = ["FREQUENCY", "PERCENT", "CUMULATIVE", "SCORE"]
        keyword_count = 0

        for table_dict in tables_data:
            data = table_dict.get("data", [])
            if data:
                first_row = " ".join(str(cell).upper() for cell in data[0])
                keyword_count += sum(1 for kw in distribution_keywords if kw in first_row)

        if keyword_count >= 3:  # At least 3 of the 4 keywords
            confidence += 0.4

        # Check for score columns (numeric first column)
        has_score_column = False
        for table_dict in tables_data:
            data = table_dict.get("data", [])
            if len(data) > 1:
                # Check if first column has numeric values
                numeric_count = 0
                for row in data[1:]:
                    if row:
                        try:
                            float(str(row[0]).replace(",", ""))
                            numeric_count += 1
                        except (ValueError, IndexError):
                            pass

                if numeric_count > len(data[1:]) * 0.7:
                    has_score_column = True
                    confidence += 0.3
                    break

        # Extract subject/document info
        subject_match = re.search(r"SUBJECT[:\s]+([A-Z\s]+)", full_text)
        if subject_match:
            metadata["subject"] = subject_match.group(1).strip()

        session_match = re.search(r"(?:SESSION|YEAR)[:\s]+(\d{4})", full_text)
        if session_match:
            metadata["session"] = session_match.group(1)

        # Look for paper types
        if "OBJECTIVE" in full_text:
            metadata["paper_type"] = "objective"
        if "ESSAY" in full_text:
            metadata["paper_type"] = "essay"

        return PluginDetectionResult(
            plugin_id=self.plugin_id, confidence=min(confidence, 1.0), metadata=metadata
        )

    def get_segmentation_strategy(self) -> SegmentationStrategy:
        """Use score-domain segmentation to prevent truncation."""
        return SegmentationStrategy.SCORE_DOMAIN

    def get_score_domains(self) -> List[ScoreDomain]:
        """
        Define WAEC score domains.

        These are the standard WAEC score ranges that must not be split across pages.
        """
        return [
            ScoreDomain(
                name="Scaled_Objective",
                min_score=0,
                max_score=19,
                description="Scaled Objective score range (0-19)",
            ),
            ScoreDomain(
                name="Scaled_Essay",
                min_score=15,
                max_score=40,
                description="Scaled Essay score range (15-40)",
            ),
            ScoreDomain(
                name="Raw_Score_40",
                min_score=0,
                max_score=40,
                description="Raw score range (0-40)",
            ),
            ScoreDomain(
                name="Raw_Score_50",
                min_score=0,
                max_score=50,
                description="Raw score range (0-50)",
            ),
            ScoreDomain(
                name="Raw_Score_60",
                min_score=0,
                max_score=60,
                description="Raw score range (0-60)",
            ),
        ]

    def extract_metadata(
        self,
        tables_data: List[Dict[str, Any]],
        page_texts: List[str],
        context: Dict[str, Any],
    ) -> DocumentMetadata:
        """Extract WAEC document metadata."""
        full_text = " ".join(page_texts)

        # Extract title
        title_match = re.search(
            r"(TASS|CASS)\s+(?:AND\s+)?(TASS|CASS)?\s*.*?STATISTICS", full_text, re.IGNORECASE
        )
        title = title_match.group(0) if title_match else "WAEC Marks Distribution"

        # Extract subject
        subject_match = re.search(r"SUBJECT[:\s]+([A-Z\s]+?)(?:\s{2,}|\n|$)", full_text)
        subject = subject_match.group(1).strip() if subject_match else None

        # Extract session/year
        session_match = re.search(r"(?:SESSION|YEAR)[:\s]+(\d{4})", full_text)
        session = session_match.group(1) if session_match else None

        return DocumentMetadata(
            title=title,
            organization="West African Examinations Council (WAEC)",
            reporting_period=session,
            subject_or_code=subject,
            plugin_id=self.plugin_id,
            plugin_version=self.version,
        )

    def summarize(self, tables: List["ExtractedTable"]) -> Optional[str]:
        """Generate summary of WAEC distribution data."""
        summaries = []

        for table in tables:
            if table.score_domain:
                summaries.append(
                    f"- {table.score_domain.name}: {table.row_count - 1} score entries"
                )

        if summaries:
            return "WAEC Marks Distribution Summary:\n" + "\n".join(summaries)

        return None
