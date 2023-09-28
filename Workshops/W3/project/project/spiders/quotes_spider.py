import json
from pathlib import Path
import pandas as pd
import jmespath
import scrapy
from scrapy.crawler import CrawlerProcess


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def start_requests(self):
        urls = [
            'https://songsara.net/117205/',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = f'quotes-{page}.html'
        Path(filename).write_bytes(response.body)
        self.log(f'Saved file {filename}')
        self.parse_post(response)

    def parse_post(self, response):
        """
        Parses a post page
        """
        if len(response.css(
                '.dl-box')) > 1:  # our spider does not support such pages with multiple music tracks like https://tinyurl.com/2p85b4hx
            return []

        data = []
        schema_graph_data = json.loads(response.xpath('//script[@type="application/ld+json"]//text()').get())
        info = jmespath.search('"@graph"[?"@type"==\'Article\']|[0]', schema_graph_data)
        if info:
            songs = response.xpath('//ul[has-class("audioplayer-audios")]//li')
            artists = response.xpath('//div[has-class("AR-Si")]//a')
            for song in songs:
                music_name = song.attrib.get('data-title', '')
                album_name = song.attrib.get('data-album', '')
                artist_name = song.attrib.get('data-artist', '')
                file_urls = song.attrib.get('data-src', '')
                data.append([music_name, album_name, artist_name, file_urls])
        df = pd.DataFrame(data, columns=['Music', 'Album', 'Artist', 'File URLs'])
        df.to_csv('results.csv')


process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
})

process.crawl(QuotesSpider)
process.start()
