"""Tests for the cursor jump history (browser-style back/forward)."""
from __future__ import annotations

from je_editor.utils.navigation.location_history import LocationHistory


class TestLocationHistoryBasics:
    def test_empty_history(self):
        history = LocationHistory()
        assert history.current() is None
        assert not history.can_go_back()
        assert not history.can_go_forward()

    def test_single_visit(self):
        history = LocationHistory()
        history.visit(10)
        assert history.current() == 10
        assert not history.can_go_back()

    def test_back_after_two_visits(self):
        history = LocationHistory()
        history.visit(1)
        history.visit(20)
        assert history.back() == 1
        assert history.current() == 1

    def test_forward_after_back(self):
        history = LocationHistory()
        history.visit(1)
        history.visit(20)
        history.back()
        assert history.forward() == 20

    def test_back_at_start_returns_none(self):
        history = LocationHistory()
        history.visit(5)
        assert history.back() is None

    def test_forward_at_end_returns_none(self):
        history = LocationHistory()
        history.visit(5)
        history.visit(9)
        assert history.forward() is None


class TestBrowserSemantics:
    def test_visit_in_middle_truncates_forward(self):
        history = LocationHistory()
        for line in (1, 2, 3):
            history.visit(line)
        history.back()          # now at 2
        history.visit(99)       # new branch from 2
        assert history.entries == [1, 2, 99]
        assert history.forward() is None

    def test_consecutive_duplicate_is_ignored(self):
        history = LocationHistory()
        history.visit(7)
        history.visit(7)
        assert history.entries == [7]

    def test_non_consecutive_duplicate_is_kept(self):
        history = LocationHistory()
        history.visit(7)
        history.visit(3)
        history.visit(7)
        assert history.entries == [7, 3, 7]

    def test_can_flags_track_position(self):
        history = LocationHistory()
        history.visit(1)
        history.visit(2)
        assert history.can_go_back()
        assert not history.can_go_forward()
        history.back()
        assert not history.can_go_back()
        assert history.can_go_forward()


class TestMaxSize:
    def test_oldest_entries_are_dropped(self):
        history = LocationHistory(max_size=3)
        for line in (1, 2, 3, 4, 5):
            history.visit(line)
        assert history.entries == [3, 4, 5]
        assert history.current() == 5

    def test_index_stays_valid_after_trim(self):
        history = LocationHistory(max_size=2)
        history.visit(1)
        history.visit(2)
        history.visit(3)
        assert history.current() == 3
        assert history.back() == 2

    def test_min_size_is_one(self):
        history = LocationHistory(max_size=0)
        history.visit(1)
        history.visit(2)
        assert history.entries == [2]


class TestClearAndShift:
    def test_clear_resets(self):
        history = LocationHistory()
        history.visit(1)
        history.visit(2)
        history.clear()
        assert history.current() is None
        assert history.entries == []

    def test_shift_after_insert_moves_later_entries(self):
        history = LocationHistory()
        history.visit(2)
        history.visit(10)
        history.shift_after_edit(changed_line=5, line_delta=3)
        # entry 2 (<=5) stays, entry 10 (>5) shifts to 13
        assert history.entries == [2, 13]

    def test_shift_after_delete_moves_later_entries(self):
        history = LocationHistory()
        history.visit(2)
        history.visit(10)
        history.shift_after_edit(changed_line=5, line_delta=-2)
        assert history.entries == [2, 8]

    def test_shift_with_zero_delta_is_noop(self):
        history = LocationHistory()
        history.visit(2)
        history.visit(10)
        history.shift_after_edit(changed_line=5, line_delta=0)
        assert history.entries == [2, 10]
