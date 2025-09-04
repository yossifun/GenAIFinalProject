# file: config/project_config.py

import os
import pathlib
import sys
from dotenv import load_dotenv
from openai import OpenAI
from logger import AppLogger


class ProjectConfig:
    def __init__(
        self,
        dotenv_path=".env",
        api_key_env_var="OPENAI_API_KEY",
        api_key_file_env_var="OPENAI_API_KEY_FILE",
        default_api_key_file="secrets/openai_api_key.txt",
        fine_tune_model_env_var="FINE_TUNE_MODEL",
        fine_tune_model_file_env_var="FINE_TUNE_MODEL_FILE",
        default_fine_tune_model_file="secrets/openai_fine_tune_model.txt",
        model_name_env="OPENAI_MODEL",
        default_model="gpt-4-turbo-preview",        
        required_dirs=None
    ):
        self.logger = AppLogger().get_logger(self.__class__.__name__)

        self.client = None
        self._check_python_version()
        self._check_directory_context()
        self._verify_directories(required_dirs or ["secrets", "fine_tune"])

        self._load_env(dotenv_path)
        self.api_key = self._load_secret_key(api_key_env_var, api_key_file_env_var, default_api_key_file)
        self.fine_tune_model = self._load_secret_key(fine_tune_model_env_var, fine_tune_model_file_env_var, default_fine_tune_model_file)
        self.model = os.getenv(model_name_env, default_model)
        self._verify_models()

        self.logger.info("✅ Project setup completed successfully.")

    def _check_python_version(self):
        if sys.version_info < (3, 11) or sys.version_info >= (3, 12):
            self.logger.error("❌ This project requires Python 3.11.x")
            sys.exit("This project requires Python 3.11.x")

    def _check_directory_context(self):
        project_root = pathlib.Path(__file__).resolve().parent.parent
        cwd = pathlib.Path.cwd().resolve()

        if project_root != cwd:
            self.logger.error("❌ Script must be run from the project root directory.")
            sys.exit("Script must be run from the project root directory.")

    def _verify_directories(self, dirs):
        for d in dirs:
            if not os.path.isdir(d):
                self.logger.error(f"❌ Mandatory directory '{d}' is missing.")
                sys.exit(f"Mandatory directory '{d}' is missing.")

    def _load_env(self, dotenv_path):
        if not os.path.isfile(dotenv_path):
            self.logger.error(f"❌ Missing {dotenv_path} file.")
            sys.exit(f"Missing {dotenv_path} file.")
        load_dotenv(dotenv_path)

    def _load_secret_key(self, env_key_name, env_file_name, default_file):
        secret_key_file = os.getenv(env_file_name, default_file)
        if not os.path.isfile(secret_key_file):
            self.logger.error(f"❌ Secret key file '{secret_key_file}' not found.")
            sys.exit(f"Secret key file '{secret_key_file}' not found.")

        with open(secret_key_file, "r") as f:
            secret_key = f.read().strip()

        if not secret_key:
            self.logger.error(f"❌ Secret key is empty in file '{secret_key_file}'.")
            sys.exit("Secret key not found.")

        os.environ[env_key_name] = secret_key
        return secret_key

    def _verify_models(self):
        if not self.client:
            self.client = self.get_client()
        try:
            self.client.models.retrieve(self.model)
            self.logger.info(f"✅ Model {self.model} is available.")
            
            self.client.models.retrieve(self.fine_tune_model)
            self.logger.info(f"✅ Fine Tune Model {self.fine_tune_model} is available.")

        except Exception as e:
            self.logger.error(f"❌ Error verifying model availability: {e}")
            sys.exit(f"Error verifying model availability: {e}")

    def get_api_key(self):
        return self.api_key
    
    def get_client(self):
        if not self.client:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.openai.com/v1"
            )
        return self.client
    
    def get_model(self):
        return self.model

    def get_fine_tune_model(self):
        return self.fine_tune_model

    def get_logger(self, logger_name=None):
        if logger_name:
            return AppLogger().get_logger(logger_name)
        return AppLogger().get_logger(self.__class__.__name__)


# === Base class for all your project classes ===
class BaseConfigurable:
    """
    Any class inheriting from this gets:
    - self.config (global ProjectConfig)
    - self.logger (logger named after class)
    """
    def __init__(self):
        from config.project_config import CONFIG  # safe import
        self.config = CONFIG
        self.logger = CONFIG.get_logger(self.__class__.__name__)


# Global singleton config
CONFIG = ProjectConfig()
