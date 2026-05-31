"""
cultivation_game.py - 修仙游戏插件
支持修炼、突破、任务、排行榜等功能
"""
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.event import MessageEvent
import json
import os
import random
from pathlib import Path
from datetime import datetime, timedelta

CULTIVATION_LEVELS = [
    "凝气期", "筑基期", "结丹期", "元婴期", "化神期",
    "婴变期", "问鼎期", "阴虚境", "阳实境", "窥涅期",
    "净涅期", "碎涅期", "空涅期", "空灵期", "空玄期",
    "空劫期", "踏天九桥", "踏天境"
]

GOD_LEVELS = [
    "凡体", "一星古神", "二星古神", "三星古神", "四星古神",
    "五星古神", "六星古神", "七星古神", "八星古神", "八星王族古神",
    "九星古神", "王族九星古神", "道古", "皇尊", "古祖"
]

SUB_LEVELS = [
    "初期", "初期巅峰", "中期", "中期巅峰", "后期", "后期巅峰", "大圆满"
]

SUB_LEVEL_REQUIREMENTS = [
    100, 150, 200, 300, 400, 500, 800
]

CULTIVATION_MULTIPLIERS = [
    1, 2, 4, 8, 16,
    32, 64, 128, 256, 512,
    1024, 2048, 4096, 8192, 16384,
    32768, 65536, 131072
]

GOD_MULTIPLIERS = [
    1, 3, 6, 12, 24,
    48, 96, 192, 384, 768,
    1536, 3072, 6144, 12288, 24576
]

DAILY_TASKS = [
    {"id": "meditate", "name": "吐纳修行", "reward": 50, "desc": "引天地灵气入体"},
    {"id": "adventure", "name": "域外历练", "reward": 120, "desc": "探索域外星空"},
    {"id": "fight", "name": "斗法切磋", "reward": 100, "desc": "与同道论道斗法"},
    {"id": "meditate_hard", "name": "闭关悟道", "reward": 180, "desc": "闭关感悟天道"},
    {"id": "cultivate", "name": "祭炼法宝", "reward": 80, "desc": "祭炼自身法宝"},
]

SHOP_ITEMS = {
    "pills": {
        "name": "丹药阁",
        "items": [
            {"id": "qi_pill", "name": "聚气丹", "price": 50, "currency": "gold", "effect": "exp", "value": 30, "desc": "快速提升修为"},
            {"id": "yuan_pill", "name": "元灵丹", "price": 150, "currency": "gold", "effect": "exp", "value": 100, "desc": "纯净灵气凝练"},
            {"id": "jing_pill", "name": "精进丹", "price": 300, "currency": "gold", "effect": "exp", "value": 250, "desc": "大幅提升修为"},
            {"id": "jie_pill", "name": "破阶丹", "price": 800, "currency": "gold", "effect": "exp", "value": 600, "desc": "助力突破瓶颈"},
            {"id": "xian_pill", "name": "仙元丹", "price": 50, "currency": "soul_jade", "effect": "exp", "value": 500, "desc": "蕴含仙力的珍贵丹药"},
            {"id": "teng_pill", "name": "腾云丹", "price": 200, "currency": "soul_jade", "effect": "exp", "value": 2000, "desc": "踏天级丹药"},
        ]
    },
    "treasures": {
        "name": "法宝阁",
        "items": [
            {"id": "sword1", "name": "青锋剑", "price": 200, "currency": "gold", "effect": "meditate_bonus", "value": 1.1, "desc": "修炼效率+10%"},
            {"id": "sword2", "name": "紫电剑", "price": 500, "currency": "gold", "effect": "meditate_bonus", "value": 1.2, "desc": "修炼效率+20%"},
            {"id": "armor1", "name": "玄铁甲", "price": 300, "currency": "gold", "effect": "meditate_bonus", "value": 1.15, "desc": "修炼效率+15%"},
            {"id": "ring1", "name": "储物戒指", "price": 1000, "currency": "gold", "effect": "meditate_bonus", "value": 1.3, "desc": "修炼效率+30%"},
            {"id": "fan1", "name": "山河扇", "price": 100, "currency": "soul_jade", "effect": "meditate_bonus", "value": 1.5, "desc": "修炼效率+50%"},
            {"id": "mirror1", "name": "轮回镜", "price": 500, "currency": "soul_jade", "effect": "meditate_bonus", "value": 2.0, "desc": "修炼效率+100%"},
        ]
    },
    "materials": {
        "name": "材料铺",
        "items": [
            {"id": "spirit_stone", "name": "下品灵石", "price": 10, "currency": "gold", "effect": "gold", "value": 5, "desc": "蕴含微弱灵气"},
            {"id": "mid_stone", "name": "中品灵石", "price": 100, "currency": "gold", "effect": "gold", "value": 60, "desc": "蕴含精纯灵气"},
            {"id": "top_stone", "name": "上品灵石", "price": 500, "currency": "gold", "effect": "gold", "value": 350, "desc": "蕴含浓郁灵气"},
            {"id": "best_stone", "name": "极品灵石", "price": 2000, "currency": "gold", "effect": "gold", "value": 1500, "desc": "蕴含磅礴灵气，极为稀有"},
            {"id": "soul_jade_item", "name": "仙玉", "price": 100, "currency": "gold", "effect": "soul_jade", "value": 1, "desc": "仙界通用货币，极为珍贵"},
            {"id": "essence", "name": "天地精华", "price": 500, "currency": "soul_jade", "effect": "exp", "value": 5000, "desc": "蕴含无尽能量"},
        ]
    }
}

