import os
import re
import plotly.graph_objects as go
from message_processor import ExpenseManager

class ChartGenerator:
    def __init__(self, summary_data):
        """
        初始化，接收由 ExpenseManager 計算後的摘要資料，
        並預先計算常用資料供各圖表使用。
        """
        self.members = summary_data["members"]
        self.payments = summary_data["payments"]
        self.detailed_split = summary_data["detailed_split"]
        self.balances = summary_data["balances"]
        self.transfers = summary_data["transfers"]

        # 預先計算用於多個圖表的共用資料
        self.total_paid = {m: sum(p["amount"] for p in self.payments if p["payer"] == m) for m in self.members}
        self.total_owed = {m: sum(p["per_person"] for p in self.detailed_split if m in p["participants"]) for m in self.members}
        self.reversed_members = self.members[::-1]
        self.items = [d["item"] for d in self.detailed_split]
        self.amounts = [d["amount"] for d in self.detailed_split]
        self.creditors = [m for m,b in self.balances.items() if b>0]
        self.debtors = [m for m,b in self.balances.items() if b<0]

        # 統一 fig.to_html 的參數
        self.to_html_params = dict(full_html=False, include_plotlyjs='cdn', config={"responsive": True})

    def _chart_pay_vs_owed(self):
        """圖表1：每人支付 vs 該付金額 (柱狀圖)"""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=self.members, y=list(self.total_paid.values()), name='支付金額',
            marker=dict(color='green', line=dict(color='black', width=1.5)),
            texttemplate="%{y:.0f}", textposition='outside'
        ))
        fig.add_trace(go.Bar(
            x=self.members, y=list(self.total_owed.values()), name='該付金額',
            marker=dict(color='red', line=dict(color='black', width=1.5)),
            texttemplate="%{y:.0f}", textposition='outside'
        ))
        fig.update_layout(
            title="每人支付 vs 該付金額",
            xaxis_title="成員", yaxis_title="金額 (元)",
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            autosize=True, height=500, margin=dict(l=50, r=50, t=70, b=50)
        )
        return fig.to_html(**self.to_html_params)

    def _chart_balances(self):
        """圖表2：結算餘額圖 (多付/少付)"""
        bal = self.balances
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=self.members,
            y=[b if b > 0 else 0 for b in bal.values()],
            name='多付',
            marker=dict(color='green', line=dict(color='black', width=1.5)),
            texttemplate=["{:.0f}".format(b) if b > 0 else "" for b in bal.values()],
            textposition='outside'
        ))
        fig.add_trace(go.Bar(
            x=self.members,
            y=[b if b < 0 else 0 for b in bal.values()],
            name='少付',
            marker=dict(color='red', line=dict(color='black', width=1.5)),
            texttemplate=["{:.0f}".format(abs(b)) if b < 0 else "" for b in bal.values()],
            textposition='outside'
        ))
        fig.update_layout(
            title="結算餘額圖",
            xaxis_title="成員", yaxis_title="金額 (元)",
            xaxis=dict(tickangle=-45),
            barmode='relative',
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            autosize=True, height=500, margin=dict(l=50, r=50, t=70, b=50)
        )
        return fig.to_html(**self.to_html_params)

    def _chart_transfers(self):
        """圖表3：轉帳方案 (節點 + 箭頭)"""
        bal = self.balances
        creditors, debtors = self.creditors, self.debtors

        # 固定節點位置：債權人(上), 債務人(下)
        creditor_idx = {c:(i*5,3) for i,c in enumerate(creditors)}
        debtor_idx = {d:(i*5,-3) for i,d in enumerate(debtors)}
        positions = {**creditor_idx, **debtor_idx}

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[positions[l][0] for l in positions],
            y=[positions[l][1] for l in positions],
            mode='markers+text', text=list(positions.keys()), textposition='top center',
            marker=dict(size=20,
                        color=['green' if bal[l]>0 else 'red' for l in positions],
                        line=dict(width=1, color="black")),
            textfont=dict(size=10, color="black")
        ))

        used_positions = set()
        # 為每筆轉帳畫箭頭與金額標示
        for tr in self.transfers:
            match = re.match(r"(\S+) → (\S+) ([0-9.]+) 元", tr)
            if not match:
                continue
            debtor, creditor, amt = match.groups()
            amt = round(float(amt))
            x0, y0 = positions[debtor]
            x1, y1 = positions[creditor]

            # 畫箭頭（保持原本設定）
            fig.add_annotation(
                x=x1, y=y1-0.4,
                ax=x0, ay=y0+0.4,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=1.5, arrowcolor="gray"
            )

            # 放置金額標示，嘗試多次位移避免重疊
            mid_x, mid_y, offset_y = (x0+x1)/2, (y0+y1)/2, 0.2
            for _ in range(6):
                candidate = (round(mid_x,2), round(mid_y+offset_y,2))
                if candidate not in used_positions:
                    mid_y += offset_y
                    used_positions.add(candidate)
                    break
                offset_y *= -1.1

            fig.add_annotation(
                x=mid_x, y=mid_y, text=f"{amt}元", showarrow=False,
                font=dict(size=10, color="black"),
                bgcolor="rgba(255,255,255,0.8)", bordercolor="gray", borderwidth=1, borderpad=2
            )

        fig.update_layout(
            title="轉帳方案",
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            plot_bgcolor="rgba(240, 240, 240, 0.6)",
            showlegend=False, autosize=True, margin=dict(l=50,r=50,t=70,b=50)
        )
        return fig.to_html(**self.to_html_params)

    def _chart_item_distribution(self):
        """圖表4：各項支付分布 (圓餅圖)"""
        fig = go.Figure(data=[go.Pie(labels=self.items, values=self.amounts, hole=0.3)])
        fig.update_layout(
            title="各項支付分布圖",
            autosize=True, height=500,
            legend=dict(orientation="h", y=-0.4, x=0.5, xanchor="center"),
            margin=dict(l=20,r=20,t=50,b=100)
        )
        return fig.to_html(**self.to_html_params)

    def _chart_per_person_items(self):
        """圖表5：每人該付項目金額 (橫條堆疊圖)"""
        fig = go.Figure()
        for item in self.detailed_split:
            owed_per_member = [
                item["per_person"] if m in item["participants"] else 0
                for m in self.members
            ]
            owed_reversed = owed_per_member[::-1]
            fig.add_trace(go.Bar(
                y=self.reversed_members, x=owed_reversed, name=item["item"], orientation='h',
                text=[f"{int(v)}" if v>0 else "" for v in owed_reversed],
                textposition='inside'
            ))
        fig.update_layout(
            title="每人該付項目金額",
            xaxis=dict(title="金額 (元)", gridcolor="lightgrey", rangemode="tozero"),
            yaxis=dict(title="成員", categoryorder="array", categoryarray=self.reversed_members),
            barmode="stack",
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"),
            height=50*len(self.members)+200,
            margin=dict(l=100, r=50, t=70, b=50),
            autosize=True
        )
        return fig.to_html(**self.to_html_params)

    def generate_charts(self, output_dir="static/charts"):
        """
        組合所有圖表為單一 HTML 檔案並輸出。
        """
        charts_html = [
            self._chart_pay_vs_owed(),
            self._chart_balances(),
            self._chart_transfers(),
            self._chart_item_distribution(),
            self._chart_per_person_items()
        ]

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>分帳結果圖表</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ margin:0; padding:0; display:flex; flex-direction:column; align-items:center; }}
                .chart-container {{ width:100%; max-width:1200px; margin:20px 0; }}
            </style>
        </head>
        <body>
            {"".join(f'<div class="chart-container">{c}</div>' for c in charts_html)}
        </body>
        </html>
        """

        # 確保輸出目錄存在
        os.makedirs(output_dir, exist_ok=True)

        # 儲存到指定路徑
        chart_path = os.path.join(output_dir, "separate_charts.html")
        with open(chart_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        return chart_path