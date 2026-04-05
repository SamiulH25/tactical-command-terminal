"""Tests for the save/load and user config systems."""

import json
import tempfile
from pathlib import Path

import pytest

from src.models.campaign import Campaign
from src.systems.save_load import (
    campaign_to_dict,
    create_save_data,
    delete_save,
    dict_to_campaign,
    get_save_metadata,
    get_save_path,
    load_game,
    save_game,
)
from src.systems.user_config import UserConfig, load_config, save_config

# ---------------------------------------------------------------------------
# Save/Load
# ---------------------------------------------------------------------------


class TestCampaignSerialization:
    """Verify campaign serialization round-trips."""

    def test_round_trip(self) -> None:
        """Campaign should serialize and deserialize identically."""
        camp = Campaign()
        camp.current_floor = 5
        camp.current_credits = 200
        camp.adjust_reputation("rebel", 15)
        camp.record_decision("event:help_rebel")
        camp.allies_rescued.append("Rebel-Alpha")

        data = campaign_to_dict(camp)
        restored = dict_to_campaign(data)

        assert restored.current_floor == camp.current_floor
        assert restored.current_credits == camp.current_credits
        assert restored.reputation["rebel"] == 15
        assert restored.has_decision("event:help_rebel")
        assert "Rebel-Alpha" in restored.allies_rescued

    def test_default_campaign_round_trip(self) -> None:
        """A fresh campaign should round-trip cleanly."""
        camp = Campaign()
        data = campaign_to_dict(camp)
        restored = dict_to_campaign(data)
        assert restored.current_floor == 0
        assert restored.current_credits == 150
        assert restored.decision_log == []


class TestSaveGameData:
    """Verify SaveData validation."""

    def test_create_save_data(self) -> None:
        """Should create valid save data."""
        camp = Campaign()
        save_data = create_save_data(camp)
        assert save_data.version == 1
        assert save_data.campaign["current_floor"] == 0


class TestSaveFileIO:
    """Verify save file read/write."""

    def _temp_save_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create a temporary directory for save files."""
        tmp = tempfile.TemporaryDirectory()
        import src.systems.save_load as sl

        sl._SAVE_DIR = Path(tmp.name)
        return tmp

    def test_save_and_load(self) -> None:
        """Should save and load campaign state."""
        tmp = self._temp_save_dir()
        try:
            camp = Campaign()
            camp.current_floor = 3
            camp.current_credits = 300
            save_game(camp, slot=1)

            loaded = load_game(slot=1)
            assert loaded is not None
            assert loaded.current_floor == 3
            assert loaded.current_credits == 300
        finally:
            tmp.cleanup()

    def test_load_empty_slot(self) -> None:
        """Loading an empty slot should return None."""
        tmp = self._temp_save_dir()
        try:
            result = load_game(slot=2)
            assert result is None
        finally:
            tmp.cleanup()

    def test_corrupted_save_raises(self) -> None:
        """A corrupted save file should raise ValueError."""
        tmp = self._temp_save_dir()
        try:
            save_path = get_save_path(slot=1)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text("not json")
            with pytest.raises(json.JSONDecodeError):
                load_game(slot=1)
        finally:
            tmp.cleanup()

    def test_version_mismatch_raises(self) -> None:
        """A save with wrong version should raise ValueError."""
        tmp = self._temp_save_dir()
        try:
            save_path = get_save_path(slot=1)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text('{"version": 999, "campaign": {}}')
            with pytest.raises(ValueError, match="version"):
                load_game(slot=1)
        finally:
            tmp.cleanup()

    def test_missing_campaign_raises(self) -> None:
        """A save with missing campaign should raise ValueError."""
        tmp = self._temp_save_dir()
        try:
            save_path = get_save_path(slot=1)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text('{"version": 1}')
            with pytest.raises(ValueError, match="corrupted"):
                load_game(slot=1)
        finally:
            tmp.cleanup()

    def test_delete_save(self) -> None:
        """Deleting a save should remove the file."""
        tmp = self._temp_save_dir()
        try:
            camp = Campaign()
            save_game(camp, slot=1)
            assert delete_save(slot=1) is True
            assert load_game(slot=1) is None
        finally:
            tmp.cleanup()

    def test_delete_nonexistent_save(self) -> None:
        """Deleting a non-existent save should return False."""
        tmp = self._temp_save_dir()
        try:
            assert delete_save(slot=3) is False
        finally:
            tmp.cleanup()

    def test_invalid_slot_raises(self) -> None:
        """Invalid slot numbers should raise ValueError."""
        with pytest.raises(ValueError, match="1-3"):
            get_save_path(slot=0)
        with pytest.raises(ValueError, match="1-3"):
            get_save_path(slot=4)


class TestSaveMetadata:
    """Verify save metadata extraction."""

    def _temp_save_dir(self) -> tempfile.TemporaryDirectory[str]:
        tmp = tempfile.TemporaryDirectory()
        import src.systems.save_load as sl

        sl._SAVE_DIR = Path(tmp.name)
        return tmp

    def test_metadata_from_save(self) -> None:
        """Should extract summary info from a save."""
        tmp = self._temp_save_dir()
        try:
            camp = Campaign()
            camp.current_floor = 5
            camp.current_credits = 250
            save_game(camp, slot=1)

            meta = get_save_metadata(slot=1)
            assert meta is not None
            assert meta.current_floor == 5
            assert meta.credits == 250
            assert "Outpost Alpha" in meta.outpost_name
        finally:
            tmp.cleanup()

    def test_metadata_empty_slot(self) -> None:
        """Empty slot should return None."""
        tmp = self._temp_save_dir()
        try:
            assert get_save_metadata(slot=1) is None
        finally:
            tmp.cleanup()


# ---------------------------------------------------------------------------
# User Config
# ---------------------------------------------------------------------------


class TestUserConfig:
    """Verify user configuration system."""

    def test_defaults(self) -> None:
        """Default config should have valid values."""
        cfg = UserConfig()
        cfg.validate()
        assert cfg.master_volume == 0.5
        assert cfg.crt_effects is True
        assert cfg.font_size == 16
        assert cfg.window_scale == 1.0

    def test_invalid_volume_raises(self) -> None:
        with pytest.raises(ValueError, match="master_volume"):
            UserConfig(master_volume=-0.1).validate()

    def test_invalid_font_raises(self) -> None:
        with pytest.raises(ValueError, match="font_size"):
            UserConfig(font_size=0).validate()

    def test_invalid_scale_raises(self) -> None:
        with pytest.raises(ValueError, match="window_scale"):
            UserConfig(window_scale=3.0).validate()


class TestConfigFileIO:
    """Verify config file read/write."""

    def test_save_and_load(self) -> None:
        """Config should round-trip through file."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = UserConfig(master_volume=0.8, crt_effects=False, font_size=20)
            save_config(cfg, path)

            loaded = load_config(path)
            assert loaded.master_volume == pytest.approx(0.8)
            assert loaded.crt_effects is False
            assert loaded.font_size == 20

    def test_missing_file_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nonexistent.json"
            cfg = load_config(path)
            assert cfg.master_volume == 0.5

    def test_corrupt_file_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("not json")
            cfg = load_config(path)
            assert cfg.master_volume == 0.5

    def test_invalid_values_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text('{"master_volume": -1.0, "font_size": -5}')
            cfg = load_config(path)
            # Should fall back to defaults
            assert cfg.master_volume == 0.5
            assert cfg.font_size == 16
