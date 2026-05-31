"""
group_admin_plus.py - 群管理增强功能
"""
from nonebot import on_message, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupIncreaseNoticeEvent
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List

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

GROUP_CONFIG_FILE = "group_configs.json"
VOTE_FILE = "active_votes.json"

class VoteManager:
    def __init__(self):
        self.votes = load_json(VOTE_FILE, {"votes": {}})
    
    def create_vote(self, group_id: str, creator: str, title: str, options: List[str], duration: int = 300) -> int:
        """创建投票，duration单位：秒"""
        vote_id = len(self.votes["votes"]) + 1
        
        vote = {
            "id": vote_id,
            "group_id": group_id,
            "creator": creator,
            "title": title,
            "options": {opt: [] for opt in options},
            "voters": [],
            "start_time": datetime.now().isoformat(),
            "duration": duration,
            "active": True
        }
        
        self.votes["votes"][str(vote_id)] = vote
        self._save()
        return vote_id
    
    def vote(self, vote_id: int, user_id: str, option: str) -> bool:
        """投票"""
        vote_key = str(vote_id)
        
        if vote_key not in self.votes["votes"]:
            return False, "投票不存在"
        
        vote = self.votes["votes"][vote_key]
        
        if not vote["active"]:
            return False, "投票已结束"
        
        if user_id in vote["voters"]:
            return False, "你已经投过票了"
        
        if option not in vote["options"]:
            return False, "选项不存在"
        
        vote["options"][option].append(user_id)
        vote["voters"].append(user_id)
        self._save()
        return True, "投票成功"
    
    def get_results(self, vote_id: int) -> str:
        """获取投票结果"""
        vote_key = str(vote_id)
        
        if vote_key not in self.votes["votes"]:
            return "投票不存在"
        
        vote = self.votes["votes"][vote_key]
        
        result = f"📊 投票结果：{vote['title']}\n"
        result += f"👥 总投票数：{len(vote['voters'])}人\n\n"
        
        for option, voters in vote["options"].items():
            percentage = (len(voters) / max(len(vote['voters']), 1)) * 100
            bar = "█" * int(percentage / 10)
            result += f"{option}: {len(voters)}票 {bar} {percentage:.1f}%\n"
        
        return result
    
    def _save(self):
        """保存数据"""
        save_json(VOTE_FILE, self.votes)

vote_manager = VoteManager()

class AutoReplyManager:
    def __init__(self):
        self.replies = load_json(GROUP_CONFIG_FILE, {"auto_replies": {}, "welcome_msgs": {}})
    
    def add_reply(self, group_id: str, keyword: str, reply: str, reply_type: str = "exact"):
        """添加自动回复"""
        if group_id not in self.replies["auto_replies"]:
            self.replies["auto_replies"][group_id] = {}
        
        if keyword not in self.replies["auto_replies"][group_id]:
            self.replies["auto_replies"][group_id][keyword] = []
        
        self.replies["auto_replies"][group_id][keyword].append({
            "reply": reply,
            "type": reply_type
        })
        
        self._save()
    
    def get_reply(self, group_id: str, message: str) -> str:
        """获取自动回复"""
        if group_id not in self.replies["auto_replies"]:
            return None
        
        for keyword, replies in self.replies["auto_replies"][group_id].items():
            for reply_config in replies:
                if reply_config["type"] == "exact" and keyword == message:
                    return reply_config["reply"]
                elif reply_config["type"] == "fuzzy" and keyword in message:
                    return reply_config["reply"]
        
        return None
    
    def _save(self):
        """保存数据"""
        save_json(GROUP_CONFIG_FILE, self.replies)

auto_reply_manager = AutoReplyManager()

group_admin = on_message(priority=5, block=False)
@group_admin.handle()
async def handle_group_admin(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    if msg.startswith("创建投票"):
        content = msg.replace("创建投票", "").strip()
        parts = content.split("|")
        
        if len(parts) < 3:
            await group_admin.finish("使用方法：创建投票 标题 | 选项1 | 选项2 | [选项3]...")
        
        title = parts[0].strip()
        options = [opt.strip() for opt in parts[1:]]
        
        vote_id = vote_manager.create_vote(group_id, user_id, title, options)
        
        reply = f"📊 投票已创建！\n"
        reply += f"编号：#{vote_id}\n"
        reply += f"标题：{title}\n\n"
        reply += "选项：\n"
        for i, opt in enumerate(options, 1):
            reply += f"{i}. {opt}\n"
        reply += f"\n回复「投票 {vote_id} 选项编号」参与投票"
        
        await group_admin.finish(reply)
    
    elif msg.startswith("投票"):
        parts = msg.split()
        
        if len(parts) < 3:
            await group_admin.finish("使用方法：投票 投票编号 选项编号")
        
        try:
            vote_id = int(parts[1])
            option_num = int(parts[2])
        except:
            await group_admin.finish("格式错误！")
        
        vote = vote_manager.votes["votes"].get(str(vote_id))
        if not vote:
            await group_admin.finish("投票不存在！")
        
        options = list(vote["options"].keys())
        if option_num < 1 or option_num > len(options):
            await group_admin.finish("选项编号错误！")
        
        option = options[option_num - 1]
        success, message = vote_manager.vote(vote_id, user_id, option)
        
        if success:
            await group_admin.finish(f"✅ 投票成功！你选择了：{option}")
        else:
            await group_admin.finish(f"❌ {message}")
    
    elif msg.startswith("投票结果"):
        try:
            vote_id = int(msg.replace("投票结果", "").strip())
        except:
            await group_admin.finish("使用方法：投票结果 投票编号")
        
        result = vote_manager.get_results(vote_id)
        await group_admin.finish(result)
    
    elif msg.startswith("自动回复"):
        content = msg.replace("自动回复", "").strip()
        parts = content.split("|")
        
        if len(parts) < 2:
            await group_admin.finish('使用方法：自动回复 关键词 | 回复内容\n例：自动回复 你好 | 你好呀！')
        
        keyword = parts[0].strip()
        reply = parts[1].strip()
        
        auto_reply_manager.add_reply(group_id, keyword, reply)
        await group_admin.finish(f"✅ 自动回复已添加：{keyword} → {reply}")
    
    elif msg in ["群规", "群公告"]:
        rules = (
            "📋 群规：\n"
            "1. 文明聊天，尊重他人\n"
            "2. 禁止发布广告和违规内容\n"
            "3. 禁止刷屏和恶意骚扰\n"
            "4. 积极参与群活动\n"
            "5. 有疑问可以@机器人\n\n"
            "遵守群规，快乐聊天！😊"
        )
        await group_admin.finish(rules)
    
    else:
        reply = auto_reply_manager.get_reply(group_id, msg)
        if reply:
            await group_admin.finish(reply)

welcome_plus = on_notice()
@welcome_plus.handle()
async def handle_welcome_plus(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    
    config = load_json(GROUP_CONFIG_FILE, {"welcome_msgs": {}})
    
    if group_id in config["welcome_msgs"]:
        welcome_msg = config["welcome_msgs"][group_id]
        await bot.send_group_msg(group_id=int(group_id), message=f"{welcome_msg}\n欢迎新朋友！")