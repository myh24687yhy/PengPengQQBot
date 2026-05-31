# QQBot - 智能QQ群机器人

基于 NoneBot2 框架开发的智能QQ群机器人，支持AI聊天、游戏娱乐、群管理等多种功能。

## 功能特点

### AI 智能聊天
- 支持 DeepSeek API 和 dobao API 的智能对话
- 多种AI角色切换（默认、毒舌、知心、中二、甜妹、御姐、搞笑、社恐、腹黑、古风等）
- 支持全网搜索功能
- 语音合成输出（可选）

### 游戏娱乐
- **修仙系统** - 修炼突破、境界飞升、商城交易
- **斗罗大陆** - 魂师养成、魂环搭配
- **成语接龙** - 群友互动小游戏
- **猜数字** - 休闲益智游戏
- **掷骰子** - 随机趣味互动

### 群管理
- 欢迎/退群通知
- 自动签到系统
- 积分排行榜
- 违禁词过滤
- 刷屏检测

### 实用工具
- 点歌播放（本地音乐）
- 天气查询
- 翻译功能
- 定时提醒
- 随机语录

## 技术栈

- **框架**: NoneBot2
- **协议**: OneBot V11
- **AI**: DeepSeek API
- **语音**: pyttsx3
- **GUI**: Tkinter
- **打包**: PyInstaller

## 环境要求

- Python 3.9+
- Windows 操作系统
- LLBot OneBot 客户端

## 快速开始

### 方式一：直接运行（推荐新手）

1. 下载最新版本的 `PengPengQQBot.exe`
2. 双击运行，首次运行会弹出配置界面
3. 填写必要配置信息：
   - 机器人QQ号
   - 自己的QQ号
   - 模型API密钥
   - 模型ID
4. 点击"保存配置并启动"
5. 启动 LLBot 并配置连接地址：`ws://127.0.0.1:8080/onebot/v11/ws`

### 方式二：源码运行

1. 克隆本仓库
```bash
git clone https://github.com/yourusername/qqbot.git
cd qqbot
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量或创建 `.env` 文件
```env
DEEPSEEK_API_KEY=your_api_key
MODEL_ID=deepseek-chat
SELF_QQ=your_bot_qq
ADMIN_QQ=your_qq
```

4. 运行机器人
```bash
python bot.py
```

## 项目结构

```
QQBot/
├── bot.py                 # 主入口文件
├── build_exe.py           # 打包脚本
├── plugins/               # 插件目录
│   ├── ai_chat.py        # AI聊天插件
│   ├── auto_reply.py      # 自动回复插件
│   ├── cultivation_game.py # 修仙游戏插件
│   ├── daily_sign.py      # 签到插件
│   ├── douluo_game.py     # 斗罗游戏插件
│   ├── group_admin_plus.py # 群管理插件
│   ├── points_system.py   # 积分系统插件
│   ├── reminder.py        # 提醒插件
│   └── study_helper.py    # 学习助手插件
├── data/                  # 数据存储目录
├── music/                 # 音乐目录（放置点歌文件）
└── .env                   # 配置文件
```

## 常用指令

### AI聊天
| 指令 | 说明 |
|------|------|
| `@机器人 + 内容` | AI对话 |
| `切换角色 角色名` | 切换AI角色 |
| `清除记忆` | 重置对话 |
| `开启全网搜` | 启用搜索功能 |

### 游戏娱乐
| 指令 | 说明 |
|------|------|
| `成语接龙` | 开始成语接龙 |
| `结束接龙` | 结束接龙游戏 |
| `猜数字` | 开始猜数字游戏 |
| `结束猜数字` | 结束猜数字 |
| `掷骰子` | 掷骰子 |
| `修仙` | 查看修仙状态 |
| `修炼` | 开始修炼 |
| `斗罗` | 查看斗罗状态 |

### 群管理
| 指令 | 说明 |
|------|------|
| `签到` / `每日签到` | 签到 |
| `签到统计` | 查看签到排行 |
| `我的签到` | 查看签到信息 |

### 实用工具
| 指令 | 说明 |
|------|------|
| `点歌 歌名` | 点播歌曲 |
| `点歌列表` | 查看本地歌曲 |
| `天气 城市` | 查询天气 |
| `翻译 内容` | 翻译文本 |
| `提醒我 事项` | 设置提醒 |

## 配置说明

### 配置文件 (.env)

```env
# 环境配置
ENVIRONMENT=prod
HOST=127.0.0.1
PORT=8080

# OneBot 配置
ONEBOT_HTTP_ENABLED=true
ONEBOT_HTTP_HOST=127.0.0.1
ONEBOT_HTTP_PORT=8080
ONEBOT_HTTP_PATH=/onebot/v11

# API配置
DEEPSEEK_API_KEY=your_api_key
MODEL_ID=

# 机器人配置
SELF_QQ=机器人QQ号
ADMIN_QQ=自己QQ号
```

### LLBot 配置

在 LLBot 配置文件中添加：
```json
{
  "ws://127.0.0.1:8080/onebot/v11/ws": {}
}
```

## 常见问题

### Q: 机器人无法启动？
- 检查是否已安装 Python 3.9+
- 确保配置文件中的 API Key 正确

### Q: AI回复显示"请求失败"？
- 检查 API Key 是否有效
- 检查网络连接是否正常

### Q: LLBot 无法连接？
- 确保 LLBot 配置的 WebSocket 地址为 `ws://127.0.0.1:8080/onebot/v11/ws`

## 开发指南

### 添加新插件

1. 在 `plugins/` 目录下创建新的 `.py` 文件
2. 使用 NoneBot2 装饰器注册指令
3. 重启机器人即可生效

### 添加点歌

将 MP3/FLAC 格式的音频文件放入 `music/` 目录即可

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

本项目采用 MIT 许可证

## 致谢

- [NoneBot2](https://github.com/nonebot/nonebot2) - 强大的 QQ 机器人框架
- [OneBot](https://github.com/howmanybots/onebot) - 统一机器人协议
- [DeepSeek](https://deepseek.com/) - AI 大模型支持
