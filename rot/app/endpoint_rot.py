import os
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
import uvicorn
import platform
from dotenv import load_dotenv
import os.path as path
from detectaicore import index_response, Job
import sys
import traceback

try:
    from rot.app.src.utils_rot import get_rot_analisys
except:
    from src.utils_rot import get_rot_analisys


# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
MODEL_PATH = os.getenv("MODEL_PATH")
if MODEL_PATH == None:
    MODEL_PATH = "/home/detectai/models/rot"


endpoint = FastAPI()

# output folder
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(ROOT_DIR, "out")

if platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models", "rot")
    two_up = path.abspath(path.join(__file__, "../.."))

    five_up = os.path.abspath(os.path.join(__file__, "../../../../.."))
    path_data = os.path.join(five_up, "files", "control_dataset.json")
    path_picke = os.path.join(five_up, "files", "dicc_metadata.pickle")
elif platform.system() == "Linux":
    five_up = output_folder
    path_data = os.path.join(output_folder, "control_dataset.json")
    path_picke = os.path.join(output_folder, "dicc_metadata.pickle")
    MODELS_PATH = MODEL_PATH


global jobs
jobs = {}


@endpoint.get("/health-check")
async def health_check(request: Request):
    return JSONResponse(status_code=200, content={"message": "OK"})


@endpoint.get("/work/status")
async def status_handler(request: Request):
    return jobs


@endpoint.post("/process")
async def process_tika(request: Request, out: index_response):
    """
    Process TIKA output received from Detect
    """
    try:
        response = await request.json()
        new_task = Job()
        # Capture Job and apply status
        jobs[new_task.uid] = new_task
        jobs[new_task.uid].status = "Job started"
        jobs[new_task.uid].type_job = "Rot Analysis"

        filters = response.get("filters")
        #
        if response.get("documents"):
            docs = response.get("documents")
        else:
            raise AttributeError("No documents on the requests")
        date_timestamp = response.get("date_timestamp")

        if date_timestamp == None or date_timestamp == "":
            dont_use_now = False

        else:
            dont_use_now = True

        if docs:
            document_count = len(docs)
        else:
            raise AttributeError("No documents on the requests")

        if isinstance(response.get("is_image"), list):
            is_image = response.get("is_image")
            is_image = [x.lower() for x in is_image]
        else:
            is_image = []
        if isinstance(response.get("is_business"), list):
            is_business = response.get("is_business")
            is_business = [x.lower() for x in is_business]
        else:
            is_business = []

        # List of document not
        documents_non_processed = []
        documents_processed = 0
        # create Rot Metadata and Run analisys
        analyzer = await run_in_threadpool(
            get_rot_analisys,
            docs,
            path_picke,
            filters,
            True,
            jobs,
            new_task,
            document_count,
            five_up,
            dont_use_now,
            date_timestamp,
            is_image,
            is_business,
            documents_non_processed,
            documents_processed,
        )
        # creating Output
        dic_output = {}
        dic_output["number_docs"] = document_count
        dic_output["business_documents_counts"] = analyzer.get_is_business()
        dic_output["image_documents_counts"] = analyzer.get_is_image()
        dic_output["rot_dictionary"] = analyzer.get_rot_dict()

        out.status = {"code": 200, "message": "Success"}
        out.data = dic_output
        out.number_documents_treated = len(analyzer.dataframe_rot)
        out.number_documents_non_treated = len(analyzer.documents_non_processed)
        out.list_id_not_treated = analyzer.documents_non_processed

        json_compatible_item_data = jsonable_encoder(out)
        # Job completed
        jobs[new_task.uid].status = "Job Completed"
        return JSONResponse(content=json_compatible_item_data)

    except Exception as e:
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
        return JSONResponse(content=json_compatible_item_data)


if __name__ == "__main__":
    uvicorn.run(
        "endpoint_rot:endpoint",
        reload=True,
        host="127.0.0.1",
        workers=2,
        port=5007,
        log_level="info",
    )
