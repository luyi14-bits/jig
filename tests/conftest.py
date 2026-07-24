"""Shared test fixtures for Jig."""

import pytest


@pytest.fixture(scope="session")
def skills_dir():
    """Path to the skills directory."""
    return "./skills"


@pytest.fixture(scope="session")
def sample_skill_name():
    """Name of a known skill for testing."""
    return "Luyi14-pm-mentor"


@pytest.fixture(scope="session")
def jig_app(skills_dir):
    """Pre-initialized Jig app instance."""
    from jig import Jig
    return Jig(skills_dir=skills_dir)
