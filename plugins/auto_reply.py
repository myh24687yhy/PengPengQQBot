"""
auto_reply.py - 核心功能插件
包含：欢迎/退群、点歌、小游戏、天气、表情包等功能
"""
import nonebot.adapters.onebot.v11
from nonebot import on_message, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, GroupIncreaseNoticeEvent, GroupDecreaseNoticeEvent
import requests
import time
import re
import os
import random
import json
from datetime import datetime, date
from pathlib import Path

SELF_QQ = int(os.getenv("SELF_QQ", ""))
ADMIN_QQ = int(os.getenv("ADMIN_QQ", ""))

BASE_DIR = Path(__file__).parent.parent
MUSIC_FOLDER = BASE_DIR / "music"
DATA_FOLDER = BASE_DIR / "data"

MUSIC_FOLDER.mkdir(parents=True, exist_ok=True)
DATA_FOLDER.mkdir(parents=True, exist_ok=True)

SIGN_FILE = DATA_FOLDER / "sign.json"
IDIOM_FILE = DATA_FOLDER / "idioms.json"
QUOTE_FILE = DATA_FOLDER / "quotes.json"

BAD_WORDS = ["训练场死全家"]
SING_TRIGGER = "点歌"

def init_data_file(file_path, default_data):
    """初始化数据文件"""
    if not file_path.exists():
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

def load_json(file_path):
    """安全加载JSON"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file_path, data):
    """安全保存JSON"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_msg(event):
    """提取纯文本消息"""
    raw_msg = str(event.message).strip()
    return raw_msg.replace(f"[CQ:at,qq={event.self_id}]", "").strip()

init_data_file(SIGN_FILE, {})
init_data_file(IDIOM_FILE, {"current_idiom": "", "players": [], "history": []})
init_data_file(QUOTE_FILE, {"quotes": ["人生如逆旅，我亦是行人。", "且将新火试新茶，诗酒趁年华。"]})

welcome = on_notice()
@welcome.handle()
async def handle_welcome(bot: Bot, event: GroupIncreaseNoticeEvent):
    if event.user_id == SELF_QQ:
        return
    
    welcome_msg = (
        f"欢迎新朋友加入本群！\n"
        "我是机器人，多功能AI助手\n"
        "指令菜单↓\n"
        "@我聊天 | 点歌 歌名 | 掷骰子\n"
        "成语接龙 | 猜数字 | 天气 城市\n"
        "表情包 | 群签到 | 随机语录\n"
        "翻译 内容 | 点歌列表 | 切换角色"
    )
    await bot.send_group_msg(group_id=event.group_id, message=welcome_msg)

leave = on_notice()
@leave.handle()
async def handle_leave(bot: Bot, event: GroupDecreaseNoticeEvent):
    if event.user_id == SELF_QQ:
        return
    
    if event.user_id == event.operator_id:
        msg = f"{event.user_id} 默默离开了群聊"
    else:
        msg = f"{event.user_id} 被管理员请出了群聊"
    
    try:
        await bot.send_group_msg(group_id=event.group_id, message=msg)
    except Exception as e:
        print(f"退群提示错误: {e}")

class MusicPlayer:
    """音乐播放器"""
    def __init__(self):
        self.cache = {}
        self.last_update = 0
    
    def get_songs(self):
        """获取歌曲列表（带缓存）"""
        now = time.time()
        if now - self.last_update < 300:
            return list(self.cache.values())
        
        self.cache = {}
        for f in MUSIC_FOLDER.iterdir():
            if f.suffix.lower() in ['.mp3', '.flac']:
                self.cache[f.stem.lower()] = f
        
        self.last_update = now
        return list(self.cache.values())
    
    def find_song(self, name):
        """查找歌曲"""
        name_lower = name.lower()
        for song_name, path in self.cache.items():
            if name_lower in song_name:
                return path
        return None

music_player = MusicPlayer()

