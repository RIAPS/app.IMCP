import datetime
import functools
import pathlib
import pytest

import pytest
import logging

import pytest
import logging

@pytest.fixture
def testslogger():
    log_dir_path = pathlib.Path(__file__).parents[1]/"test_logs"
    print(log_dir_path)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    # Create a logger
    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.DEBUG)  # Set the logger's level to the lowest level you want to capture

    # Create a file handler for DEBUG level messages
    debug_handler = logging.FileHandler(f"{log_dir_path}/debug.log")
    debug_handler.setLevel(logging.DEBUG)

    # Create a file handler for ERROR level messages
    error_handler = logging.FileHandler(f"{log_dir_path}/error.log")
    error_handler.setLevel(logging.ERROR)

    # Create a formatter and set it for the handlers
    formatter = logging.Formatter('%(asctime)s | %(message)s')
    debug_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)

    yield logger  # Provide the logger to the test functions

    # Teardown code (optional): Remove the handlers
    logger.removeHandler(debug_handler)
    logger.removeHandler(error_handler)
    debug_handler.close()
    error_handler.close()

# Example test function that uses the logger fixture
def test_logging(file_logger):
    file_logger.debug("This is a DEBUG message")
    file_logger.error("This is an ERROR message")

# Run the test with pytest