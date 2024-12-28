import unittest
from message_processor import ExpenseManager

class TestExpenseManager(unittest.TestCase):

    def setUp(self):
        # 初始化 ExpenseManager 實例
        self.manager = ExpenseManager()

    def test_process_members_valid(self):
        # 測試有效的成員名單
        input_members = "Alice、Bob、Charlie"
        result = self.manager.process_members(input_members)
        self.assertEqual(result, ["Alice", "Bob", "Charlie"])

    def test_process_members_empty(self):
        # 測試空成員名單
        input_members = ""
        with self.assertRaises(ValueError) as context:
            self.manager.process_members(input_members)
        self.assertEqual(str(context.exception), "成員名單不得為空。")

    def test_process_members_duplicates(self):
        # 測試重複成員
        input_members = "Alice、Bob、Alice"
        with self.assertRaises(ValueError) as context:
            self.manager.process_members(input_members)
        self.assertIn("重複成員", str(context.exception))

    def test_process_payments_valid(self):
        # 測試有效的付款紀錄
        self.manager.process_members("Alice、Bob、Charlie")
        input_payments = "Alice付了100元晚餐\nBob付了200元電影"
        result = self.manager.process_payments(input_payments)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["payer"], "Alice")
        self.assertEqual(result[0]["amount"], 100.0)
        self.assertEqual(result[0]["item"], "晚餐")

    def test_process_payments_invalid_format(self):
        # 測試格式錯誤的付款紀錄
        self.manager.process_members("Alice、Bob、Charlie")
        input_payments = "Alice付了100元"
        with self.assertRaises(ValueError) as context:
            self.manager.process_payments(input_payments)
        self.assertIn("格式錯誤", str(context.exception))

    def test_process_splits_valid(self):
        # 測試有效的分攤狀況
        self.manager.process_members("Alice、Bob、Charlie")
        self.manager.process_payments("Alice付了300元晚餐")
        input_splits = "晚餐沒Charlie"
        result = self.manager.process_splits(input_splits)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["per_person"], 150.0)
        self.assertEqual(result[0]["participants"], ["Alice", "Bob"])

    def test_process_splits_invalid_item(self):
        # 測試無效的分攤項目
        self.manager.process_members("Alice、Bob、Charlie")
        self.manager.process_payments("Alice付了300元晚餐")
        input_splits = "電影沒Alice"
        with self.assertRaises(ValueError) as context:
            self.manager.process_splits(input_splits)
        self.assertIn("無此項目", str(context.exception))

    def test_calculate_and_format(self):
        # 測試完整計算與格式化
        self.manager.process_members("Alice、Bob、Charlie")
        self.manager.process_payments("Alice付了300元晚餐\nBob付了150元電影")
        self.manager.process_splits("晚餐沒Charlie")
        result = self.manager.calculate_and_format()
        self.assertIn("【四、每人結算金額】", result)
        self.assertIn("【五、轉帳方案】", result)

    def test_calculate_transfers(self):
        # 測試轉帳計算
        self.manager.process_members("Alice、Bob、Charlie")
        self.manager.process_payments("Alice付了300元晚餐\nBob付了150元電影")
        self.manager.process_splits("晚餐沒Charlie")
        self.manager.calculate_and_format()
        transfers = self.manager.get_summary()["transfers"]
        self.assertGreater(len(transfers), 0)
        self.assertIn("→", transfers[0])

if __name__ == "__main__":
    unittest.main()
