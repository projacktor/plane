import logging

from django.db import migrations, models

logger = logging.getLogger("plane.migrations")

BATCH_SIZE = 4000

HOLD_STATE_COLOR = "#8B5CF6"
HOLD_STATE_SEQUENCE = 30000


def create_hold_states(apps, _schema_editor):
    """Create the default Hold state for every active project.

    All non-deleted projects are covered, archived ones included. Projects that
    already have an active state in the hold group are skipped, which makes the
    migration idempotent. When a project already has an active user-defined
    state named "Hold" in another group, that state is left untouched and the
    system state is created as "Hold-<first 5 chars of project id>" instead.
    Existing issues are never moved between states.
    """
    Project = apps.get_model("db", "Project")
    State = apps.get_model("db", "State")

    # _base_manager is a plain manager both on historical and real models, so
    # these lookups see every row; "active" is pinned by the explicit
    # deleted_at filter instead of relying on manager behaviour.
    projects_with_hold_group = set(
        State._base_manager.filter(group="hold", deleted_at__isnull=True)
        .values_list("project_id", flat=True)
        .distinct()
    )
    projects_with_hold_name = set(
        State._base_manager.filter(name="Hold", deleted_at__isnull=True)
        .values_list("project_id", flat=True)
        .distinct()
    )
    logger.info(f"Projects with an active hold-group state: {len(projects_with_hold_group)}")
    logger.info(f"Projects with an active 'Hold'-named state: {len(projects_with_hold_name)}")

    # Iterate projects in chunks to avoid a memory spike.
    states_to_create = []
    created_count = 0
    projects = (
        Project._base_manager.filter(deleted_at__isnull=True)
        .values_list("id", "workspace_id")
        .iterator()
    )
    for project_id, workspace_id in projects:
        if project_id in projects_with_hold_group:
            continue
        if project_id in projects_with_hold_name:
            name = f"Hold-{str(project_id)[:5]}"
        else:
            name = "Hold"
        states_to_create.append(
            State(
                name=name,
                group="hold",
                project_id=project_id,
                workspace_id=workspace_id,
                color=HOLD_STATE_COLOR,
                sequence=HOLD_STATE_SEQUENCE,
                default=False,
            )
        )
        created_count += 1
        if len(states_to_create) >= BATCH_SIZE:
            State._base_manager.bulk_create(states_to_create, batch_size=BATCH_SIZE)
            states_to_create = []

    if states_to_create:
        State._base_manager.bulk_create(states_to_create, batch_size=BATCH_SIZE)
    logger.info(f"Created {created_count} hold states.")


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0125_reset_project_deploy_board_identity"),
    ]

    operations = [
        migrations.AlterField(
            model_name="state",
            name="group",
            field=models.CharField(
                choices=[
                    ("backlog", "Backlog"),
                    ("unstarted", "Unstarted"),
                    ("hold", "Hold"),
                    ("started", "Started"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                    ("triage", "Triage"),
                ],
                default="backlog",
                max_length=20,
            ),
        ),
        migrations.RunPython(create_hold_states, reverse_code=migrations.RunPython.noop),
    ]
