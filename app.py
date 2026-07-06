import sys
import os

import certifi
ca = certifi.where()
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, FileResponse
from dotenv import load_dotenv
load_dotenv()
mongo_db_url = os.getenv("MONGODB_URL_KEY")
print(mongo_db_url)
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile,Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd

from networksecurity.utils.main_utils.utils import load_object

from networksecurity.utils.ml_utils.model.estimater import NetworkModel

from fastapi.templating import Jinja2Templates
client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)

from networksecurity.constant.training_pipeline import DATA_INGESTION_COLLECTION_NAME
from networksecurity.constant.training_pipeline import DATA_INGESTION_DATABASE_NAME

database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

app = FastAPI(
    title="Network Security Phishing Detection",
    description="Predict phishing websites using Machine Learning",
    version="1.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/docs-page")
async def docs():
    return RedirectResponse("/docs")


@app.get("/train")
async def train(request: Request):
    try:
        pipeline = TrainingPipeline()
        pipeline.run_pipeline()

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "message": "Model Training Completed Successfully"
            }
        )

    except Exception as e:
        raise NetworkSecurityException(e, sys)

@app.post("/predict")
async def predict(
    request: Request,
    file: UploadFile = File(...)
):
    try:

        df = pd.read_csv(file.file)

        preprocessor = load_object("final_models/preprocessor.pkl")
        model = load_object("final_models/model.pkl")

        network_model = NetworkModel(
            preprocessor=preprocessor,
            model=model
        )

        prediction = network_model.predict(df)

        df["Prediction"] = prediction

        total_records = len(df)

        phishing_count = (df["Prediction"] == 1).sum()
        legitimate_count = (df["Prediction"] == -1).sum()

        phishing_percentage = round(
            phishing_count * 100 / total_records,
            2
        )

        legitimate_percentage = round(
            legitimate_count * 100 / total_records,
            2
        )

        os.makedirs(
            "prediction_output",
            exist_ok=True
        )

        output_path = os.path.join(
            "prediction_output",
            "output.csv"
        )

        df.to_csv(
            output_path,
            index=False
        )

        table = df.to_html(
            index=False,
            classes="table table-striped table-hover table-bordered text-center"
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "table": table,
                "filename": file.filename,
                "rows": total_records,
                "phishing": phishing_count,
                "legitimate": legitimate_count,
                "phishing_percentage": phishing_percentage,
                "legitimate_percentage": legitimate_percentage
            }
        )

    except Exception as e:
        raise NetworkSecurityException(e, sys)


@app.get("/download")
async def download():

    return FileResponse(
        path="prediction_output/output.csv",
        filename="prediction_output.csv",
        media_type="text/csv"
    )


if __name__ == "__main__":
    app_run(
        app,
        host="0.0.0.0",
        port=8000
    )