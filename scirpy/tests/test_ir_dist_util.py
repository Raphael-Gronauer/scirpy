"""Test ir_dist._util utility functions"""

from scirpy.ir_dist._util import DoubleLookupNeighborFinder
import pytest
import numpy as np
import scipy.sparse as sp
import pandas as pd
import numpy.testing as npt


@pytest.fixture
def dlnf():
    clonotypes = pd.DataFrame().assign(
        VJ=["A", "B", "C", "D", "A", "C", "D", "G"],
        VDJ=["A", "B", "C", "D", "nan", "D", "nan", "F"],
    )
    dlnf = DoubleLookupNeighborFinder(feature_table=clonotypes)
    dlnf.add_distance_matrix(
        name="test",
        distance_matrix=sp.csr_matrix(
            [
                [1, 0, 0, 0, 0, 0],
                [0, 2, 0, 0, 1, 0],
                [0, 0, 3, 4, 0, 0],
                [0, 0, 4, 3, 0, 0],
                [0, 1, 0, 0, 5, 0],
                [0, 0, 0, 0, 0, 6],
            ]
        ),
        labels=np.array(["A", "B", "C", "D", "G", "F"]),
    )
    return dlnf


@pytest.fixture
def dlnf_with_lookup(dlnf):
    dlnf.add_lookup_table(feature_col="VJ", distance_matrix="test", name="VJ_test")
    dlnf.add_lookup_table(feature_col="VDJ", distance_matrix="test", name="VDJ_test")
    return dlnf


def test_dlnf_lookup_table(dlnf):
    dlnf.add_lookup_table(feature_col="VJ", distance_matrix="test", name="VJ_test")
    dist_mat, forward, reverse = dlnf.lookups["VJ_test"]
    assert dist_mat == "test"
    npt.assert_array_equal(forward, np.array([0, 1, 2, 3, 0, 2, 3, 4]))
    assert reverse == {
        0: [0, 4],
        1: [1],
        2: [2, 5],
        3: [3, 6],
        4: [7],
    }

    dlnf.add_lookup_table(feature_col="VDJ", distance_matrix="test", name="VDJ_test")
    dist_mat, forward, reverse = dlnf.lookups["VDJ_test"]
    assert dist_mat == "test"
    npt.assert_array_equal(forward, np.array([0, 1, 2, 3, np.nan, 3, np.nan, 5]))
    assert reverse == {
        0: [0],
        1: [1],
        2: [2],
        3: [3, 5],
        np.nan: [4, 6],
        5: [7],
    }


def test_dlnf_lookup(dlnf_with_lookup):
    assert (
        list(dlnf_with_lookup.lookup(0, "VJ_test"))
        == list(dlnf_with_lookup.lookup(4, "VJ_test"))
        == [1, 0, 0, 0, 1, 0, 0, 0]
    )
    assert list(dlnf_with_lookup.lookup(1, "VJ_test")) == [0, 2, 0, 0, 0, 0, 0, 1]
    assert (
        list(dlnf_with_lookup.lookup(2, "VJ_test"))
        == list(dlnf_with_lookup.lookup(5, "VJ_test"))
        == [0, 0, 3, 4, 0, 3, 4, 0]
    )
    assert (
        list(dlnf_with_lookup.lookup(3, "VJ_test"))
        == list(dlnf_with_lookup.lookup(6, "VJ_test"))
        == [0, 0, 4, 3, 0, 4, 3, 0]
    )


def test_dlnf_lookup_nan(dlnf_with_lookup):
    assert dlnf_with_lookup.lookup(0, "VDJ_test") == np.array([1, 0, 0, 0, 0, 0, 0, 0])
    assert (
        dlnf_with_lookup.lookup(3, "VDJ_test")
        == dlnf_with_lookup.lookup(5, "VDJ_test")
        == [0, 0, 4, 3, 0, 3, 0, 0]
    )
    assert (
        dlnf_with_lookup.lookup(4, "VDJ_test")
        == dlnf_with_lookup.lookup(6, "VDJ_test")
        == [0, 0, 0, 0, 1, 0, 1, 0]
    )


@pytest.mark.parametrize("clonotype_id", range(8))
def test_dnlf_lookup_with_two_identical_forward_and_reverse_tables(
    dlnf_with_lookup, clonotype_id
):
    npt.assert_array_equal(
        list(dlnf_with_lookup.lookup(clonotype_id, "VJ_test")),
        list(dlnf_with_lookup.lookup(clonotype_id, "VJ_test", "VJ_test")),
    )
    npt.assert_array_equal(
        list(dlnf_with_lookup.lookup(clonotype_id, "VDJ_test")),
        list(dlnf_with_lookup.lookup(clonotype_id, "VDJ_test", "VDJ_test")),
    )


def test_dlnf_lookup_with_different_forward_and_reverse_tables(dlnf_with_lookup):
    # if entries don't exist the the other lookup table, should return empty iterator.
    assert list(dlnf_with_lookup.lookup(7, "VDJ_test", "VJ_test")) == (
        [0, 0, 0, 0, 0, 0, 0, 0]
    )

    assert list(dlnf_with_lookup.lookup(7, "VJ_test", "VDJ_test")) == (
        [0, 1, 0, 0, 0, 0, 0, 0]
    )
    assert (
        list(dlnf_with_lookup.lookup(0, "VJ_test", "VDJ_test"))
        == list(dlnf_with_lookup.lookup(4, "VJ_test", "VDJ_test"))
        == [1, 0, 0, 0, 0, 0, 0, 0]
    )
    assert (
        list(dlnf_with_lookup.lookup(3, "VJ_test", "VDJ_test"))
        == list(dlnf_with_lookup.lookup(6, "VJ_test", "VDJ_test"))
        == [0, 0, 4, 3, 0, 3, 0, 0]
    )
    assert list(dlnf_with_lookup.lookup(2, "VDJ_test", "VJ_test")) == (
        [0, 0, 3, 4, 0, 3, 4, 0]
    )
    assert (
        list(dlnf_with_lookup.lookup(4, "VDJ_test", "VJ_test"))
        == list(dlnf_with_lookup.lookup(6, "VDJ_test", "VJ_test"))
        == [0] * 8
    )
