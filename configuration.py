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
        self.default_bgem3_path = ''  # 默认bgem3路径
        self.default_rerank_path = ''  # 默认rerank路径
        self.default_state_path = '' # 默认state文件

        self.validate(self.config)

    def validate(self, settings):
        base_model_file = settings.get("base_model_path", '')
        if not base_model_file:
            raise ValueError(f"base_model_path is required")
        if not os.path.exists(base_model_file):
            raise FileNotFoundError(f"base_model_path {base_model_file} ")

        bgem3_path = settings.get("embedding_path", '')
        if not bgem3_path:
            raise ValueError(f"embedding_path is required")
        if not os.path.exists(bgem3_path):
            raise FileNotFoundError(f"embedding_path {bgem3_path} not found")
        rerank_path = settings.get("reranker_path", '')
        if not rerank_path:
            raise ValueError(f"reranker_path is required")
        if not os.path.exists(rerank_path):
            raise FileNotFoundError(f"reranker_path {rerank_path} not found ")
        state_path = settings.get("state_path", '') or ''
        if state_path:
            if not os.path.exists(state_path):
                raise FileNotFoundError(f"state_path {state_path} ")
        self.default_base_model_path = base_model_file.strip()
        self.default_bgem3_path = bgem3_path
        self.default_rerank_path = rerank_path
        self.default_state_path = state_path

        chroma_path = settings.get("chroma_path", '')
        if not chroma_path:
            raise ValueError(f"chroma_path is required ")
        if not os.path.exists(chroma_path):
            raise NotADirectoryError(f"chroma_path {chroma_path} ")
        chroma_host = settings.get("chroma_host", '0.0.0.0')
        if not chroma_host:
            raise ValueError(f"chroma_host is required for index service")

        chroma_port = settings.get("chroma_port", '')
        if not (isinstance(chroma_port, int) or (isinstance(chroma_port, str) and chroma_port.isdigit())):
            raise ValueError(f"chroma_port is required for index service")

        sqlite_db_path = settings.get("sqlite_db_path", '')
        if not sqlite_db_path:
            raise ValueError(f"sqlite_db_path is required for index service")
        sqlite_db_path_dir = os.path.dirname(sqlite_db_path)
        if not os.path.exists(sqlite_db_path_dir):
            raise NotADirectoryError(f"sqlite_db_path {sqlite_db_path_dir}")
        knowledge_base_path = settings.get("knowledge_base_path", '')
        if knowledge_base_path:
            if not os.path.exists(knowledge_base_path):
                raise NotADirectoryError(f"knowledge_base_path {knowledge_base_path}")


config = Configuration("ragq.yml")



