"""
Basic tests for DocTura Desktop.

Run with: pytest
"""

import pytest
from docutura.core.models import ExtractionMode, ExtractionOptions, ScoreDomain
from docutura.core.themes import CORPORATE_THEME, INDIGENOUS_THEME, ThemeType, get_theme


class TestThemes:
    """Test theme system."""

    def test_corporate_theme_colors(self):
        """Test corporate theme has correct colors."""
        assert CORPORATE_THEME.palette.primary == "#0B1F3B"
        assert CORPORATE_THEME.palette.accent == "#C9A227"

    def test_indigenous_theme_colors(self):
        """Test indigenous theme has correct colors."""
        assert INDIGENOUS_THEME.palette.primary == "#5A3E2B"
        assert INDIGENOUS_THEME.palette.accent == "#C05621"

    def test_get_theme(self):
        """Test theme retrieval."""
        corporate = get_theme(ThemeType.CORPORATE)
        assert corporate.name == "Corporate"

        indigenous = get_theme(ThemeType.INDIGENOUS)
        assert indigenous.name == "Indigenous"


class TestModels:
    """Test data models."""

    def test_extraction_options_defaults(self):
        """Test ExtractionOptions defaults."""
        options = ExtractionOptions()

        assert options.mode == ExtractionMode.HYBRID
        assert options.theme == "corporate"
        assert options.validation_enabled is True
        assert options.metadata_sheet_enabled is True

    def test_score_domain(self):
        """Test ScoreDomain dataclass."""
        domain = ScoreDomain(
            name="Scaled Essay", min_score=15, max_score=40, description="WAEC Essay scores"
        )

        assert domain.name == "Scaled Essay"
        assert domain.min_score == 15
        assert domain.max_score == 40


class TestValidation:
    """Test validation logic."""

    def test_validator_initialization(self):
        """Test validator can be initialized."""
        from docutura.core.validator import TableValidator

        validator = TableValidator(tolerance=0.01)
        assert validator.tolerance == 0.01


class TestNaming:
    """Test smart naming engine."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from docutura.core.naming import SmartNamingEngine

        engine = SmartNamingEngine()

        # Test invalid characters removal
        result = engine._sanitize("File: Name / With \\ Invalid * Chars")
        assert "/" not in result
        assert "\\" not in result
        assert "*" not in result
        assert ":" not in result

    def test_name_truncation(self):
        """Test long names are truncated."""
        from docutura.core.naming import SmartNamingEngine

        engine = SmartNamingEngine()

        long_name = "A" * 150
        result = engine._sanitize(long_name)
        assert len(result) <= 100


class TestPlugins:
    """Test plugin system."""

    def test_plugin_registry(self):
        """Test plugin registry."""
        from docutura.plugins.base import PluginRegistry
        from docutura.plugins.waec_marksdist import WAECMarksDistributionPlugin

        registry = PluginRegistry()
        plugin = WAECMarksDistributionPlugin()

        registry.register(plugin)

        assert len(registry.list_plugins()) == 1
        assert "waec_marksdist" in registry.list_plugins()

    def test_waec_plugin_id(self):
        """Test WAEC plugin identification."""
        from docutura.plugins.waec_marksdist import WAECMarksDistributionPlugin

        plugin = WAECMarksDistributionPlugin()

        assert plugin.get_plugin_id() == "waec_marksdist"
        assert plugin.get_version() == "1.0.0"

    def test_staff_list_plugin_id(self):
        """Test staff list plugin identification."""
        from docutura.plugins.staff_list import InternationalStaffListPlugin

        plugin = InternationalStaffListPlugin()

        assert plugin.get_plugin_id() == "international_staff_list"
        assert plugin.get_version() == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
