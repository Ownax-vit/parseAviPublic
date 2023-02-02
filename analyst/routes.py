
from apscheduler.jobstores.base import ConflictingIdError
from flask import render_template, flash, redirect, \
    url_for, request, session
from termcolor import cprint
from redis.exceptions import ConnectionError

from analyst import app
from analyst.crawlers import startCrawlingResearch
from . import scheduler
from . import objectResearch, objectStatuses
from .utils import getNewViews, getDataTimeScheduler, \
    getFreeTimeForJob, calcProgresses, getPageLimitOffset
from .forms import DateTimeForm, ResearchForm, DeleteResearch, \
    ResearchTypeForm
from .logging import traceExc


@app.route('/')
@app.route('/index')
def index():
    """ Получить типы исследований и вывести на главной странице """

    title = "Главная"
    allCategories = objectResearch.getAllCategories()


    return render_template('index.html',  all_category=allCategories,
                           title=title,)


@app.route('/createResearch', methods=['GET', 'POST'])
def createResearch():
    """
        Создание исследования, автоматически создается работа
        в планировщике при наличии свободного времени
    """
    title = "Создание исследования"


    form = ResearchForm()
    typesResearch = objectResearch.getTypesResearch()
    typesResearch = [(str(item[0]), item[1]) for item in typesResearch]
    form.typeResearch.choices = typesResearch

    if form.validate_on_submit():
        # добавить проверку валидности ссылки
        name = form.name.data
        description = form.description.data
        url = form.url.data
        typeResearchId = form.typeResearch.data[0]

        if url.startswith('https://www.youla.ru'):
            typeServiceId = 2
        elif url.startswith('https://www.avito.ru'):
            typeServiceId = 1
        else:
            flash("Выбранный тип сервиса не поддерживается!")
            return render_template('createResearch.html',
                                   form=form)
        try:
            res, objectResearch_id = objectResearch.createNewResearch(typeResearchId,
                                                                      typeServiceId, name, description, url)
            objectStatuses.initCrawler(objectResearch_id, name)
            if res is None:
                flash('Исследование создано')
                return redirect(url_for('addJob', objectResearch_id=objectResearch_id))
            else:
                flash("Не удается создать исследование!")
        except Exception as exc:
            traceExc(exc)
            flash('Не удается создать исследование! Проверьте правильность введенных данных')
    return render_template('createResearch.html',
                           form=form,
                           title=title,
                           )


@app.route('/createTypeResearch', methods=['GET', 'POST'])
def createTypeResearch():
    """ Создание типа исследования """
    title = "Создание категории исследования"


    form = ResearchTypeForm()

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        try:
            res = objectResearch.createTypeResearch(name, description)
            if res is None:
                flash("Категория добавлена!")
                return redirect(url_for('index'))
            else:
                flash("Не удается создать категорию!")
        except Exception as exc:
            traceExc(exc)
            flash('Не удается создать категорию! '
                  'Проверьте правильность введенных данных, либо наличие соединения с БД')
    return render_template('createTypeResearch.html',
                           form=form,
                           title=title,
                           )


@app.route('/researchs/<int:category_id>')
def getResearchs_category(category_id):
    """Список исследований для категории"""
    title = "Список исследований"
    form = DeleteResearch()  # форма для удаления исследований

    all_researchs_category = objectResearch.getResearchsCategory(category_id)
    return render_template('all_researchs_category.html',
                           all_researchs_category=all_researchs_category,
                           category_id=category_id,
                           form=form,
                           title=title,
                           )


@app.route('/removeResearch/<int:objectResearch_id>', methods=['GET', 'POST'])
def removeResearch(objectResearch_id):
    """ Удаление исследования и ее работы в планировщике и записи в редисе, если есть"""
    if objectResearch.removeResearch(objectResearch_id) and objectStatuses.delCrawlerStats(objectResearch_id):
        flash(f'Исследование {objectResearch_id} удалено!')
        return redirect(url_for('removeJob', objectResearch_id=objectResearch_id))
    else:
        flash(f"Что-то пошло не так при удалении исследования {objectResearch_id}")
        return redirect(url_for('index'))


