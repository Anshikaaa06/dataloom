"""Tests for save and revert logic in the project service."""

import time
import pytest
from app.services.project_service import (
    create_project,
    create_checkpoint,
    log_transformation,
)
from app import models


class TestCheckpoint:
    def test_create_checkpoint_marks_logs(self, db):
        """Creating a checkpoint should mark unapplied logs as applied."""
        # Create a project record
        project = models.Project(name="test", file_path="/tmp/test.csv", description="test")
        db.add(project)
        db.commit()
        db.refresh(project)

        # Log a transformation
        log_transformation(db, project.project_id, "addRow", {"row_params": {"index": 0}})

        # Verify log is unapplied
        logs = db.query(models.ProjectChangeLog).filter_by(project_id=project.project_id).all()
        assert len(logs) == 1
        assert logs[0].applied == False

        # Create checkpoint
        checkpoint = create_checkpoint(db, project.project_id, "First save")

        # Verify log is now applied
        db.refresh(logs[0])
        assert logs[0].applied == True
        assert logs[0].checkpoint_id == checkpoint.id

    def test_checkpoint_message(self, db):
        """Checkpoint should store the commit message."""
        project = models.Project(name="test", file_path="/tmp/test.csv", description="test")
        db.add(project)
        db.commit()
        db.refresh(project)

        checkpoint = create_checkpoint(db, project.project_id, "My save message")
        assert checkpoint.message == "My save message"


class TestLastModifiedUpdate:
    """Verify that last_modified is updated on transformations and checkpoints."""

    def test_log_transformation_updates_last_modified(self, db):
        """Logging a transformation should update the project's last_modified timestamp."""
        project = models.Project(name="test", file_path="/tmp/test.csv", description="test")
        db.add(project)
        db.commit()
        db.refresh(project)

        original_modified = project.last_modified

        # Small delay to ensure timestamp difference
        time.sleep(0.1)

        log_transformation(db, project.project_id, "addRow", {"row_params": {"index": 0}})
        db.refresh(project)

        assert project.last_modified is not None
        assert project.last_modified > original_modified

    def test_create_checkpoint_updates_last_modified(self, db):
        """Creating a checkpoint should update the project's last_modified timestamp."""
        project = models.Project(name="test", file_path="/tmp/test.csv", description="test")
        db.add(project)
        db.commit()
        db.refresh(project)

        original_modified = project.last_modified

        time.sleep(0.1)

        create_checkpoint(db, project.project_id, "Save point")
        db.refresh(project)

        assert project.last_modified is not None
        assert project.last_modified > original_modified
