"""斗罗大陆游戏插件 - 基于《斗罗大陆》修炼体系"""

import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from nonebot import on_message, Bot
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message

DATA_FOLDER = Path("d:/my_qq_bot/data")
DULO_FILE = DATA_FOLDER / "douluo.json"

SOUL_MASTER_LEVELS = [
    "魂士", "魂师", "大魂师", "魂尊", "魂宗", "魂王", "魂帝", "魂圣",
    "魂斗罗", "封号斗罗", "超级斗罗", "极限斗罗"
]

GOD_LEVELS = [
    "神官", "三级神祇", "二级神祇", "一级神祇", "神王"
]

SOUL_RING_COLORS = {
    "white": {"name": "白色", "min_year": 10, "max_year": 99, "color": "⚪"},
    "yellow": {"name": "黄色", "min_year": 100, "max_year": 999, "color": "🟡"},
    "purple": {"name": "紫色", "min_year": 1000, "max_year": 9999, "color": "🟣"},
    "black": {"name": "黑色", "min_year": 10000, "max_year": 99999, "color": "⚫"},
    "red": {"name": "红色", "min_year": 100000, "max_year": 999999, "color": "🔴"},
    "gold": {"name": "金色", "min_year": 1000000, "max_year": 9999999, "color": "🟠"}
}

MARTIAL_SOULS = {
    "blade": {"name": "刀武魂", "type": "器武魂", "desc": "霸道凌厉的刀之武魂"},
    "sword": {"name": "剑武魂", "type": "器武魂", "desc": "君子之剑，刚正不阿"},
    "hammer": {"name": "昊天锤", "type": "器武魂", "desc": "天下第一器武魂，威力无穷"},
    "seven_kill": {"name": "七杀剑", "type": "器武魂", "desc": "剑中霸主，杀伐果断"},
    "tower": {"name": "七宝琉璃塔", "type": "器武魂", "desc": "天下第一辅助武魂"},
    "dragon": {"name": "蓝电霸王龙", "type": "兽武魂", "desc": "顶级兽武魂，强攻无双"},
    "tiger": {"name": "白虎", "type": "兽武魂", "desc": "战神之虎，威猛无比"},
    "rabbit": {"name": "柔骨兔", "type": "兽武魂", "desc": "柔美灵动，变幻莫测"},
    "medusa": {"name": "邪火凤凰", "type": "兽武魂", "desc": "变异武魂，浴火重生"},
    "body": {"name": "本体武魂", "type": "本体武魂", "desc": "以身为武，潜力无穷"}
}

SOUL_BEASTS = [
    {"name": "曼陀罗蛇", "level": 10, "year": 100, "ring_color": "yellow", "reward": 50},
    {"name": "鬼虎", "level": 15, "year": 200, "ring_color": "yellow", "reward": 80},
    {"name": "地穴领主", "level": 20, "year": 500, "ring_color": "purple", "reward": 150},
    {"name": "人面魔蛛", "level": 25, "year": 1000, "ring_color": "purple", "reward": 250},
    {"name": "暗魔邪神虎", "level": 30, "year": 2000, "ring_color": "purple", "reward": 400},
    {"name": "泰坦巨猿", "level": 35, "year": 5000, "ring_color": "black", "reward": 800},
    {"name": "星斗大森林主上", "level": 40, "year": 10000, "ring_color": "black", "reward": 1500},
    {"name": "深海魔鲸王", "level": 45, "year": 50000, "ring_color": "red", "reward": 3000},
    {"name": "天青牛蟒", "level": 48, "year": 80000, "ring_color": "red", "reward": 5000},
    {"name": "十万年柔骨兔", "level": 50, "year": 100000, "ring_color": "red", "reward": 8000}
]

DAILY_TASKS = [
    {"id": "meditate", "name": "冥想修炼", "exp": 20, "desc": "静心冥想，提升魂力"},
    {"id": "hunt", "name": "猎杀魂兽", "exp": 30, "gold": 50, "desc": "前往星斗大森林猎杀魂兽"},
    {"id": "train", "name": "功法修炼", "exp": 25, "desc": "修炼唐门功法，提升实力"}
]

