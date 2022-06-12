import asyncio
import csv
import json
import os
import re
import sys
import time
from asyncio import Semaphore
from datetime import datetime
from typing import List, Tuple

import aiofiles
from aiohttp import ClientSession
from al_utils.console import ColoredConsole
from al_utils.logger import Logger

from config import (DOWNLOAD_TIMEOUT, DS, HEADERS, REQ_TIMEOUT, RESUME,
                    RETRY_SLEEP, RETRY_TIMES, SAVE_DIR, SLEEP)
from util import Record, human_size

logger = Logger('main').logger


async def get_chapters(teller: str = None, novel_id: str = None, url: str = None, timeout: float = REQ_TIMEOUT) -> List[Tuple[str, str]]:
    """
    获取该说书人:param:`teller`的指定小说:param:`novel_id`的章节列表

    :param teller: 说书人
    :param novel_id: 小说
    :param timeout: 请求超时时间
    :returns: (章节页面, 章节名称)组成的列表
    :raises: :class:`ConnectionError` if response status is not `200`.
    """
    url = url or f'http://{teller}.zgpingshu.com/{novel_id}/'
    async with ClientSession() as session:
        async with session.get(url=url, headers=HEADERS, timeout=timeout) as resp:
            if resp.status == 200:
                logger.info(f'get chapters from {url} successfully.')
                chapters = re.findall(
                    r'<li><div class="player"><a href="//(.*?)".*?>(.*?)</a>.*?</li>',
                    await resp.text('GBK'),
                    re.S
                )
                return chapters
    raise ConnectionError(
        f'get chapters {url} failed with status {resp.status}.')


async def get_audio_url(chapter_url: str, timeout: float = 0) -> str:
    """
    获取该章节的音频链接

    :param chapter_url: 章节链接
    :param timeout: 请求超时时长
    :returns: 音频链接
    :raises: :class:`ConnectionError` if response status is not `200`.
    """
    url = "http://"+chapter_url.replace("play", "playdata")
    async with ClientSession() as session:
        async with session.post(url, headers=HEADERS, timeout=timeout) as resp:
            if resp.status == 200:
                logger.info(f'get audio url from {url} successfully.')
                data: dict = json.loads(await resp.text())
                indexes = data["indexes"]
                seconds = datetime.now().second
                urlpath = data["urlpath"]
                index = indexes[seconds % len(indexes)]
                urlpath: str = urlpath.replace('[INDEX]', str(index))
                urlpath = urlpath.replace('.flv', '.mp3')
                return urlpath
    raise ConnectionError(
        f'get audio url {url} failed with status {resp.status}.')


async def download(url: str, save_to: str, chunk_size: int = 1024*1024, timeout: float = DOWNLOAD_TIMEOUT, semaphore: Semaphore = Semaphore(3)):
    """
    下载链接的内容

    :param url: 下载链接
    :param save_to: 保存的文件名
    :param chunk_size: 分段下载大小(B)
    :param timeout: 请求超时时长
    :param semaphore: 并发下载数
    """
    save_to = save_to or os.path.join(SAVE_DIR, os.path.basename(url))
    async with semaphore:
        async with ClientSession() as session:
            async with await session.get(url=url, headers=HEADERS, timeout=timeout) as resp:
                if resp.status == 200:
                    length = int(resp.headers.get(
                        'Content-Length', '0'))
                    async with aiofiles.open(save_to, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(chunk_size):
                            await f.write(chunk)
                    logger.info(
                        f'download {url} successfully. {human_size(length)}')
                    return
    raise ConnectionError(
        f'get audio url {url} failed with status {resp.status}.')


def help(status=0):
    print("Example:")
    print("main.py http://shantianfang.zgpingshu.com/58/")
    print("main.py shantianfang 58")
    exit(status)


def get_resume(chapters: list[tuple[str, str]], record: Record):
    """
    Get undownload chapters.

    :param chapters: All chapters.
    :return: Undownload chapters if RESUME.
    """
    if RESUME:
        rec = record.last()
        if rec:
            c = rec[0][-1]
            for index, chapter in enumerate(chapters):
                if c in chapter:
                    logger.info(f'Skip {index+1} chapters.')
                    ColoredConsole.warn(f'Skip {index+1} chapters.')
                    return chapters[index+1:]
    return chapters


async def process(save_dir: str, url: str):
    record = Record(f'{save_dir}.log')
    logger.info(f'Starting {save_dir}.')
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
        logger.debug(f"{save_dir} doesn't exist, create it.")
    chapters = await get_chapters(url=url)
    logger.info(f'Get {len(chapters)} chapters.')
    ColoredConsole.success(f'Get chapters successfully. '
                           f'Got {len(chapters)} chapters.')
    err_urls = open(os.path.join(save_dir, 'errors.log'),
                    'w+', encoding='utf-8')
    for chapter in get_resume(chapters, record):
        try:
            url = await get_audio_url(chapter[0])
            await download(url, os.path.join(save_dir, f'{chapter[1]}.mp3'))
            ColoredConsole.success(
                f'Download {chapter[1]} successfully.')
            record.log(save_dir, url, *chapter)
        except Exception as ex:
            # region retry
            ColoredConsole.warn(f'Got {chapter[1]} failed. '
                                f'Retry {RETRY_TIMES} times.')
            suc: bool = False
            for index in range(RETRY_TIMES):
                try:
                    ColoredConsole.debug(f'Retry {index+1} time.')
                    url = await get_audio_url(chapter[0])
                    await download(url, os.path.join(save_dir, f'{chapter[1]}.mp3'))
                    ColoredConsole.success(
                        f'Download {chapter[1]} successfully.')
                    record.log(save_dir, url, *chapter)
                    suc = True
                except:
                    await asyncio.sleep(RETRY_SLEEP)
                    continue
            # endregion
            # region failed
            if suc:
                continue
            logger.error(str(ex), exc_info=1)
            err_urls.write(f'{chapter[1]}\n')
            err_urls.flush()
            ColoredConsole.error(f'Got {chapter[1]} failed. {ex}')
            ColoredConsole.debug(f'Sleep {SLEEP} seconds.')
            # endregion
            time.sleep(SLEEP)  # sleep all coroutines
    err_urls.close()
    record.delete()
    ColoredConsole.success(f'Downloaded finished.')
    logger.info(f'Finished {save_dir}.')


async def main():
    record = Record('downloaded.log')
    if len(sys.argv) == 2:
        if sys.argv[1] == '-h':
            help()
    ds = DS or sys.argv[1]
    if not os.path.isfile(ds):
        ColoredConsole.error(f"File {ds} does not exist.")
        exit(1)
    if RESUME:
        res = record.all()
    with open(DS, encoding="utf-8") as f:
        f_csv = csv.reader(f)
        _ = next(f_csv)
        for row in f_csv:
            save_dir = row[0]
            url = row[1]
            if res and row in res:
                logger.debug(f'Skip {row}.')
                ColoredConsole.warn(f'Skip {save_dir}.')
                continue
            await process(save_dir, url)
            record.log(*row)
    record.delete()
    logger.info('Process finished.')
    ColoredConsole.warn('ヾ(￣▽￣)Bye~Bye~', '😸')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Cancled by user.')
        ColoredConsole.warn('Canceled by user. ヾ(￣▽￣)Bye~Bye~', '🐱')
