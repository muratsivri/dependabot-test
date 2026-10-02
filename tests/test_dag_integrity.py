"""DAG butunluk testleri.

Dependabot bir paketi guncellediginde CI bu testleri calistirir; bir DAG
import edilemiyorsa PR kirmizi olur ve merge etmeden once fark edersiniz.
"""

from pathlib import Path

import pytest
from airflow.models import DagBag

DAGS_DIR = Path(__file__).resolve().parents[1] / "dags"
EXPECTED_DAGS = {"hello_world", "etl_example", "insecure_example"}


@pytest.fixture(scope="session")
def dagbag() -> DagBag:
    return DagBag(dag_folder=str(DAGS_DIR), include_examples=False)


def test_no_import_errors(dagbag):
    assert dagbag.import_errors == {}, f"Import hatalari: {dagbag.import_errors}"


def test_expected_dags_loaded(dagbag):
    assert EXPECTED_DAGS <= set(dagbag.dag_ids)


@pytest.mark.parametrize("dag_id", sorted(EXPECTED_DAGS))
def test_dag_has_tags_and_retries(dagbag, dag_id):
    dag = dagbag.get_dag(dag_id)
    assert dag.tags, f"{dag_id} icin tag tanimlanmamis"
    assert "retries" in dag.default_args, f"{dag_id} icin retries tanimlanmamis"


def test_etl_pipeline_logic(dagbag):
    dag = dagbag.get_dag("etl_example")
    assert [t.task_id for t in dag.topological_sort()] == ["extract", "transform", "load"]
