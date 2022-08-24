"""----- Модуль работы с базами данных -----"""
from typing import Optional

import redis
import psycopg2
from psycopg2 import Error

from .logging import traceExc


class Database:
    """ Класс БД postgres """
    __instanceDatabase = None

    def __new__(cls, *args, **kwargs):
        """ Синглтон """
        if cls.__instanceDatabase is None:
            cls.__instanceDatabase = super(Database, cls).__new__(cls)
        return cls.__instanceDatabase

    def __init__(self, host='',
                 database='',
                 user='',
                 password='',
                 port=5432):
        try:
            self._conn = psycopg2.connect(database=database,
                                          user=user,
                                          password=password,
                                          host=host,
                                          port=port)
            self._cursor = self._conn.cursor()
        except (Exception, Error) as exc:
            traceExc(exc)

    def reconnect(self):
        traceExc('reconnect')
        self.__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        try:
            self.connection.commit()
        except (Exception, Error) as exc:
            traceExc(exc)
            self.reconnect()

    def close(self, commit=True) -> None:
        try:
            if commit:
                self.commit()
            self.connection.close()
        except (Exception, Error) as exc:
            traceExc(exc)
            self.reconnect()

    def execute(self, sql, params=None) -> None:
        """ Выполнение команды без получения ответа """
        try:
            # reconnect при удалении старых объектов, проверить
            self.cursor.execute(sql, params or ())
        except (Exception, Error) as exc:
            traceExc(exc)
            self.reconnect()

    def fetchall(self) -> Optional[list]:
        try:
            res = self.cursor.fetchall()
        except (Exception, Error) as exc:
            traceExc(exc)
            self.reconnect()
            return
        return res

    def fetchone(self) -> Optional[tuple]:
        try:
            res = self.cursor.fetchone()
        except (Exception, Error) as exc:
            traceExc(exc)
            return
        return res

    def query(self, sql, params=None) -> Optional[tuple]:
        """ Выполнение запроса с получением ответа  """
        try:
            self.execute(sql, params or ())
        except (Exception, Error) as exc:
            traceExc(exc)
            self.reconnect()
            return
        return self.fetchall()


class RedisDB:
    """ Класс обращения к редису """
    __instanceRedis = None

    def __new__(cls, *args, **kwargs):
        """ Синглтон """
        if cls.__instanceRedis is None:
            cls.__instanceRedis = super(RedisDB, cls).__new__(cls)
        return cls.__instanceRedis

    def __init__(self, host="",
                 port=49153, password="", db=1):
        try:
            self.redis = redis.StrictRedis(host=host,
                                           port=port,
                                           password=password,
                                           db=db)
            self.redis.ping()
        except redis.exceptions.ConnectionError as exc:
            traceExc(exc)
            traceExc(f"Redis not connection! "
                     f"Statuses crawlers will not working!")
        except (Exception, Error) as exc:
            traceExc(exc)
            traceExc(f"Redis is not connected! "
                     f"Statuses crawlers will not working!")
        else:
            traceExc("Redis is connected", "Debug")

    def setHash(self, name: str, data: dict) -> Optional[int]:
        """ Добавить хэш """
        try:
            res = self.redis.hset(name, mapping=data)
            return res
        except redis.exceptions.ConnectionError as exc:
            traceExc(exc, "Warning")
        except Exception as exc:
            traceExc(f"Error set hash to redis: {exc}")

    def getHash(self, name: str) -> Optional[dict[bytes, bytes]]:
        """ Получить хэш по имени"""
        try:
            crawler = self.redis.hget(name)
            return crawler
        except redis.exceptions.ConnectionError as exc:
            traceExc(exc, "Warning")
        except Exception as exc:
            traceExc(f"Error get hash from redis: {exc}")

    def getHashAll(self, name: str) -> Optional[dict[bytes, bytes]]:
        """ Получить хэши по имени"""
        try:
            crawler = self.redis.hgetall(name)
            return crawler
        except redis.exceptions.ConnectionError as exc:
            traceExc(exc, "Warning")
        except Exception as exc:
            traceExc(f"Error get hash from redis: {exc}")

    def getKeys(self, name: str) -> Optional[list]:
        """Получить записи по шаблону"""
        try:
            allKeys = self.redis.keys(name)
            return allKeys
        except redis.exceptions.ConnectionError as exc:
            traceExc(exc, "Warning")
        except Exception as exc:
            traceExc(f"Error get All Crawlers from redis: {exc}")

    def deleteKey(self, name: str) -> bool:
        """Удалить запись по ключу"""
        try:
            self.redis.delete(name)
            return True
        except redis.exceptions.ConnectionError as exc:
            traceExc(exc, "Warning")
        except Exception as exc:
            traceExc(f"Error delete key from redis {exc}")
        return False
