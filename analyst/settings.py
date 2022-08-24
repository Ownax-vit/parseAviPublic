import os

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from tzlocal import get_localzone

basedir = os.path.abspath(os.path.dirname(__file__))


class ConfigApp:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-quess'

    POSTGRES_USER = os.environ.get('POSTGRES_USER') or ''
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or ''
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or 'localhost'
    POSTGRES_DATABASE = os.environ.get('POSTGRES_DATABASE') or ''
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT') or '5432'

    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or ''
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = os.environ.get('REDIS_PORT') or ''
    REDIS_DB = os.environ.get('REDIS_DB') or ''


def setupScheduler(user="", password="",
                   host="localhost", db="analystparsedb") -> BackgroundScheduler:
    """ Конфигурирование планировщика задач """
    tz = get_localzone()
    executors = {
        'default': ThreadPoolExecutor(max_workers=1),
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }
    scheduler = BackgroundScheduler({'apscheduler.timezone': tz.zone},
                                    executors=executors,
                                    job_defaults=job_defaults,
                                    )
    scheduler.add_jobstore('sqlalchemy',
                           url=f'postgresql+psycopg2://{user}:{password}@{host}/{db}',
                           alias='sqlalchemy')
    return scheduler


def setupLoggers(nameErrorFile="analystErrors.log", nameDebugFile="analystDebug.log") \
        -> tuple[logging.Logger, logging.Logger]:
    """ Конфигурация логгеров """

    if not os.path.exists("logs"):
        os.mkdir("logs")

    loggerError = logging.getLogger('loggerError')
    loggerError.setLevel(logging.ERROR)
    loggerDebug = logging.getLogger('loggerDebug')
    loggerDebug.setLevel(logging.DEBUG)

    formatLogger = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handlerLoggerError = logging.FileHandler(nameErrorFile)
    handlerLoggerError.setLevel(logging.ERROR)
    handlerLoggerError.setFormatter(formatLogger)
    loggerError.addHandler(handlerLoggerError)

    handlerLoggerDebug = logging.FileHandler(nameDebugFile)
    handlerLoggerDebug.setLevel(logging.DEBUG)
    handlerLoggerDebug.setFormatter(formatLogger)
    loggerDebug.addHandler(handlerLoggerDebug)

    return loggerError, loggerDebug
