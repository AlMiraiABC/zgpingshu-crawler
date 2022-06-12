HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36 Edg/102.0.1245.33",
}

SAVE_DIR = 'download'  # 下载目录

SLEEP = 30  # 失败时等待时长/秒

RETRY_TIMES = 5  # 失败链接重试次数

RETRY_SLEEP = 10  # 重试时的等待时长

DS = 'pingshu.csv'  # DataStore.csv

RESUME = True  # 是否断点续传

REQ_TIMEOUT = 30  # 页面请求超时时长
DOWNLOAD_TIMEOUT = 5*60  # 下载超时时长
