Проект системы мониторинга объявлений 
=====================

***
Основное назначение проекта - обеспечение более подробной и углубленной информации об объектах продаж и услуг 
на торговых площадках (в основном Авито, но предусмотрена возможность масштабирования для других 
сервисов, в частности, протестирована Юла)

Подразумевается применение программы в различных сферах: в маркетинговых исследованиях 
для сбора данных и статистики, выявления трендов и факторов спроса; для бизнеса в поиске необходимых товаров, 
поставщиков, сотрудников и т.д. в соответствии с различными критериями, которые отсутствуют в основном сервисе; 
для частных лиц - уведомление новых объявлений, соответствующих стоимости и т.п.

Принцип использования системы:
-----------------------------------
***
    Работа с необходимыми данными ведется с помощью конкретных исследований, 
    каждое из которых представляет собой определенный раздел (результат, запрос) поиска в основном сервисе (Авито).
    Для каждого исследования планируется периодическое выполнение краулинга (скрепинга, парсинга) сервиса:
    получение новых и обновление уже имеющихся данных. 

Некоторые особенности программы:
-----------------------------------
:heavy_check_mark: планировщик задач для планирования периодического обновления данных \
:heavy_check_mark: страница прогресса обновления данных \
:heavy_check_mark: наличие различных статистических показателей исследования, хронологии цен и просмотров по объектам \
:heavy_check_mark: возможность географического анализа объектов с помощью цифровой карты \
:heavy_check_mark: возможность привязки бота в телеграм для получения новых объявлений \
:heavy_check_mark: возможность выгрузки данных в различных форматах: html, csv, xlsx \
:heavy_check_mark: возможность исследования закрытых объектов, выявления факторов спроса, в т.ч. географически\

Примеры работы с системой:
-----------------------------------

![Использование карты](readmi-source/using-map.gif)
#### Использование карты

![Изучение хронологий объектов](readmi-source/chronologies.PNG)
#### Изучение хронологии объектов

![Использование планировщика](readmi-source/scheduler.PNG)
#### Использование планировщика

Используемые технологии:
-----------------------------------
<li> Flask - веб-фрейвормк </li>
<li> Flask-RESTful - расширение flask для создания REST API, 
используется для взаимодействия с ботом 
</li>
<li> APScheduler - планировщик задач для запусков парсера </li>
<li> Selenium (Selenium-wire), Requests -  для получения данных страниц </li>
<li> Beautiful soup - для обработки html страниц и извлечения структурированных данных </li> 
<li> threading - для работы с потоками задач </li>
<li> logging - для ведения логов работы системы </li>
<li> Postgres (postgis) - в качестве основной СУБД для хранения данных</li>
<li> Redis - в качестве хранения статусов задач </li>
<li> JS, Chart.js, ProgressBar.js, Leaflet, Bootstrap в качестве отображения различных компонентов клиентской части </li>
<li> Colorama, Queue, SQLAlchemy и т.п. </li>



-----------------------------------
Большая часть исходного кода и модулей скрыта
-----------------------------------
