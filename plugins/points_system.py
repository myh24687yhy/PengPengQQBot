"""
points_system.py - 积分系统插件
支持积分获取、消费、排行、商城
"""
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
import random
import json
import pathlib
import time
from typing import Dict, List

def load_json(filename, default=None):
    """加载JSON文件"""
    data_dir = pathlib.Path(__file__).parent.parent / "data"
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
    data_dir = pathlib.Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / filename
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存{filename}失败: {e}")
        return False

class RateLimiter:
    """简单的频率限制器"""
    def __init__(self):
        self.records: Dict[str, List[float]] = {}
    
    def check(self, key: str, max_times: int = 5, time_window: int = 60) -> bool:
        now = time.time()
        if key not in self.records:
            self.records[key] = []
        self.records[key] = [t for t in self.records[key] if now - t < time_window]
        if len(self.records[key]) >= max_times:
            return False
        self.records[key].append(now)
        return True

rate_limiter = RateLimiter()

POINTS_FILE = "points_system.json"

POINTS_RULES = {
    "chat": (1, 3),
    "game_win": (5, 10),
    "daily_sign": 10,
}

POINTS_SHOP = {
    "头衔称号": {"price": 100, "description": "获得特殊群头衔称号"},
    "颜色昵称": {"price": 200, "description": "获得彩色昵称（24小时）"},
    "专属表情包": {"price": 50, "description": "解锁专属表情包"},
    "VIP特权": {"price": 500, "description": "获得VIP特权3天"}
}

class PointsManager:
    def __init__(self):
        self.data = load_json(POINTS_FILE, {"users": {}, "shop_logs": []})
    
    def add_points(self, user_id: str, points: int, reason: str = "") -> int:
        """添加积分"""
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {"points": 0, "total_earned": 0, "total_spent": 0, "history": []}
        
        user_data = self.data["users"][user_id]
        user_data["points"] += points
        user_data["total_earned"] += points
        
        if reason:
            user_data["history"].append({
                "type": "earn",
                "points": points,
                "reason": reason,
                "time": str(__import__('datetime').datetime.now())
            })
        
        self._save()
        return user_data["points"]
    
    def spend_points(self, user_id: str, points: int, item: str) -> bool:
        """消费积分"""
        if user_id not in self.data["users"]:
            return False
        
        user_data = self.data["users"][user_id]
        if user_data["points"] < points:
            return False
        
        user_data["points"] -= points
        user_data["total_spent"] += points
        user_data["history"].append({
            "type": "spend",
            "points": points,
            "reason": f"购买{item}",
            "time": str(__import__('datetime').datetime.now())
        })
        
        self._save()
        return True
    
    def get_points(self, user_id: str) -> int:
        """获取积分"""
        if user_id not in self.data["users"]:
            return 0
        return self.data["users"][user_id]["points"]
    
    def get_rank(self, top_n: int = 10) -> list:
        """获取积分排行"""
        users = []
        for uid, data in self.data["users"].items():
            users.append((uid, data["points"], data["total_earned"]))
        
        users.sort(key=lambda x: x[1], reverse=True)
        return users[:top_n]
    
    def _save(self):
        """保存数据"""
        save_json(POINTS_FILE, self.data)

points_manager = PointsManager()

points = on_message(priority=15, block=False)
@points.handle()
async def handle_points(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    user_id = str(event.user_id)
    
    if msg in ["积分", "我的积分"]:
        user_points = points_manager.get_points(user_id)
        rank = points_manager.get_rank()
        
        reply = f"⭐ 你的积分：{user_points}\n"
        
        for i, (uid, pts, _) in enumerate(rank, 1):
            if uid == user_id:
                reply += f"📊 积分排行：第{i}名\n"
                break
        
        await points.finish(reply)
    
    elif msg in ["积分排行", "积分榜"]:
        rank = points_manager.get_rank()
        
        reply = "📊 积分排行榜：\n"
        for i, (uid, pts, earned) in enumerate(rank, 1):
            crown = ["👑", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            reply += f"{crown} {uid}: {pts}分 (总赚{earned}分)\n"
        
        if not rank:
            reply = "还没有人获得积分哦～"
        
        await points.finish(reply)
    
    elif msg in ["积分商城", "商城"]:
        reply = "🏪 积分商城：\n"
        for item, info in POINTS_SHOP.items():
            reply += f"• {item}: {info['price']}积分 - {info['description']}\n"
        reply += "\n使用方法：购买 商品名"
        
        await points.finish(reply)
    
    elif msg.startswith("购买"):
        item = msg.replace("购买", "").strip()
        
        if item not in POINTS_SHOP:
            await points.finish(f"❌ 商品不存在！\n发送「商城」查看可用商品")
        
        if not rate_limiter.check(f"buy_{user_id}", max_times=3, time_window=60):
            await points.finish("购买太频繁了，请60秒后再试～")
        
        price = POINTS_SHOP[item]["price"]
        success = points_manager.spend_points(user_id, price, item)
        
        if success:
            await points.finish(f"✅ 成功购买「{item}」！\n消耗：{price}积分\n剩余：{points_manager.get_points(user_id)}积分")
        else:
            await points.finish(f"❌ 积分不足！\n需要：{price}积分\n当前：{points_manager.get_points(user_id)}积分")
    
    elif msg.startswith("赠送积分"):
        parts = msg.split()
        if len(parts) < 3:
            await points.finish("使用方法：赠送积分 @用户 数量")
        
        await points.finish("此功能开发中...")