from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio
import aiosqlite
from textwrap import dedent

from sqlite3 import Row
from aiosqlite import Cursor
from aiosqlite.context import Result
from typing import Coroutine, Iterable, Any


async def return_gather():
    queries: list[str] = (
        dedent("""
        select 1
        select 2
        select 3
        select 4
    """)
        .strip()
        .splitlines()
    )

    logF.info(f"{queries}")

    # Используем aiosqlite для асинхронной работы с БД
    async with aiosqlite.connect(":memory:") as conn:
        res_cur: Result[Cursor] = conn.execute("select 0")
        cur: Cursor = await res_cur
        iter_row: Iterable[Row] = await cur.fetchall()
        print(f"{res_cur=} {type(res_cur)=} {isinstance(res_cur, Coroutine)=}")
        print(f"{cur=} {type(cur)=} {isinstance(cur, Coroutine)=}")
        print(f"{iter_row=} {type(iter_row)=} {isinstance(iter_row, Coroutine)=}")

        dict_cor: dict[Result[Cursor], Any] = {conn.execute(q): None for q in queries}

        # asyncio.gather запускает все запросы параллельно
        fut_gathers: asyncio.Future[list[Iterable[Row]]] = asyncio.gather(*dict_cor)
        print(f"{type(fut_gathers)=} {isinstance(fut_gathers, Coroutine)=}")

        list_cur: list[Cursor] = await fut_gathers
        print(f"{type(list_cur)=} {type(list_cur[0])=} {isinstance(list_cur, Coroutine)=}")

        for res_cur, cur in zip(dict_cor, list_cur):
            # dict_cor[res_cur] = cur
            # dict_cor[res_cur] = await cur.fetchone()
            dict_cor[res_cur] = [x async for x in cur]
            # dict_cor[res_cur] = await cur.fetchall()

        keys = list(dict_cor.keys())
        values = list(dict_cor.values())
        print(f"{keys[0]=} {type(keys[0])=}")
        print(f"{values[0]=} {type(values[0])=}")

    logF.info(f"{dict_cor=}")
