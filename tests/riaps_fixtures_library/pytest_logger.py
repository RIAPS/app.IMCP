import logging
import pathlib
import pytest

class TestLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level=level)

        log_dir_path = pathlib.Path(__file__).parents[1]/"test_logs"
        print(log_dir_path)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        # Create a logger
        # logger = logging.getLogger("my_logger")
        # logger.setLevel(logging.DEBUG)  # Set the logger's level to the lowest level you want to capture
        # logger.propagate = False

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Create a file handler for DEBUG level messages
        # debug_handler = TimedRotatingFileHandler(f"{log_dir_path}/debug.log", when="s", interval=5, backupCount=0)
        debug_handler = logging.FileHandler(f"{log_dir_path}/debug.log")
        debug_handler.setLevel(logging.DEBUG)

        # Create a file handler for ERROR level messages
        info_handler = logging.FileHandler(f"{log_dir_path}/info.log")
        info_handler.setLevel(logging.INFO)

        # Create a file handler for ERROR level messages
        error_handler = logging.FileHandler(f"{log_dir_path}/error.log")
        error_handler.setLevel(logging.ERROR)

        # Create a formatter and set it for the handlers
        formatter = logging.Formatter('%(asctime)s | %(message)s')
        debug_handler.setFormatter(formatter)
        info_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        self.addHandler(debug_handler)
        self.addHandler(info_handler)
        self.addHandler(error_handler)    
        self.addHandler(console_handler)


@pytest.fixture
def testslogger():
    logger = TestLogger("test_logger")

    return logger  # Provide the logger to the test functions

    # Teardown code (optional): Remove the handlers
    # logger.removeHandler(debug_handler)
    # logger.removeHandler(info_handler)
    # logger.removeHandler(error_handler)
    # logger.removeHandler(console_handler)
    # debug_handler.close()
    # info_handler.close()
    # error_handler.close()
    # console_handler.close()

# Example test function that uses the logger fixture
def test_logging(testslogger):
    testslogger.debug("This is a DEBUG message")
    testslogger.info("This is a Info message")
    testslogger.error("This is an ERROR message")

# Run the test with pytest