import unittest
import os
from expense_chart_generator import ChartGenerator

class TestChartGenerator(unittest.TestCase):

    def setUp(self):
        # 更新模擬數據，包含必要的字段
        self.summary_data = {
            "members": ["Alice", "Bob", "Charlie"],
            "balances": {"Alice": 150, "Bob": -75, "Charlie": -75},
            "transfers": ["Bob → Alice 75 元", "Charlie → Alice 75 元"],
            "payments": [
                {"payer": "Alice", "amount": 300, "item": "晚餐"},
                {"payer": "Bob", "amount": 150, "item": "電影"}
            ],
            "detailed_split": [
                {"item": "晚餐", "amount": 300, "participants": ["Alice", "Bob"], "per_person": 150},
                {"item": "電影", "amount": 150, "participants": ["Bob", "Charlie"], "per_person": 75}
            ]
        }
        self.generator = ChartGenerator(self.summary_data)

    def test_chart_pay_vs_owed(self):
        # 測試支付 vs 該付金額
        html = self.generator._chart_pay_vs_owed()
        self.assertIn("Alice", html)

    def test_chart_balances(self):
        # 測試結算餘額圖
        html = self.generator._chart_balances()
        self.assertIn("plotly-graph-div", html)  # 確保圖表容器存在

    def test_generate_charts(self):
        # 測試生成圖表 HTML 文件
        output_dir = "test_charts"
        chart_path = self.generator.generate_charts(output_dir)
        self.assertTrue(os.path.exists(chart_path))
        with open(chart_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Alice", content)

        # 清理測試文件
        os.remove(chart_path)
        os.rmdir(output_dir)

if __name__ == "__main__":
    unittest.main()
