import random
import string
from datetime import datetime


def generar_codigo_tutoria() -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TUT-{date_part}-{random_part}"
