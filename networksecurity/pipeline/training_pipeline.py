import os
import sys

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.components.model_trainer import ModelTrainer

from networksecurity.entity.config_entity import(
    TrainingPipelineConfig,
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
)

from networksecurity.entity.artifact_entity import (
    DataIngestionArtifact,
    DataValidationArtifact,
    DataTransformationArtifact,
    ModelTrainerArtifact,
)

from networksecurity.constant.training_pipeline import TRAINING_BUCKET_NAME
from networksecurity.cloud.s3_syncer import S3Sync
from networksecurity.constant.training_pipeline import SAVED_MODEL_DIR

class TrainingPipeline:
    def __init__(self):
        self.training_pipeline_config=TrainingPipelineConfig()
        self.s3_sync=S3Sync()
       
    def start_data_ingestion(self):
        try:
            self.data_ingestion_config=DataIngestionConfig(training_pipeline_config=self.training_pipeline_config)
            logging.info("Start data Ingestion")
            data_ingestion=DataIngestion(data_ingestion_config=self.data_ingestion_config)
            data_ingestion_artifact=data_ingestion.initiate_data_ingestion()
            logging.info(f"Data Ingestion completed and artifact: {data_ingestion_artifact}")
            return data_ingestion_artifact
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        
        
    def start_data_validation(self,data_ingestion_artifact:DataIngestionArtifact):
        try:
            data_validation_config=DataValidationConfig(training_pipeline_config=self.training_pipeline_config)
            data_validation=DataValidation(data_ingestion_artifact=data_ingestion_artifact,data_validation_config=data_validation_config)
            logging.info("Initiate the data Validation")
            data_validation_artifact=data_validation.initiate_data_validation()
            return data_validation_artifact
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        
    def start_data_transformation(self,data_validation_artifact:DataValidationArtifact):
        try:
            data_transformation_config = DataTransformationConfig(training_pipeline_config=self.training_pipeline_config)
            data_transformation = DataTransformation(data_validation_artifact=data_validation_artifact,
            data_transformation_config=data_transformation_config)
            
            data_transformation_artifact = data_transformation.initiate_data_transformation()
            return data_transformation_artifact
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        
    def start_model_trainer(self,data_transformation_artifact:DataTransformationArtifact)->ModelTrainerArtifact:
        try:
            self.model_trainer_config: ModelTrainerConfig = ModelTrainerConfig(
                training_pipeline_config=self.training_pipeline_config
            )
            model_trainer = ModelTrainer(
                data_transformation_artifact=data_transformation_artifact,
                model_trainer_config=self.model_trainer_config,
            )
            model_trainer_artifact = model_trainer.initiate_model_trainer()
            return model_trainer_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys) 
        
    def sync_artifact_dir_to_s3(self):
        try:
            logging.info("Uploading Artifacts to S3...")

            aws_bucket_url = (
                f"s3://{TRAINING_BUCKET_NAME}/artifact/{self.training_pipeline_config.timestamp}"
            )

            logging.info(f"Bucket URL : {aws_bucket_url}")

            self.s3_sync.sync_folder_to_s3(
            folder=self.training_pipeline_config.artifact_dir,
            aws_bucket_url=aws_bucket_url
            )

            logging.info("Artifact Upload Finished.")

        except Exception as e:
            raise NetworkSecurityException(e, sys)
         
    def sync_saved_model_dir_to_s3(self):
        try:
            logging.info("Uploading Final Models to S3...")

            aws_bucket_url = (
                f"s3://{TRAINING_BUCKET_NAME}/final_models/{self.training_pipeline_config.timestamp}"
            )

            logging.info(f"Bucket URL : {aws_bucket_url}")

            self.s3_sync.sync_folder_to_s3(
                folder=self.training_pipeline_config.model_dir,
                aws_bucket_url=aws_bucket_url
            )

            logging.info("Final Model Upload Finished.")

        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def run_pipeline(self):
        try:
            logging.info("=" * 80)
            logging.info("Training Pipeline Started")
            logging.info("=" * 80)

            logging.info("Starting Data Ingestion...")
            data_ingestion_artifact = self.start_data_ingestion()
            logging.info(f"Data Ingestion Completed\n{data_ingestion_artifact}")

            logging.info("Starting Data Validation...")
            data_validation_artifact = self.start_data_validation(
                data_ingestion_artifact=data_ingestion_artifact
            )
            logging.info(f"Data Validation Completed\n{data_validation_artifact}")

            logging.info("Starting Data Transformation...")
            data_transformation_artifact = self.start_data_transformation(
                data_validation_artifact=data_validation_artifact
            )
            logging.info(f"Data Transformation Completed\n{data_transformation_artifact}")

            logging.info("Starting Model Training...")
            model_trainer_artifact = self.start_model_trainer(
                data_transformation_artifact=data_transformation_artifact
            )
            logging.info(f"Model Training Completed\n{model_trainer_artifact}")

            logging.info("Uploading Artifacts to S3...")
            self.sync_artifact_dir_to_s3()
            logging.info("Artifacts uploaded successfully.")

            logging.info("Uploading Final Models to S3...")
            self.sync_saved_model_dir_to_s3()
            logging.info("Final Models uploaded successfully.")

            logging.info("=" * 80)
            logging.info("Training Pipeline Completed Successfully")
            logging.info("=" * 80)

            return model_trainer_artifact

        except Exception as e:
            logging.exception("Training Pipeline Failed")
            raise NetworkSecurityException(e, sys)          
        