from linebot.models import TextSendMessage
from message_processor import ExpenseManager
from expense_chart_generator import ChartGenerator
import os

class MessageHandler:
    def __init__(self, line_bot_api, user_context):
        self.line_bot_api = line_bot_api
        self.user_context = user_context
        self.base_url = os.getenv("BASE_URL", "http://localhost:5000")

    def reset_workflow(self, user_id):
        """重置使用者的整個分帳流程狀態"""
        self.user_context[user_id] = {
            "processor": ExpenseManager(),
            "step": 0,
            "confirmation": False,
            "data": None,
            "chart_path": None
        }

    def handle_message(self, event):
        # 取得使用者 ID 與輸入訊息
        user_id = event.source.user_id
        user_message = event.message.text.strip()

        # 若使用者輸入「重置」，則將流程重置並回覆提示訊息
        if user_message == "重置":
            self.reset_workflow(user_id)
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "流程已重置！\n"
                        "請重新開始。\n\n"
                        "嗨！我是您的記帳助手\n"
                        "卓波 (=^･ω･^=)\n"
                        "請輸入成員名單\n"
                        "（例如：卓波、野獸、柿子）。"
                    )
                )
            )
            return

        # 取得或初始化使用者的上下文資料
        context = self.user_context.get(user_id, {
            "processor": ExpenseManager(),
            "step": 0,
            "confirmation": False,
            "data": None
        })

        # 根據使用者流程階段決定回覆訊息
        try:
            if context["step"] == 0:
                # 第0步：歡迎訊息
                response_message = self.welcome_user(context)
            elif context["confirmation"]:
                # 確認階段：使用 handle_confirmation
                response_message = self.handle_confirmation(context, user_message, event)
            else:
                # 一般輸入階段：使用 handle_input
                response_message = self.handle_input(context, user_message, event)

            # 更新上下文狀態
            self.user_context[user_id] = context

        except Exception as e:
            # 若發生例外，回覆錯誤訊息
            response_message = f"發生錯誤：{str(e)}\n請重新輸入。"

        # 回覆使用者訊息
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_message)
        )

        # 若已完成計算（step == 5）且有圖表連結，則另行 push 圖表連結，並重置流程
        if context.get("step") == 5 and "chart_path" in context:
            self.line_bot_api.push_message(
                user_id,
                TextSendMessage(
                    text=(
                        "圖表生成完畢！\n"
                        "您可以從以下連結查看：\n"
                        f"{context['chart_path']}"
                    )
                )
            )
            self.reset_workflow(user_id)

    def welcome_user(self, context):
        """引導使用者輸入成員名單"""
        context["step"] += 1
        return (
            "嗨！我是您的記帳助手\n"
            "卓波 (=^･ω･^=)\n\n"
            "我會幫您處理分帳問題！\n\n"
            "請輸入成員名單\n"
            "（例如：卓波、野獸、柿子）。"
        )

    def handle_input(self, context, user_message=None, event=None):
        """依據不同的流程階段處理使用者輸入"""
        processor = context["processor"]
        step = context["step"]

        if step == 1:
            # 成員名單確認
            context["data"] = user_message
            members = user_message.split("、")
            processor.process_members(user_message)
            context["confirmation"] = True
            return (
                f"成員名單為：\n{'、'.join(members)}\n"
                "請確認是否正確？（是/否）"
            )

        elif step == 2:
            # 付款記錄確認
            context["data"] = user_message
            processor.process_payments(user_message)
            context["confirmation"] = True
            return (
                f"付款記錄為：\n{user_message}\n"
                "請確認是否正確？（是/否）"
            )

        elif step == 3:
            # 分攤情況確認
            context["data"] = user_message
            processor.process_splits(user_message)
            context["confirmation"] = True
            return (
                f"分攤情況為：\n{user_message}\n"
                "請確認是否正確？（是/否）"
            )

        elif step == 4:
            # 計算與圖表生成
            result = processor.calculate_and_format()
            summary_data = processor.get_summary()
            chart_generator = ChartGenerator(summary_data)
            chart_path = chart_generator.generate_charts(output_dir="static/charts")
            context["step"] += 1

            # 使用可公開存取的 URL
            context["chart_path"] = f"{self.base_url}/chart/{os.path.basename(chart_path)}"

            return (
                "計算結果如下：\n"
                f"{result}"
            )

        else:
            # 非預期的步驟
            return "無效的步驟，請輸入'重置'重新開始。"

    def handle_confirmation(self, context, user_message, event):
        """處理使用者對於成員、付款記錄、分攤情況的確認 (是/否)"""
        user_input = user_message.lower()
        step = context["step"]

        if user_input == "是":
            # 使用者確認正確，進入下一步
            context["confirmation"] = False
            context["step"] += 1
            if context["step"] == 2:
                return (
                    "請輸入付款記錄\n"
                    "格式:[成員]付了[金額]元[項目]\n"
                    "（例如：卓波付了1000元晚餐）。\n"
                    "多筆記錄請換行。"
                )
            elif context["step"] == 3:
                return (
                    "請輸入分攤情況\n"
                    "格式:[項目]沒[成員(可填複數)]\n"
                    "（例如：晚餐沒卓波、野獸）。\n"
                    "多筆記錄請換行。\n\n"
                    "ps.這邊只記錄沒有要分的\n"
                    "若都要分則不用特別打"
                    
                )
            elif context["step"] == 4:
                # 第四步直接呼叫 handle_input 觸發計算
                return self.handle_input(context=context, user_message="", event=event)

        elif user_input == "否":
            # 使用者不確認正確，請重新輸入
            context["confirmation"] = False
            if step == 1:
                return (
                    "請重新輸入成員名單\n"
                    "（例如：卓波、野獸、柿子）。"
                )
            elif step == 2:
                return "請重新輸入付款記錄。"
            elif step == 3:
                return "請重新輸入分攤情況。"

        else:
            # 非預期輸入，提示使用者輸入「是」或「否」
            return "請輸入 '是' 或 '否'\n來確認資料是否正確。"
