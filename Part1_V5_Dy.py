
#!/usr/bin/env python
# coding: utf-8



#!pip install requests beautifulsoup4 selenium webdriver_manager pandas
### 这个是下载notebook为py时候自动转换的，如果用GitHub的话要有个requirements.txt文件




# 配置模拟浏览器 应该在strategies 里面解决了，只返回一个信息列表数据包
"""
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

# Set up the Chrome driver with options
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 测试网站信息回馈
driver.get("https://www.qq.com")
print(driver.title)
driver.quit()
"""


# 其他import
import csv
import requests
import pandas as pd
from datetime import datetime
import time
import json

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr

import logging
import os
from io import StringIO

from urllib.parse import urlparse #这部分用于解析url以及找到对应的信息抓取方法，详见strategies.py





"""test of the successful run and the right saving place"""
print("Current working directory:", os.getcwd())

# Get the directory where the current script is located
#script_dir = os.path.dirname(os.path.abspath(__file__)) ###Github似乎可以用这个，如果后面那个不行就换回来
script_dir = os.getcwd()
### 这里因为文件位置不确定的关系，用了自动搜索，会把所有读取和生成的文件在同一文件夹里面自动寻找，后面的变量名也都对应改了

# 设置日志 - 建议只在最开始初始化设置一次
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join(script_dir,'policy_monitor.log')
)





timestring = datetime.now().strftime('%Y-%m-%d_%H-%M')

