from typing import Optional
from datetime import datetime

from .logging import traceExc
from .database import Database, RedisDB


class ObjectResearch:
    """ Класс работы с исследованием """

    def __init__(self, host: str, port: str, password: str, db: str):
        self.redis = RedisDB(host=host, port=port, password=password, db=db)

    def getAllCategories(self) -> Optional[tuple]:
        """ Возвращает существующие типы категорий  """
        try:
            allCategories = self.db.query("SELECT id, name, description FROM objecttyperesearch")
            return allCategories
        except Exception as exc:
            traceExc(exc)

    def getTypesResearch(self) -> Optional[list]:
        typesResearch = self.db.query('SELECT id, name FROM objecttyperesearch')
        if typesResearch is not None:
            typesResearch = [(str(item[0]), item[1]) for item in typesResearch]
        return typesResearch

    def createNewResearch(self, typeResearchId: int, typeServiceId: int, name: str,
                          description: str, url: str) -> Optional[tuple]:
        """ Создает исследование """
        res = self.db.execute(
            'INSERT INTO objectresearch (objecttyperesearch_id, objecttypeservice_id, name, description, url) '
            'VALUES (%s, %s, %s, %s, %s) RETURNING id',
            (int(typeResearchId), int(typeServiceId), name, description, url))
        objectResearch_id = self.db.fetchone()[0]
        self.db.commit()
        return (res, objectResearch_id)

    def createTypeResearch(self, name: str, description: str) -> None:
        """ Создает тип исследования (категорию) """
        result = self.db.execute(
            'INSERT INTO objectTypeResearch (name, description) '
            'VALUES (%s, %s)', (name, description))
        self.db.commit()
        return result

    def getResearchsCategory(self, category_id: int) -> Optional[tuple]:
        """ Получает список исследования по категории"""
        result = self.db.query(f'SELECT id, objecttyperesearch_id, objecttypeservice_id, '
                               f'name, description, url, last_update '
                               f'FROM objectresearch WHERE objecttyperesearch_id=%s ',
                               (category_id, ))
        return result

    def removeResearch(self, objectResearch_id: int) -> bool:
        """ Отправляет запрос на удаление исследования"""
        try:
            self.db.execute("DELETE FROM objectResearch WHERE id=%s", (objectResearch_id,))
            self.db.commit()
            return True
        except Exception as exc:
            traceExc(exc)
            return False

    def getNameUrl(self, objectResearch_id: int) -> Optional[tuple]:
        """Возвращает заголовок и url исследования"""
        queryForNameUrl = self.db.query('Select name, url from objectresearch WHERE id=%s', (objectResearch_id,))
        objectResearchName = queryForNameUrl[0][0]
        urlResearch = queryForNameUrl[0][1]
        return objectResearchName, urlResearch

    def getDataStatistics(self, objectResearch_id: int) -> Optional[tuple]:
        """Возвращает данные статистики для исследования"""
        data_statistics = self.db.query('SELECT * FROM timeline WHERE objectresearch_id=%s', (objectResearch_id,))
        return data_statistics

    def getCountItems(self, objectResearch_id: int) -> int:
        """Возвращает количество объектов в исследовании"""
        count = self.db.query('SELECT count(*) from objectanalyst WHERE objectresearch_id=%s',
                              (objectResearch_id, ))[0][0]
        return count

    def getItemsResearchYoula(self, objectResearch_id: int, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает объекты исследования по ограничению для вывода постранично"""
        items_research = self.db.query('SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, oa.description, '
                                       'oa.location,  ST_AsText(oa.coords), oa.author_rate, '
                                       'oa.date_added, oa.last_update, oa.url_image FROM objectanalyst '
                                       'oa INNER JOIN timelineprice tp ON tp.objectanalyst_id=oa.id '
                                       'AND oa.objectresearch_id=%s '
                                       'ORDER BY oa.date_added DESC LIMIT %s OFFSET %s',
                                       (objectResearch_id, limit, offset))
        return items_research

    def getItemsResearchAvito(self, objectResearch_id, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает объекты исследования по ограничению для вывода постранично"""
        items_research = self.db.query("""
                                SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, oa.description, 
                                oa.location, ST_AsText(oa.coords), oa.author_rate, 
                                oa.date_added, oa.last_update, oa.url_image
                                FROM objectanalyst as oa 
                                INNER JOIN (SELECT tp.objectanalyst_id, tp.id, tp.price, tp.date 
                                FROM timelineprice tp 
                                INNER JOIN (SELECT objectanalyst_id, MAX(date) as maxDate FROM timelineprice 
                                GROUP BY objectanalyst_id) tp1 
                                ON tp.objectanalyst_id=tp1.objectanalyst_id AND tp.date=maxDate) as tp
                                ON tp.objectanalyst_id=oa.id 
                                WHERE oa.objectresearch_id=%s
                                ORDER BY oa.date_added DESC LIMIT %s OFFSET %s
                                """, (objectResearch_id, limit, offset))
        return items_research

    def getDataViews(self, listId: list) -> Optional[tuple]:
        """Возвращает просмотры объектов из переданного списка id"""
        dataViews = self.db.query('SELECT oa.id, tv.date, tv.views from objectanalyst oa INNER JOIN  timelineviews tv '
                                  'ON tv.objectanalyst_id=oa.id WHERE oa.id in %s ORDER BY oa.id, tv.date ASC',
                                  (tuple(listId),))
        return dataViews

    def getDataPrices(self, listId: list) -> Optional[tuple]:
        """Возвращает цены объектов из переданного списка id"""
        dataPrices = self.db.query('SELECT oa.id, tp.date, tp.price from objectanalyst oa INNER JOIN timelineprice tp '
                                   ' ON tp.objectanalyst_id=oa.id WHERE oa.id in %s ORDER BY oa.id, tp.date ASC',
                                   (tuple(listId), ))
        return dataPrices

    def getCountCloseItems(self, objectResearch_id: int) -> int:
        """Возвращает количество закрытых объектов"""
        count = \
            self.db.query('SELECT count(*) from objectanalyst WHERE objectresearch_id=%s AND status_id=4',
                          (objectResearch_id,))[0][0]
        return count

    def getCloseItemsYoula(self, objectResearch_id: int, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает закрытые объекты"""
        items_research = self.db.query('SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, oa.description, '
                                       'oa.location,  ST_AsText(oa.coords), oa.author_rate, '
                                       'oa.date_added, oa.last_update, oa.url_image FROM objectanalyst '
                                       'oa INNER JOIN timelineprice tp ON tp.objectanalyst_id=oa.id '
                                       'AND oa.objectresearch_id=%s '
                                       'AND oa.status_id=4 ORDER BY oa.date_added DESC LIMIT %s OFFSET %s',
                                       (objectResearch_id, limit, offset))
        return items_research

    def getCloseItemsAvito(self, objectResearch_id: int, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает закрытые объекты"""
        items_research = self.db.query("""
                                      SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, oa.description, 
                                      oa.location, ST_AsText(oa.coords), oa.author_rate, 
                                      oa.date_added, oa.last_update, oa.url_image
                                      FROM objectanalyst as oa 
                                      INNER JOIN (SELECT tp.objectanalyst_id, tp.id, tp.price, tp.date 
                                      FROM timelineprice tp 
                                      INNER JOIN (SELECT objectanalyst_id, MAX(date) as maxDate 
                                      FROM timelineprice GROUP BY objectanalyst_id) tp1 
                                      ON tp.objectanalyst_id=tp1.objectanalyst_id AND tp.date=maxDate) as tp
                                      ON tp.objectanalyst_id=oa.id 
                                      WHERE oa.objectresearch_id=%s AND oa.status_id=4
                                      ORDER BY oa.date_added DESC LIMIT %s OFFSET %s
                                      """, (objectResearch_id, limit, offset))
        return items_research

    def getCountItemsForPrices(self, objectResearch_id: int) -> int:
        """Возвращает количество объектов, изменивших цену"""
        count = self.db.query('SELECT count(*) FROM objectanalyst WHERE id in '
                              '(SELECT objectanalyst_id FROM timelineprice GROUP BY (objectanalyst_id) '
                              'HAVING count(*)>1) AND objectResearch_id=%s', (int(objectResearch_id), ))[0][0]

        return count

    def getItemsForPricesYoula(self, objectResearch_id: int, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает объекты, изменивших цену"""
        items_research = self.db.query('SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, oa.description, '
                                       'oa.location,  ST_AsText(oa.coords), oa.author_rate, '
                                       'oa.date_added, oa.last_update, oa.url_image FROM objectanalyst '
                                       'oa INNER JOIN timelineprice tp ON tp.objectanalyst_id=oa.id '
                                       'AND oa.objectresearch_id=%s '
                                       'ORDER BY oa.last_update DESC LIMIT %s OFFSET %s',
                                       (objectResearch_id, limit, offset))
        return items_research

    def getItemsForPricesAvito(self, objectResearch_id: int, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает объекты, изменивших цену"""
        items_research = self.db.query("""
                                             SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, oa.description, 
                                             oa.location, ST_AsText(oa.coords), oa.author_rate, 
                                             oa.date_added, oa.last_update, oa.url_image
                                             FROM objectanalyst as oa 
                                             INNER JOIN (SELECT tp.objectanalyst_id, tp.id, tp.price, tp.date 
                                             FROM timelineprice tp 
                                             INNER JOIN (SELECT objectanalyst_id, MAX(date) as maxDate 
                                             FROM timelineprice GROUP BY objectanalyst_id) tp1 
                                             ON tp.objectanalyst_id=tp1.objectanalyst_id AND tp.date=maxDate) as tp
                                             ON tp.objectanalyst_id=oa.id 
                                             WHERE oa.objectresearch_id=%s AND oa.id in 
                                             (SELECT objectanalyst_id  FROM timelineprice 
                                             GROUP BY (objectanalyst_id) HAVING count(*)>1)
                                             ORDER BY oa.date_added DESC LIMIT %s OFFSET %s
                                             """, (objectResearch_id, limit, offset))
        return items_research

    def getItemsSortDescYoula(self, objectResearch_id: int, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает отсортированные объекты по количеству просмотров"""
        items_research = self.db.query('SELECT DISTINCT oa.id, oa.status_id, oa.name, oa.url, max(tv.views), '
                                       'oa.description, oa.location, ST_AsText(oa.coords), oa.author_rate, '
                                       'oa.date_added, oa.last_update, oa.url_image '
                                       'FROM timelineviews tv INNER JOIN objectanalyst oa '
                                       'ON oa.id=tv.objectanalyst_id  WHERE oa.objectresearch_id=%s GROUP BY (oa.id) '
                                       'ORDER BY max DESC LIMIT %s OFFSET %s',
                                       (objectResearch_id, limit, offset))
        return items_research

    def getItemsSortDescAvito(self, objectResearch_id: int, limit: int, offset: int) -> Optional[tuple]:
        """Возвращает отсортированные объекты по количеству просмотров"""
        items_research = self.db.query('SELECT DISTINCT oa.id, oa.status_id, oa.name, oa.url, max(tv.views), '
                                       'oa.description, oa.location, ST_AsText(oa.coords), oa.author_rate, '
                                       'oa.date_added, oa.last_update, oa.url_image '
                                       'FROM timelineviews tv INNER JOIN objectanalyst oa '
                                       'ON oa.id=tv.objectanalyst_id  WHERE oa.objectresearch_id=%s GROUP BY (oa.id) '
                                       'ORDER BY max DESC LIMIT %s OFFSET %s',
                                       (objectResearch_id, limit, offset))
        return items_research

    def getJsonCoordsItemsNotClose(self, objectResearch_id: int) -> Optional[tuple]:
        """Возвращает открытые объекты для вывода на карте с геоданными в формате geojson"""
        self.db.execute("""
                        SELECT json_build_object('type', 'FeatureCollection', 'features', 
                        json_agg(ST_AsGeoJSON((oa.id, oa.url, oa.url_image, 
                        tp.price, oa.coords, oa.status_id, oa.name))::json)) 
                        FROM objectanalyst oa INNER JOIN (SELECT tp.objectanalyst_id, tp.id, tp.price, tp.date 
                        FROM timelineprice tp INNER JOIN (SELECT objectanalyst_id, MAX(date) as maxDate 
                        FROM timelineprice GROUP BY objectanalyst_id) tp1 
                        ON tp.objectanalyst_id=tp1.objectanalyst_id AND tp.date=maxDate) as tp
                        ON tp.objectanalyst_id=oa.id 
                        WHERE oa.objectresearch_id=%s AND oa.status_id not in (4) AND oa.coords != ''
                        """,                   # запрос на получение данных с
                        (objectResearch_id, ))  # непустыми координатами и преобразования в geojson
        geoJsonDataNotClose = self.db.fetchone()
        return geoJsonDataNotClose

    def getJsonCoordsItemsClose(self, objectResearch_id: int) -> Optional[tuple]:
        """ Возвращает закрытые объекты для вывода на карте с геоданными """
        self.db.execute("""
                                SELECT json_build_object('type', 'FeatureCollection', 
                                'features', json_agg(ST_AsGeoJSON((oa.id, oa.url, oa.url_image, 
                                tp.price, oa.coords, oa.status_id, oa.name))::json)) 
                                FROM objectanalyst oa INNER JOIN (SELECT tp.objectanalyst_id, tp.id, tp.price, tp.date 
                                FROM timelineprice tp INNER JOIN (SELECT objectanalyst_id, MAX(date) as maxDate 
                                FROM timelineprice GROUP BY objectanalyst_id) tp1 
                                ON tp.objectanalyst_id=tp1.objectanalyst_id AND tp.date=maxDate) as tp
                                ON tp.objectanalyst_id=oa.id 
                                WHERE oa.objectresearch_id=%s AND oa.status_id in (4) AND oa.coords != ''
                                """,  # запрос на получение данных с
                        (objectResearch_id, ))  # f1-id, f2-url, f3-price, f4-url_img, f5-status_id.
        geoJsonDataClose = self.db.fetchone()
        return geoJsonDataClose

    def getAllItemsFromId(self, listId: list) -> Optional[list]:
        """Возвращает объекты исходя из спика id"""
        newItems = self.db.query(
            'SELECT oa.id, oa.objectResearch_id, oa.status_id, oa.name, oa.url, tp.price, oa.description, '
            'oa.location, ST_AsText(oa.coords), oa.author_rate, ' 
            'oa.date_added, oa.last_update, oa.url_image FROM objectanalyst ' 
            'oa INNER JOIN timelineprice tp ON tp.objectanalyst_id=oa.id ' 
            'WHERE tp.date = (SELECT MAX(date) FROM timelineprice WHERE objectanalyst_id=tp.objectanalyst_id) ' 
            'AND oa.id in %s ORDER BY oa.date_added', (tuple(listId), ))
        return newItems

    def getIdResearchFromUrl(self, url: str) -> Optional[int]:
        """Возвращает id объекта в зависимости от его url """
        self.db.execute("SELECT id FROM objectResearch WHERE objectResearch.url=%s", (url, ))
        idResearch = self.db.fetchone()
        if idResearch is not None:
            return idResearch[0]
        return None


    def getTitleResearchFromUrl(self, url: str) -> Optional[str]:
        """Возвращает заголовок объекта в зависимости от его url """
        self.db.execute("SELECT name FROM objectResearch WHERE objectResearch.url=%s", (url, ))
        titleResearch = self.db.fetchone()
        if titleResearch is not None:
            return titleResearch[0]
        return None

    def getCountObjectAnalyst(self) -> int:
        """Возвращает количество объектов """
        self.db.execute("SELECT COUNT(*) FROM objectanalyst")
        count = self.db.fetchone()
        if count is None:
            return 0
        return count[0]

    def getCountObjectAnalystCategory(self, category_id: int) -> int:
        """Возвращает количество объектов в категории """
        self.db.execute("SELECT COUNT(*) FROM objectanalyst oa "
                        "INNER JOIN objectresearch objR ON objR.id=oa.objectresearch_id "
                        "WHERE objR.objecttyperesearch_id=%s", (category_id, ))
        count = self.db.fetchone()
        if count is None:
            return 0
        return count[0]

    def getLastItemUpdate(self) -> Optional[tuple]:
        """Возвращает последний обновленный объект """
        item = self.db.query("""
                                        SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, 
                                        oa.date_added, oa.last_update, oa.url_image
                                        FROM objectanalyst as oa 
                                        INNER JOIN (SELECT tp.objectanalyst_id, tp.id, tp.price, tp.date 
                                        FROM timelineprice tp 
                                        INNER JOIN (SELECT objectanalyst_id, MAX(date) as maxDate FROM timelineprice 
                                        GROUP BY objectanalyst_id) tp1 
                                        ON tp.objectanalyst_id=tp1.objectanalyst_id AND tp.date=maxDate) as tp
                                        ON tp.objectanalyst_id=oa.id 
                                        WHERE oa.status_id NOT IN (4)
                                        ORDER BY oa.date_added DESC LIMIT 1 
                                        """)
        if item is None:
            return None
        return item

    def getLastItemUpdateCategory(self, category_id: int) -> Optional[tuple]:
        """Возвращает последний обновленный объект из категории """
        item = self.db.query("""
                                        SELECT oa.id, oa.status_id, oa.name, oa.url, tp.price, 
                                        oa.date_added, oa.last_update, oa.url_image
                                        FROM objectanalyst as oa 
                                        INNER JOIN (SELECT tp.objectanalyst_id, tp.id, tp.price, tp.date 
                                        FROM timelineprice tp 
                                        INNER JOIN (SELECT objectanalyst_id, MAX(date) as maxDate FROM timelineprice 
                                        GROUP BY objectanalyst_id) tp1 
                                        ON tp.objectanalyst_id=tp1.objectanalyst_id AND tp.date=maxDate) as tp
                                        ON tp.objectanalyst_id=oa.id 
										INNER JOIN objectresearch objR ON objR.id=oa.objectresearch_id 
               							WHERE objR.objecttyperesearch_id=%s
                                        AND oa.status_id NOT IN (4)
                                        ORDER BY oa.date_added DESC LIMIT 1 
                                         """, (category_id, ))
        if item is None:
            return None
        return item

    def getMaxPriceItem(self) -> Optional[tuple]:
        """Возвращает объект с максимальной ценой """
        item = self.db.query("""
                                SELECT oa.id, oa.status_id, oa.name, oa.url, 
                                tp.maxPrice, oa.date_added, oa.last_update, oa.url_image
                                FROM objectanalyst as oa  
                                INNER JOIN (SELECT objectanalyst_id, max(price) as maxPrice FROM timelineprice 
                                GROUP BY objectanalyst_id ORDER BY maxPrice) tp
                                ON oa.id=tp.objectanalyst_id 
                                ORDER BY tp.maxPrice DESC LIMIT 1
        """)
        if item is None:
            return None
        return item

    def getMaxPriceItemCategory(self, category_id: int) -> Optional[tuple]:
        """Возвращает объект с максимальной ценой из категории"""
        item = self.db.query("""
                SELECT oa.id, oa.status_id, oa.name, oa.url, tp.maxPrice, oa.date_added, oa.last_update, oa.url_image
                FROM objectanalyst as oa  
                INNER JOIN (SELECT objectanalyst_id, max(price) as maxPrice FROM timelineprice 
                GROUP BY objectanalyst_id) tp
                ON oa.id=tp.objectanalyst_id 
                INNER JOIN objectresearch objR ON objR.id=oa.objectresearch_id 
                WHERE objR.objecttyperesearch_id=%s
                ORDER BY tp.maxPrice DESC LIMIT 1   
        """, (category_id, ))
        if item is None:
            return None
        return item

    def getRandomItem(self) -> Optional[tuple]:
        """Возвращает рандомный итем из БД"""
        item = self.db.query("""
                SELECT oa.id, oa.status_id, oa.name, oa.url, tp.maxPrice, oa.date_added, oa.last_update, oa.url_image
                FROM objectanalyst as oa  
                INNER JOIN (SELECT objectanalyst_id, max(price) as maxPrice FROM timelineprice GROUP BY objectanalyst_id) tp
                ON oa.id=tp.objectanalyst_id 
                ORDER BY RANDOM()
                LIMIT 1
        """)
        if item is None:
            return None
        return item

    def getRandomItemCategory(self, category_id: int) -> Optional[tuple]:
        """Возвращает рандомный итем из БД"""
        item = self.db.query("""
                SELECT oa.id, oa.status_id, oa.name, oa.url, tp.maxPrice, oa.date_added, oa.last_update, oa.url_image
                FROM objectanalyst as oa  
                INNER JOIN (SELECT objectanalyst_id, max(price) as maxPrice FROM timelineprice GROUP BY objectanalyst_id) tp
                ON oa.id=tp.objectanalyst_id 
                INNER JOIN objectresearch objR ON objR.id=oa.objectresearch_id 
                WHERE objR.objecttyperesearch_id=%s
                ORDER BY RANDOM()
                LIMIT 1
        """, (category_id, ))
        if item is None:
            return None
        return item


class ObjectStatuses():

    def __init__(self, host: str, port: str, password: str, db: str):
        self.redis = RedisDB(host=host, port=port, password=password, db=db)

    def initCrawler(self, objectResearch_id: int, title: str) -> Optional[int]:
        """ Инициализация краулера в редис, указания тайтла
            вызывается при создании исследования
        """
        res = self.redis.setHash(f"research:{objectResearch_id}", data={"title": title,
                                                                      "status": "init",
                                                                      "currentPage": 0,
                                                                      "countPages": 0,
                                                                      "currentItem": 0,
                                                                      "date": datetime.now().strftime('%B-%d, %H:%M:%S')
                                                                      })
        if res is not None:
            return res
        traceExc("Error init crawlers to Redis")
        return res

    def setCrawlerStats(self, objectResearch_id: int, status: str,
                   currentPage: int, countPages: int, currentItem: int):
        """ Инициализировать запись краулера """

        res = self.redis.setHash(f"research:{objectResearch_id}", data={"status": status,
                                                                      "currentPage": currentPage,
                                                                      "countPages": countPages,
                                                                      "currentItem": currentItem,
                                                                      "date": datetime.now().strftime('%B-%d, %H:%M:%S')
                                                                      })
        if res is not None:
            return res
        traceExc("Error set Crawler stats to Redis", "Warning")
        return res

    def updatePage(self, objectResearch_id: int, currentPage: int):
        """ Обновить текущую страницу краулера """
        res = self.redis.setHash(f"research:{objectResearch_id}", data={"currentPage": currentPage,
                                                                      "date": datetime.now().strftime('%B-%d, %H:%M:%S')
                                                                      })
        if res is not None:
            return res
        traceExc("Error update current page to Redis", "Warning")
        return res

    def updateCurrentItem(self, objectResearch_id: int, currentItem: int):
        """ Обновить текущее объявление краулера """
        res = self.redis.setHash(f"research:{objectResearch_id}", data={"currentItem": currentItem,
                                                                      "date": datetime.now().strftime('%B-%d, %H:%M:%S')
                                                                      })
        if res is not None:
            return res
        traceExc("Error update current Item to Redis", "Warning")
        return res

    def updateStatus(self, objectResearch_id: int, status):
        """ Обновить статус краулера"""
        res = self.redis.setHash(f"research:{objectResearch_id}", data={"status": status,
                                                                      "date": datetime.now().strftime('%B-%d, %H:%M:%S')
                                                                      })
        if res is not None:
            return res
        traceExc("Error set Crawler stats to Redis", "Warning")
        return res

    def getCrawler(self, objectResearch_id: int) -> Optional[dict]:
        """ Получить конкретную запись краулера"""
        res = self.redis.getHash(f"research:{objectResearch_id}")

        if res is not None:
            crawler = {k.decode("utf-8"): v.decode("utf-8") for k, v in res.items()}
            return crawler
        traceExc("Error get Crawler From Redis", "Warning")
        return res

    def getAllCrawlers(self, name="research:*") -> Optional[dict]:
        """ Получение статусов всех краулеров через обход всех ключей в БД
            Формат результата:
            {"research:1": {""title": title,
                            "status": "init",
                            "currentPage": 0,
                            "countPages": 0,
                            "currentItem": 0,
                            "date": datetime.now().strftime('%B-%d, %H:%M:%S'),
            "research:2": {...}...
            }
        """
        allKeys = self.redis.getKeys(name)
        if allKeys:
            allKeys = [el.decode("utf-8") for el in allKeys]
            crawlers = {}

            for crawler in allKeys:
                statsCrawler = self.redis.getHashAll(crawler)
                statsCrawler = {k.decode("utf-8"): v.decode("utf-8") for k, v in statsCrawler.items()}
                crawlers[crawler] = statsCrawler
            return crawlers

        traceExc(f"Error get keys {name} From Redis", "Warning")
        return

    def delCrawlerStats(self, objectResearch_id: int) -> bool:
        """ Удалить запись статуса краулера"""
        res = self.redis.deleteKey(f"research:{objectResearch_id}")
        return res