class CultivationManager:
    def __init__(self):
        self.players = {}
        self.load_data()
    
    def load_data(self):
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        data_file = data_dir / "cultivation.json"
        
        if data_file.exists():
            with open(data_file, "r", encoding="utf-8") as f:
                self.players = json.load(f)
    
    def save_data(self):
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        data_file = data_dir / "cultivation.json"
        
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(self.players, f, ensure_ascii=False, indent=2)
    
    def get_player(self, user_id):
        user_id = str(user_id)
        if user_id not in self.players:
            self.create_player(user_id)
        return self.players[user_id]
    
    def create_player(self, user_id):
        user_id = str(user_id)
        self.players[user_id] = {
            "name": "初入山门",
            "level": 0,
            "sub_level": 0,
            "exp": 0,
            "gold": 100,      
            "soul_jade": 0,   
            "tasks": {},
            "last_meditate": "",
            "total_meditate": 0,
            "achievements": [],
            "title": "凡人",
            "cultivation_system": ""  
        }
        self.save_data()
    
    def set_cultivation_system(self, user_id, system):
        """选择修炼体系"""
        player = self.get_player(user_id)
        if system not in ["cultivation", "god"]:
            return "无效的修炼体系！"
        if player.get("cultivation_system", "") != "":
            return "修炼体系一旦选定，不可更改！"
        
        player["cultivation_system"] = system
        player["level"] = 0
        player["sub_level"] = 0
        player["exp"] = 0
        
        if system == "cultivation":
            player["title"] = "修真者"
            result = "选择修真之路！踏上逆道修仙之路！"
        else:
            player["title"] = "古神后裔"
            result = "选择古神之路！觉醒古神血脉传承！"
        
        self.save_data()
        return result
    
    def exchange_soul_jade(self, user_id, amount):
        """灵石兑换仙玉（汇率：100灵石 = 1仙玉）"""
        player = self.get_player(user_id)
        gold = player.get("gold", 0)
        soul_jade = player.get("soul_jade", 0)
        
        cost = amount * 100
        
        if gold < cost:
            return f"灵石不足！兑换 {amount} 仙玉需要 {cost} 灵石，你只有 {gold} 灵石。"
        
        player["gold"] -= cost
        player["soul_jade"] += amount
        self.save_data()
        
        return f"成功兑换 {amount} 仙玉！消耗 {cost} 灵石。\n当前灵石：{player['gold']}\n当前仙玉：{player['soul_jade']}"
    
    def exchange_gold(self, user_id, amount):
        """仙玉兑换灵石（汇率：1仙玉 = 80灵石）"""
        player = self.get_player(user_id)
        gold = player.get("gold", 0)
        soul_jade = player.get("soul_jade", 0)
        
        if soul_jade < amount:
            return f"仙玉不足！兑换 {amount} 灵石需要 {amount} 仙玉，你只有 {soul_jade} 仙玉。"
        
        player["soul_jade"] -= amount
        player["gold"] += amount * 80
        self.save_data()
        
        return f"成功兑换 {amount * 80} 灵石！消耗 {amount} 仙玉。\n💰 当前灵石：{player['gold']}\n当前仙玉：{player['soul_jade']}"
    
    def get_shop_items(self):
        """获取商城商品列表"""
        result = "修仙商城 \n\n"
        for category, data in SHOP_ITEMS.items():
            result += f"{data['name']}\n"
            for item in data["items"]:
                currency = "灵石" if item["currency"] == "gold" else "仙玉"
                result += f"  • {item['name']} - {item['price']}{currency} - {item['desc']}\n"
            result += "\n"
        result += "使用「购买 商品名」进行购买\n例如：购买 聚气丹"
        return result
    
    def buy_item(self, user_id, item_name):
        """购买商品"""
        player = self.get_player(user_id)
        gold = player.get("gold", 0)
        soul_jade = player.get("soul_jade", 0)
        
        
        found_item = None
        for category, data in SHOP_ITEMS.items():
            for item in data["items"]:
                if item["name"] == item_name:
                    found_item = item
                    break
            if found_item:
                break
        
        if not found_item:
            return f"未找到商品：{item_name}"
        
        
        price = found_item["price"]
        currency = found_item["currency"]
        
        if currency == "gold":
            if gold < price:
                return f"灵石不足！购买 {item_name} 需要 {price} 灵石，你只有 {gold} 灵石。"
            player["gold"] -= price
        else:
            if soul_jade < price:
                return f"仙玉不足！购买 {item_name} 需要 {price} 仙玉，你只有 {soul_jade} 仙玉。"
            player["soul_jade"] -= price
        
        
        effect = found_item["effect"]
        value = found_item["value"]
        
        if effect == "exp":
            player["exp"] += value
            self.save_data()
            return f"成功购买 {item_name}！获得 {value} 修为！\n当前修为：{player['exp']}"
        
        elif effect == "gold":
            player["gold"] += value
            self.save_data()
            return f"成功购买 {item_name}！获得 {value} 灵石！\n当前灵石：{player['gold']}"
        
        elif effect == "soul_jade":
            player["soul_jade"] += value
            self.save_data()
            return f"成功购买 {item_name}！获得 {value} 仙玉！\n当前仙玉：{player['soul_jade']}"
        
        elif effect == "meditate_bonus":
            player["meditate_bonus"] = player.get("meditate_bonus", 1.0) * value
            self.save_data()
            bonus_percent = (player["meditate_bonus"] - 1) * 100
            return f"成功购买 {item_name}！\n修炼效率提升至 {bonus_percent:.0f}%！"
        
        self.save_data()
        return f"成功购买 {item_name}！"
    
    def meditate(self, user_id):
        """修炼"""
        player = self.get_player(user_id)
        
        if player["cultivation_system"] == "":
            return "❌ 请先选择修炼体系！\n\n请发送「选择体系」查看选项。"
        level = player["level"]
        sub_level = player.get("sub_level", 0)
        system = player["cultivation_system"]
        
        soul_jade_cost = 0
        if system == "cultivation" and level >= 5:
            soul_jade_cost = max(1, (level - 4))  
        
        soul_jade = player.get("soul_jade", 0)
        if soul_jade_cost > 0 and soul_jade < soul_jade_cost:
            return f"❌仙玉不足！当前境界修炼需要 {soul_jade_cost} 仙玉，你只有 {soul_jade} 仙玉。\n💡可通过商城购买或兑换获取仙玉。"
        
        if soul_jade_cost > 0:
            player["soul_jade"] -= soul_jade_cost
        
        base_reward = 20 + level * 15 + sub_level * 5
        bonus = random.randint(0, 15)
        total = base_reward + bonus
        
        player["exp"] += total
        player["total_meditate"] += 1
        player["last_meditate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result = self.check_level_up(user_id)
        self.save_data()
        
        if soul_jade_cost > 0:
            return f"引动天地灵气（消耗 {soul_jade_cost} 仙玉），获得 {total} 修为！{result}"
        else:
            return f"引动天地灵气，获得 {total} 修为！{result}"
    
    def get_requirement(self, level, sub_level, system):
        """获取当前小境界所需修为"""
        if system == "cultivation":
            multiplier = CULTIVATION_MULTIPLIERS[level]
        else:
            multiplier = GOD_MULTIPLIERS[level]
        return SUB_LEVEL_REQUIREMENTS[sub_level] * multiplier
    
    def check_level_up(self, user_id):
        """检查是否突破（支持小境界和两种修炼体系）"""
        player = self.get_player(user_id)
        system = player.get("cultivation_system", "")
        
        if system == "":
            return ""
        
        level = player["level"]
        sub_level = player.get("sub_level", 0)
        exp = player["exp"]
        
        if "sub_level" not in player:
            player["sub_level"] = 0
            sub_level = 0
        
        if system == "cultivation":
            levels = CULTIVATION_LEVELS
            titles = [
                "修真者", "筑基蝼蚁", "结丹小儿", "元婴道友", "化神前辈",
                "婴变老祖", "问鼎大能", "阴虚仙人", "阳实仙王", "窥涅天仙",
                "净涅仙王", "碎涅仙君", "空涅仙帝", "空灵圣尊", "空玄道尊",
                "空劫大天尊", "半步踏天", "踏天超脱"
            ]
        else:
            levels = GOD_LEVELS
            titles = [
                "凡人", "一星古神", "二星古神", "三星古神", "四星古神",
                "五星古神", "六星古神", "七星古神", "八星古神", "八星王族古神",
                "九星古神", "王族九星古神", "道古", "皇尊", "古祖"
            ]
        
        if level < len(levels):
            requirement = self.get_requirement(level, sub_level, system)
            if exp >= requirement:
                player["exp"] -= requirement
                
                if sub_level < len(SUB_LEVELS) - 1:
                    player["sub_level"] += 1
                    old_sub = SUB_LEVELS[sub_level]
                    new_sub = SUB_LEVELS[player["sub_level"]]
                    current_big = levels[level]
                    
                    sub_reward = 10 * (level + 1) * (sub_level + 1)
                    player["gold"] = player.get("gold", 0) + sub_reward
                    
                    if system == "cultivation":
                        return f"\n道基稳固！{current_big}{old_sub} → {current_big}{new_sub}！\n获得 {sub_reward} 灵石！"
                    else:
                        return f"\n古神血脉觉醒！{current_big}{old_sub} → {current_big}{new_sub}！\n获得 {sub_reward} 灵石！"
                else:
                    if level < len(levels) - 1:
                        old_big = levels[level]
                        new_big = levels[level + 1]
                        
                        soul_jade_needed = 0
                        if system == "cultivation" and level == 4:  
                            soul_jade_needed = 100  
                        elif system == "cultivation" and level >= 5:  
                            soul_jade_needed = (level - 4) * 200  
                        
                        soul_jade = player.get("soul_jade", 0)
                        if soul_jade_needed > 0 and soul_jade < soul_jade_needed:
                            return f"\n仙玉不足！突破至{new_big}需要 {soul_jade_needed} 仙玉，你只有 {soul_jade} 仙玉。\n可通过商城购买或兑换获取仙玉。"
                        
                        if soul_jade_needed > 0:
                            player["soul_jade"] -= soul_jade_needed
                        
                        big_reward = 100 * (level + 1) * (level + 1)
                        player["gold"] = player.get("gold", 0) + big_reward
                        
                        player["level"] += 1
                        player["sub_level"] = 0
                        player["title"] = titles[player["level"]]
                        
                        if system == "cultivation":
                            if new_big == "踏天九桥":
                                return f"\n开启踏天九桥试炼！历经九曲三相，争夺成祖资格！\n获得 {big_reward} 灵石！"
                            elif new_big == "踏天境":
                                return f"\n逆道超脱！成就踏天超脱，挣脱轮回束缚！\n获得 {big_reward} 灵石！"
                            elif old_big == "化神期":
                                return f"\n逆道而行！消耗 {soul_jade_needed} 仙玉，化神期 → 婴变期！\n获得 {big_reward} 灵石！"
                            else:
                                return f"\n逆道而行！消耗 {soul_jade_needed} 仙玉，{old_big} → {new_big}！\n获得 {big_reward} 灵石！"
                        else:
                            if new_big == "古祖":
                                return f"\n成就古祖！执掌古神一族，超脱轮回！\n获得 {big_reward} 灵石！"
                            elif new_big == "皇尊":
                                return f"\n登临皇尊！古神之巅，俯瞰众生！\n获得 {big_reward} 灵石！"
                            else:
                                return f"\n古神进阶！{old_big} → {new_big}！\n获得 {big_reward} 灵石！"
        return ""
    
    def do_task(self, user_id, task_id):
        """完成任务"""
        player = self.get_player(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in player["tasks"]:
            player["tasks"][today] = []
        
        if task_id in player["tasks"][today]:
            return "今日已完成该任务"
        
        task = next((t for t in DAILY_TASKS if t["id"] == task_id), None)
        if not task:
            return "任务不存在"
        
        player["tasks"][today].append(task_id)
        player["exp"] += task["reward"]
        
        result = self.check_level_up(user_id)
        self.save_data()
        
        return f"完成「{task['name']}」，获得 {task['reward']} 修为！{result}"
    
    def get_status(self, user_id):
        """获取状态"""
        player = self.get_player(user_id)
        system = player.get("cultivation_system", "")
        
        if system == "":
            return """❌ 尚未选择修炼体系！

请发送「选择体系」来选择你的修炼之路：
1️⃣ 修真之路 - 踏上逆道修仙之路
2️⃣ 古神之路 - 觉醒古神血脉传承"""
        
        level = player["level"]
        sub_level = player.get("sub_level", 0)
        exp = player["exp"]

        if system == "cultivation":
            levels = CULTIVATION_LEVELS
            title_prefix = ""
            title_suffix = "的逆道之路"
            currency_name = "仙玉" if level >= 5 else "灵石"
        else:
            levels = GOD_LEVELS
            title_prefix = ""
            title_suffix = "的古神传承"
            currency_name = "仙玉" if level >= 3 else "灵石"

        if level < len(levels):
            requirement = self.get_requirement(level, sub_level, system)
            progress = (exp / requirement) * 100
        else:
            requirement = "MAX"
            progress = 100

        current_level = levels[level]
        current_sub = SUB_LEVELS[sub_level]
        gold = player.get("gold", 0)
        soul_jade = player.get("soul_jade", 0)

        return f"""{title_prefix} {player['name']} {title_suffix} {title_prefix}

当前境界：{current_level}{current_sub}
称号：{player['title']}
修为：{exp}/{requirement} ({progress:.1f}%)
灵石：{gold}
仙玉：{soul_jade}
累计修炼：{player['total_meditate']} 次
成就：{len(player['achievements'])} 个

{self.get_tasks_status(user_id)}"""
    
    def get_tasks_status(self, user_id):
        """获取任务状态"""
        player = self.get_player(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        completed = player["tasks"].get(today, [])
        
        result = "\n今日任务：\n"
        for task in DAILY_TASKS:
            status = "✅️" if task["id"] in completed else "⬜"
            result += f"{status} {task['name']} - {task['desc']} (+{task['reward']}修为)\n"
        
        return result
    
    def get_rankings(self):
        """获取排行榜"""
        sorted_players = sorted(
            self.players.items(),
            key=lambda x: (x[1]["level"], x[1].get("sub_level", 0), x[1]["exp"]),
            reverse=True
        )
        
        result = " 修炼排行榜 \n\n"
        for i, (uid, player) in enumerate(sorted_players[:10], 1):
            level = player.get("level", 0)
            sub_level = player.get("sub_level", 0)
            system = player.get("cultivation_system", "")
            
            if system == "god" and level < len(GOD_LEVELS):
                big_level = GOD_LEVELS[level]
                icon = "🔱"
            elif system == "cultivation" and level < len(CULTIVATION_LEVELS):
                big_level = CULTIVATION_LEVELS[level]
                icon = "🗡️"
            else:
                big_level = "未选择"
                icon = "❓"
            
            sub_level_name = SUB_LEVELS[sub_level] if sub_level < len(SUB_LEVELS) else ""
            result += f"{i}. {icon} {player['name']} - {big_level}{sub_level_name} - {player['exp']}修为\n"
        
        return result

cultivation_manager = CultivationManager()

cultivation = on_message(priority=5, block=False)
@cultivation.handle()
async def handle_cultivation(bot: Bot, event: MessageEvent):
    if isinstance(event, GroupMessageEvent):
        msg = str(event.message).strip().replace(f"[CQ:at,qq={event.self_id}]", "").strip()
    else:
        msg = str(event.message).strip()
    
    user_id = str(event.user_id)
    
    print(f"[DEBUG cultivation] 收到消息: msg='{msg}', user_id={user_id}")
    
    commands = {
        "修仙": "status",
        "修炼": "meditate",
        "打坐": "meditate",
        "闭关": "meditate",
        "查看状态": "status",
        "排行榜": "rankings",
        "修仙排行榜": "rankings",
        "完成任务": "tasks_list",
        "任务": "tasks_list",
        "选择体系": "select_system",
        "兑换仙玉": "exchange_jade",
        "兑换灵石": "exchange_gold_cmd",
        "商城": "shop",
        "打开商城": "shop",
        "修仙商城": "shop",
    }
    
    if msg in commands:
        action = commands[msg]
        print(f"[DEBUG cultivation] 匹配到命令: action={action}")
        
        if action == "status":
            result = cultivation_manager.get_status(user_id)
            print(f"[DEBUG cultivation] status结果: {result[:100]}...")
            await cultivation.finish(result)
        
        elif action == "meditate":
            result = cultivation_manager.meditate(user_id)
            await cultivation.finish(result)
        
        elif action == "rankings":
            await cultivation.finish(cultivation_manager.get_rankings())
        
        elif action == "tasks_list":
            await cultivation.finish(cultivation_manager.get_tasks_status(user_id))
        
        elif action == "select_system":
            await cultivation.finish("""⚔️ 请选择修炼体系 ⚔️

1️⃣ 修真之路 - 踏上逆道修仙之路，历经凝气、筑基、结丹、元婴、化神等境界，最终踏天超脱
2️⃣ 古神之路 - 觉醒古神血脉传承，从一星古神开始，逐步晋升至古祖之位

请发送「修真之路」选择修真之道，或发送「古神之路」觉醒古神血脉。

注意：修炼体系一旦选定，不可更改！""")
        
        elif action == "exchange_jade":
            await cultivation.finish(""" 灵石兑换仙玉 

汇率：100灵石 = 1仙玉

使用方法：
• 兑换仙玉 数量

例如：兑换仙玉 10（将消耗1000灵石获得10仙玉）""")
        
        elif action == "exchange_gold_cmd":
            await cultivation.finish(""" 仙玉兑换灵石 

汇率：1仙玉 = 80灵石

使用方法：
• 兑换灵石 数量

例如：兑换灵石 800（将消耗10仙玉获得800灵石）

注意：兑换后不可逆！""")
        
        elif action == "shop":
            await cultivation.finish(cultivation_manager.get_shop_items())
    
    if msg == "修真之路":
        result = cultivation_manager.set_cultivation_system(user_id, "cultivation")
        await cultivation.finish(result)
    elif msg == "古神之路":
        result = cultivation_manager.set_cultivation_system(user_id, "god")
        await cultivation.finish(result)
    
    if msg.startswith("兑换仙玉 "):
        amount_str = msg.replace("兑换仙玉", "").strip()
        try:
            amount = int(amount_str)
            if amount <= 0:
                await cultivation.finish("兑换数量必须大于0！")
            result = cultivation_manager.exchange_soul_jade(user_id, amount)
            await cultivation.finish(result)
        except ValueError:
            await cultivation.finish("请输入正确的数量！\n例如：兑换仙玉 10")
    
    if msg.startswith("兑换灵石 "):
        amount_str = msg.replace("兑换灵石", "").strip()
        try:
            amount = int(amount_str)
            if amount <= 0:
                await cultivation.finish("兑换数量必须大于0！")
            result = cultivation_manager.exchange_gold(user_id, amount)
            await cultivation.finish(result)
        except ValueError:
            await cultivation.finish("请输入正确的数量！\n例如：兑换灵石 800")
    
    for task in DAILY_TASKS:
        if msg == f"完成{task['name']}" or msg == task['name']:
            result = cultivation_manager.do_task(user_id, task["id"])
            await cultivation.finish(result)
    
    if msg.startswith("购买 "):
        item_name = msg.replace("购买", "").strip()
        if not item_name:
            await cultivation.finish("请输入要购买的商品名称！\n例如：购买 聚气丹")
        else:
            result = cultivation_manager.buy_item(user_id, item_name)
            await cultivation.finish(result)
    
    return