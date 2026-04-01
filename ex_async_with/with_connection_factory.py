from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio


class SessionManager:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def send(self):
        logF.info(f"Отправка данных на -> {self:addr}")
        await asyncio.sleep(1)
        logF.info(f"Данные отправлены на -> {self:addr}")

    async def recv(self):
        logF.info(f"Получение данных с <- {self:addr}")
        await asyncio.sleep(1)
        logF.info(f"Данные получены с <- {self:addr}")

    async def close(self):
        logF.info(f"Завершение соединения {self:addr}")
        await asyncio.sleep(1)
        logF.info(f"Соединение завершено {self:addr}")

    def __format__(self, format_spec):
        if format_spec == "addr":
            return f"{self.host}:{self.port}"
        else:
            return str(self)


class ConnectionHelper:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def _create_session(self, host, port):
        logF.info(f"Устанавливаем соединение {self.port=}")
        await asyncio.sleep(1)
        logF.info(f"Соединение установлено {self.port=}")
        return SessionManager(host, port)

    async def __aenter__(self):
        logF.info(f"Call '__aenter__'")
        self.conn = await self._create_session(self.host, self.port)
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        logF.info(f"Call '__aexit__'")
        await self.conn.close()
