import logging
import structlog
import os
import uuid
from functools import wraps
import inspect
from structlog.stdlib import BoundLogger
from typing import Any, Callable

PTM_LOG_CONSOLE = os.getenv('PTMLOG_CONSOLE', '0')

if PTM_LOG_CONSOLE == '1':
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S.%f"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        logger_factory=structlog.PrintLoggerFactory(),
    )
else:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_logger() -> BoundLogger:
    return structlog.get_logger()

class procedure:
    def __init__(self, procedure_id: str) -> None:
        self.procedure_id = procedure_id
    
    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: tuple[Any], **kwargs: dict[str, Any]) -> Any:
            run_id = str(uuid.uuid4())
            run_arguments = inspect.signature(func).bind(*args, **kwargs).arguments
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                procedure_id     = self.procedure_id,
                run_id           = run_id,
            )
            logger = get_logger()
            logger.info('procedure started', run_status='started', run_arguments=run_arguments)
            try:
                return_value = func(*args, **kwargs)
            except Exception as e:
                logger.exception('procedure failed', run_status='failed', run_arguments=run_arguments)
                raise e
            else:
                logger.info('procedure succeeded', run_status='succeeded', run_arguments=run_arguments, run_return_value=return_value)
                return return_value
            finally:
                structlog.contextvars.unbind_contextvars(
                    'procedure_id',
                    'run_id',
                )
        return wrapper
