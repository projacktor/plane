# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.utils.issue_filters import filter_issue_state_type, filter_updated_at


@pytest.mark.unit
class TestFilterIssueStateTypeIncludesHold:
    """Hold is open work: the ``type`` filter must select it under ``all`` and ``active``."""

    def test_all_type_includes_hold_in_canonical_order(self):
        issue_filter = filter_issue_state_type({"type": "all"}, {}, method="GET")
        assert issue_filter["state__group__in"] == [
            "backlog",
            "unstarted",
            "hold",
            "started",
            "completed",
            "cancelled",
        ]

    def test_default_type_includes_hold_in_canonical_order(self):
        issue_filter = filter_issue_state_type({}, {}, method="GET")
        assert issue_filter["state__group__in"] == [
            "backlog",
            "unstarted",
            "hold",
            "started",
            "completed",
            "cancelled",
        ]

    def test_active_type_includes_hold(self):
        issue_filter = filter_issue_state_type({"type": "active"}, {}, method="GET")
        assert issue_filter["state__group__in"] == ["unstarted", "hold", "started"]

    def test_backlog_type_stays_backlog_only(self):
        issue_filter = filter_issue_state_type({"type": "backlog"}, {}, method="GET")
        assert issue_filter["state__group__in"] == ["backlog"]


@pytest.mark.unit
class TestFilterUpdatedAt:
    """Regression test for the "Updated At" filter bug — the filter was
    applying to the `created_at` column instead of `updated_at`, so work
    items updated today but created earlier never showed up under
    `Updated At -> is -> today`. See issue #9316."""

    def test_get_method_targets_updated_at_column(self):
        issue_filter = {}
        params = {"updated_at": "2026-06-26"}
        filter_updated_at(params, issue_filter, method="GET")
        # The filter must key on updated_at, not created_at. A bare date goes through
        # date_filter's single-value branch, which appends a lookup suffix
        # (updated_at__date__contains), so match on the prefix rather than the exact key.
        assert any(key.startswith("updated_at__date") for key in issue_filter)
        assert not any("created_at" in key for key in issue_filter)

    def test_get_method_with_csv_targets_updated_at_column(self):
        issue_filter = {}
        params = {"updated_at": "2026-06-25,2026-06-26"}
        filter_updated_at(params, issue_filter, method="GET")
        assert all("updated_at" in key for key in issue_filter)
        assert not any("created_at" in key for key in issue_filter)

    def test_post_method_targets_updated_at_column(self):
        issue_filter = {}
        params = {"updated_at": ["2026-06-26"]}
        filter_updated_at(params, issue_filter, method="POST")
        assert all("updated_at" in key for key in issue_filter)
        assert not any("created_at" in key for key in issue_filter)

    def test_get_method_with_prefix_targets_updated_at_column(self):
        issue_filter = {}
        params = {"updated_at": "2026-06-26"}
        filter_updated_at(params, issue_filter, method="GET", prefix="cycle_issue__")
        keys = list(issue_filter)
        assert any("cycle_issue__updated_at" in k for k in keys)
        assert not any("created_at" in k for k in keys)

    def test_empty_get_filter_is_noop(self):
        issue_filter = {}
        params = {"updated_at": ""}
        filter_updated_at(params, issue_filter, method="GET")
        assert issue_filter == {}
