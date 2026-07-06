import os
import subprocess
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import NetworkSecurityException
import sys


class S3Sync:

    def sync_folder_to_s3(self, folder: str, aws_bucket_url: str):
        try:
            logging.info("=" * 80)
            logging.info("Starting S3 Upload")
            logging.info(f"Local Folder : {folder}")
            logging.info(f"S3 Bucket URL: {aws_bucket_url}")

            if not os.path.exists(folder):
                raise Exception(f"Folder does not exist: {folder}")

            command = [
                "aws",
                "s3",
                "sync",
                folder,
                aws_bucket_url
            ]

            logging.info(f"Executing Command: {' '.join(command)}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )

            logging.info(f"Return Code : {result.returncode}")
            logging.info(f"STDOUT:\n{result.stdout}")
            logging.info(f"STDERR:\n{result.stderr}")

            result.check_returncode()

            logging.info("Artifacts uploaded successfully to S3.")
            logging.info("=" * 80)

        except Exception as e:
            logging.error(f"S3 Upload Failed: {str(e)}")
            raise NetworkSecurityException(e, sys)

    def sync_folder_from_s3(self, folder: str, aws_bucket_url: str):
        try:
            logging.info("=" * 80)
            logging.info("Downloading Folder From S3")
            logging.info(f"S3 Bucket URL: {aws_bucket_url}")
            logging.info(f"Local Folder : {folder}")

            os.makedirs(folder, exist_ok=True)

            command = [
                "aws",
                "s3",
                "sync",
                aws_bucket_url,
                folder
            ]

            logging.info(f"Executing Command: {' '.join(command)}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )

            logging.info(f"Return Code : {result.returncode}")
            logging.info(f"STDOUT:\n{result.stdout}")
            logging.info(f"STDERR:\n{result.stderr}")

            result.check_returncode()

            logging.info("Download completed successfully.")
            logging.info("=" * 80)

        except Exception as e:
            logging.error(f"S3 Download Failed: {str(e)}")
            raise NetworkSecurityException(e, sys)