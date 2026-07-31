"""Tests for ConfigManager — 对齐实际 API。"""

import tempfile
from pathlib import Path

from src.jig.core.config_manager import ConfigManager


class TestConfigManager:
    def setup_method(self):
        self._tmp = tempfile.mktemp(suffix=".json")
        self.mgr = ConfigManager(config_path=self._tmp)

    def teardown_method(self):
        Path(self._tmp).unlink(missing_ok=True)

    def test_defaults(self):
        assert self.mgr.api_key == ""
        assert self.mgr.risk_mode_enabled is False

    def test_api_key_property(self):
        self.mgr.api_key = "sk-test-123"
        assert self.mgr.api_key == "sk-test-123"

    def test_persistence(self):
        self.mgr.api_key = "sk-persist"
        self.mgr.save()
        mgr2 = ConfigManager(config_path=self._tmp)
        assert mgr2.api_key == "sk-persist"

    def test_risk_mode(self):
        assert self.mgr.risk_mode_enabled is False
        self.mgr.enable_risk_mode()
        assert self.mgr.risk_mode_enabled is True
        assert self.mgr._config.risk_mode_acknowledged_at is not None
        self.mgr.disable_risk_mode()
        assert self.mgr.risk_mode_enabled is False

    def test_agent_display_name(self):
        self.mgr.set_agent_display_name("pm", "产品经理一号")
        assert self.mgr.get_agent_display_name("pm") == "产品经理一号"
        assert self.mgr.get_agent_display_name("nonexistent") == ""

    def test_agent_overrides_model(self):
        self.mgr.set_agent_model("pm", "pro")
        assert self.mgr.get_agent_model("pm") == "pro"

    def test_agent_overrides_exist(self):
        overrides = self.mgr.agent_overrides
        assert isinstance(overrides, dict)

    def test_mcp_servers(self):
        assert self.mgr.mcp_servers == []
