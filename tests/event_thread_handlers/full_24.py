import datetime
import json
import pathlib
import queue
import time


def watch24(logger, event_q, task_q, end_time, nodes_to_watch, operator_node_id):
    files = {}
    start_time = time.time()
    datetime_start = datetime.datetime.fromtimestamp(start_time)
    datetime_end = datetime.datetime.fromtimestamp(end_time)
    duration_seconds = end_time - start_time

    task_count = 0
    last_active_state = None
    current_target_state = "GRID-TIED"
    no_errors = True

    logger.info(f"Watchdog started at {datetime_start}, "
                f"will run for {duration_seconds} seconds until {datetime_end}")
    while end_time > time.time() and no_errors:
        try:
            event_source = event_q.get(10)  #
        except queue.Empty:
            logger.info(f"File event queue is empty")
            continue

        if ".log" not in event_source:  # required to filter out the directory events
            continue

        file_name = pathlib.Path(event_source).name
        file_data = files.get(file_name, None)
        if file_data is None:
            file_handle = open(event_source, "r")
            files[file_name] = {"fh": file_handle, "offset": 0}
        else:
            file_handle = file_data["fh"]

        if not any(node_id in file_name for node_id in nodes_to_watch):
            continue  # Not interested in this file

        for line in file_handle:
            files[file_name]["offset"] += len(line)
            if "ERROR" in line:
                no_errors = False
                logger.info(f"Encountered an ERROR in {file_name} at {time.time()}: {line}")
                break
            elif "exception" in line:
                no_errors = False
                logger.info(f"Encountered an exception in {file_name} at {time.time()}: {line}")
                break
            if "app_event" not in line:
                continue

            try:
                ignore1, level, timestamp, pid, json_msg, ignore2 = line.split("::")
            except ValueError:
                no_errors = False
                logger.info(f"Encountered a malformed line in {file_name} at {time.time()}: {line}")
                break

            msg = json.loads(json_msg)

            if operator_node_id in file_name and "COMPONENT_INITIALIZED" in msg["app_event"]:
                task = {"StartStop": 1}
                task_q.put(task)
                task = {"active": 400, "reactive": 300}
                task_q.put(task)
                logger.info(f"System operator is initialized, start the generators")
            elif "FAIL" in msg["app_event"]:
                action = msg["app_event"]["FAIL"]
                if action == "ISLAND":
                    logger.info(f"Failed to open PCC relay. Retry task {task_count}| {line}")
                    task_count -= 1
                    current_target_state = "GRID-TIED"
                elif action == "RESYNC":
                    logger.info(f"Failed to close PCC relay. Retry task {task_count}| {line}")
                    task_count -= 1
                    current_target_state = "ISLANDED"
                elif action == "DISCONNECT":
                    logger.info(f"Failed to disconnect relay | {line}")
                    current_target_state = "ISLANDED"
                    # TODO: I know these last two are clearly not correct.
                    #  I need to figure out how to get the correct state.
                elif action == "CONNECT":
                    logger.info(f"Failed to connect relay. Retry task {task_count}| {line}")
                    task_count -= 1
                    current_target_state = "ISLANDED"

            elif "ENTER_STATE" in msg["app_event"]:

                logger.info(f"ENTERED STATE: {msg['app_event']['ENTER_STATE']} at {timestamp} "
                               f"caused by {msg['app_event']['trigger']}. "
                               f"Current task: {task_count} "
                               f"Current target state: {current_target_state}")
                task = None
                if "LOCAL-CONTROL" in msg["app_event"].get("ENTER_STATE"):
                    logger.info(f"Generator is in local control, enable secondary control")
                    task_q.put({"SecCtrlEnable": 1})
                elif "GRID-TIED" in msg["app_event"].get("ENTER_STATE"):
                    logger.info(f"Grid is tied, open the PCC relay")
                    last_active_state = "GRID-TIED"
                    if current_target_state == "GRID-TIED":
                        task = {"event": "relay_click", "requestedRelay": "F1PCC", "requestedAction": "OPEN"}
                        task_count += 1
                        current_target_state = "ISLANDED"

                elif "ISLANDED" in msg["app_event"].get("ENTER_STATE"):
                    logger.info(f"Grid is islanded, close the PCC relay")
                    last_active_state = "ISLANDED"
                    if current_target_state == "ISLANDED":
                        task = {"event": "relay_click", "requestedRelay": "F1PCC", "requestedAction": "CLOSE"}
                        task_count += 1
                        current_target_state = "GRID-TIED"

                if task is not None:

                    if task_count in [2, 3]:
                        # This will disable secondary control, causing the generator to go back to local control
                        # where secondary control will be re-enabled.j
                        logger.info(f"Task {task_count}. Queue task: {task}")
                        task_q.put({"SecCtrlEnable": 0})
                        task_q.put(task)
                    elif task_count == 5:
                        task_count = 0
                        current_target_state = last_active_state
                        # I probably don't need this as well as the task count reset when a task fails.
                        # This is necessary because I want to make sure that the generator is back in "GRID-TIED"
                        # before I disable the control and when it comes back online it will be in "GRID-TIED" and
                        # correctly set the current_target_state to ISLANDED as well as add the OPEN relay command to
                        # the queue. In other words, we're going back to the beginning of the loop and need to set the
                        # values back to their initial state.
                        logger.info(f"Task {task_count}. Skip task: {task}")
                        task_q.put({"SecCtrlEnable": 0})
                    else:
                        logger.info(f"Task {task_count}. Queue task: {task}")
                        task_q.put(task)

                logger.info(f"task_q: {list(task_q.queue)}")

    task_q.put("terminate")