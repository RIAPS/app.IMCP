import inspect

# Log some messages with automatic JSON formatting
import json
import time


def log_json(logger, level, message, event=None):
    frame = inspect.currentframe().f_back
    module_name = frame.f_globals['__name__']
    function_name = frame.f_code.co_name
    line_number = frame.f_lineno

    log_entry = {
        "timestamp": time.time(),
        "level": level,
        "module": module_name,
        "function": function_name,
        "line": line_number,
        "message": message,
        "app_event": event
    }
    getattr(logger, level)(json.dumps(log_entry))  # Convert the dictionary to a string


if __name__ == '__main__':
    import spdlog

    logger = spdlog.ConsoleLogger("json_logger")
    logger.set_level(spdlog.LogLevel.DEBUG)
    log_json(logger, "debug", "This is a debug message")
    log_json(logger, "info", "This is an info message")
    log_json(logger, "warn", "This is a warning message")
    log_json(logger, "error", "This is an error message")
    log_json(logger, "critical", "This is a critical message")
