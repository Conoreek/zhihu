# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Request

from zhihuuser.items import UserItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_user = 'excited-vczh'

    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'thanked_Count,voteup_count,business,locations,description,allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    followee_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}$limit={limit}'
    followee_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    follower_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    follower_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        yield Request(self.user_url.format(user=self.start_user, include=self.user_query), callback=self.parse_user)
        yield Request(self.followee_url.format(user=self.start_user, include=self.followee_query, offset=0, limit=20), callback=self.parse_followee)
        yield Request(self.follower_url.format(user=self.start_user, include=self.follower_query, offset=0, limit=20), callback=self.parse_follower)

    def parse_user(self, response):
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item
        yield Request(self.followee_url.format(user=item.get('url_token'), include=self.followee_query, offset=0, limit=20), callback=self.parse_followee)
        yield Request(self.follower_url.format(user=item.get('url_token'), include=self.follower_query, offset=0, limit=20), callback=self.parse_follower)


    def parse_followee(self, response):
        result = json.loads(response.text)
        if 'data' in result.keys():
            for user in result.get('data'):
                yield Request(self.user_url.format(user=user.get('url_token'), include=self.user_query), callback=self.parse_user)

        if 'paging' in result.keys() and result.get('paging').get('is_end') == False:
            next = result.get('paging').get('next')
            yield Request(next, callback=self.parse_followee)

    def parse_follower(self, response):
        result = json.loads(response.text)
        if 'data' in result.keys():
            for user in result.get('data'):
                yield Request(self.user_url.format(user=user.get('url_token'), include=self.user_query), callback=self.parse_user)

        if 'paging' in result.keys() and result.get('paging').get('is_end') == False:
            next = result.get('paging').get('next')
            yield Request(next, callback=self.parse_follower)