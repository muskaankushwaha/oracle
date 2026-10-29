"""Smoke test: proves the package imports and CI is wired up. Real tests arrive with each module."""

import oracle


def test_package_imports():
    assert oracle.__version__
