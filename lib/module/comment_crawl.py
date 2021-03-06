#!/usr/bin/python3
#coding=utf-8
'''
Created on 2018年5月17日

@author: leonlee
'''

import conf
import re
import os
import json
from lib.utility.threadpool import ThreadPool
import math
import requests

class CommentCrawl(object):
    """评论爬取
    """
    def __init__(self):
        pass
        
    @staticmethod
    def crawl_page(params):
        """爬取页面
            @param params:参数 
            @return: 页面的字符串形式
        """
        response = requests.get(conf.base_url,params)
        return response.text
    
    
    def crawl_comment(self,productId,start_page = 0,page_length = None,save_way = None):
        """爬取评论
            @param productId: 商品ID
            @param start_page: 爬取评论开始页  
            @param page_length:  爬取评论页数长度，默认为None表示从开始页到最后一页
            @param save_way: 保存方式，分别为txt，mongodb，csv，None，默认为None表示不保存 
            @return: 评论的dict形式
        """
        #长度判定
        if page_length:
            assert page_length >= 1,"评论页数长度不能小于1"
        else:
            page_length = math.inf
            
        
        comments = []
        #设置参数
        comment_param = conf.comment_crawl_params
        comment_param["productId"] = productId
        
        current_page_length = 0
        while current_page_length < page_length:
            comment_param["page"] = start_page + current_page_length
            
            #正则匹配
            response_text = CommentCrawl.crawl_page(comment_param)
            pattern = re.compile(conf.crawl_comment_rule, re.S)
            match_result = pattern.findall(response_text)
            match_result = [json.loads(x) for x in match_result]
            
            #结束条件
            if len(match_result) == 0 and page_length == math.inf:
                break
            
            comments.extend(match_result)
            
            current_page_length += 1
            
        #保存
        if save_way: 
            save_func = conf.save_ways[save_way];
            save_func("{0}{1}.{2}".format(conf.save_folder,productId,save_way),data = comments)
            
        return comments
        
        
    def get_productId(self,items_url = conf.items_url):
        """根据商品列表取得商品的ID
            @param items_url : 商品列表的url 
            @return: 商品的字典形式{商品ID ： 商品名} 
        """
        response = requests.get(url = items_url)
        match_rule = "<div class=\"p-name\".*?(href.*?)</em>"
        match_result = re.findall(match_rule,response.text, re.S)
            
        products = dict()
        for product_str in match_result[1:]:
            product_id = re.findall("\/(\d+)\.",product_str,re.S)[-1]
            product_id = int(product_id)
            
            product_name = re.findall("<em>(.*)",product_str,re.S)[0]
            product_name = product_name.strip()
            
            products[product_id] = product_name
            
        return  products
    
    def crawl_from_itemlist(self,items_url = conf.items_url,max_page = conf.max_page,save_way = "csv",max_thread = conf.max_threads):
        """从商品列表爬去评论并保存
            @param items_url:  商品列表url
            @param max_page:  爬取评论的最大页数，None表示爬取商品的所有页数  
            @return: 结果的queue
        """
        assert save_way in conf.save_ways.keys(),"保存方式错误"
        save_func = conf.save_ways[save_way]
            
        product_Ids = self.get_productId(items_url);
        
        thread_pool = ThreadPool(
                            save_func = save_func,
                            crawl_func = self.crawl_comment,
                            workers = product_Ids,
                            max_page = max_page,
                            max_thread = max_thread
                            )
        thread_pool.start_all_threads()
        
        
        return thread_pool.result_queue
        
        
        
        

    