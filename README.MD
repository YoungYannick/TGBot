# 🤖 Telegram 传话筒 Bot & Web 管理面板

这是一个集成了 Telegram Bot 和 Web 管理面板的消息转发系统。Bot 负责接收用户消息、进行验证和关键词屏蔽，并将消息转发给管理员；Web 面板则提供了一个可视化的界面，用于配置 Bot、管理用户、查看消息记录和统计数据。

![](/static/images/仪表盘.jpg)
[其他界面](https://github.com/YoungYannick/TGBot/tree/master/static/images)

## ✨ 主要功能

* **Telegram Bot**：
    * **用户验证**：支持简单的按钮验证和数学验证（可配置难度），防止垃圾信息。
    * **消息转发**：将私聊消息转发给指定的管理员。
    * **关键词屏蔽**：自动过滤包含预设屏蔽关键词的消息。
    * **管理员命令**：通过 Telegram 命令管理用户（拉黑/解封）、管理关键词、查看设置等。
    * **多语言支持**：支持配置中文和英文的欢迎消息。
* **Web 管理面板 (基于 Flask)**：
    * **初始设置**：首次运行时，引导用户配置 Bot Token、管理员 ID 和面板登录信息。
    * **安全登录**：使用用户名和密码进行登录。
    * **仪表盘**：提供用户统计、消息趋势图表等概览信息。
    * **用户管理**：查看和管理所有用户（包括拉黑/解封）。
    * **关键词管理**：添加、删除和查看屏蔽关键词。
    * **系统配置**：修改 Bot 核心设置，如验证开关、验证类型和难度。
    * **聊天记录**：按用户查看详细的聊天记录，支持搜索和日期筛选。
    * **主题切换**：支持浅色/深色/自动主题。

## 📁 项目结构

```
TGBot/
├── app.py                # Flask Web 应用主文件
├── bot.py                # Telegram Bot 主程序
├── database.py           # 数据库模型定义
├── requirements.txt      # Python 依赖包
├── bot_data.db           # SQLite 数据库（运行后生成）
│
├── templates/            # HTML 模板文件
│   ├── setup.html        # 初始设置页面
│   ├── login.html        # 登录页面
│   └── dashboard.html    # 管理面板主页
│
└── static/               # 静态资源文件
├── css/
│   └── styles.css        # 样式表
├── js/
│   ├── dashboard.js      # 面板交互逻辑
│   └── auth_theme.js     # 主题切换逻辑
└── images/
│   └── favicon.ico       # 网站图标
```

## 📝 使用指南

### Bot 命令（管理员专用）

在 Telegram 中回复用户转发的消息使用以下命令：

- `/block` - 屏蔽用户（回复用户消息）
- `/unblock` - 解除屏蔽（回复用户消息）
- `/checkblock` 或 `/info` - 查看用户信息（回复用户消息）
- `/addkw <关键词>` - 添加屏蔽关键词
- `/rmkw <关键词>` - 移除屏蔽关键词
- `/listkw_all` - 查看所有屏蔽关键词
- `/listblock_all` - 查看所有被屏蔽用户
- `/setstart_zh <内容>` - 设置中文欢迎语
- `/setstart_en <内容>` - 设置英文欢迎语
- `/verify_settings` - 打开人机验证设置菜单

### 用户命令

- `/start` - 开始使用机器人，获取欢迎消息

## 🚀 部署与运行

```bash
pip install -r requirements.txt
```
```
python app.py
```