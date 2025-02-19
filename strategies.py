# strategies.py
# 更新日期2025.02.11
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
# 用于处理警告框
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.alert import Alert


# Set up Chrome options
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')  # Add this line
options.add_argument('--disable-dev-shm-usage')  # Add this line
options.add_argument('--remote-debugging-port=9222')  # Add this line
options.add_argument("--remote-debugging-port=9230")


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
#### 网易的测试版
class NeteaseScraper(ScraperStrategy):
    def scrape(self, institution, url):
        # Set up the Chrome driver with options
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(600)  # 设置 10 分钟超时
        
        try:
            driver.get(url)
        except Exception as e:
            print(f"页面加载超时: {e}")
            
        data = driver.title
        
        driver.stop_client()
        driver.close()
        driver.quit()
        
        return data
#### 腾讯的测试版
class TencentScraper(ScraperStrategy):
    def scrape(self, institution, url):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(600)  # 设置 10 分钟超时
        
        try:
            driver.get(url)
        except Exception as e:
            print(f"页面加载超时: {e}")
            
        data = driver.title
        
        driver.stop_client()
        driver.close()
        driver.quit()
        
        return data
        
#### 中央人民政府搜索的抓取版
# 中央政府政策搜索页 https://www.gov.cn/search/zhengce/?t=zhengce&q=&timetype=timeyy&mintime=&maxtime=&sort=score&sortType=1&searchfield=&pcodeJiguan=&childtype=&subchildtype=&tsbq=&pubtimeyear=&puborg=&pcodeYear=&pcodeNum=&filetype=&p=0&n=5&inpro=&sug_t=zhengce
class WwwGovCnScraper(ScraperStrategy):
    def scrape(self, institution, url):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.set_page_load_timeout(600)  # 设置 10 分钟超时
        
        try:
            driver.get(url)
        except Exception as e:
            print(f"页面加载超时: {e}")

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
            # '政策名称', '发布机构','关键词', '发布时间', '主要内容', '政策链接', '抓取时间'
            # 'Policy Name','Issuing Agency','Key Words','Release Date','Main Content','Policy Link','Scraping Time' （中英文对照，主要是ai给我的全是英文的还要一遍一遍改）
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
            
        driver.stop_client()
        driver.close()
        driver.quit()
        
        return data

#### 公安部搜索的抓取版
# 公安部搜索网站 https://app.mps.gov.cn/searchweb/search_new.jsp#
class MpsGovCnScraper(ScraperStrategy):

    def scrape(self, institution, url):
        institution_parts = institution.split('-') #把机构部分分成发布机构和关键词，对应后面0和1的选择
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        driver.set_page_load_timeout(600)  # 设置 10 分钟超时
        
        try:
            driver.get(url)
        except Exception as e:
            print(f"页面加载超时: {e}")

        #等待 15 秒以确保页面加载完成
        time.sleep(15)

        # 处理警告框
        ###额外定义函数好像没法被引用，所以都写在一起了
        #check_and_accept_alert(driver)
        try:
            alert = Alert(driver)
            alert_text = alert.text
            alert.accept()
            print(f"处理了警告框，内容为: {alert_text}")
        except NoAlertPresentException:
            pass
    
        # 找到搜索框并点击
        search_box = driver.find_element(By.ID, 'fullText')
        search_box.click()

        # 输入获取的关键词部分
        search_box.send_keys(institution_parts[1])

        # 找到搜索按钮并点击
        search_button = driver.find_element(By.ID, 'search')
        search_button.click()

        # 等待 15 秒以确保搜索结果加载完成
        time.sleep(15)

        # 找到“标题”下拉菜单并点击
        title_dropdown = driver.find_element(By.ID, 'titleOrfull')
        title_dropdown.click()

        # 在下拉菜单中选择“全文”
        full_text_option = driver.find_element(By.XPATH, "//option[@value='1']")
        full_text_option.click()

        # 等待 15 秒以确保搜索结果加载完成
        time.sleep(15)

        # 在导航栏中找到“政策解读”并点击
        policy_interpretation = driver.find_element(By.XPATH, "//li[@jsfl='zcjd']")
        policy_interpretation.click()
    
        #点击 时间不限 （因为下拉菜单格式有点难处理）
        # 等待并点击显示当前选项的元素（例如，包含“时间不限”文本的元素）
        current_selection = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//cite[contains(text(), '时间不限')]"))
        )
        current_selection.click()
        # 等待并选择“一年内”选项
        one_year_option = WebDriverWait(driver, 10).until(
            #EC.element_to_be_clickable((By.XPATH, "//li[@timerange='4']/a")) #这个是 一年内 选项
            EC.element_to_be_clickable((By.XPATH, "//li[@timerange='0']/a")) #这个是 时间不限 选项
        )
        one_year_option.click()

        # 等待 30 秒以加载结果
        time.sleep(30)

        ### 从加载好的搜索列表项里面抓取信息
        #定位包含所有列表项的父元素
        list_container = driver.find_element(By.ID, 'info')
        #获取所有包含信息的子元素
        policy_items = list_container.find_elements(By.CLASS_NAME, 'list')
        #遍历每个子元素，提取所需信息并存入字典
        
        policy = []
        data = []
    
        for item in policy_items:
            # 提取标题
            title_element = item.find_element(By.TAG_NAME, 'h3')
            title = title_element.text

            # 提取URL链接
            policylink = title_element.find_element(By.XPATH, '..').get_attribute('href')

            # 提取发布时间
            span_text = item.find_element(By.TAG_NAME, 'span').text
            publish_date = span_text.split('发布时间：')[-1]

            # 将提取的信息存入字典
            policy = {
                '政策名称': title,
                '发布机构': institution_parts[0], #institution,
                '关键词': institution_parts[1],
                '发布时间': publish_date,
                '主要内容': '',   # Main content is not directly available in the list 暂时只包含搜索条目标题，不涉及主要内容
                '政策链接': policylink,
                '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            data.append(policy)

        ### 后面还要再抓取一遍“政策文件”
        # 在导航栏中找到“政策文件”并点击
        policy_interpretation = driver.find_element(By.XPATH, "//li[@jsfl='zcwj']")
        policy_interpretation.click()

        # 等待 30 秒以加载结果
        time.sleep(30)

        ### 从加载好的搜索列表项里面抓取信息
        #定位包含所有列表项的父元素
        list_container = driver.find_element(By.ID, 'info')
        #获取所有包含信息的子元素
        policy_items = list_container.find_elements(By.CLASS_NAME, 'list')
        #遍历每个子元素，提取所需信息并存入字典
        ### 不需要重新初始化，直接找新的policy并且并入data

        for item in policy_items:
            # 提取标题
            title_element = item.find_element(By.TAG_NAME, 'h3')
            title = title_element.text

            # 提取URL链接
            policylink = title_element.find_element(By.XPATH, '..').get_attribute('href')

            # 提取发布时间
            span_text = item.find_element(By.TAG_NAME, 'span').text
            publish_date = span_text.split('发布时间：')[-1]

            # 将提取的信息存入字典
            policy = {
                '政策名称': title,
                '发布机构': institution_parts[0], #institution,
                '关键词': institution_parts[1],
                '发布时间': publish_date,
                '主要内容': '',   # Main content is not directly available in the list 暂时只包含搜索条目标题，不涉及主要内容
                '政策链接': policylink,
                '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            data.append(policy)

        driver.stop_client()
        driver.close()
        driver.quit()
        
        return data