def load_data():
    if DULO_FILE.exists():
        with open(DULO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    with open(DULO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_player(user_id):
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "name": "未觉醒",
            "level": 0,
            "exp": 0,
            "gold": 100,
            "soul_power": 0,
            "martial_soul": None,
            "soul_rings": [],
            "skills": [],
            "tasks": {},
            "last_meditate": None,
            "title": "凡人"
        }
        save_data(data)
    return data[user_id]

def get_level_info(level):
    if level <= 0:
        return {"name": "未觉醒", "exp_max": 100}
    elif level < 100:
        name = SOUL_MASTER_LEVELS[min(level - 1, len(SOUL_MASTER_LEVELS) - 1)]
        exp_max = level * 100
        return {"name": name, "exp_max": exp_max}
    elif level < 110:
        name = GOD_LEVELS[min(level - 100, len(GOD_LEVELS) - 1)]
        exp_max = level * 500
        return {"name": name, "exp_max": exp_max}
    else:
        name = "神王"
        exp_max = 999999
        return {"name": name, "exp_max": exp_max}

def check_level_up(user_id, player):
    level = player["level"]
    exp = player["exp"]
    info = get_level_info(level)
    exp_max = info["exp_max"]

    if level == 0:
        if exp >= 100:
            player["level"] = 1
            player["exp"] = 0
            player["title"] = "魂士"
            return True, "武魂觉醒！恭喜你成为了一级魂士！"
    elif level < 100:
        if exp >= exp_max:
            player["level"] = level + 1
            player["exp"] = 0
            player["title"] = get_level_info(level + 1)["name"]
            return True, f"突破成功！你的境界提升到了 {player['title']}！"
        return False, None
    elif level < 113:
        if exp >= exp_max:
            player["level"] = level + 1
            player["exp"] = 0
            player["title"] = get_level_info(level + 1)["name"]
            return True, f"神位突破！你的境界提升到了 {player['title']}！"
        return False, None
    return False, None

class DouluoGameManager:
    def __init__(self):
        pass

    def awaken_martial_soul(self, user_id, soul_type):
        player = get_player(user_id)
        if player["martial_soul"] is not None:
            return "❌ 你已经觉醒过武魂了！"
        if soul_type not in MARTIAL_SOULS:
            return "❌ 无效的武魂类型！"
        soul = MARTIAL_SOULS[soul_type]
        player["martial_soul"] = soul_type
        player["name"] = soul["name"]
        player["title"] = "觉醒者"
        save_data(load_data())
        return f"""🎉 武魂觉醒成功！
武魂：{soul['name']}
类型：{soul['type']}
描述：{soul['desc']}
💡 现在发送「修炼」开始你的魂师之路！"""

    def meditate(self, user_id):
        player = get_player(user_id)
        if player["martial_soul"] is None:
            return "❌ 你还没有觉醒武魂！请先发送「觉醒武魂」选择你的武魂。"
        exp_gain = random.randint(15, 35)
        player["exp"] += exp_gain
        player["soul_power"] += exp_gain
        player["last_meditate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_up, msg = check_level_up(user_id, player)
        save_data(load_data())
        result = (
            f"🧘 冥想修炼完成！\n"
            f"💠 魂力 +{exp_gain}\n"
            f"📊 当前修为：{player['exp']}/{get_level_info(player['level'])['exp_max']}"
        )
        if level_up:
            result += f"\n\n🎊 {msg}"
        return result

    def hunt_soul_beast(self, user_id):
        player = get_player(user_id)
        if player["martial_soul"] is None:
            return "❌ 你还没有觉醒武魂！"
        if player["level"] < 10:
            return f"❌ 你的实力不足！需要达到魂师（10级）才能猎杀魂兽。\n当前等级：{player['level']}级"
        level = player["level"]
        suitable_beasts = [b for b in SOUL_BEASTS if b["level"] <= level + 10]
        beast = random.choice(suitable_beasts)
        exp_gain = random.randint(beast["year"] // 10, beast["year"] // 5)
        gold_gain = beast["reward"] + random.randint(10, 50)
        player["exp"] += exp_gain
        player["gold"] += gold_gain
        player["soul_power"] += exp_gain // 2
        can_get_ring = len(player["soul_rings"]) < 9 and player["level"] >= 10
        ring_msg = ""
        if can_get_ring and random.random() < 0.3:
            ring_info = SOUL_RING_COLORS[beast["ring_color"]]
            player["soul_rings"].append({
                "color": beast["ring_color"],
                "year": beast["year"],
                "name": f"{ring_info['name']}魂环",
                "skill": f"第{len(player['soul_rings']) + 1}魂技"
            })
            ring_msg = f"\n🌟 获得 {ring_info['color']}{ring_info['name']}！（年限：{beast['year']}年）"
        level_up, msg = check_level_up(user_id, player)
        save_data(load_data())
        result = f"""⚔️ 猎杀魂兽：{beast['name']}
💀 魂兽年限：{beast['year']}年
💠 魂力 +{exp_gain}
💰 魂币 +{gold_gain}{ring_msg}"""
        if level_up:
            result += f"\n\n🎊 {msg}"
        return result

    def train唐门功法(self, user_id):
        player = get_player(user_id)
        if player["martial_soul"] is None:
            return "❌ 你还没有觉醒武魂！"
        exp_gain = random.randint(20, 40)
        player["exp"] += exp_gain
        player["soul_power"] += exp_gain
        level_up, msg = check_level_up(user_id, player)
        save_data(load_data())
        result = f"""📜 功法修炼完成！
💠 魂力 +{exp_gain}
📊 当前修为：{player['exp']}/{get_level_info(player['level'])['exp_max']}"""
        if level_up:
            result += f"\n\n🎊 {msg}"
        return result

    def get_status(self, user_id):
        player = get_player(user_id)
        if player["martial_soul"] is None:
            return """📿 斗罗大陆 - 魂师状态
🆔 状态：未觉醒武魂
💡 发送「觉醒武魂」开始你的魂师之路！"""
        level_info = get_level_info(player["level"])
        martial_soul = MARTIAL_SOULS.get(player["martial_soul"], {"name": "未知", "type": "未知"})
        rings_info = ""
        if player["soul_rings"]:
            rings = [f"{SOUL_RING_COLORS[r['color']]['color']}{r['name']}" for r in player["soul_rings"]]
            rings_info = "\n".join([f"  {i+1}. {r}" for i, r in enumerate(rings)])
        else:
            rings_info = "  暂无魂环"
        return f"""📿 斗罗大陆 - 魂师状态
━━━━━━━━━━━━━━━━━━━━
🆔 名称：{player['name']}
🏷️ 称号：{player['title']}
💠 等级：{player['level']}级 ({level_info['name']})
📊 修为：{player['exp']}/{level_info['exp_max']}
⚡ 魂力：{player['soul_power']}
💰 魂币：{player['gold']}
━━━━━━━━━━━━━━━━━━━━
🔥 武魂：{martial_soul['name']}
📦 类型：{martial_soul['type']}
━━━━━━━━━━━━━━━━━━━━
💍 魂环：
{rings_info}
━━━━━━━━━━━━━━━━━━━━
💡 发送「修炼」「猎杀」「功法」提升实力！"""

    def get_martial_souls_list(self):
        msg = "🔥 可觉醒武魂列表：\n\n"
        for key, soul in MARTIAL_SOULS.items():
            msg += f"📦 {soul['name']}（{soul['type']}）\n   {soul['desc']}\n"
        msg += "\n💡 使用「觉醒 武魂名」觉醒，如：觉醒 昊天锤"
        return msg

    def get_help(self):
        return """📜 斗罗大陆 - 指令帮助

━━━━ 基础指令 ━━━━
「斗罗」- 查看状态
「修炼」- 冥想修炼
「猎杀」- 猎杀魂兽
「功法」- 修炼唐门功法

━━━━ 武魂系统 ━━━━
「觉醒武魂」- 查看可觉醒武魂
「觉醒 XXX」- 觉醒指定武魂

━━━━ 日常任务 ━━━━
「完成冥想」「完成猎杀」「完成功法」

━━━━ 其他 ━━━━
「斗罗大陆」- 查看帮助
「斗罗大陆 排行榜」- 查看等级排行

💡 修炼体系：
凡人 → 魂士(1级) → ... → 封号斗罗(99级) → 神官(100级) → 神王
"""

douluo_game = on_message(priority=5, block=False)
douluo_manager = DouluoGameManager()

@douluo_game.handle()
async def handle_douluo(bot: Bot, event: MessageEvent):
    user_id = str(event.user_id)
    msg = str(event.message).strip()

    if isinstance(event, GroupMessageEvent):
        raw_msg = str(event.message).strip()
        msg = raw_msg.replace(f"[CQ:at,qq={event.self_id}]", "").strip()

    if msg == "斗罗" or msg == "斗罗大陆":
        result = douluo_manager.get_status(user_id)
        await douluo_game.finish(result)
    elif msg == "斗罗大陆帮助" or msg == "斗罗帮助":
        result = douluo_manager.get_help()
        await douluo_game.finish(result)
    elif msg == "觉醒武魂":
        result = douluo_manager.get_martial_souls_list()
        await douluo_game.finish(result)
    elif msg.startswith("觉醒 "):
        soul_type = msg.replace("觉醒", "").strip()
        soul_map = {
            "刀": "blade", "刀武魂": "blade",
            "剑": "sword", "剑武魂": "sword",
            "昊天锤": "hammer", "锤": "hammer",
            "七杀剑": "seven_kill", "杀剑": "seven_kill",
            "七宝琉璃塔": "tower", "琉璃塔": "tower",
            "蓝电霸王龙": "dragon", "霸王龙": "dragon",
            "白虎": "tiger", "虎": "tiger",
            "柔骨兔": "rabbit", "兔": "rabbit",
            "邪火凤凰": "medusa", "凤凰": "medusa",
            "本体武魂": "body", "本体": "body"
        }
        soul_id = soul_map.get(soul_type, soul_type)
        result = douluo_manager.awaken_martial_soul(user_id, soul_id)
        await douluo_game.finish(result)
    elif msg == "修炼" or msg == "冥想" or msg == "打坐":
        result = douluo_manager.meditate(user_id)
        await douluo_game.finish(result)
    elif msg == "猎杀" or msg == "猎杀魂兽":
        result = douluo_manager.hunt_soul_beast(user_id)
        await douluo_game.finish(result)
    elif msg == "功法" or msg == "唐门功法" or msg == "功法修炼":
        result = douluo_manager.train唐门功法(user_id)
        await douluo_game.finish(result)
    elif msg == "完成冥想" or msg == "冥想修炼":
        result = douluo_manager.meditate(user_id)
        await douluo_game.finish(result)
    elif msg == "完成猎杀" or msg == "猎杀魂兽":
        result = douluo_manager.hunt_soul_beast(user_id)
        await douluo_game.finish(result)
    elif msg == "完成功法" or msg == "功法修炼":
        result = douluo_manager.train唐门功法(user_id)
        await douluo_game.finish(result)
    elif msg == "排行榜" or msg == "斗罗排行榜":
        data = load_data()
        sorted_players = sorted(data.items(), key=lambda x: x[1]["level"], reverse=True)[:10]
        if not sorted_players:
            await douluo_game.finish("📊 暂无排行榜数据！")
        result = "🏆 斗罗大陆 - 等级排行榜\n━━━━━━━━━━━━━━━━━━━━\n"
        for i, (uid, p) in enumerate(sorted_players, 1):
            title = p.get("title", "凡人")
            level = p.get("level", 0)
            result += f"{i}. {p['name']} - {title}（{level}级）\n"
        await douluo_game.finish(result)

    return