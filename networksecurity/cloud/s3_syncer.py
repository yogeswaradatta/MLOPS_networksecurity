import subprocess
from networksecurity.logging.logger import logging

class S3Sync:

    def sync_folder_to_s3(self, folder, aws_bucket_url):
        command = ["aws", "s3", "sync", folder, aws_bucket_url]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        logging.info(result.stdout)

        if result.returncode != 0:
            logging.error(result.stderr)
            raise Exception(result.stderr)

    def sync_folder_from_s3(self, folder, aws_bucket_url):
        command = ["aws", "s3", "sync", aws_bucket_url, folder]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        logging.info(result.stdout)

        if result.returncode != 0:
            logging.error(result.stderr)
            raise Exception(result.stderr)