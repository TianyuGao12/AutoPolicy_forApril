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

再次试验定时系统：
