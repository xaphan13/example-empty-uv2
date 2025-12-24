from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import json
from zipfile import ZipFile, ZIP_DEFLATED
from .zip_config import DIR_FILES


def read_extract_from_zip():
    # Создаем директорию, куда будут сохраняться файлы, если она не существует
    DIR_FILES.mkdir(parents=True, exist_ok=True)

    # Открываем менеджер контекста для создания ZIP-архива
    zip_path = DIR_FILES / "zip_no_temp.zip"
    with ZipFile(
        zip_path,
        "r",
        compression=ZIP_DEFLATED,
        compresslevel=9,
    ) as open_zip:
        # Извлечь все файлы
        open_zip.extractall(DIR_FILES / "extract_zip/")
        # Извлечь один файл
        open_zip.extract("json_no_temp1.json", DIR_FILES / "extract_zip/")

        # Прочитать файл как байты
        read_bytes: bytes = open_zip.read("json_no_temp1.json")
        # Прочитать как текст
        read_text: str = open_zip.read("json_no_temp1.json").decode("utf-8")
        logF.info(f"{read_bytes=} \n{read_text=}")

        with open_zip.open("json_no_temp2.json") as open_json:
            data_json: str = json.load(open_json)
            logF.info(f"{data_json=}")
