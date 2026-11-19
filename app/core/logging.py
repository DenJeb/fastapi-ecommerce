import logging

import app.core.request_context


class RequestIDFilter(logging.Filter):
    """给每条日志记录注入当前请求 ID"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = app.core.request_context.get_request_id() or "-"
        return True


def setup_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(
        level=log_level.upper(),
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(request_id)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True,
    )

    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIDFilter())