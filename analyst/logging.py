import sys
from datetime import datetime

from termcolor import cprint


try:
    from . import loggerError, loggerDebug
except ImportError as exc:
    from analyst.settings import setupLoggers
    loggerError, loggerDebug = setupLoggers(nameErrorFile="logs/analystErrorsTest.log",
                                            nameDebugFile="logs/analystDebugTest.log")


def traceExc(exc, type_error="Error", url="") -> None:

    """
        Логирование ошибок, запись в файл и в консоль
        logger по умолчанию выводит критические ошибки в файл
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()

    if type_error == "Info":
        cprint(f"{datetime.now()} \t---{url if url else ''} \t-{exc}-{exc_type}---", 'green')
        return
    elif type_error == "Warning":
        cprint(f"{datetime.now()} \t---{url if url else ''} \t---{exc}-----{exc_type}-", 'yellow')
        return
    elif type_error == "Error":
        cprint(f"{datetime.now()} \t---{url if url else ''} \t---  {exc}   ----{exc_type}--", 'red')
        loggerError.error(exc)
        return
    elif type_error == "Debug":
        cprint(f"{datetime.now()} \t---{url if url else ''} \t- {exc} -{exc_type}---", 'magenta')
        loggerDebug.debug(exc)
        return
    else:
        print("Something not wrong, type Error unknown", type_error)