@app.route('/getStatusesCrawlers')
def getStatusesCrawlers():
    """ Страница статусов кроулеров """
    title = f"Статусы кроулеров"


    try:
        currentProgressCrawl = objectStatuses.getAllCrawlers()
    except ConnectionError as exc:
        traceExc(exc)
        flash("Redis not connection!")
        return redirect(url_for('index'))

    currentProgressCrawl = calcProgresses(currentProgressCrawl)  # добавление процента прогресса

    return render_template('statusesCrawlers.html',
                           title=title,
                           currentProgressCrawl=currentProgressCrawl,
                           )


@app.route('/getStatistics_Research/<int:objectResearch_id>')
def getStatistics_Research(objectResearch_id):
    """ Страница статистики исследования"""
    title = f"Статистика исследования {objectResearch_id}"
    objectResearchName, urlResearch = objectResearch.getNameUrl(objectResearch_id)
    data_statistics = objectResearch.getDataStatistics(objectResearch_id)
    return render_template('currentResearch/statistics_research.html',
                           objectResearch_id=objectResearch_id,
                           urlResearch=urlResearch,
                           objectResearchName=objectResearchName,
                           data_statistics=data_statistics,
                           title=title)


@app.route('/getListItems/<int:objectResearch_id>')
def getListItems(objectResearch_id):
    """ Страница списка всех итемов исследования """
    title = f"Список итемов {objectResearch_id}"
    objectResearchName, urlResearch = objectResearch.getNameUrl(objectResearch_id)
    isYoula = True if urlResearch.startswith("https://youla.ru") else False

    print(session.get("stateItems"))
    # реализация пагинации
    page = request.args.get('page', 1, type=int)
    count = objectResearch.getCountItems(objectResearch_id)  # количество объектов в исследовании
    limit, offset, pages = getPageLimitOffset(page, count)

    if isYoula:
        items_research = objectResearch.getItemsResearchYoula(objectResearch_id, limit, offset)
    else:
        items_research = objectResearch.getItemsResearchAvito(objectResearch_id, limit, offset)
    isData = True
    if not items_research:
        return render_template('currentResearch/all_items_research.html',
                               items_research=items_research,
                               objectResearch_id=objectResearch_id,
                               objectResearchName=objectResearchName,
                               page=page,
                               pages=pages,
                               isYoula=isYoula,
                               title=title,
                               )

    listId = [item[0] for item in items_research]
    dictPrices = {}   # Example: {23: [[datetime.datetime(2021, 7, 26, 10, 27, 53, 27912), 296],
                      # [datetime.datetime(2021, 7, 25, 11, 7, 2, 164023), 294]], ...}
    dictViews = {}

    dataViews = objectResearch.getDataViews(listId)  # данные для спарклайна просмотров и цен
    dataPrices = objectResearch.getDataPrices(listId)

    for i in dataViews:
        if i[0] not in dictViews:
            dictViews[i[0]] = []
        dictViews[i[0]].append([i[1], i[2]])

    for i in dataPrices:
        if i[0] not in dictPrices:
            dictPrices[i[0]] = []
        dictPrices[i[0]].append([i[1], i[2]])

    if isYoula:
        dictNewViews = None
    else:
        dictNewViews = getNewViews(dictViews)  # ошибка, изучить
    # необходимо от None избавиться, из-за пустых значений ошибки

    # вычисление страниц для перехода
    start_url = url_for('getListItems', objectResearch_id=objectResearch_id, page=1) \
        if pages > 3 and page not in (1, 2) else None
    end_url = url_for('getListItems', objectResearch_id=objectResearch_id, page=pages) \
        if pages > 1 and pages != page else None
    prev_url = url_for('getListItems', objectResearch_id=objectResearch_id, page=page - 1)\
        if page > 1 else None
    next_url = url_for('getListItems', objectResearch_id=objectResearch_id, page=page + 1) \
        if page < pages-1 else None

    return render_template('currentResearch/all_items_research.html',  items_research=items_research,
                           objectResearch_id=objectResearch_id,
                           objectResearchName=objectResearchName,
                           page=page,
                           pages=pages,
                           isYoula=isYoula,
                           start_url=start_url,
                           isData=isData,
                           end_url=end_url,
                           prev_url=prev_url,
                           next_url=next_url,
                           dictnewViews=dictNewViews,
                           dictPrices=dictPrices,
                           title=title,
                           )


