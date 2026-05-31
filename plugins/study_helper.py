"""
study_helper.py - 学习助手插件
支持背单词、知识问答、学习计划
"""
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
import random
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

STUDY_FILE = "study_data.json"

WORD_BANK = {
    "apple": "苹果",
    "book": "书",
    "cat": "猫",
    "dog": "狗",
    "elephant": "大象",
    "flower": "花",
    "garden": "花园",
    "house": "房子",
    "ice": "冰",
    "jungle": "丛林",
    "king": "国王",
    "lion": "狮子",
    "moon": "月亮",
    "night": "夜晚",
    "ocean": "海洋",
    "pencil": "铅笔",
    "queen": "女王",
    "rain": "雨",
    "sun": "太阳",
    "tree": "树"
}

KNOWLEDGE_QA = [
    {"q": "地球绕太阳转一圈需要多长时间？", "a": "一年"},
    {"q": "中国的首都是哪里？", "a": "北京"},
    {"q": "水的化学式是什么？", "a": "H2O"},
    {"q": "光的速度是多少？", "a": "约30万公里/秒"},
    {"q": "人体最大的器官是什么？", "a": "皮肤"},
    {"q": "世界上最长的河流是什么？", "a": "尼罗河"},
    {"q": "圆周率π约等于多少？", "a": "3.14"},
    {"q": "一年有多少天？", "a": "365天"},
    {"q": "世界上最高的山峰是什么？", "a": "珠穆朗玛峰"},
    {"q": "声音在真空中能传播吗？", "a": "不能"}
]

class StudyManager:
    def __init__(self):
        self.data = load_json(STUDY_FILE, {
            "word_progress": {},
            "quiz_scores": {},
            "study_time": {}
        })
    
    def record_word_learned(self, user_id: str, word: str):
        """记录学习的单词"""
        if user_id not in self.data["word_progress"]:
            self.data["word_progress"][user_id] = {"learned": [], "correct_count": 0, "total_count": 0}
        
        user_words = self.data["word_progress"][user_id]
        if word not in user_words["learned"]:
            user_words["learned"].append(word)
        user_words["total_count"] += 1
        self._save()
    
    def record_correct_word(self, user_id: str, word: str):
        """记录正确的单词"""
        if user_id in self.data["word_progress"]:
            self.data["word_progress"][user_id]["correct_count"] += 1
            self._save()
    
    def get_word_progress(self, user_id: str) -> dict:
        """获取单词学习进度"""
        return self.data["word_progress"].get(user_id, {"learned": [], "correct_count": 0, "total_count": 0})
    
    def _save(self):
        """保存数据"""
        save_json(STUDY_FILE, self.data)

study_manager = StudyManager()

study = on_message(priority=17, block=False)
@study.handle()
async def handle_study(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    user_id = str(event.user_id)
    
    if msg in ["背单词", "学英语", "单词"]:
        word, meaning = random.choice(list(WORD_BANK.items()))
        
        await study.finish(f"📖 今日单词：\n🔤 {word}\n📝 {meaning}\n\n回复「下一个单词」继续学习")
    
    elif msg == "下一个单词":
        word, meaning = random.choice(list(WORD_BANK.items()))
        study_manager.record_word_learned(user_id, word)
        
        await study.finish(f"📖 单词挑战：\n{word} 是什么意思？\n回复你的答案～")
    
    elif msg.startswith("测试"):
        word, meaning = random.choice(list(WORD_BANK.items()))
        
        options = [meaning]
        while len(options) < 4:
            fake_meaning = random.choice(list(WORD_BANK.values()))
            if fake_meaning != meaning and fake_meaning not in options:
                options.append(fake_meaning)
        
        random.shuffle(options)
        
        question = f"📝 单词测试：\n{word} 是什么意思？\n"
        for i, opt in enumerate(options, 1):
            question += f"{i}. {opt}\n"
        question += "回复数字选择答案"
        
        await study.finish(question)
    
    elif msg in ["知识问答", "问答"]:
        qa = random.choice(KNOWLEDGE_QA)
        
        await study.finish(f"❓ 知识问答：\n{qa['q']}\n\n回复你的答案～")
    
    elif msg in ["学习统计", "学习进度"]:
        progress = study_manager.get_word_progress(user_id)
        
        reply = (
            f"📊 你的学习统计：\n"
            f"📖 学习单词：{len(progress['learned'])}个\n"
            f"✅ 正确率：{progress['correct_count']}/{progress['total_count']} "
            f"({progress['correct_count']/max(progress['total_count'], 1)*100:.1f}%)\n"
            f"📝 已学单词：{'、'.join(progress['learned'][-5:])}"
        )
        
        await study.finish(reply)