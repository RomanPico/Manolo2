"""Run the ASGI server with uvicorn."""

import logging

import uvicorn

from manolo.settings import get_settings


def main() -> None:
    """Entry point for `python -m manolo`."""
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "manolo.server.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
