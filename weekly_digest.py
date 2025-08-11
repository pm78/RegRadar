"""Utility script to send the weekly digest email."""

from regradar.database import init_db
from regradar.nodes import build_weekly_digest


def main() -> None:
    init_db()
    build_weekly_digest()


if __name__ == "__main__":
    main()

