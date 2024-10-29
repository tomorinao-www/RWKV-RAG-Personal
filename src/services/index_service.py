import time
import uuid
import subprocess
from datetime import datetime
from multiprocessing import Lock

import chromadb
import psutil
from src.services import AbstractServiceWorker


CHROMA_DB_COLLECTION_NAME = 'initial'

    
class ServiceWorker(AbstractServiceWorker):

    lock = Lock()

    def init_with_config(self, config):
        # 向量数据库相关配置
        chroma_port = config["chroma_port"]
        chroma_host = config.get("chroma_host", )
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.init_once(config)
        self.init_chroma_db()


    def init_chroma_db(self):
        """
        Init the chromadb
        """
        if self.lock.acquire(False):
            try:
                chroma_client = chromadb.HttpClient(host=self.chroma_host,
                                                port=self.chroma_port)
                if CHROMA_DB_COLLECTION_NAME not in [c.name for c in chroma_client.list_collections()]:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    chroma_client.create_collection(CHROMA_DB_COLLECTION_NAME,
                                                metadata={"hnsw:space": "cosine",
                                                          "create_time": now})
                    print(f"Chroma db collection {CHROMA_DB_COLLECTION_NAME} is created")
                    print(f"Chroma db collection {CHROMA_DB_COLLECTION_NAME} is ready")
                    print(f'Current collections are {chroma_client.list_collections()}')
                del chroma_client
            finally:
                self.lock.release()

    @staticmethod
    def init_once(config):
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chroma' == proc.info['name'].lower() or 'chroma.exe' == proc.info['name'].lower():
                return True


        chroma_path = config.get("chroma_path")
        chroma_port = config.get("chroma_port")
        chroma_host =  '0.0.0.0'
        print(f"Start chroma db")
        # spawn a process "chroma run --path chroma_path --port chroma_port --host chroma_host"
        command = f"chroma run --path {chroma_path} --port {chroma_port} --host {chroma_host}"
        process = subprocess.Popen(command, shell=True)
        print(f"Started indexing service with command {command}, pid is {process.pid}")
        time.sleep(5)

    def index_texts(self, cmd: dict):
        keys = cmd.get("keys")
        values = cmd["texts"]
        collection_name = cmd['collection_name']
        embeddings = cmd['embeddings']
        if keys is None or isinstance(keys, list) is False or len(keys) != len(values):
            keys = [str(uuid.uuid4()) for i in range(len(values))]
        chroma_client = chromadb.HttpClient(host=self.chroma_host,
                                            port=self.chroma_port)

        collection = chroma_client.get_collection(collection_name)

        collection.add(
            ids=keys,
            embeddings=embeddings,
            documents=values
        )
        # index the value
        return True

    def show_collections(self, cmd: dict):
        # TODO 如果集合数太多，要做分页处理
        chroma_client = chromadb.HttpClient(host=self.chroma_host,
                                            port=self.chroma_port)
        collections = chroma_client.list_collections()

        return [(i.name, i.metadata) for i in collections]

    def create_collection(self, cmd: dict):
        collection_name = cmd['collection_name']
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chroma_client = chromadb.HttpClient(host=self.chroma_host,
                                            port=self.chroma_port)
        chroma_client.create_collection(collection_name,
                                        metadata={"hnsw:space": "cosine",
                                                  "create_time": now})
        return True

    def delete_collection(self, cmd: dict):
        collection_name = cmd['collection_name']
        chroma_client = chromadb.HttpClient(host=self.chroma_host,
                                            port=self.chroma_port)
        chroma_client.delete_collection(collection_name)
        return True

    def search_nearby(self, cmd: dict):
        # text = cmd["text"]
        collection_name = cmd.get('collection_name')
        embeddings = cmd.get('embeddings')
        # embeddings = self.llm_client.encode([text])["value"]
        chroma_client = chromadb.HttpClient(host=self.chroma_host,
                                            port=self.chroma_port)
        collection = chroma_client.get_collection(collection_name or CHROMA_DB_COLLECTION_NAME)
        search_result = collection.query(
            query_embeddings=embeddings,
            n_results=3,
            include=['documents', 'distances'])
        return search_result


