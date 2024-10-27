from .abc import AbstractServiceWorker
from .files_service import SqliteDB, FileStatusManager
from .index_service import ServiceWorker as IndexServiceWorker
from .llm_service import ServiceWorker as LLMServiceWorker, LLMService
from configuration import config as project_config


sqlite_db = SqliteDB(project_config.config.get('sqlite_db_path'))
files_status_manager = FileStatusManager(project_config.config.get('sqlite_db_path'), project_config.default_base_model_path)
index_service_worker = IndexServiceWorker(project_config.config)
llm_service_worker = LLMServiceWorker(project_config.config)



