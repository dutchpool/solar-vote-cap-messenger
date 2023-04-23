import time
import traceback
from typing import Optional


def handle_error(e: Optional[Exception], message: str, fatal: bool):
    if e is None:
        short_message = "fatal:{0} | {1}".format(str(fatal), message)
        full_message = "\n" + short_message
    else:
        short_message = "fatal:{0} | {1} - {2}".format(str(fatal), message, repr(e))
        full_message = "\n" + short_message + "\n\n" + traceback.format_exc()
    log_message = time.strftime("%Y-%m-%d %H:%M:%S: ") + full_message
    print(log_message)
    file = open("logs/error.log", "a")
    file.write(log_message + "\n")
    file.close()
    if fatal:
        quit(code=1)
