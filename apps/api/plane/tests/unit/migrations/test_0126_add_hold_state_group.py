# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Unit tests for the data migration ``0126_add_hold_state_group``.

The migration module name starts with a digit, so the callable is pulled in
through importlib. ``create_hold_states`` is exercised directly against the
real app registry (``django.apps.apps``) with a ``None`` schema editor, the
same way the migration invokes it.
"""

import importlib

import pytest
from django.apps import apps
from django.utils import timezone

from plane.db.models import Issue, Project, State, Workspace

create_hold_states = importlib.import_module("plane.db.migrations.0126_add_hold_state_group").create_hold_states


@pytest.fixture
def workspace(create_user):
    """Create a test workspace"""
    return Workspace.objects.create(
        name="Hold Workspace",
        slug="hold-workspace",
        owner=create_user,
    )


@pytest.fixture
def project(workspace, create_user):
    """Create a test project without any states"""
    return Project.objects.create(
        name="Hold Project",
        identifier="HP",
        workspace=workspace,
        created_by=create_user,
    )


@pytest.mark.unit
class TestCreateHoldStates:
    """Tests for create_hold_states(apps, schema_editor)"""

    @pytest.mark.django_db
    def test_creates_hold_state_for_project_without_states(self, project):
        """A project with no states at all gets the default Hold state."""
        assert State.objects.filter(project=project).count() == 0

        create_hold_states(apps, None)

        states = State.objects.filter(project=project)
        assert states.count() == 1
        hold_state = states.get()
        assert hold_state.name == "Hold"
        assert hold_state.group == "hold"
        assert hold_state.sequence == 30000
        assert hold_state.color == "#8B5CF6"
        assert hold_state.default is False

    @pytest.mark.django_db
    def test_skips_project_with_existing_active_hold_group_state(self, project):
        """A project that already has an active state in the hold group is skipped."""
        existing = State.objects.create(
            name="Paused",
            project=project,
            workspace=project.workspace,
            group="hold",
            color="#123456",
            default=False,
        )

        create_hold_states(apps, None)

        hold_states = State.objects.filter(project=project, group="hold")
        assert hold_states.count() == 1
        assert hold_states.get().id == existing.id

    @pytest.mark.django_db
    def test_custom_hold_state_in_other_group_is_preserved_and_suffixed(self, project):
        """A user-created 'Hold' state in another group stays untouched and the
        system state gets the ``Hold-<first 5 chars of project id>`` suffix."""
        custom_hold = State.objects.create(
            name="Hold",
            project=project,
            workspace=project.workspace,
            group="unstarted",
            color="#123456",
            default=True,
        )
        before = {
            "id": custom_hold.id,
            "name": custom_hold.name,
            "group": custom_hold.group,
            "color": custom_hold.color,
            "sequence": custom_hold.sequence,
            "default": custom_hold.default,
        }

        create_hold_states(apps, None)

        # The user's state is unchanged in every field.
        custom_hold.refresh_from_db()
        assert custom_hold.id == before["id"]
        assert custom_hold.name == before["name"]
        assert custom_hold.group == before["group"]
        assert custom_hold.color == before["color"]
        assert custom_hold.sequence == before["sequence"]
        assert custom_hold.default == before["default"]

        # The system state carries the suffix and lives in the hold group.
        system_hold = State.objects.get(project=project, group="hold")
        assert system_hold.name == f"Hold-{str(project.id)[:5]}"
        assert system_hold.sequence == 30000
        assert system_hold.color == "#8B5CF6"
        assert system_hold.default is False

    @pytest.mark.django_db
    def test_issue_state_is_unchanged(self, project, create_user):
        """Existing issues are never moved into Hold."""
        started = State.objects.create(
            name="In Progress",
            project=project,
            workspace=project.workspace,
            group="started",
        )
        issue = Issue.objects.create(
            name="Original Issue",
            workspace=project.workspace,
            project=project,
            state=started,
            created_by=create_user,
        )

        create_hold_states(apps, None)

        issue.refresh_from_db()
        assert issue.state_id == started.id
        assert issue.state_id != State.objects.get(project=project, group="hold").id

    @pytest.mark.django_db
    def test_idempotent_on_repeated_calls(self, project):
        """Running the migration twice creates exactly one hold-group state."""
        create_hold_states(apps, None)
        create_hold_states(apps, None)

        assert State.objects.filter(project=project, group="hold").count() == 1
        assert State.objects.filter(project=project).count() == 1

    @pytest.mark.django_db
    def test_archived_project_gets_hold_state(self, project):
        """Archived (but not deleted) projects are covered too."""
        Project.objects.filter(id=project.id).update(archived_at=timezone.now())

        create_hold_states(apps, None)

        hold_state = State.objects.get(project=project, group="hold")
        assert hold_state.name == "Hold"

    @pytest.mark.django_db
    def test_deleted_project_is_skipped(self, project):
        """Soft-deleted projects must not receive a hold state."""
        Project.objects.filter(id=project.id).update(deleted_at=timezone.now())

        create_hold_states(apps, None)

        assert State.objects.filter(project_id=project.id).count() == 0

    @pytest.mark.django_db
    def test_soft_deleted_hold_state_is_not_active(self, project):
        """A soft-deleted hold-group state does not make the project complete."""
        State.objects.create(
            name="Paused",
            project=project,
            workspace=project.workspace,
            group="hold",
        )
        State.objects.filter(project=project, group="hold").update(deleted_at=timezone.now())

        create_hold_states(apps, None)

        hold_states = State.objects.filter(project=project, group="hold")
        assert hold_states.count() == 1
        assert hold_states.get().name == "Hold"
