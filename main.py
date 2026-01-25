# 1. 视觉识别结果 (蓝色)
self.ui_queue.put({
    "type": "VISION",
    "text": "OCR 识别到 '开始行动'",
    "detail": "Confidence: 0.98\nBox: [100, 200, 300, 400]\nRaw Text: 'Start Battle'"
})

# 2. AI 思考过程 (紫色)
self.ui_queue.put({
    "type": "THOUGHT",
    "text": "决策：准备进入战斗",
    "detail": "Current State: Main_Menu\nTarget: Resource_Stage\nLLM Reasoning: 玩家体力和资源充足，符合自动挂机条件。"
})

# 3. 执行操作 (绿色)
self.ui_queue.put({
    "type": "ACTION",
    "text": "点击坐标 (850, 420)",
    "detail": "Action: Click\nCoordinates: (850, 420)\nDelay: 0.5s"
})

# 4. 错误信息 (红色)
self.ui_queue.put({
    "type": "ERROR",
    "text": "无法连接到 ADB",
    "detail": "Traceback (most recent call last):\n  File 'adb.py', line 42\nConnectionRefusedError"
})