sing = on_message(priority=1, block=False)
@sing.handle()
async def handle_sing(bot: Bot, event):
    if isinstance(event, GroupMessageEvent):
        pure_msg = extract_msg(event)
    else:
        pure_msg = str(event.message).strip()
    
    if pure_msg == "点歌列表":
        songs = music_player.get_songs()
        if not songs:
            await sing.finish("本地暂无任何歌曲！")
        
        song_names = [f.stem for f in songs]
        song_list = "\n".join([f"{name}" for name in song_names])
        await bot.send(event, f"本地可播放歌曲列表：\n{song_list}")
        return
    
    
    if not pure_msg.startswith(SING_TRIGGER):
        return
    
    song_name = pure_msg.replace(SING_TRIGGER, "").strip()
    if not song_name:
        await sing.finish("使用方法：点歌 歌曲名\n如：点歌 晴天")
    
    try:
        song_file = music_player.find_song(song_name)
        if not song_file:
            songs = music_player.get_songs()
            song_names = [f.stem for f in songs]
            song_list = "、".join(song_names) if song_names else "暂无"
            await sing.finish(f"未找到歌曲「{song_name}」\n可用歌曲：{song_list}")
        
        abs_path = str(song_file.absolute()).replace("\\", "/")
        song_file_url = f"file:///{abs_path}"
        voice = nonebot.adapters.onebot.v11.MessageSegment.record(song_file_url)
        
        await bot.send(event, f"正在播放：{song_name}")
        await bot.send(event, voice)
        
    except Exception as e:
        await sing.finish(f"播放失败：{str(e)}")

ban_msg = on_message(priority=2, block=False)
@ban_msg.handle()
async def handle_ban_msg(bot: Bot, event: GroupMessageEvent):
    txt = str(event.message).strip()
    for w in BAD_WORDS:
        if w in txt:
            try:
                await bot.delete_msg(message_id=event.message_id)
            except Exception as e:
                print(f"违禁词检测错误: {e}")
            return

msg_records = {}
spam = on_message(priority=3, block=False)
@spam.handle()
async def handle_spam(bot: Bot, event: GroupMessageEvent):
    user = event.user_id
    group = event.group_id
    msg_id = event.message_id
    now = time.time()
    key = f"{group}_{user}"
    
    if key not in msg_records:
        msg_records[key] = {"times": [], "msg_ids": []}
    
    valid_indices = [i for i, t in enumerate(msg_records[key]["times"]) if now - t < 10]
    msg_records[key]["times"] = [msg_records[key]["times"][i] for i in valid_indices]
    msg_records[key]["msg_ids"] = [msg_records[key]["msg_ids"][i] for i in valid_indices]
    
    msg_records[key]["times"].append(now)
    msg_records[key]["msg_ids"].append(msg_id)
    
    if len(msg_records[key]["times"]) >= 6:
        try:
            for m_id in msg_records[key]["msg_ids"]:
                try:
                    await bot.delete_msg(message_id=m_id)
                except:
                    pass
            await bot.send(event, f"检测到刷屏行为，消息已被删除")
            msg_records.pop(key, None)
        except Exception as e:
            print(f"刷屏处理失败：{e}")

idiom_game = on_message(priority=4, block=False)
@idiom_game.handle()
async def handle_idiom_game(bot: Bot, event: GroupMessageEvent):
    pure_msg = extract_msg(event)
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    idiom_data = load_json(IDIOM_FILE)
    
    if pure_msg == "成语接龙":
        idiom_list = ["一帆风顺", "二龙戏珠", "三阳开泰", "四季平安", "五福临门", "六六大顺", "七星高照", "八方来财"]
        start_idiom = random.choice(idiom_list)
        idiom_data["current_idiom"] = start_idiom
        idiom_data["players"] = [user_id]
        save_json(IDIOM_FILE, idiom_data)
        await bot.send(event, f"成语接龙开始！\n我出：{start_idiom}\n接最后一个字（同音亦可）")
        return
    
    if pure_msg == "结束接龙":
        idiom_data["current_idiom"] = ""
        idiom_data["players"] = []
        save_json(IDIOM_FILE, idiom_data)
        await bot.send(event, "成语接龙结束！")
        return
    
    if idiom_data["current_idiom"] and pure_msg not in ["成语接龙", "结束接龙"]:
        last_char = idiom_data["current_idiom"][-1]
        
        if pure_msg[0] == last_char:
            used_idioms = [idiom_data["current_idiom"]] + [h.get("idiom", "") for h in idiom_data.get("history", [])]
            if pure_msg in used_idioms:
                await bot.send(event, f"成语「{pure_msg}」已使用过！")
                return
            
            idiom_data["current_idiom"] = pure_msg
            idiom_data["players"].append(user_id)
            save_json(IDIOM_FILE, idiom_data)
            await bot.send(event, f"接得好！「{pure_msg}」\n下一个接「{pure_msg[-1]}」")
        else:
            await bot.send(event, f"接龙错误！要用「{last_char}」开头哦～")

