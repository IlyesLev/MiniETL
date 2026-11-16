from datetime import datetime, timezone
from uuid import UUID

from mini_etl.metadata.model import PipelineRun


class PipelineRunRepository:
    """Persistence operations for pipeline execution records."""

    def __init__(self, session):
        self.session = session

    def create_run(self, pipeline_id: int) -> PipelineRun:
        run = PipelineRun(
            pipeline_id=pipeline_id,
            status="running",
            trigger_type="manual",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        self.session.flush()
        return run

    def mark_succeeded(self, run_id: UUID) -> None:
        run = self._get_run(run_id)
        run.status = "success"
        run.finished_at = datetime.now(timezone.utc)

    def mark_failed(self, run_id: UUID, error_message: str) -> None:
        run = self._get_run(run_id)
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = error_message

    def _get_run(self, run_id: UUID) -> PipelineRun:
        run = self.session.get(PipelineRun, run_id)
        if run is None:
            raise ValueError(f"Pipeline run not found: {run_id}")
        return run
