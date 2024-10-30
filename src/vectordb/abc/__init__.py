#coding=utf-8
import os
from abc import ABC, abstractmethod



class AbstractVectorDBManager(ABC):

    def __init__(self, db_path: str, db_port: int, db_host: str= '0.0.0.0'):
        self.db_path = db_path
        self.db_port = db_port
        self.db_host = db_host
        self._client = None

    @abstractmethod
    def client(self):
        """
        初始化数据库连接
        :return:
        """
        pass

    @abstractmethod
    def run(self):
        """
        start process
        :return:
        """
        pass

    @abstractmethod
    def show_collections(self, page: int=None, page_size: int=None):
        """
        集合列表
        :param page:
        :param page_size:
        :return:
        """

    @abstractmethod
    def create_collection(self, collection_name: str, metadata: dict=None):
        """
        创建集合
        :param collection_name:
        :param metadata:
        :return:
        """

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """
        删除集合
        :param collection_name:
        :return:
        """

    @abstractmethod
    def add(self, kwargs: dict):
        """
        添加向量
        :param kwargs:keys
        :return:
        """

    @abstractmethod
    def search_nearby(self, cmd: dict):
        """
        搜索向量
        :param cmd:
        :return:
        """