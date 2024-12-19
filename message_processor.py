import re
import os

class ExpenseManager:
    def __init__(self, members=None, payments=None):
        # 初始化屬性
        self.members = members if members else []     # 成員名單
        self.payments = payments if payments else []  # 付款記錄
        self.detailed_split = []                      # 詳細分攤資料
        self.balances = {}                            # 每人餘額
        self.transfers = []                           # 轉帳方案

    def process_members(self, input_members):
        # 處理成員輸入（不得重複、不得為空）
        self.members = input_members.strip().split("、")
        if not self.members:
            raise ValueError("成員名單不得為空。")
        if len(self.members) != len(set(self.members)):
            dup = [m for m in self.members if self.members.count(m) > 1]
            raise ValueError(f"重複成員：{dup}")
        return self.members

    def process_payments(self, input_payments):
        # 處理付款紀錄：格式 "X付了Y元Z"
        ptn = r"(.+)付了(.+)元(.+)"
        self.payments = []
        for line in input_payments.strip().split('\n'):
            match = re.match(ptn, line)
            if not match:
                raise ValueError(f"格式錯誤：{line}")
            payer, amt_str, item = match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
            try:
                amount = float(amt_str)
            except ValueError:
                raise ValueError(f"金額格式錯誤：{amt_str}")
            if payer not in self.members:
                raise ValueError(f"付款人 '{payer}' 不在成員名單中。")
            self.payments.append({
                "payer": payer,
                "amount": amount,
                "item": item,
                "participants": self.members[:]
            })
        return self.payments

    def process_splits(self, input_splits):
        # 處理"沒"字句，排除不參與者，例如："晚餐沒Alice、Bob"
        pay_map = {p["item"]: p for p in self.payments}
        for line in input_splits.strip().split('\n'):
            if "沒" in line:
                item, excluded_str = line.split("沒", 1)
                item = item.strip()
                excluded = excluded_str.strip().split("、") if excluded_str.strip() else []
                if item not in pay_map:
                    raise ValueError(f"無此項目：{item}")
                pay_map[item]["participants"] = [m for m in pay_map[item]["participants"] if m not in excluded]

        # 計算分攤結果
        self.detailed_split = []
        for p in self.payments:
            part = p["participants"]
            per_person = round(p["amount"] / len(part), 2) if part else 0
            self.detailed_split.append({
                "item": p["item"],
                "amount": p["amount"],
                "participants": part,
                "per_person": per_person,
                "payer": p["payer"]
            })
        return self.detailed_split

    def calculate_and_format(self):
        # 計算每人多/少付狀況
        total_paid = {m: 0 for m in self.members}
        total_owed = {m: 0 for m in self.members}

        for d in self.detailed_split:
            total_paid[d["payer"]] += d["amount"]
            for pt in d["participants"]:
                total_owed[pt] += d["per_person"]

        self.balances = {m: round(total_paid[m] - total_owed[m], 2) for m in self.members}
        self.transfers = self.calculate_transfers(self.balances)
        return self.format_output(self.detailed_split, self.balances, self.transfers, total_paid, total_owed)

    def calculate_transfers(self, balances):
        # 根據餘額計算轉帳方案
        transfers = []
        creditors = {m: b for m, b in balances.items() if b > 0}
        debtors = {m: -b for m, b in balances.items() if b < 0}

        while creditors and debtors:
            cred = max(creditors.items(), key=lambda x: x[1])
            debt = max(debtors.items(), key=lambda x: x[1])
            amt = min(cred[1], debt[1])
            transfers.append(f"{debt[0]} → {cred[0]} {self.format_number(amt)} 元")
            creditors[cred[0]] -= amt
            debtors[debt[0]] -= amt
            if creditors[cred[0]] <= 0.001:
                del creditors[cred[0]]
            if debtors[debt[0]] <= 0.001:
                del debtors[debt[0]]

        return transfers

    def format_output(self, detailed_split, balances, transfers, total_paid, total_owed):
        # 確保 fmt() 回傳字串
        def fmt(n):
            val = self.format_number(n)
            return str(val)  # 強制轉字串，避免 join 時發生型態錯誤

        out = "【一、成員名單】\n" + "、".join(self.members) + "\n\n"
        out += "【二、付款記錄】\n"
        for p in self.payments:
            out += f'{p["payer"]}付了${fmt(p["amount"])}({p["item"]})\n'
        out += "\n【三、分攤情況】\n"
        for d in detailed_split:
            out += (f'{d["item"]}${fmt(d["amount"])}\n'
                    f'- 參與者：{"、".join(d["participants"])}\n'
                    f'- 每人應付：{fmt(d["per_person"])} 元\n')
        out += "\n【四、每人結算金額】\n"
        for m in self.members:
            bal = balances[m]
            status = "多付" if bal > 0 else "少付"
            # 將 owed_items 全轉成字串
            owed_items = [fmt(d["per_person"]) if m in d["participants"] else "0" for d in detailed_split]
            out += (f'{m}：{status} {fmt(abs(bal))} 元\n'
                    f'  詳細計算：({fmt(total_paid[m])} - {" - ".join(owed_items)})\n')

        out += "\n【五、轉帳方案】\n"
        out += "\n".join(transfers) + "\n" if transfers else "無需轉帳，一切平衡！\n"
        return out

    def get_summary(self):
        # 傳回摘要資料
        return {
            "members": self.members,
            "payments": self.payments,
            "detailed_split": self.detailed_split,
            "balances": self.balances,
            "transfers": self.transfers
        }

    @staticmethod
    def format_number(num):
        # 若為整數則轉為 int 否則四捨五入至2位小數
        return int(num) if num == int(num) else round(num, 2)