@app.route('/getListItemsClose/<int:objectResearch_id>')
def getListItemsClose(objectResearch_id):
    title = f"Список закрытых итемов {objectResearch_id}"

    objectResearchName, urlResearch = objectResearch.getNameUrl(objectResearch_id)
    isYoula = True if urlResearch.startswith("https://youla.ru") else False

    page = request.args.get('page', 1, type=int)
    count = objectResearch.getCountItems(objectResearch_id)  # количество объектов в исследовании
    limit, offset, pages = getPageLimitOffset(page, count)

    if isYoula:
        items_research = objectResearch.getCloseItemsYoula(objectResearch_id, limit, offset)
    else:
        items_research = objectResearch.getCloseItemsAvito(objectResearch_id, limit, offset)

    isData = True
    if not items_research:
        return render_template('currentResearch/all_itemsClose_research.html', items_research=items_research,
                               objectResearch_id=objectResearch_id,
                               objectResearchName=objectResearchName,
                               page=page,
                               pages=pages,
                               isYoula=isYoula,
                               title=title
                               )

    listId = [item[0] for item in items_research]
    dictPrices = {}  # Example: {23: [[datetime.datetime(2021, 7, 26, 10, 27, 53, 27912), 296],
                     # [datetime.datetime(2021, 7, 25, 11, 7, 2, 164023), 294]], ...}
    dictViews = {}
    dataViews = objectResearch.getDataViews(listId)
    dataPrices = objectResearch.getDataPrices(listId)

    for i in dataViews:
        if i[0] not in dictViews:
            dictViews[i[0]] = []
        dictViews[i[0]].append([i[1], i[2]])

    for i in dataPrices:
        if i[0] not in dictPrices:
            dictPrices[i[0]] = []
        dictPrices[i[0]].append([i[1], i[2]])

    if isYoula:
        dictNewViews = None
    else:
        dictNewViews = getNewViews(dictViews)  # ошибка, изучить
    # необходимо от None избавиться, из-за пустых значений ошибки

    # вычисление страниц для перехода
    start_url = url_for('getListItemsClose', objectResearch_id=objectResearch_id, page=1) \
        if pages > 3 and page not in (1, 2) else None
    end_url = url_for('getListItemsClose', objectResearch_id=objectResearch_id, page=pages) \
        if pages > 1 and pages != page else None
    prev_url = url_for('getListItemsClose', objectResearch_id=objectResearch_id, page=page - 1) \
        if page > 1 else None
    next_url = url_for('getListItemsClose', objectResearch_id=objectResearch_id, page=page + 1) \
        if page < pages-1 else None

    return render_template('currentResearch/all_itemsClose_research.html',  items_research=items_research,
                           objectResearch_id=objectResearch_id,
                           objectResearchName=objectResearchName,
                           page=page,
                           pages=pages,
                           isYoula=isYoula,
                           isData=isData,
                           start_url=start_url,
                           end_url=end_url,
                           prev_url=prev_url,
                           next_url=next_url,
                           dictnewViews=dictNewViews,
                           dictPrices=dictPrices,
                           title=title
                           )


