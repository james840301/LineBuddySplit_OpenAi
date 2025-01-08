from linebot.models import TextSendMessage
from message_processor import ExpenseManager
from expense_chart_generator import ChartGenerator
import openai
import os
import re


class MessageHandler:
    """
    簡易記帳流程：
    1. step=0：等待使用者輸入記帳資訊（呼叫OpenAI解析）=> step=1
    2. step=1：請使用者「是/否」確認解析結果
        - 是：計算、出圖 => step=3
        - 否：若拒絕2次 => 進入手動模式 manual_input
    3. step=manual_input：使用者手動貼上完整格式，人工解析 => step=3
    4. step=3：流程已完成，可重置或再次輸入。
    """

    def __init__(self, line_bot_api, user_context):
        """初始化訊息處理類別"""
        self.line_bot_api = line_bot_api
        self.user_context = user_context
        self.base_url = os.getenv("BASE_URL", "http://localhost:5000")
        self.max_retry = 3
        self.openai_model = "gpt-3.5-turbo"

    # -------------------------------------------------------------------------
    # 基本工具 / 共用方法
    # -------------------------------------------------------------------------
    def reply_user(self, event, text):
        """統一回覆使用者訊息"""
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=text)
        )

    def update_context(self, user_id, context):
        """更新使用者上下文資料"""
        self.user_context[user_id] = context

    def reset_workflow(self, user_id):
        """重置使用者的分帳流程狀態"""
        self.user_context[user_id] = {
            "processor": ExpenseManager(),
            "step": 0,
            "retry_count": 0,
            "chart_path": None,
            "data": None
        }

    # -------------------------------------------------------------------------
    # 入口：收到使用者訊息時，程式從這裡開始
    # -------------------------------------------------------------------------
    def handle_message(self, event):
        """處理 LINE Bot 收到的訊息事件"""
        user_id = event.source.user_id

        # 確保為文字訊息
        if not hasattr(event.message, 'text'):
            self.reply_user(event, "請輸入文字訊息。")
            return

        user_message = event.message.text.strip()

        # 若輸入 "重置" => 直接重置
        if user_message == "重置":
            self.reset_workflow(user_id)
            self.reply_user(event, self.welcome_message())
            return

        # 取得/初始化使用者上下文
        context = self.user_context.get(user_id, {
            "processor": ExpenseManager(),
            "step": 0,
            "retry_count": 0,
            "data": None,
            "chart_path": None
        })
        step = context["step"]

        # 依 step 不同，進入對應處理
        if step == 3:
            # 流程完成，引導重置或再次輸入
            resp = self.handle_step_3(context)
            self.update_context(user_id, context)
            self.reply_user(event, resp)
            return

        if step == "manual_input":
            # 手動模式：直接解析使用者貼上的完整格式
            resp = self.handle_manual_input(context, user_message, event)
            self.update_context(user_id, context)
            self.reply_user(event, resp)
            return

        # 其他 step => 0 或 1 或未知
        resp = self.handle_other_steps(context, user_message, event)
        self.update_context(user_id, context)
        self.reply_user(event, resp)

    # -------------------------------------------------------------------------
    # step=0、1、(錯誤) 狀態處理
    # -------------------------------------------------------------------------
    def handle_other_steps(self, context, user_message, event):
        """處理 step=0、1 或錯誤狀態"""
        step = context["step"]

        try:
            if step == 0:
                return self.handle_step_0(context, user_message, event)
            elif step == 1:
                return self.handle_step_1(context, user_message, event)
            else:
                # 非預期狀態
                return "狀態錯誤，請輸入「重置」重新開始。"
        except Exception as e:
            return f"發生錯誤：{str(e)}，請重新輸入。"

    def handle_step_0(self, context, user_message, event):
        """
        step=0：等待使用者一次性輸入資訊 (可呼叫 OpenAI 解析)。
        如果輸入有效 => 進入 step=1
        """
        if self.is_valid_expense_input(user_message):
            # 呼叫OpenAI解析
            parse_result = self.handle_input(context, user_message)
            context["step"] = 1
            return parse_result
        else:
            # 輸入無效 => 顯示歡迎訊息
            return self.welcome_message()

    def handle_step_1(self, context, user_message, event):
        """
        step=1：OpenAI 解析結果後，請使用者「是/否」確認。
        - 是 => 完成計算 => step=3
        - 否 => 若拒絕2次 => step=manual_input
        """
        resp, new_step = self.handle_confirmation(context, user_message, event)
        context["step"] = new_step
        return resp

    # -------------------------------------------------------------------------
    # step=3、manual_input 狀態處理
    # -------------------------------------------------------------------------
    def handle_step_3(self, context):
        """
        step=3：流程已完成，若使用者想輸入新記帳資料 => 重置 or step=0
        這裡簡單提示即可。
        """
        # 顯示完成後，引導輸入或重置
        context["step"] = 0  # 重置到0，讓使用者再次輸入就能重新開始
        return (
            "流程已完成！\n"
            "如有新的記帳資料，請再次輸入。\n"
            "如需重新開始流程，請輸入「重置」。"
        )

    def handle_manual_input(self, context, user_message, event):
        """
        step=manual_input：
        使用者手動貼上「三段式」資料，直接做人工解析 => 生成結果
        成功 => step=3；失敗 => 維持 manual_input
        """
        try:
            if not self.is_valid_expense_input(user_message):
                return "輸入格式不正確，請依照以下格式重新輸入：\n" + self.welcome_message()
            else:
                context["data"] = user_message
                response_message, new_step = self.process_parsed_data(context, event)
                context["step"] = new_step
                return response_message
        except Exception as e:
            return f"手動輸入處理失敗：{str(e)}，請檢查格式並重新輸入。"

    # -------------------------------------------------------------------------
    # 解析 / 確認 / OpenAI 相關
    # -------------------------------------------------------------------------
    def is_valid_expense_input(self, user_message):
        """
        檢查用戶輸入是否為有效的記帳格式 (最簡單檢查: '付了' or '沒')
        可依需求擴充(如檢查【一、】【二、】【三、】等)
        """
        return ("付了" in user_message or "沒" in user_message)

    def welcome_message(self):
        """回傳歡迎訊息"""
        return (
            "嗨！我是您的記帳助手\n"
            "卓波 (=^･ω･^=)\n\n"
            "請一次性輸入所有資訊，\n"
            "例如：\n"
            "成員有Alice、Bob、Charlie\n"
            "Alice付了100元晚餐\n"
            "Bob付了200元電影\n"
            "晚餐沒Charlie\n"
            "電影沒Alice"
        )

    def handle_input(self, context, user_message):
        """
        呼叫 OpenAI API 做自動解析。
        成功 => 回傳「解析結果」，等待是/否確認 => step=1
        失敗 => 累積retry_count，若達 max_retry => 提示手動輸入
        """
        try:
            openai_response = self.call_openai_api(user_message)
            context["data"] = openai_response.strip()
            return f"解析結果如下：\n{context['data']}\n請確認是否正確？（是/否）"
        except Exception as e:
            context["retry_count"] += 1
            if context["retry_count"] >= self.max_retry:
                return (
                    "多次嘗試解析失敗，請重新檢查輸入格式。\n"
                    "請輸入：\n"
                    "成員有：成員名單\n"
                    "付費記錄：成員、金額與項目\n"
                    "分攤規則：具體規則描述。"
                )
            return f"解析失敗，錯誤原因：{str(e)}\n請修正後重新輸入。"

    def handle_confirmation(self, context, user_message, event):
        """
        使用者確認 OpenAI 解析結果 (是/否)。
        - 是 => 解析並計算 => step=3
        - 否 => 若拒絕2次 => step=manual_input
        """
        if user_message.lower() == "是":
            return self.confirmation_yes(context, event)
        elif user_message.lower() == "否":
            return self.confirmation_no(context)
        else:
            return ("請輸入 '是' 或 '否' 來確認解析結果是否正確。\n或輸入「重置」重新開始。", 1)

    def confirmation_yes(self, context, event):
        """
        使用者確認解析結果正確 => 進行資料處理 + 出圖 => step=3
        """
        try:
            processor = context["processor"]
            data = self.clean_data(context["data"])

            # 以標題進行分割
            parsed_text = self.split_into_three_sections(data)
            if len(parsed_text) != 3:
                return (
                    f"解析失敗，以下段落可能缺失或格式錯誤：\n{parsed_text}。\n請檢查輸入內容並重試。",
                    1
                )

            # 處理三段資料
            processor.process_members(parsed_text[0])
            processor.process_payments(parsed_text[1])
            processor.process_splits(parsed_text[2])

            # 計算結果 & 生成圖表
            self.generate_and_send_chart(context, processor, event)

            # 完成
            context["data"] = None
            return ("流程已完成！如需重新開始，請直接輸入任意文字或「重置」。", 3)

        except Exception as e:
            return (f"處理解析時發生錯誤：{str(e)}，請檢查您的輸入格式。", 1)

    def confirmation_no(self, context):
        """
        使用者否定結果，retry_count++，若2次後 => step=manual_input
        否則 => 重呼叫 openai_api 重新解析
        """
        context["retry_count"] += 1
        if context["retry_count"] >= 2:
            # 進入手動輸入模式
            context["step"] = "manual_input"
            return (
                "多次拒絕解析結果。\n"
                "請手動輸入正確的格式：\n"
                "例如：\n"
                "【一、成員名單】\nAlice、Bob、Charlie\n"
                "【二、付款記錄】\nAlice付了100元晚餐\n"
                "Bob付了200元電影\n"
                "【三、分攤情況】\n晚餐沒Charlie\n電影沒Alice\n",
                "manual_input"
            )
        try:
            # 再次呼叫 openai_api 解析 data
            openai_response = self.call_openai_api(context["data"])
            context["data"] = openai_response.strip()
            return (f"解析結果如下（重新解析）：\n{context['data']}\n請確認是否正確？（是/否）", 1)
        except Exception as e:
            return (f"解析失敗，錯誤原因：{str(e)}。\n請檢查輸入內容並重新輸入。", 1)

    # -------------------------------------------------------------------------
    # OpenAI / 人工解析 共用工具
    # -------------------------------------------------------------------------
    def call_openai_api(self, user_message):
        """調用 OpenAI API 分析使用者輸入"""
        try:
            response = openai.ChatCompletion.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": (
                        "你是記帳助手，請根據以下格式解析訊息：\n"
                        "【一、成員名單】\n用頓號區隔的成員名單\n"
                        "【二、付款記錄】\n每行格式為：[成員]付了[金額]元[項目]\n"
                        "【三、分攤情況】\n每行格式為：[項目]沒[成員]\n\n"
                        "特別規則：\n"
                        "1. 如果用戶在【分攤狀況】打'無'，則【分攤情況】應顯示為'所有均分'。\n"
                        "2. 嚴格按照上述格式輸出，並確保解析結果準確。"
                    )},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"OpenAI API 呼叫失敗：{str(e)}")

    def clean_data(self, raw_data):
        """
        清理解析後的資料，把空白行移除
        回傳純淨的文字
        """
        lines = [line.strip() for line in raw_data.splitlines() if line.strip()]
        return "\n".join(lines)

    def split_into_three_sections(self, data):
        """
        以標題進行分割，並移除標題本身
        """
        parts = re.split(r"(【一、成員名單】|【二、付款記錄】|【三、分攤情況】)", data)
        # 重新拼成三段：['成員內容', '付款內容', '分攤內容']
        merged = [
            f"{parts[i+1]}".strip()
            for i in range(1, len(parts)-1, 2)
        ]
        return merged

    def generate_and_send_chart(self, context, processor, event):
        """
        計算完後生成圖表，回傳使用者
        """
        result = processor.calculate_and_format()
        summary_data = processor.get_summary()
        chart_generator = ChartGenerator(summary_data)
        chart_path = chart_generator.generate_charts(output_dir="static/charts")

        context["chart_path"] = f"{self.base_url}/chart/{os.path.basename(chart_path)}"

        # 回傳計算結果
        self.line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage(text=f"計算結果如下：\n{result}")
        )
        # 推送圖表連結
        self.line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage(text=f"圖表生成完畢！您可以從以下連結查看圖表：\n{context['chart_path']}")
        )

    # -------------------------------------------------------------------------
    # 手動解析 (manual_input) 處理
    # -------------------------------------------------------------------------
    def process_parsed_data(self, context, event):
        """
        step=manual_input時，使用者貼上三段式資料 -> 解析、計算、出圖
        成功 => 回傳 (成功訊息, 3)
        失敗 => 回傳 (錯誤訊息, "manual_input")
        """
        try:
            processor = context["processor"]
            data = self.clean_data(context["data"])

            # 分段
            parsed_text = re.split(r"(【一、成員名單】|【二、付款記錄】|【三、分攤情況】)", data)
            # 重新拼三段
            merged = [
                f"{parsed_text[i+1]}".strip()
                for i in range(1, len(parsed_text)-1, 2)
            ]
            if len(merged) != 3:
                return (
                    "解析失敗，以下段落可能缺失或格式錯誤：\n"
                    f"{merged}\n"
                    "請檢查輸入內容並重新輸入。",
                    "manual_input"
                )

            # 分別處理三段
            processor.process_members(merged[0])
            processor.process_payments(merged[1])
            processor.process_splits(merged[2])

            # 出圖
            self.generate_and_send_chart(context, processor, event)
            context["data"] = None
            return ("流程已完成！如需重新開始，請直接輸入任意文字或「重置」。", 3)

        except Exception as e:
            return (f"手動輸入解析時發生錯誤：{str(e)}", "manual_input")