guess_game = {}
guess = on_message(priority=5, block=False)
@guess.handle()
async def handle_guess(bot: Bot, event: GroupMessageEvent):
    pure_msg = extract_msg(event)
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    if pure_msg == "猜数字":
        target = random.randint(1, 100)
        guess_game[group_id] = {"target": target, "times": 0, "players": {}}
        await bot.send(event, "猜数字游戏开始！我想了一个1-100之间的数字，快来猜猜～")
        return
    
    if pure_msg == "结束猜数字":
        if group_id in guess_game:
            target = guess_game[group_id]["target"]
            await bot.send(event, f"游戏结束！答案是：{target}")
            del guess_game[group_id]
        else:
            await bot.send(event, "还没开始猜数字游戏呢～")
        return
    
    if group_id in guess_game and pure_msg.isdigit():
        num = int(pure_msg)
        target = guess_game[group_id]["target"]
        guess_game[group_id]["times"] += 1
        guess_game[group_id]["players"][user_id] = guess_game[group_id]["players"].get(user_id, 0) + 1
        
        if num < target:
            await bot.send(event, f"猜小啦！再试试～（已猜{guess_game[group_id]['times']}次）")
        elif num > target:
            await bot.send(event, f"猜大啦！再试试～（已猜{guess_game[group_id]['times']}次）")
        else:
            await bot.send(event, f"恭喜猜对了！答案是{target}～\n共猜了{guess_game[group_id]['times']}次")
            del guess_game[group_id]

weather = on_message(priority=6, block=False)
@weather.handle()
async def handle_weather(bot: Bot, event):
    if isinstance(event, GroupMessageEvent):
        pure_msg = extract_msg(event)
    else:
        pure_msg = str(event.message).strip()
    
    if not pure_msg.startswith("天气"):
        return
    
    city = pure_msg.replace("天气", "").strip()
    if not city:
        await bot.send(event, "使用方法：天气 城市名\n如：天气 北京")
        return
    
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "curl/7.68.0"})
        
        if resp.status_code != 200:
            await bot.send(event, f"未找到「{city}」的天气信息～")
            return
        
        data = resp.json()
        current = data["current_condition"][0]
        
        weather_desc = current["lang_zh"][0]["value"] if "lang_zh" in current else current["weatherDesc"][0]["value"]
        temp = current["temp_C"]
        humidity = current["humidity"]
        
        reply = f"{city} 实时天气：\n天气：{weather_desc}\n温度：{temp}°C\n湿度：{humidity}%"
        await bot.send(event, reply)
        
    except Exception as e:
        print(f"天气查询错误: {e}")
        await bot.send(event, f"天气查询失败：{str(e)}")

emoji = on_message(priority=7, block=False)
@emoji.handle()
async def handle_emoji(bot: Bot, event):
    if isinstance(event, GroupMessageEvent):
        pure_msg = extract_msg(event)
    else:
        pure_msg = str(event.message).strip()
    
    if pure_msg in ["表情包", "来个表情包", "沙雕图"]:
        try:
            resp = requests.get("https://api.ixiaowai.cn/api/api.php", timeout=10)
            img_msg = nonebot.adapters.onebot.v11.MessageSegment.image(resp.url)
            await bot.send(event, img_msg)
        except Exception as e:
            print(f"表情包错误: {e}")
            await bot.send(event, "表情包离家出走了，稍后再试吧～")

