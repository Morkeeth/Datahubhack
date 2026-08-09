"""dbt materialisation is required before solidify."""

from pathlib import Path

import pytest

from nullspace.builder import materialize_dbt_model


def test_materialize_refuses_missing_project(tmp_path: Path):
    with pytest.raises(ValueError, match="dbt_project.yml missing"):
        materialize_dbt_model(tmp_path, "ghost_missing")
