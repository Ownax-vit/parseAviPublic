from typing import Optional
from math import ceil

from .logging import traceExc


def getPageLimitOffset(currentPage: int, count: int) -> tuple[int, int, int]:
    """ Реализация пагинации, вычисляет лимит и количество выводимых записей
        Также возвращает количество страниц
    """
    per_page = 20 # количество итемов на странице
    pages = ceil(count / per_page)
    offset = (currentPage - 1) * per_page
    limit = 20 if currentPage == pages else per_page  # limit for SQL query
    return limit, offset, pages

def getNewViews(dataViews:dict) -> dict:
    """
        Из совокупных данных просмотров извлекает
        разницу между днями как количество новых просмотров
    """
    newViews = {}
    for key, value in dataViews.items():
        if key not in newViews:
            newViews[key] = []
        last = value[0][1]
        for i in value:
            newViews[key].append([i[0], i[1]-last])
            last = i[1]
    return newViews

def getDataTimeScheduler(jobs) -> dict:
    """
    Формируем данные для графика загруженности
    в формате {"0":0, "1":1, ... "24":1} где 0,1...24 - часы
    """

    dataJobTime = {x: 0 for x in range(25)}
    for job in jobs:
        jobTimeHour = job.next_run_time.hour
        if jobTimeHour not in dataJobTime:
            dataJobTime[jobTimeHour] = 1
        else:
            dataJobTime[jobTimeHour] += 1
    return dataJobTime

def getFreeTimeForJob(jobs) -> Optional[int]:
    """
        Возвращает ключ свободного времени от 0 до 24
        Если свободного времени нет, возвращает None

        В один час добавляет не больше 2 задач
    """
    dataJobTime = getDataTimeScheduler(jobs)
    for key, value in dataJobTime.items():
        if value < 2:
            return int(key)
    return None

def getDictItemsForJSON(listItem: list) -> dict:
    """
        Формирование словаря из списка итемов для JSON
    """
    dictItems = {}
    for i in listItem:
        idItem = i[0]
        dictItems[idItem] = {}
        dictItems[idItem]['objectResearch_id'] = i[1]
        dictItems[idItem]['status_id'] = i[2]
        dictItems[idItem]['name'] = i[3]
        dictItems[idItem]['url'] = i[4]
        dictItems[idItem]['price'] = str(i[5])
        dictItems[idItem]['description'] = i[6]
        dictItems[idItem]['location'] = i[7]
        dictItems[idItem]['coords'] = str(i[8])
        dictItems[idItem]['author_rate'] = str(i[9])
        dictItems[idItem]['date_added'] = str(i[10])
        dictItems[idItem]['last_update'] = str(i[11])
        dictItems[idItem]['url_image'] = i[12]
    return dictItems

def calcProgresses(currentProgressCrawl: dict) -> dict:
    """ Вычисляет процент пройденных итемов и добавляет
        соответствующее значение в словарь
        если кроулинг окончен - возвращает 100%
        выдает неточные данные из-за последней страницы
     """
    try:
        if currentProgressCrawl is None:
            return

        for key, value in currentProgressCrawl.items():

            if currentProgressCrawl[key].get("status") is not None and currentProgressCrawl[key]["status"] == "working":
                currentProgressCrawl[key]['progress'] = 100 * ((int(currentProgressCrawl[key]["currentPage"]) - 1) * 50 + \
                                                               int(currentProgressCrawl[key]["currentItem"])) / \
                                                        (int(currentProgressCrawl[key]["countPages"]) * 50)
                currentProgressCrawl[key]['progress'] = int(currentProgressCrawl[key]['progress'])
            else:
                currentProgressCrawl[key]['progress'] = 0
    except KeyError as exc:
        traceExc(exc, "warning")
    return currentProgressCrawl