@app.route('/getListItemsDPrice/<int:objectResearch_id>')
def getListItemsDPrice(objectResearch_id):
    """Список объектов, имеющих более одной записи изменения цены"""
    title = f"Динамика цен итемов {objectResearch_id}"

    objectResearchName, urlResearch = objectResearch.getNameUrl(objectResearch_id)
    isYoula = True if urlResearch.startswith("https://youla.ru") else False

    page = request.args.get('page', 1, type=int)
    count = objectResearch.getCountItems(objectResearch_id)  # количество объектов в исследовании
    limit, offset, pages = getPageLimitOffset(page, count)

    if isYoula:
        items_research = objectResearch.getItemsForPricesYoula(objectResearch_id, limit, offset)
    else:
        items_research = objectResearch.getItemsForPricesAvito(objectResearch_id, limit, offset)


    isData = True
    if not items_research:
        return render_template('currentResearch/all_itemsDPrice_research.html',
                               items_research=items_research,
                               objectResearch_id=objectResearch_id,
                               objectResearchName=objectResearchName,
                               page=page,
                               pages=pages,
                               title=title,
                               )


    listId = [item[0] for item in items_research]
    dictPrices = {}
    dictViews = {}
    dataViews = objectResearch.getDataViews(listId)
    dataPrices = objectResearch.getDataPrices(listId)

    for i in dataViews:
        if i[0] not in dictViews:
            dictViews[i[0]] = []
        if i[2] is None:
            continue  # попадаются битые данные, реализовать их очистку
        dictViews[i[0]].append([i[1], i[2]])

    for i in dataPrices:
        if i[0] not in dictPrices:
            dictPrices[i[0]] = []
        dictPrices[i[0]].append([i[1], i[2]])

    if isYoula:
        dictNewViews = None
    else:
        # dictNewViews = getNewViews(dictViews) # ошибка, изучить
        dictNewViews = dictViews
    # необходимо от None избавиться, из-за пустых значений ошибки

    # вычисление страниц для перехода
    start_url = url_for('getListItemsDPrice', objectResearch_id=objectResearch_id, page=1) \
        if pages > 3 and page not in(1, 2) else None
    end_url = url_for('getListItemsDPrice', objectResearch_id=objectResearch_id, page=pages) \
        if pages > 1 and pages != page else None
    prev_url = url_for('getListItemsDPrice', objectResearch_id=objectResearch_id, page=page - 1) \
        if page > 1 else None
    next_url = url_for('getListItemsDPrice', objectResearch_id=objectResearch_id, page=page + 1) \
        if page < pages-1 else None

    return render_template('currentResearch/all_itemsDPrice_research.html',
                           items_research=items_research,
                           objectResearch_id=objectResearch_id,
                           objectResearchName=objectResearchName,
                           page=page,
                           pages=pages,
                           isYoula=isYoula,
                           isData=isData,
                           start_url=start_url,
                           end_url=end_url,
                           prev_url=prev_url,
                           next_url=next_url,
                           dictnewViews=dictNewViews,
                           dictPrices=dictPrices,
                           title=title,
                           )


