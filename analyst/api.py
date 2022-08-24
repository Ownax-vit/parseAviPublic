""" Модуль api для реализации бота на будущее """

from flask_restful import Resource, Api

from analyst import objectResearch, objectStatuses
from analyst import newItemsId
from .utils import getDictItemsForJSON


class Research(Resource):
    """ Инфо об исследовании, все исследования, запуск исследования,
        Возможно создание исследования, редактирование, удаление.
    """
    pass


class NewItems(Resource):
    """ Новые объявления """
    def get(self) -> dict:
        if newItemsId:
            newItems = objectResearch.getAllItemsFromId(newItemsId)
            newItemsId.clear()
            dictNewItems = getDictItemsForJSON(newItems)
            return dictNewItems
        else:
            return {}


class CrawlMonitor(Resource):
    """ Состояние краулера: запущенные исследования, прогресс """
    def get(self) -> dict:
        currentProgressCrawl = objectStatuses.getAllCrawlers()
        if currentProgressCrawl:
            return currentProgressCrawl
        else:
            return {}


class Item(Resource):
    """Информация об объявлении, его статистика, хронологии и т.д."""
    pass


class Scheduler(Resource):
    """ Управление планировщиком: изменение времени запуска,
    добавление, удаление в расписание. В последнюю очередь реализация"""
    pass

api = Api()
# api.add_resource(NewItems, "/api/newItems")
api.add_resource(CrawlMonitor, "/api/statusesCrawler")
