"""
Base plugin system for DocTura Desktop.

Defines plugin interface and registry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from docutura.core.models import (
    DocumentMetadata,
    ExtractedTable,
    ScoreDomain,
    SegmentationStrategy,
)


@dataclass
class PluginDetectionResult:
    """Result of plugin detection."""

    plugin_id: str
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]  # Plugin-specific metadata


class DocumentPlugin(ABC):
    """Base class for document processing plugins."""

    def __init__(self):
        self.plugin_id = self.get_plugin_id()
        self.version = self.get_version()

    @abstractmethod
    def get_plugin_id(self) -> str:
        """Get unique plugin identifier."""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get plugin version."""
        pass

    @abstractmethod
    def detect(
        self,
        tables_data: List[Dict[str, Any]],
        page_texts: List[str],
        context: Dict[str, Any],
    ) -> PluginDetectionResult:
        """
        Detect if this plugin can handle the document.

        Args:
            tables_data: Raw extracted tables
            page_texts: Text from each page
            context: Extraction context

        Returns:
            Detection result with confidence score
        """
        pass

    @abstractmethod
    def get_segmentation_strategy(self) -> SegmentationStrategy:
        """Get preferred segmentation strategy."""
        pass

    def get_score_domains(self) -> Optional[List[ScoreDomain]]:
        """
        Get score domain definitions (for score-domain segmentation).

        Returns:
            List of score domains, or None if not applicable
        """
        return None

    @abstractmethod
    def extract_metadata(
        self,
        tables_data: List[Dict[str, Any]],
        page_texts: List[str],
        context: Dict[str, Any],
    ) -> DocumentMetadata:
        """
        Extract document metadata.

        Args:
            tables_data: Raw extracted tables
            page_texts: Text from each page
            context: Extraction context

        Returns:
            Document metadata
        """
        pass

    def post_process_tables(
        self, tables: List[ExtractedTable]
    ) -> List[ExtractedTable]:
        """
        Post-process extracted tables (optional).

        Args:
            tables: Extracted tables

        Returns:
            Processed tables
        """
        return tables

    def get_validation_rules(self) -> List[str]:
        """
        Get plugin-specific validation rules.

        Returns:
            List of validation rule names
        """
        return []

    def summarize(self, tables: List[ExtractedTable]) -> Optional[str]:
        """
        Generate summary of extracted data (optional).

        Args:
            tables: Extracted tables

        Returns:
            Summary text, or None
        """
        return None


class PluginRegistry:
    """Registry for managing document plugins."""

    def __init__(self):
        self.plugins: List[DocumentPlugin] = []

    def register(self, plugin: DocumentPlugin) -> None:
        """Register a plugin."""
        self.plugins.append(plugin)

    def detect_plugin(
        self,
        tables_data: List[Dict[str, Any]],
        page_texts: List[str],
        context: Dict[str, Any],
        min_confidence: float = 0.5,
    ) -> Optional[Tuple[DocumentPlugin, PluginDetectionResult]]:
        """
        Detect which plugin should handle the document.

        Args:
            tables_data: Raw extracted tables
            page_texts: Text from each page
            context: Extraction context
            min_confidence: Minimum confidence threshold

        Returns:
            Tuple of (plugin, detection_result) or None
        """
        best_plugin = None
        best_result = None
        best_confidence = 0.0

        for plugin in self.plugins:
            try:
                result = plugin.detect(tables_data, page_texts, context)

                if result.confidence > best_confidence and result.confidence >= min_confidence:
                    best_confidence = result.confidence
                    best_plugin = plugin
                    best_result = result
            except Exception as e:
                # Log error and continue
                print(f"Error in plugin {plugin.get_plugin_id()}: {e}")
                continue

        if best_plugin and best_result:
            return (best_plugin, best_result)

        return None

    def get_plugin_by_id(self, plugin_id: str) -> Optional[DocumentPlugin]:
        """Get plugin by ID."""
        for plugin in self.plugins:
            if plugin.get_plugin_id() == plugin_id:
                return plugin
        return None

    def list_plugins(self) -> List[str]:
        """List all registered plugin IDs."""
        return [plugin.get_plugin_id() for plugin in self.plugins]
