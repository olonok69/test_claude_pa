import sys
import traceback
from fastapi.encoders import jsonable_encoder


def print_stack(out):
    # cath exception with sys and return the error stack
    out.status = {"code": 500, "message": "Error"}
    ex_type, ex_value, ex_traceback = sys.exc_info()
    # Extract unformatter stack traces as tuples
    trace_back = traceback.extract_tb(ex_traceback)

    # Format stacktrace
    stack_trace = list()

    for trace in trace_back:
        stack_trace.append(
            "File : %s , Line : %d, Func.Name : %s, Message : %s"
            % (trace[0], trace[1], trace[2], trace[3])
        )

    error = ex_type.__name__ + "\n" + str(ex_value) + "\n"
    for err in stack_trace:
        error = error + str(err) + "\n"
    out.error = error
    json_compatible_item_data = jsonable_encoder(out)
    return json_compatible_item_data