sign = on_message(priority=8, block=False)
@sign.handle()
async def handle_sign(bot: Bot, event: GroupMessageEvent):
    pure_msg = extract_msg(event)
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    today = str(date.today())
    
    if pure_msg == "群签到":
        sign_data = load_json(SIGN_FILE)
        
        if group_id not in sign_data:
            sign_data[group_id] = {}
        if today not in sign_data[group_id]:
            sign_data[group_id][today] = []
        
        if user_id in sign_data[group_id][today]:
            await bot.send(event, f"@{user_id} 今日已签到！")
        else:
            sign_data[group_id][today].append(user_id)
            save_json(SIGN_FILE, sign_data)
            sign_count = len(sign_data[group_id][today])
            await bot.send(event, f"@{user_id} 签到成功！\n今日本群签到人数：{sign_count}")
    
    if pure_msg == "签到统计":
        sign_data = load_json(SIGN_FILE)
        
        if group_id not in sign_data or today not in sign_data[group_id]:
            await bot.send(event, "今日本群暂无签到记录～")
        else:
            sign_list = sign_data[group_id][today]
            sign_count = len(sign_list)
            reply = f"今日本群签到统计：\n总人数：{sign_count}\n签到列表：\n"
            reply += "\n".join([f"👉 @{uid}" for uid in sign_list[:10]])
            if sign_count > 10:
                reply += f"\n...还有{sign_count - 10}人"
            await bot.send(event, reply)

quote = on_message(priority=9, block=False)
@quote.handle()
async def handle_quote(bot: Bot, event):
    if isinstance(event, GroupMessageEvent):
        pure_msg = extract_msg(event)
    else:
        pure_msg = str(event.message).strip()
    
    if pure_msg == "随机语录":
        quote_data = load_json(QUOTE_FILE)
        if quote_data.get("quotes"):
            random_quote = random.choice(quote_data["quotes"])
            await bot.send(event, f"「{random_quote}」")
        else:
            await bot.send(event, "语录库空空如也～")
    
    if pure_msg.startswith("添加语录"):
        new_quote = pure_msg.replace("添加语录", "").strip()
        if not new_quote:
            await bot.send(event, "使用方法：添加语录 内容")
            return
        
        quote_data = load_json(QUOTE_FILE)
        quote_data.setdefault("quotes", []).append(new_quote)
        save_json(QUOTE_FILE, quote_data)
        await bot.send(event, f"语录添加成功！")

dice = on_message(priority=11, block=False)
@dice.handle()
async def handle_dice(bot: Bot, event):
    if isinstance(event, GroupMessageEvent):
        pure_msg = extract_msg(event)
    else:
        pure_msg = str(event.message).strip()
    
    if pure_msg in ["掷骰子", "骰子", "摇骰子"]:
        num = random.randint(1, 6)
        dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][num-1]
        await bot.send(event, f"你掷出了：{dice_emoji}（{num}点）")

translate = on_message(priority=12, block=False)
@translate.handle()
async def handle_translate(bot: Bot, event):
    if isinstance(event, GroupMessageEvent):
        pure_msg = extract_msg(event)
    else:
        pure_msg = str(event.message).strip()
    
    if not pure_msg.startswith("翻译"):
        return
    
    content = pure_msg.replace("翻译", "").strip()
    if not content:
        await bot.send(event, "使用方法：\n翻译 内容\n翻译 内容 目标语言\n例：翻译 你好 英文")
        return
    
    LANG_MAP = {
        "英文": "英语", "英语": "英语",
        "中文": "中文", "汉语": "中文",
        "日文": "日语", "日语": "日语",
        "韩文": "韩语", "韩语": "韩语",
        "法文": "法语", "法语": "法语",
        "德语": "德语", "俄语": "俄语"
    }
    
    target_lang = "中文"
    text = content
    
    for lang_name, lang_full in LANG_MAP.items():
        if content.endswith(lang_name):
            text = content.replace(lang_name, "").strip()
            target_lang = lang_full
            break
    
    try:
        
        API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-9952a92ad39842dda883fd792027fecc")
        
        messages = [
            {"role": "system", "content": f"你是专业翻译器，将文本翻译成{target_lang}，只输出翻译结果"},
            {"role": "user", "content": text}
        ]
        
        resp = requests.post(
            url="https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.2
            },
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        result = data["choices"][0]["message"]["content"].strip()
        
        await bot.send(event, f"翻译结果（{target_lang}）：\n{result}")
        
    except Exception as e:
        print(f"翻译错误: {e}")
        await bot.send(event, f"翻译失败：{str(e)}")