"""
daily_sign.py - 每日签到插件
支持签到、补签、签到排行、连续签到奖励
"""
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from datetime import date, datetime, timedelta
import random
from pathlib import Path
import json

def load_json(filename, default=None):
    """加载JSON文件"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / filename
    
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception as e:
        print(f"加载{filename}失败: {e}")
        return default if default is not None else {}

def save_json(filename, data):
    """保存JSON文件"""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / filename
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存{filename}失败: {e}")
        return False

SIGN_FILE = "daily_sign.json"

def init_sign_data():
    return {
        "users": {},
        "groups": {}
    }

CONTINUOUS_REWARDS = {
    1: "获得1点经验",
    3: "获得额外5点经验", 
    7: "获得特殊称号「签到达人」",
    15: "获得「坚持不懈」勋章",
    30: "获得「月度全勤」成就"
}

sign = on_message(priority=8, block=False)
@sign.handle()
async def handle_sign(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    today = str(date.today())
    
    if msg in ["签到", "每日签到", "群签到"]:
        data = load_json(SIGN_FILE, init_sign_data())
        
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "total_signs": 0,
                "continuous_signs": 0,
                "last_sign_date": "",
                "sign_history": [],
                "experience": 0
            }
        
        user_data = data["users"][user_id]
        
        if today in user_data["sign_history"]:
            await sign.finish(f"你今天已经签到过了哦！\n连续签到：{user_data['continuous_signs']}天")
        
        yesterday = str(date.today() - timedelta(days=1))
        if user_data["last_sign_date"] == yesterday:
            user_data["continuous_signs"] += 1
        else:
            user_data["continuous_signs"] = 1
        
        user_data["total_signs"] += 1
        user_data["last_sign_date"] = today
        user_data["sign_history"].append(today)
        user_data["experience"] += 10 + user_data["continuous_signs"] * 2
        
        reward_msg = ""
        for days, reward in CONTINUOUS_REWARDS.items():
            if user_data["continuous_signs"] == days:
                reward_msg = f"\n🎁 连续签到{days}天奖励：{reward}"
                user_data["experience"] += 5 * days
                break
        
        if group_id not in data["groups"]:
            data["groups"][group_id] = {}
        if today not in data["groups"][group_id]:
            data["groups"][group_id][today] = []
        
        if user_id not in data["groups"][group_id][today]:
            data["groups"][group_id][today].append(user_id)
        
        save_json(SIGN_FILE, data)
        
        sign_count = len(data["groups"][group_id][today])
        
        msg = (
            f"签到成功！\n"
            f"总签到：{user_data['total_signs']}天\n"
            f"连续签到：{user_data['continuous_signs']}天\n"
            f"当前经验：{user_data['experience']}\n"
            f"今日签到人数：{sign_count}"
            f"{reward_msg}"
        )
        
        await sign.finish(msg)
    
    elif msg in ["签到统计", "签到排行"]:
        data = load_json(SIGN_FILE, init_sign_data())
        
        if group_id not in data["groups"] or today not in data["groups"][group_id]:
            await sign.finish("今天还没有人签到哦～")
        
        sign_list = data["groups"][group_id][today]
        
        reply = f"今日签到统计：\n"
        reply += f"签到人数：{len(sign_list)}人\n"
        reply += f"日期：{today}\n"
        reply += f"签到列表：\n"
        
        for i, uid in enumerate(sign_list[:10], 1):
            user_signs = data["users"].get(uid, {}).get("continuous_signs", 0)
            reply += f"{i}. {uid} (连续{user_signs}天)\n"
        
        if len(sign_list) > 10:
            reply += f"...还有{len(sign_list) - 10}位小伙伴"
        
        await sign.finish(reply)
    
    elif msg in ["我的签到", "签到信息"]:
        data = load_json(SIGN_FILE, init_sign_data())
        
        if user_id not in data["users"]:
            await sign.finish("你还没有签到过哦～发送「签到」开始吧！")
        
        user_data = data["users"][user_id]
        
        info = (
            f"你的签到数据：\n"
            f"总签到：{user_data['total_signs']}天\n"
            f"连续签到：{user_data['continuous_signs']}天\n"
            f"总经验：{user_data['experience']}\n"
            f"最后签到：{user_data['last_sign_date']}"
        )
        
        await sign.finish(info)