import os
import yaml



class Configuration:
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file {config_file} not found")
        with open(config_file) as f:
            try:
                self.config = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid config file {config_file}")
        self.config_file_path = config_file
        self.default_base_model_path = ''  # 默认基座模型路径
        self.default_embedding_path = ''  # 默认bgem3路径
        self.default_rerank_path = ''  # 默认rerank路径
        self.default_state_path = '' # 默认state文件

        self.validate(self.config)

    def validate(self, settings):
        is_init = settings.get('is_init')
        if not is_init:
            # 如果没有初始化，不做参数校验
            return False
        base_model_file = settings.get("base_model_path") or ''
        if is_init and not base_model_file:
            raise ValueError(f"base_model_path is required")
        if is_init and not os.path.exists(base_model_file):
            raise FileNotFoundError(f"base_model_path {base_model_file} ")

        embedding_path = settings.get("embedding_path") or ''
        if is_init and not embedding_path:
            raise ValueError(f"embedding_path is required")
        if is_init and not os.path.exists(embedding_path):
            raise FileNotFoundError(f"embedding_path {embedding_path} not found")
        rerank_path = settings.get("reranker_path") or ''
        if is_init and not rerank_path:
            raise ValueError(f"reranker_path is required")
        if is_init and not os.path.exists(rerank_path):
            raise FileNotFoundError(f"reranker_path {rerank_path} not found ")

        self.default_base_model_path = base_model_file.strip()
        self.default_embedding_path = embedding_path.strip()
        self.default_rerank_path = rerank_path.strip()

        chroma_path = settings.get("chroma_path") or ''
        if is_init and not chroma_path:
            raise ValueError(f"chroma_path is required ")
        if is_init and not os.path.exists(chroma_path):
            raise NotADirectoryError(f"chroma_path {chroma_path} ")
        chroma_host = settings.get("chroma_host", '0.0.0.0')
        if is_init and not chroma_host:
            raise ValueError(f"chroma_host is required for index service")

        chroma_port = settings.get("chroma_port", '')
        if not (isinstance(chroma_port, int) or (isinstance(chroma_port, str) and chroma_port.isdigit())):
            raise ValueError(f"chroma_port is required for index service")

        sqlite_db_path = settings.get("sqlite_db_path", '')
        if is_init and not sqlite_db_path:
            raise ValueError(f"sqlite_db_path is required for index service")
        sqlite_db_path_dir = os.path.dirname(sqlite_db_path)
        if is_init and not os.path.exists(sqlite_db_path_dir):
            raise NotADirectoryError(f"sqlite_db_path {sqlite_db_path_dir}")
        knowledge_base_path = settings.get("knowledge_base_path", '')
        if knowledge_base_path:
            if is_init and not os.path.exists(knowledge_base_path):
                raise NotADirectoryError(f"knowledge_base_path {knowledge_base_path}")


    def set_config(self, base_model_path=None, embedding_path=None, reranker_path=None,
                   knowledge_base_path=None,sqlite_db_path=None, chroma_path=None, chroma_port=None,strategy=None):
        is_save = False
        if base_model_path and base_model_path != self.default_base_model_path:
            self.default_base_model_path = base_model_path.strip()
            self.config['base_model_path'] = base_model_path
            is_save = True
        if embedding_path and embedding_path != self.default_embedding_path:
            self.default_embedding_path = embedding_path
            self.config['embedding_path'] = embedding_path
            is_save = True
        if reranker_path and reranker_path != self.default_rerank_path:
            self.default_rerank_path = reranker_path
            self.config['reranker_path'] = reranker_path
        if knowledge_base_path and knowledge_base_path != self.config.get("knowledge_base_path"):
            self.config['knowledge_base_path'] = knowledge_base_path
            is_save = True
        if sqlite_db_path and sqlite_db_path != self.config.get("sqlite_db_path"):
            self.config['sqlite_db_path'] = sqlite_db_path
            is_save = True
        if chroma_path and chroma_path != self.config.get("chroma_path"):
            self.config['chroma_path'] = chroma_path
            is_save = True
        if chroma_port and chroma_port != self.config.get("chroma_port"):
            self.config['chroma_port'] = chroma_port
            is_save = True
        if strategy and strategy != self.config.get("strategy"):
            self.config['strategy'] = strategy
            is_save = True
        if is_save:
            self.config['is_init'] = True
            with open(self.config_file_path, "w") as f:
                yaml.dump(self.config, f)


config = Configuration("ragq.yml")