class PolicyMonitor:
    def __init__(self):
        # 初始化数据存储
        self.policy_data_file = os.path.join(script_dir, 'Policy_Data_All.csv')
        ### 每个词首字母都大写的是我们需要读取或写入的其他数据文件
        self.load_existing_data()

        #初始化一个空白csv来添加本次更新的内容
        self.policy_newdata_file = os.path.join(script_dir,f'Policy_Data_New_{timestring}.csv')
        # Check if the new data file exists
        if not os.path.isfile(self.policy_newdata_file):
            # File doesn't exist, create it and log the creation
            with open(self.policy_newdata_file, 'w', newline='') as file:
                pass  # Just create the file
            logging.info(f"已创建csv更新文件: {self.policy_newdata_file}")
        else:
            # File exists, log that it already exists
            logging.info(f"已存在同名csv更新文件: {self.policy_newdata_file}")
        # Load existing data
        self.load_existing_data()
        
        # 配置监控的网站（可以根据需要添加）
        ### 加载监控网站列表
        self.monitoring_sites = self.load_monitoring_sites(os.path.join(script_dir,'Monitoring_Sites.txt'))
        #print(f"{self.monitoring_sites}")
        
        ### 手动写入列表部分，暂时注释掉
        """
        self.monitoring_sites = {
            # 可添加更多网站
            # 格式为 - '政府部门和搜索内容(institution)': '具体网址(url)',
            '中央政府网站搜索-新能源汽车': 'https://www.gov.cn/search/zhengce/?t=zhengce&q=%E6%96%B0%E8%83%BD%E6%BA%90%E6%B1%BD%E8%BD%A6&timetype=timeyy&mintime=&maxtime=&sort=score&sortType=1&searchfield=&pcodeJiguan=&childtype=&subchildtype=&tsbq=&pubtimeyear=&puborg=&pcodeYear=&pcodeNum=&filetype=&p=0&n=5&inpro=&sug_t=zhengce',
            ### 备注--搜索词："新能源汽车"，日期筛选："一月内"，"搜索全文"，"相关程度排序"，"全部"，"第1页"
            # 可考虑在这部分改成读取一个网址列表文件
        }
        """

    # 读取监控网站文件
    def load_monitoring_sites(self, filepath):
        monitoring_sites = {}
        if not os.path.isfile(filepath):
            logging.warning(f"警告: 未找到监控列表文件 {filepath}")

        else:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line and not line.startswith('#'):  # 忽略空行和注释
                            institution, url = line.split(',', 1)  # 仅分割一次，防止URL中包含逗号
                            monitoring_sites[institution.strip()] = url.strip()
            except Exception as e:
                logging.error(f"加载监控网站列表时出错: {e}")
            return monitoring_sites

    # 读取现有政策文件
    def load_existing_data(self):
        # 加载已存在的政策数据如果文件不存在则创建新的DataFrame
        try:
            self.policy_df = pd.read_csv(self.policy_data_file)
        except FileNotFoundError:
            #print(f"未找到已存在政策文件，已生成空白内容csv文件")
            ### 将输出的警告信息改为写在日志里面
            logging.info(f"未找到已存在政策文件，已生成空白内容csv文件")
            self.policy_df = pd.DataFrame(columns=[
                '政策名称', '发布机构', '发布时间', '主要内容', '政策链接', '抓取时间'
            ])
            ### 为确定新生成文件的情况，调试时增加了每列第一个数据，实际运行时候可以跳过
            self.policy_df.loc[0] = ['TestCol1', 'TestCol2', 'TestCol3', 'TestCol4', 'TestCol5', 'TestCol6']
            self.save_data()

    def save_data(self):
        # 保存政策数据到CSV文件
        self.policy_df.to_csv(self.policy_data_file, index=False, encoding='utf-8')

    def get_scraper_class(self,domain, config):
        # 从URL中对照抓取方法，见文件strategy.py和Website_Config.json
        module_name, class_name = config[domain].rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)

    def web_fetch_data(self, institution, url):
        config = {}
        with open(os.path.join(script_dir, 'Website_Config.json')) as f:
            try:
                config = json.load(f)
                #print(config)
            except json.JSONDecodeError as e:
                logging.error(f'解析JSON文件时出错: {e}')
    
        ### 备注：urlparse类别里面的URL必须有http或者https抬头
        #url = 'www.163.com/v/video/VIMSCM2RB.html?clickfrom=w_yw_wysl' #测试用，后面改成不是主函数的时候会注释掉
        #url = 'https://www.qq.com/' #测试2
        ## 测试3
        #url = 'https://www.gov.cn/search/zhengce/?t=zhengce&q=%E6%96%B0%E8%83%BD%E6%BA%90%E6%B1%BD%E8%BD%A6&timetype=timeyy&mintime=&maxtime=&sort=score&sortType=1&searchfield=&pcodeJiguan=&childtype=&subchildtype=&tsbq=&pubtimeyear=&puborg=&pcodeYear=&pcodeNum=&filetype=&p=0&n=5&inpro=&sug_t=zhengce'
        if not urlparse(url).scheme:
            url = 'http://' + url
    
        domain = urlparse(url).netloc
        print(domain)

        new_policies = [] ###初始化一下，run函数中每次for循环都会将新网站的new policies添加入csv文件，所以不用一直保留
        
        if domain in config:
            #如果网址和JSON文件中的映射能找到配对的话，可以对应找到strategies文件里面的提取方法
            ScraperClass = self.get_scraper_class(domain, config)
            scraper = ScraperClass()
            data = scraper.scrape(institution, url) #scrape是实际在strategies.py里面参与解析的函数，返回data是以列表形式返回抓取到的所有数据

            if data:
                logging.info(f"来自{institution}的政策获取正常")
                print(f"来自{institution}的政策获取正常")
            else:
                logging.warning(f"来自{institution}的政策获取异常")
                print(f"来自{institution}的政策获取异常")
            
            ###### 现在的情况是以列表形式返回抓取到的所有数据，对应应该找一个拆解分析去掉重复部分的函数
            ###### 然后return应该是 - 如果按照之前版本fetch的话 - 一份写入全列表，一份写入new policies
            
            for policy in data:
                if not self._is_policy_exists(policy):
                    new_policies.append(policy) #添加到new policies
                    self._add_policy(policy) #函数内将单独条目写入原有总表文档并保存
                    
        else:
            logging.warning(f'未找到对应网站解析方法: {domain}')
            
        return new_policies

    ###### 标准的话是会废止的 如果有的话可能还得额外标注一下
    
    def _is_policy_exists(self, policy):
        # 检查政策是否已存在
        return any((self.policy_df['政策名称'] == policy['政策名称']) & 
                  (self.policy_df['发布时间'] == policy['发布时间']))

    def _add_policy(self, policy):
        # 添加新政策到数据总表
        self.policy_df = pd.concat([self.policy_df, pd.DataFrame([policy])], 
                                 ignore_index=True)
        self.save_data()

    def append_to_csv(self, policies):
        # 新政策转换格式并存储为新文件
        new_df = pd.DataFrame(policies)
        
        # Check if the file exists to determine whether to write the header
        if os.path.exists(self.policy_newdata_file):
            # Append to the existing file without writing the header
            new_df.to_csv(self.policy_newdata_file, mode='a', header=False, index=False)
            logging.info(f"已从头添加 {len(policies)} 条新政策到 {self.policy_newdata_file}")
        else:
            new_df.to_csv(self.policy_newdata_file, mode='w', header=False, index=False)
            logging.info(f"已继续添加 {len(policies)} 条新政策到 {self.policy_newdata_file}")
            
    def run(self):
        # 运行监控程序 - 手动运行没有定时
        logging.info("开始政策监控...")

        # 检查 monitoring_sites 是否为 None
        if self.monitoring_sites is None:
            logging.error("监控网站列表未加载成功，无法开始监控。")
            return
            
        YNPolicy = False #默认情况为未发现
        for institution, url in self.monitoring_sites.items():
            #new_policies = self.fetch_policy(institution, url) #老版本的，参考上面注释掉的函数
            new_policies = self.web_fetch_data(institution, url) 
            ###### 注意是否是验证过没有重复的项目，前面不一定改成了一样的结构
            
            if new_policies:
                logging.info(f"发现{len(new_policies)}条来自{institution}的新政策")
                # Append new policies to the CSV_new file
                self.append_to_csv(new_policies)
                #将new_policies添加到之前的更新csv文件中，每for循环一次会换一套搜索网址
                YNPolicy = True
            else:
                logging.info(f"未发现新政策")
                YNPolicy = False
            return YNPolicy
            


if __name__ == '__main__':
    monitor = PolicyMonitor()
    YNPolicy = monitor.run()
    if YNPolicy == None:
        logging.error("代码有错误，YNPolicy为None")
    
# 含时间的小输出，确认代码成功跑到最后
print(f"运行顺利，时间：{timestring}")
print(f"{YNPolicy}")