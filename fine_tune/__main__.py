import argparse
import os
import shutil

from fine_tune.sample_set_classifier import SampleSetClassifier
from fine_tune.fine_tune_manager_api import FineTuneManagerAPI
from config.project_config import ProjectConfig

self.logger = ProjectConfig(logger_name="fine_tune").get_logger()
api_key = ProjectConfig().get_api_key()
input_file = "data/sms_conversations.json"
training_file = "fine_tune/training_data/classified_samples.jsonl"

def generate_training_set():
    classifier = SampleSetClassifier()
    try:
        classifier.generate_training_set(input_file, training_file)
    except Exception as e:
        self.logger.error(f"Error during classification: {e}")
        raise e
    self.logger.info("Training set generated successfully.")

def train_model():
    fine_tune_manager = FineTuneManagerAPI(api_key)
    file_id = fine_tune_manager.upload_training_file(training_file)
    fine_tune_id = fine_tune_manager.start_fine_tune(file_id)
    fine_tune_manager.monitor_fine_tune(fine_tune_id)


def clean():
    paths_to_delete = [
        "fine_tune/training_data",
        "__pycache__",
        "fine_tune/__pycache__",
        "config/__pycache__",
    ]

    for path in paths_to_delete:
        if os.path.isdir(path):
            shutil.rmtree(path)
            self.logger.info(f"Deleted directory: {path}")
        elif os.path.isfile(path):
            os.remove(path)
            self.logger.info(f"Deleted file: {path}")
        else:
            self.logger.info(f"Nothing to delete at: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fine-tuning pipeline runner for GenAI project.\n\n"
                    "Available commands:\n"
                    "  generate_training_set - Classify raw samples into training format\n"
                    "  train_model           - Upload and fine-tune model\n"
                    "  all                   - Run both classification and fine-tuning\n"
                    "  clean                 - Delete training data and __pycache__ files",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "function",
        choices=["generate_training_set", "train_model", "all", "clean"],
        nargs="?",
        default="all",
        help="Function to run (default: all)"
    )
    args = parser.parse_args()

    if args.function == "generate_training_set":
        generate_training_set()
    elif args.function == "train_model":
        train_model()
    elif args.function == "all":
        generate_training_set()
        train_model()
    elif args.function == "clean":
        clean()
    else: 
        clean()
        generate_training_set()
        train_model()