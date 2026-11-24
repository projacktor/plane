# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.space.utils.grouper import issue_group_values as space_issue_group_values
from plane.utils.grouper import issue_group_values

# Canonical state-group order: backlog -> unstarted -> hold -> started -> completed -> cancelled.
CANONICAL_STATE_GROUPS = ["backlog", "unstarted", "hold", "started", "completed", "cancelled"]


@pytest.mark.unit
def test_issue_group_values_requires_project_or_user():
    with pytest.raises(ValueError):
        issue_group_values(field="state_id", slug="workspace")


@pytest.mark.unit
def test_state_group_values_are_canonical_with_hold():
    """``state__group`` keys must list Hold between Unstarted and Started."""
    groups = issue_group_values(
        field="state__group",
        slug="workspace",
        project_id="00000000-0000-0000-0000-000000000000",
    )
    assert groups == CANONICAL_STATE_GROUPS


@pytest.mark.unit
def test_space_state_group_values_are_canonical_with_hold():
    """The space grouper mirrors the app grouper's canonical state-group order."""
    groups = space_issue_group_values(field="state__group", slug="workspace", project_id=None)
    assert groups == CANONICAL_STATE_GROUPS