@app.route('/getListItemsSortViews/<int:objectResearch_id>')
def getListItemsSortViews(objectResearch_id):
    title = f"Сортировка итемов по просмотров {objectResearch_id}"
    objectResearchName, urlResearch = objectResearch.getNameUrl(objectResearch_id)
    isYoula = True if urlResearch.startswith("https://youla.ru") else False

    page = request.args.get('page', 1, type=int)
    count = objectResearch.getCountItems(objectResearch_id)  # количество объектов в исследовании
    limit, offset, pages = getPageLimitOffset(page, count)

    if isYoula:
        items_research = objectResearch.getItemsSortDescYoula(objectResearch_id, limit, offset)
    else:
        items_research = objectResearch.getItemsSortDescAvito(objectResearch_id, limit, offset)

    # берет не актуальную последнюю цену - исправить
    isData = True
    # берет не актуальную последнюю цену - исправить
    if not items_research:
        isData = False
        return render_template('currentResearch/all_itemsViews_research.html', items_research=items_research,
                               objectResearch_id=objectResearch_id,
                               objectResearchName=objectResearchName,
                               page=page,
                               pages=pages,
                               isYoula=isYoula,
                               title=title,
                               )

    listId = [item[0] for item in items_research]
    dictPrices = {}
    dictViews = {}
    dataViews = objectResearch.getDataViews(listId)
    dataPrices = objectResearch.getDataPrices(listId)

    for i in dataViews:
        if i[0] not in dictViews:
            dictViews[i[0]] = []
        dictViews[i[0]].append([i[1], i[2]])

    for i in dataPrices:
        if i[0] not in dictPrices:
            dictPrices[i[0]] = []
        dictPrices[i[0]].append([i[1], i[2]])

    if isYoula:
        dictNewViews = None
    else:
        dictNewViews = getNewViews(dictViews) # ошибка, изучить
    # необходимо от None избавиться, из-за пустых значений ошибки

    # вычисление страниц для перехода
    start_url = url_for('getListItemsSortViews', objectResearch_id=objectResearch_id, page=1) \
        if pages > 3 and page not in (1, 2) else None
    end_url = url_for('getListItemsSortViews', objectResearch_id=objectResearch_id, page=pages) \
        if pages > 1 and pages !=page else None
    prev_url = url_for('getListItemsSortViews', objectResearch_id=objectResearch_id, page=page - 1) \
        if page > 1 else None
    next_url = url_for('getListItemsSortViews', objectResearch_id=objectResearch_id, page=page + 1) \
        if page < pages-1 else None

    return render_template('currentResearch/all_itemsViews_research.html',  items_research=items_research,
                           objectResearch_id=objectResearch_id,
                           objectResearchName=objectResearchName,
                           page=page,
                           pages=pages,
                           isYoula=isYoula,
                           isData=isData,
                           start_url=start_url,
                           end_url=end_url,
                           prev_url=prev_url,
                           next_url=next_url,
                           dictnewViews=dictNewViews,
                           dictPrices=dictPrices,
                           title=title,
                           )

@app.route('/getMap_items/<int:objectResearch_id>')
def getMap_items(objectResearch_id):
    """Страница карты итемов, вытягивает из бд данные координат и атрибутов, формирует их в GeoJson"""
    title = f"Карта итемов {objectResearch_id}"
    objectResearchName, urlResearch = objectResearch.getNameUrl(objectResearch_id)

    isYoula = True if urlResearch.startswith("https://youla.ru") else False
    geoJsonDataNotClose = objectResearch.getJsonCoordsItemsNotClose(objectResearch_id)
    geoJsonDataClose = objectResearch.getJsonCoordsItemsClose(objectResearch_id)

    return render_template('currentResearch/map.html',
                           objectResearch_id=objectResearch_id,
                           objectResearchName=objectResearchName,
                           geoJsonDataClose=geoJsonDataClose,
                           geoJsonDataNotClose=geoJsonDataNotClose,
                           isYoula=isYoula,
                           title=title,
                           )


@app.route('/view_item/<int:item_id>')
def view_item(item_id):
    return item_id


@app.route('/menu_scheduler',  methods=['GET', 'POST'])
def menu_scheduler():
    """Страница управления планировщиком, изменение, добавление и удаление задач"""
    title = "Планировщик"
    countItems = objectResearch.getCountObjectAnalyst()
    lastItemUpdate = objectResearch.getLastItemUpdate()
    maxPriceItem = objectResearch.getMaxPriceItem()
    randomItem = objectResearch.getRandomItem()



    jobs = scheduler.get_jobs('sqlalchemy')
    form = None
    dataJobTime = None
    if jobs is not None:
        form = DateTimeForm()
        dataJobTime = getDataTimeScheduler(jobs)

        # cprint(form.startdate.data.isoformat(), 'green')
        if form.validate_on_submit():
            cprint(form.dateCrawl.data, 'red')
            return redirect(url_for('index'))

    return render_template('menu_scheduler.html',
                           jobs=jobs,
                           form=form,
                           dataJobTime=dataJobTime,
                           title=title,
                           countItems=countItems,
                           lastItemUpdate=lastItemUpdate,
                           maxPriceItem=maxPriceItem, randomItem=randomItem)


