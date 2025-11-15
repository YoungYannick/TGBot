# 🤖 Telegram 传话筒 Bot & Web 管理面板

这是一个功能强大的 Telegram 消息转发系统，集成了智能 Bot 和一个现代化的 Web 管理面板。Bot 负责接收用户消息、执行多种验证策略、屏蔽关键词，并将安全的消息转发给管理员。Web 面板则提供了一个直观、可视化的界面，用于配置 Bot 的所有功能、管理用户、查看详细的聊天记录和数据统计。

![](/static/images/仪表盘.jpg)
*查看[其他界面截图](https://github.com/YoungYannick/TGBot/tree/master/static/images)了解更多。*

## ✨ 主要功能

*   **Telegram Bot**：
    *   **多重用户验证**：支持简单的"我是人类"按钮、数学计算题和图形验证码，并可配置难度等级，有效抵御垃圾信息和机器人骚扰。
    *   **验证有效期**：可自定义用户通过验证后的有效时间（从秒到年，或仅首次），过期后需重新验证。
    *   **智能消息转发**：将通过验证和过滤的用户私聊消息安全地转发给指定的管理员。
    *   **关键词屏蔽**：自动拦截并过滤包含预设屏蔽关键词的消息，并通知管理员。
    *   **便捷的管理员命令**：管理员可直接在 Telegram 中通过命令快速管理用户（拉黑/解封）、增删关键词、查看设置等。
    *   **多语言支持**：为不同语言的用户（中文/英文）配置个性化的欢迎消息。

*   **Web 管理面板 (基于 Flask)**：
    *   **引导式初始设置**：首次运行，通过网页引导轻松完成 Bot Token、管理员 ID 和面板登录信息的配置。
    *   **安全登录机制**：通过用户名和密码保护您的管理后台。
    *   **数据可视化仪表盘**：提供核心数据概览，包括用户总数、今日新增、消息统计和趋势图表。
    *   **全面的用户管理**：集中查看、搜索所有用户，并进行拉黑/解封、手动验证/取消验证等操作。支持显示用户语言、创建及验证时间。
    *   **高效的关键词管理**：批量添加、删除和搜索屏蔽关键词。
    *   **灵活的系统配置**：在网页上轻松切换 Bot 的连接方式 (Polling/Webhook)、调整验证开关、验证类型、难度和有效期。
    *   **聊天记录追溯**：按用户查看详细的聊天记录(图片除外)，并支持按内容和日期范围进行高级搜索。
    *   **个性化主题**：支持浅色、深色及跟随系统的自动主题切换，提升使用体验。

## 🛠️ 技术栈

*   **后端**: Python, Flask, python-telegram-bot, SQLAlchemy
*   **前端**: HTML, CSS, JavaScript (原生)
*   **数据库**: SQLite

## 📁 项目结构

```
TGBot/
├── app.py                # Flask Web 应用主文件
├── bot.py                # Telegram Bot 主程序
├── database.py           # 数据库模型与初始化
├── requirements.txt      # Python 依赖包
├── bot_data.db           # SQLite 数据库文件（运行后自动生成）
├── blocklist.txt         # 关键词示例
│
├── templates/            # Flask HTML 模板
│   ├── setup.html        # 初始设置页面
│   ├── login.html        # 登录页面
│   └── dashboard.html    # 管理面板主页
│
└── static/               # 静态资源
├── css/
│   └── styles.css        # 样式表
├── js/
│   ├── dashboard.js      # 面板交互逻辑
│   └── auth_theme.js     # 登录页与主题切换逻辑
└── images/
    ├── favicon.ico       # 网站图标
    └── ...               # 截图等图片资源
```

## 🚀 部署与运行

### 1. 环境准备

*   Python 3.8+
*   一个 Telegram Bot Token (通过 [@BotFather](https://t.me/BotFather) 创建)
*   您的 Telegram User ID (可通过 [@userinfobot](https://t.me/userinfobot) 获取)

### 2. 克隆项目

```bash
git clone https://github.com/YoungYannick/TGBot.git
cd TGBot
```

### 3. 安装依赖

建议在虚拟环境中安装，以避免与系统库冲突。

```bash
# 创建虚拟环境 (可选)
python -m venv venv
# 激活虚拟环境 (Windows)
.\venv\Scripts\activate
# 激活虚拟环境 (Linux/macOS)
source venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt
```

### 4. 运行应用

```bash
python app.py
```

应用启动后会同时运行 Web 面板和 Telegram Bot。

### 5. 初始设置

*   首次运行时，后台会提示您进行配置。
*   在浏览器中打开 `http://<您的服务器IP>:8080/setup`。
*   按照页面提示，填入您的 Bot Token、管理员 ID、Webhook 设置（如果需要）以及您想设置的 Web 面板登录名和密码。
*   提交后，系统将自动保存配置并重启 Bot。之后，您将被重定向到登录页面。

### 6. 登录和使用

*   访问 `http://<您的服务器IP>:8080/` 并使用您刚刚设置的用户名和密码登录。
*   现在，您可以在 Web 面板中管理您的 Bot，同时 Bot 也已在 Telegram 上线。

## 📝 使用指南

### Bot 命令（管理员专用）

您需要成为 Bot 的管理员才能使用这些命令。大部分操作都支持通过**回复**由 Bot 转发的用户消息来执行，非常方便。

-   `/block` - **屏蔽**用户。
-   `/unblock` - **解封**用户。
-   `/checkblock` 或 `/info` - 查看用户的**详细信息**和状态。
-   `/addkw <关键词>` - 添加一个屏蔽关键词。
-   `/rmkw <关键词>` - 移除一个屏蔽关键词。
-   `/listkw_all` - 查看所有屏蔽关键词列表。
-   `/listblock_all` - 分页查看所有被屏蔽的用户列表。
-   `/setstart_zh <内容>` - 设置**中文**欢迎消息。
-   `/setstart_en <内容>` - 设置**英文**欢迎消息。
-   `/verify_settings` - 在聊天中打开一个**人机验证设置**的快捷菜单。

### 用户命令

-   `/start` - 开始与机器人交互，接收欢迎消息和验证。

## ⚠️ 注意事项

*   **数据库**: 项目使用 SQLite，数据库文件 `bot_data.db` 会在首次运行后在根目录创建。请勿手动删除此文件，否则所有用户数据和设置将会丢失。
*   **Webhook**: 如果您选择使用 Webhook 模式，请确保您的服务器拥有一个域名和有效的 SSL 证书，并且 `8443` 端口可以被公网访问。
*   **重启**: 在 Web 面板中修改核心设置（如 Bot Token, Webhook 配置等）后，后台服务会自动重启以应用更改。

> >> 代码由Gemini AI辅助完成
