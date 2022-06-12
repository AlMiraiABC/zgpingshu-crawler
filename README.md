# 评书网/zgpingshu 爬取

## 功能

* 下载说书音频MP3格式，根据CSV的标题列按文件夹存储。
* 支持停止后继续下载

## 使用方法

```python
python main.py file.csv
```

### csv格式

标题|链接
-|-
小说名|页面链接

```csv
标题,标题链接
隋唐演义(216回版),http://shantianfang.zgpingshu.com/1040
```
