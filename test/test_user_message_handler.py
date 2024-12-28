import unittest
from unittest.mock import Mock
from user_message_handler import MessageHandler
from linebot.models import TextSendMessage

class TestMessageHandler(unittest.TestCase):

    def setUp(self):
        # 設定測試環境，初始化模擬的依賴項以及主要的處理類別
        self.line_bot_api_mock = Mock()
        self.user_context_mock = {}
        self.handler = MessageHandler(self.line_bot_api_mock, self.user_context_mock)

    def create_text_event(self, user_id, text):
        # 創建模擬的文字事件，用於模擬用戶傳送訊息的情境
        return Mock(
            source=Mock(user_id=user_id),
            reply_token='dummy_token',
            message=Mock(text=text)
        )

    def test_reset_workflow(self):
        # 測試 reset_workflow 方法，確認能正確初始化使用者的上下文
        user_id = 'test_user'
        self.handler.reset_workflow(user_id)

        expected_context = {
            "processor": Mock(),
            "step": 0,
            "retry_count": 0,
            "chart_path": None,
            "data": None
        }

        self.assertIn(user_id, self.handler.user_context)
        self.assertEqual(self.handler.user_context[user_id]["step"], 0)

    def test_handle_message_reset(self):
        # 測試當用戶輸入「重置」時，是否正確重置流程並傳送歡迎訊息
        user_id = 'test_user'
        event = self.create_text_event(user_id, "重置")

        self.handler.handle_message(event)
        self.line_bot_api_mock.reply_message.assert_called_with(
            event.reply_token,
            TextSendMessage(text=self.handler.welcome_message())
        )
        self.assertIn(user_id, self.handler.user_context)

    def test_handle_message_invalid_input(self):
        # 測試無效輸入時，是否正確回應預設的歡迎訊息
        user_id = 'test_user'
        event = self.create_text_event(user_id, "invalid_input")

        self.handler.handle_message(event)
        self.line_bot_api_mock.reply_message.assert_called_with(
            event.reply_token,
            TextSendMessage(text=self.handler.welcome_message())
        )

    def test_handle_step_0_valid_input(self):
        # 測試在 step=0 時，提供有效輸入是否能將步驟更新為 1
        user_id = 'test_user'
        event = self.create_text_event(user_id, "Alice付了100元晚餐")

        self.handler.handle_message(event)
        context = self.handler.user_context[user_id]
        self.assertEqual(context["step"], 1)

    def test_handle_step_1_confirmation_yes(self):
        # 測試在 step=1 時，用戶確認「是」是否能正確處理資料並進入 step=3
        user_id = 'test_user'
        self.handler.user_context[user_id] = {
            "processor": Mock(),
            "step": 1,
            "retry_count": 0,
            "data": "Mocked data"
        }
        event = self.create_text_event(user_id, "是")

        # 模擬處理方法
        self.handler.clean_data = Mock(return_value="Cleaned data")
        self.handler.split_into_three_sections = Mock(return_value=["members", "payments", "splits"])
        self.handler.generate_and_send_chart = Mock()

        self.handler.handle_message(event)
        
        # 驗證步驟是否更新為 3
        self.assertEqual(self.handler.user_context[user_id]["step"], 3)
        self.handler.generate_and_send_chart.assert_called_once()

    def test_handle_step_1_confirmation_no(self):
        # 測試在 step=1 時，用戶確認「否」是否能正確進入手動輸入模式
        user_id = 'test_user'
        self.handler.user_context[user_id] = {
            "processor": Mock(),
            "step": 1,
            "retry_count": 1,
            "data": "Mocked data"
        }
        event = self.create_text_event(user_id, "否")

        self.handler.handle_message(event)
        self.line_bot_api_mock.reply_message.assert_called()
        self.assertEqual(self.handler.user_context[user_id]["step"], "manual_input")

if __name__ == "__main__":
    unittest.main()
