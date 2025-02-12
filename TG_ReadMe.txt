似乎需要在workflow文件夹内设置yaml文件，但是要把实际需要运行和读取的文件放在根目录（不要放在workflow里面）方便读取？ ----20250209
增加改进了一些workflow的写入、读取、更新github内容的条目，能正常运行了
定时检查：14:15和14:20看一次，运行情况；理论上应该第一次可以把文件都发过来，第二次会提醒没有更新政策了
实际情况：不成功

确认了位置，yaml文件要在rep/.github/workflows/才能被识别，运行文件要放在根目录
repository/
├── .github/
│   └── workflows/
│       └── python-workflow.yml
├── AutoPolicy-20250208-Ready_V3_Chrome_GitHubAutoSource.py
├── requirements.txt
└── other_files/

再次试验定时系统：成功，但是不一定准时，应该还好

2025.02.10 文件版本：AutoPolicy_20250210_Ready_V5_Chrome_GitAuto_DynURL.py
====
正式启用
已经加入了aprilzyp@163.com
====
把运行文件分拆成了主文件+strategy+strategies三个py, 加上Website_Config.json, 此外需要的是Monitoring_Sites.txt
可以达成识别网址并且根据网址进行对应的关键词寻找

文件运行逻辑：
主文件：运行并且控制csv和日志的生成存储内容，一般会写入总表，加上生成一个新表（如果有更新的话）
主文件会读取Monitoring_Sites里面的搜索网站名和URL,使用Website_Config.json进行映射产生一个关键词搜索法，然后这个方法名到strategies.py里面对应一个网站内容读取算法，返回的是一个所有条目的dictionary，然后主函数逐条进行判断是否已经在总表中出现，并更新+保存新文件；strategy.py定义了strategies里面的一个虚拟什么什么的，反正就是一个前提条件

在github运行的话，需要requirements.txt来预安装环境，并且在workflow的YAML里面提前装配Chrome

******
如果要添加新的网站和关键词寻找的话，需要更改的有Monitoring_Sites.txt (添加关键词和网址)，Website_Config.json （添加网址和关键词寻找算法的映射）strategies.py （添加关键词寻找方法）
******
如果要加新的邮箱的话，在主文件的邮箱部分有个列表可以改
==END==

2025.02.12 文件版本：AutoPolicy_Ready_V6_Chrome_GitAuto_DynURL.py （对应workflow已经更新）
====
更新了Monitoring_Sites.txt (添加关键词和网址)，Website_Config.json （添加网址和关键词寻找算法的映射）strategies.py （添加关键词寻找方法）
适配公安部网站的关键词查找，基于虚拟chrome的点击和列表信息提取，可能运行需要花费时间较长
对应改正了主文件的一些算法，主要是适配了分别读多个网站的可能性
==END==


