"""
reminder.py - 定时提醒插件
支持定时提醒、倒计时、纪念日
"""
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path

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

REMINDER_FILE = "reminders.json"

class ReminderManager:
    def __init__(self):
        self.reminders = load_json(REMINDER_FILE, {"reminders": []})
        self.running_tasks = {}
    
    def add_reminder(self, user_id: str, group_id: str, reminder_time: str, content: str, repeat: str = "once"):
        """添加提醒"""
        reminder = {
            "id": len(self.reminders["reminders"]) + 1,
            "user_id": user_id,
            "group_id": group_id,
            "time": reminder_time,
            "content": content,
            "repeat": repeat,
            "active": True,
            "created": str(datetime.now())
        }
        
        self.reminders["reminders"].append(reminder)
        self._save()
        return reminder["id"]
    
    def get_user_reminders(self, user_id: str) -> list:
        """获取用户的所有提醒"""
        return [r for r in self.reminders["reminders"] if r["user_id"] == user_id]
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """删除提醒"""
        for i, r in enumerate(self.reminders["reminders"]):
            if r["id"] == reminder_id:
                self.reminders["reminders"].pop(i)
                self._save()
                return True
        return False
    
    def _save(self):
        """保存数据"""
        save_json(REMINDER_FILE, self.reminders)

reminder_manager = ReminderManager()

reminder = on_message(priority=16, block=False)
@reminder.handle()
async def handle_reminder(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    user_id = str(event.user_id)
    group_id = str(event.group_id)
    
    if msg.startswith("提醒我"):
        parts = msg.replace("提醒我", "").strip().split(" ", 2)
        
        if len(parts) < 2:
            await reminder.finish("使用方法：提醒我 时间 内容\n例：提醒我 明天 15:00 开会")
        
        time_str = f"{parts[0]} {parts[1]}" if len(parts) > 2 else parts[0]
        content = parts[2] if len(parts) > 2 else parts[1]
        
        now = datetime.now()
        
        if time_str.startswith("明天"):
            if len(parts) == 3:
                reminder_time = time_str.replace("明天", str((now + timedelta(days=1)).date()))
            else:
                await reminder.finish("时间格式错误！")
        elif time_str.startswith("后天"):
            reminder_time = time_str.replace("后天", str((now + timedelta(days=2)).date()))
        else:
            try:
                if ":" in time_str and "-" not in time_str:
                    reminder_time = f"{now.date()} {time_str}"
                else:
                    reminder_time = time_str
            except:
                await reminder.finish("时间格式错误！")
        
        reminder_id = reminder_manager.add_reminder(user_id, group_id, reminder_time, content)
        await reminder.finish(f"✅ 提醒已设置！\n编号：{reminder_id}\n时间：{reminder_time}\n内容：{content}")
    
    elif msg in ["我的提醒", "提醒列表"]:
        reminders = reminder_manager.get_user_reminders(user_id)
        
        if not reminders:
            await reminder.finish("你没有设置任何提醒哦～")
        
        reply = "📋 你的提醒列表：\n"
        for r in reminders:
            status = "🟢" if r["active"] else "🔴"
            reply += f"{status} #{r['id']} {r['time']} - {r['content']}\n"
        
        await reminder.finish(reply)
    
    elif msg.startswith("删除提醒"):
        try:
            reminder_id = int(msg.replace("删除提醒", "").strip())
            if reminder_manager.delete_reminder(reminder_id):
                await reminder.finish(f"✅ 已删除提醒 #{reminder_id}")
            else:
                await reminder.finish("❌ 提醒不存在或无权删除")
        except:
            await reminder.finish("使用方法：删除提醒 编号")