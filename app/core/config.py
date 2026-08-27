from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent.parent


class Settings:
    APP_NAME: str = os.getenv(
        "NEXUS_APP_NAME",
        "NEXUS AI",
    )

    APP_VERSION: str = os.getenv(
        "NEXUS_APP_VERSION",
        "4.0",
    )

    ENVIRONMENT: str = os.getenv(
        "NEXUS_ENVIRONMENT",
        "development",
    )

    LOG_LEVEL: str = os.getenv(
        "NEXUS_LOG_LEVEL",
        "INFO",
    )

    MAX_PREVIEW_ROWS: int = int(
        os.getenv(
            "NEXUS_MAX_PREVIEW_ROWS",
            "100",
        )
    )

    MAX_REPORT_ROWS: int = int(
        os.getenv(
            "NEXUS_MAX_REPORT_ROWS",
            "10000",
        )
    )

    DATA_DIR: Path = (
        PROJECT_ROOT / "data"
    )

    LOG_DIR: Path = (
        PROJECT_ROOT / "logs"
    )

    REPORT_DIR: Path = (
        PROJECT_ROOT / "reports"
    )

    TEST_DIR: Path = (
        PROJECT_ROOT / "tests"
    )

    @classmethod
    def ensure_directories(
        cls,
    ) -> None:

        cls.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        cls.LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        cls.REPORT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )


settings = Settings()

settings.ensure_directories()