@app.route('/update_date_research/<int:objectResearch_id>',  methods=['GET', 'POST'])
def update_date_research(objectResearch_id):
    """ Изменяет время следующего и последующих запусков краулинга """
    form = DateTimeForm()
    if form.validate_on_submit():
        job = scheduler.get_job(str(objectResearch_id))
        dateFromForm = form.dateCrawl.data
        hour = dateFromForm.hour
        minute = dateFromForm.minute
        job.reschedule(trigger='cron', hour=f'{hour}', minute=f'{minute}')
        job.modify(next_run_time=dateFromForm)  # время следующего запуска
        flash(f'Время в исследовании {objectResearch_id} изменено на {hour}ч. {minute}м.')
        return redirect(url_for('menu_scheduler'))
    flash('Указанные данные неверны!')
    return redirect(url_for('menu_scheduler'))


@app.route('/addJob/<int:objectResearch_id>')
def addJob(objectResearch_id):
    """
        В ДЕБАГ режиме срабатывает дважды и выбрасывает исключение,
        использовать только в отключенном дебаг режиме
        Добавляет задачу в планировщик, свободное время вычисляет сам

    """

    cprint('adding scheduler...', 'green')
    objectResearch_id = str(objectResearch_id)
    jobs = scheduler.get_jobs('sqlalchemy')
    freeHour = getFreeTimeForJob(jobs)

    if freeHour is None:
        flash(f'Свободного времени нет')
        return redirect(url_for('index'))

    try:
        job = scheduler.add_job(startCrawlingResearch,
                                id=objectResearch_id, jobstore='sqlalchemy',
                                args=(objectResearch_id,), trigger='cron',
                                hour=freeHour, misfire_grace_time=None)
    except ConflictingIdError as exc:
        traceExc(exc)
        flash("Задача уже добавлена")
        return redirect(url_for('index'))

    # id.modify(next_run_time=datetime.now())c

    flash(f'Задача {objectResearch_id} было добавлено в планировщик')
    flash(f'Время следующего запуска: {job.next_run_time}')
    return redirect(url_for('index'))


@app.route('/removeJob/<int:objectResearch_id>',  methods=['GET', 'POST'])
def removeJob(objectResearch_id):
    """Удаление задач из планировщика"""
    try:
        job = scheduler.get_job(str(objectResearch_id))
        job.remove()
        flash(f"Работа для исследования {objectResearch_id} удалена!")
    except Exception as exc:
        traceExc(exc)
        flash("Что-то пошло не так при удалении работы! Проверьте, существует ли данная работа! ")
    return redirect(url_for('index'))


@app.route('/get_all_jobs')
def get_all_job():
    """ Получить все запланированные задачи """
    jobs = scheduler.get_jobs('sqlalchemy')
    flash(f'All jobs: {jobs}')
    for job in jobs:
        print(job.next_run_time.hour)
    return redirect(url_for('index'))


@app.route('/runJobNow/<int:objectResearch_id>')
def runJobNow(objectResearch_id):
    """ Запуск задачи в настоящее время """
    # доработать проверку запущенных текущих работ
    try:
        startCrawlingResearch(objectResearch_id)
        flash(f"Работа для исследования {objectResearch_id} запущена!")
    except Exception as exc:
        traceExc(exc)
        flash("Что-то пошло не так!")
    return redirect(url_for('index'))


@app.route('/remove_all_jobs')
def remove_all_jobs():
    """ Удаление всех задач из планировщика """
    try:
        scheduler.remove_all_jobs('sqlalchemy')
        flash('Все работы удалены!')
    except Exception as exc:
        traceExc(exc)
        flash('Произошла ошибка! Удаление работ не выполнено! ')
    return redirect(url_for('index'))


