import unittest
from unittest.mock import Mock, patch
from linebot.models import MessageEvent, TextMessage, SourceUser, TextSendMessage
from user_message_handler import MessageHandler

class TestMessageHandler(unittest.TestCase):
    def setUp(self):
        # 初始化 Mock 的 LINE Bot API 和使用者上下文
        self.line_bot_api = Mock()
        self.user_context = {}
        self.handler = MessageHandler(self.line_bot_api, self.user_context)

    def simulate_event(self, user_id, message_text):
        """模擬使用者傳送文字訊息事件"""
        return MessageEvent(
            reply_token="test_reply_token",
            source=SourceUser(user_id=user_id),
            message=TextMessage(text=message_text)
        )

    def test_step_1_member_confirmation(self):
        """測試在 Step 1 時輸入成員名單後的回覆訊息"""
        self.user_context["test_user"] = {"step": 1, "processor": Mock(), "confirmation": False}
        event = self.simulate_event("test_user", "Alice、Bob、Charlie")
        self.handler.handle_message(event)
        self.line_bot_api.reply_message.assert_called_with(
            "test_reply_token",
            TextSendMessage(text="成員名單為：Alice、Bob、Charlie\n請確認是否正確？（是/否）")
        )

    def test_step_2_payment_confirmation(self):
        """測試在 Step 2 時輸入付款記錄後的回覆訊息"""
        self.user_context["test_user"] = {"step": 2, "processor": Mock(), "confirmation": False}
        event = self.simulate_event("test_user", "Alice付了1000元晚餐。")
        self.handler.handle_message(event)
        self.line_bot_api.reply_message.assert_called_with(
            "test_reply_token",
            TextSendMessage(text="付款記錄為：\nAlice付了1000元晚餐。\n請確認是否正確？（是/否）")
        )

    def test_step_3_split_confirmation(self):
        """測試在 Step 3 時輸入分攤情況後的回覆訊息"""
        self.user_context["test_user"] = {"step": 3, "processor": Mock(), "confirmation": False}
        event = self.simulate_event("test_user", "晚餐由Alice、Bob分攤。")
        self.handler.handle_message(event)
        self.line_bot_api.reply_message.assert_called_with(
            "test_reply_token",
            TextSendMessage(text="分攤情況為：\n晚餐由Alice、Bob分攤。\n請確認是否正確？（是/否）")
        )

    def test_step_4_calculation_and_chart(self):
        """測試在 Step 4 計算結果與生成圖表後的回覆與推播"""
        processor_mock = Mock()
        processor_mock.calculate_and_format.return_value = "Alice應付500元，Bob應付500元。"
        processor_mock.get_summary.return_value = {"members": ["Alice", "Bob"], "expenses": {"Alice": 500, "Bob": 500}}
        self.user_context["test_user"] = {"step": 4, "processor": processor_mock, "confirmation": False}

        with patch('user_message_handler.ChartGenerator') as MockChartGenerator:
            chart_mock = MockChartGenerator.return_value
            chart_mock.generate_charts.return_value = "http://example.com/chart.png"
            event = self.simulate_event("test_user", "是")
            self.handler.handle_message(event)

            # 驗證計算結果回覆
            self.line_bot_api.reply_message.assert_called_with(
                "test_reply_token",
                TextSendMessage(text="計算結果如下：\nAlice應付500元，Bob應付500元。")
            )
            # 驗證推送圖表連結
            self.line_bot_api.push_message.assert_called_with(
                "test_user",
                TextSendMessage(text="圖表生成完畢！您可以從以下連結查看圖表：\nhttp://example.com/chart.png")
            )

    def test_invalid_confirmation_input(self):
        """測試在確認階段輸入非「是/否」的狀況"""
        self.user_context["test_user"] = {"step": 2, "confirmation": True}
        event = self.simulate_event("test_user", "隨便亂打")
        self.handler.handle_message(event)
        self.line_bot_api.reply_message.assert_called_with(
            "test_reply_token",
            TextSendMessage(text="請輸入 '是' 或 '否' 來確認資料是否正確。")
        )

    def test_error_handling(self):
        """測試處理過程中發生例外時的錯誤訊息回覆"""
        processor_mock = Mock()
        processor_mock.process_members.side_effect = Exception("處理錯誤")
        self.user_context["test_user"] = {"step": 1, "processor": processor_mock, "confirmation": False}
        event = self.simulate_event("test_user", "Alice、Bob、Charlie")
        self.handler.handle_message(event)
        self.line_bot_api.reply_message.assert_called_with(
            "test_reply_token",
            TextSendMessage(text="發生錯誤：處理錯誤，請重新輸入。")
        )

if __name__ == "__main__":
    unittest.main()
