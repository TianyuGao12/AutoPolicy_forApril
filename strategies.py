# strategies.py
# 更新日期2025.02.10
# 适配主文件版本V5
# 对应json文件更新检测：已更新
# 对应Monitoring_Sites.txt 文件已更新
# 可适配抓取网站：
## 1.检测用：网易，腾讯），
## 2.中央人民政府搜索-新能源汽车 （全部，一个月内，相关程度排序，搜索全文，只查看第一页搜索结果）
###### 需要结合Institution重新考虑关键词适配的问题，每次一个词一个网站还是每次多个词一个网站
## 3.国家公安部搜索-新能源汽车 （政策文件+政策解读，排序方式：相关度，时间范围：时间不限（暂定，为了能输出结果)，只查看第一页）

# 配置模拟浏览器
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


# Set up Chrome options
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')  # Add this line
options.add_argument('--disable-dev-shm-usage')  # Add this line
options.add_argument('--remote-debugging-port=9222')  # Add this line

# 其他import
import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import json

#import smtplib
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
#from email.mime.base import MIMEBase
#from email import encoders
#from email.header import Header
#from email.utils import formataddr

import logging
import os
from io import StringIO

# 推荐的Strategy部分
from strategy import ScraperStrategy
import requests

### 主要部分，按不同网站确定不同回复，回复格式为：？？
class NeteaseScraper(ScraperStrategy):
    def scrape(self, institution, url):
        # Set up the Chrome driver with options
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        data = driver.title
        
        driver.quit()
        
        return data

class TencentScraper(ScraperStrategy):
    def scrape(self, institution, url):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        data = driver.title
        
        driver.quit()
        
        return data

class WwwGovCnScraper(ScraperStrategy):
    def scrape(self, institution, url):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)

        # Wait for the policy list to load
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.middle_result_con.show li'))
        )
        # 等待60秒知道选择器匹配了后面所示的字段（对应网页里面中间显示出来的内容部分）

        # Parse policy items
        policy_items = driver.find_elements(By.CSS_SELECTOR, '.middle_result_con.show li')
        #new_policies = []
        policy = []
        data = []
        institution_parts = institution.split('-') #把机构部分分成发布机构和关键词，对应后面0和1的选择

        
        for item in policy_items:
            link_element = item.find_element(By.TAG_NAME, 'a')
            # ----This line searches for the first <a> (anchor) tag within the current item. The <a> tag typically contains the hyperlink reference (href) and the visible text of the policy. （可以查看最后面的范例来确认）
            # '政策名称', '发布机构', '发布时间', '主要内容', '政策链接', '抓取时间'
            # 'Policy Name','Issuing Agency','Release Date','Main Content','Policy Link','Scraping Time' （中英文对照，主要是ai给我的全是英文的还要一遍一遍改）
            policy = {
                '政策名称': link_element.text.strip(),
                '发布机构': institution_parts[0], #institution,
                '关键词': institution_parts[1],
                '发布时间': item.find_element(By.CSS_SELECTOR, '.date').text.strip(),
                '主要内容': '',   # Main content is not directly available in the list 暂时只包含搜索条目标题，不涉及主要内容
                '政策链接': link_element.get_attribute('href'),
                '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            # Check if the policy already exists
            ###### 这里有点难办，最好是能写在一起，一起返回主函数去验证
            #if not self._is_policy_exists(policy):
            #    new_policies.append(policy)
            #    self._add_policy(policy) #函数内将单独条目写入原有总表文档并保存
            data.append(policy)
            
        driver.quit()
        
        return data


