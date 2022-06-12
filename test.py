from unittest import IsolatedAsyncioTestCase

from main import *


class Test(IsolatedAsyncioTestCase):
    async def test_get_chapters(self):
        teller = 'shantianfang'
        novel = '58'
        chapters = await get_chapters(teller, novel)
        print(chapters)
        self.assertNotEqual(len(chapters), 0)

    async def test_get_chapters_status_err(self):
        teller = 'shantianfang'
        novel = '1234567890'
        with self.assertRaises(ConnectionError):
            await get_chapters(teller, novel)

    async def test_get_audio_url(self):
        chapter='www.zgpingshu.com/play/58/483.html'
        url = await get_audio_url(chapter)
        print(url)
        self.assertTrue(url)

    async def test_download(self):
        url = 'http://oshantianfang1.zgpingshu.com/%E5%8D%95%E7%94%B0%E8%8A%B3%E8%AF%84%E4%B9%A6_%E4%B9%B1%E4%B8%96%E6%9E%AD%E9%9B%84%28485%E5%9B%9E%E7%89%88%29401-485_448MB_32k/AC62CC4C38.mp3'
        fn = 'test.mp3'
        await download(url, fn)
