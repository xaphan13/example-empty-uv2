from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import json
from zipfile import ZipFile, ZIP_DEFLATED
from .zip_config import DIR_FILES


def write_to_zip_no_temp():
    """
    1. Создает ZIP-архив и добавляет в него файл напрямую из памяти,
       без создания временного файла.
    2. Записывает JSON данные напрямую в архив с помощью writestr.
    """
    # Создаем директорию, куда будут сохраняться файлы, если она не существует
    DIR_FILES.mkdir(parents=True, exist_ok=True)

    # Открываем менеджер контекста для создания ZIP-архива
    zip_path = DIR_FILES / "zip_no_temp.zip"
    with ZipFile(
        zip_path,
        "w",
        compression=ZIP_DEFLATED,
        compresslevel=9,
    ) as open_zip:
        data: dict = {"a": "1", "b": "2", "method": "writestr"}
        # Записываем JSON данные напрямую в архив под именем 'json_no_temp.json'
        # writestr принимает имя файла в архиве и данные (строка или байты)
        open_zip.writestr("json_no_temp1.json", json.dumps(data))
        open_zip.writestr("json_no_temp2.json", json.dumps(data))
