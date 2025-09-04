# file: fine_tune/fine_tune_manager_api.py

import json
import os
import time
import requests
import openai

from config.project_config import ProjectConfig as config
logger = config(logger_name="fine_tune").get_logger()



class FineTuneManagerAPI:
    
    def __init__(self,api_key):
        self.logger =logger
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def upload_training_file(self, training_file_path):
        if not os.path.isfile(training_file_path):
            self.logger.error(f"Training file not found: {training_file_path}")
            raise FileNotFoundError(training_file_path)

        self.logger.info(f"Uploading training file: {training_file_path}")
        with open(training_file_path, "rb") as f:
            response = requests.post(
                "https://api.openai.com/v1/files",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": (training_file_path, f)},
                data={"purpose": "fine-tune"}
            )

        if response.status_code == 200:
            file_id = response.json()["id"]
            self.logger.info(f"Uploaded. File ID: {file_id}")
            return file_id
        else:
            self.logger.error(f"File upload failed: {response.text}")
            raise Exception("File upload failed")

    def start_fine_tune(self, file_id, model="gpt-3.5-turbo-1106"):
        self.logger.info(f"Starting fine-tune with model '{model}' and file ID '{file_id}'")

        response = requests.post(
            "https://api.openai.com/v1/fine_tuning/jobs",
            headers=self.headers,
            json={
                "training_file": file_id,
                "model": model
            }
        )

        if response.status_code == 200:
            job_id = response.json()["id"]
            self.logger.info(f"Fine-tune job started. ID: {job_id}")
            return job_id
        else:
            self.logger.error(f"Fine-tune start failed: {response.text}")
            return None

    def monitor_fine_tune(self, job_id, poll_interval=10):
        self.logger.info(f"Monitoring fine-tune job: {job_id}")
        url = f"https://api.openai.com/v1/fine_tuning/jobs/{job_id}"

        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                self.logger.error(f"Failed to get job status: {response.text}")
                break

            job = response.json()
            status = job.get("status")
            self.logger.info(f"Job status: {status}")

            if status in ["succeeded", "cancelled", "failed"]:
                self.logger.info(f"Final job status: {status}")
                break

            time.sleep(poll_interval)
