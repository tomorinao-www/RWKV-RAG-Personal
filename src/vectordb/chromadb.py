# coding=utf-8
import uuid
import subprocess
from abc import ABC
from datetime import datetime

import psutil
import chromadb

from src.vectordb import AbstractVectorDBManager


class ChromaDBManager(AbstractVectorDBManager, ABC):

    def client(self):
        if self._client is None:
            self._client = chromadb.HttpClient(host=self.db_host,
                                            port=self.db_port)
            self._client.heartbeat()
            return self._client
        return self._client
    def run(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chroma' == proc.info['name'].lower() or 'chroma.exe' == proc.info['name'].lower():
                return True

        print(f"Start chroma db")
        # spawn a process "chroma run --path chroma_path --port chroma_port --host chroma_host"
        command = f"chroma run --path {self.db_path} --port {self.db_port} --host {self.db_host}"
        process = subprocess.Popen(command, shell=True)
        print(f"Started indexing service with command {command}, pid is {process.pid}")

    def show_collections(self, page: int=None, page_size: int=None):
        """
        集合列表
        :param page:
        :param page_size:
        :return:
        """
        chroma_client = self.client()
        offset = (page - 1) * page_size if page is not None and page_size is not None else None
        collections = chroma_client.list_collections(page_size, offset)

        return [(i.name, i.metadata) for i in collections]

    def create_collection(self, collection_name: str, metadata: dict = None):
        """
        创建集合
        :param collection_name:
        :param metadata:
        :return:
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client = self.client()
        client.create_collection(collection_name,
                                        metadata={"hnsw:space": "cosine",
                                                  "create_time": now})
        return True

    def delete_collection(self, collection_name: str):
        """
        删除集合
        :param collection_name:
        :return:
        """
        client = self.client()
        client.delete_collection(collection_name)
        return True

    def add(self,kwargs:dict):
        """
        添加向量
        :param kwargs:
        :return:
        """
        keys = kwargs.get("keys")
        values = kwargs["texts"]
        collection_name = kwargs['collection_name']
        embeddings = kwargs['embeddings']
        if keys is None or isinstance(keys, list) is False or len(keys) != len(values):
            keys = [str(uuid.uuid4()) for i in range(len(values))]

        collection = self.client().get_collection(collection_name)

        collection.add(
            ids=keys,
            embeddings=embeddings,
            documents=values
        )
        # index the value
        return True

    def search_nearby(self, cmd: dict):
        """
        搜索向量
        :param cmd:
        :return:
        """
