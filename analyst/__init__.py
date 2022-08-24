from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from .settings import ConfigApp, setupLoggers, setupScheduler
from analyst.database import Database
from analyst.classes import ObjectResearch, ObjectStatuses


app = Flask(__name__)
app.config.from_object(ConfigApp)
csrf = CSRFProtect(app)
scheduler = setupScheduler()
scheduler.start()
loggerError, loggerDebug = setupLoggers()

objectResearch = ObjectResearch(user=app.config["POSTGRES_USER"], password=app.config["POSTGRES_PASSWORD"],
                           database=app.config["POSTGRES_DATABASE"],
                           host=app.config["POSTGRES_HOST"]) # объект работы с данными в Postgres
objectStatuses = ObjectStatuses(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"],
                                password=app.config["REDIS_PASSWORD"], db=app.config["REDIS_DB"],
                                ) # объект работы с данными в Redis (статусы краулеров)

# при инициализации db кроме записей статусов добавлять категории исследований
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://' \
                                        f'{app.config["POSTGRES_USER"]}:{app.config["POSTGRES_PASSWORD"]}' \
                                        f'@{app.config["POSTGRES_HOST"]}/{app.config["POSTGRES_DATABASE"]}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
dbAlchemy = SQLAlchemy(app)
migrate = Migrate(app, dbAlchemy)

newItemsId = []  # глобальный список id новых объявлений
currentProgressCrawl = {}  # глобальный прогресс парсинга

from analyst import routes
from analyst import errors
from .api import api
api.init_app(app)



