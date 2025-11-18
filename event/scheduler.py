# -*- coding: utf-8 -*-
#1）调整日程使其合理  2）消解冲突  3）事件插入+后续调整  4）事件插入  5）事件粒度对齐
import json
import os

from utils.IO import *
from datetime import datetime, timedelta
from utils.llm_call import *
from event.templates import *
import re
from datetime import datetime, timedelta
import holidays  # 需安装：pip install holidays

class Scheduler:
    def __init__(self,persona,file_path):
        """初始化日程调度器，创建空的日程存储结构"""
        self.schedule = {}  # 存储日程数据，格式如{"2025-01-01":["event1","event2"],...}
        # 保存原始事件信息，包括所有可能的时间范围
        self.raw_events = []
        self.persona = persona
        self.relation = ""
        self.final_schedule = {}
        self.decompose_schedule = {}
        d = persona
        if type(persona)==str:
            d = json.loads(persona)
        self.relation = d['relation']
        self.name = d['name']
        self.summary=""
        self.file_path = file_path
    def load_from_json(self, json_data,persona):
        """
        从JSON数据加载日程，支持起止时间为数组的格式

        参数:
            json_data: 符合指定格式的JSON数据列表
                       每个元素包含"主题事件"和"起止时间"，其中"起止时间"是数组
        """
        self.raw_events = json_data
        self.persona = persona
        self.relation = persona['relation']

    def load_finalevent(self,json):
        self.final_schedule = json
        return True

    def save_to_json(self):
        """
        将日程转换为JSON格式

        返回:
            符合指定格式的JSON数据列表，其中起止时间为数组
        """
        return self.raw_events

    def llm_call_sr(self,prompt,record=0):
        """调用大模型的函数"""
        res = llm_call_reason(prompt,context2,record=record)
        return res

    def llm_call_s(self,prompt,record=0):
        """调用大模型的函数"""
        res = llm_call(prompt,context2,record=record)
        return res

    def handle_profie(self,persona):
        prompt = template_analyse.format(persona=persona)
        res = llm_call(prompt, context,1)
        print(res)
        persona_summary = res
        self.summary = persona_summary
        return persona_summary

    def genevent_yearterm(self,persona):
        #基于persona提取重点+分配不同类型事件概率
        summary = self.handle_profie(persona)
        prompt = template_yearterm_eventgen.format(summary=summary)
        #第一轮生成，基于不同类别和概率。100件
        res1 = llm_call(prompt, context, 1)
        print(res1)
        prompt = template_yearterm_complete.format(persona=persona)
        #第二轮，基于画像，挖掘没在重点中的细节。100件
        res2 = llm_call(prompt, context, 1)
        print(res2)
        prompt = template_yearterm_complete_2.format()
        #第三轮，聚焦类别百分比平衡和人类共性事件。100件
        res3 = llm_call(prompt, context, 1)
        print(res3)
        prompt = template_yearterm_complete_3.format(summary=summary)
        #第四轮，聚焦波折、困难、负面事件。20件
        res4 = llm_call(prompt, context)
        print(res4)
        return [res1, res2, res3, res4]

    def extract_events_by_categories(self,file_path):
        CATEGORIES = [
            "Career & Education",
            "Relationships",
            "Living Situation",
            "Social & Lifestyle",
            "Finance",
            "Self Satisfy/Care & Entertainment",
            "Personal Growth",
            "Health & Well-being",
            "Unexpected Events",
            "Other"
        ]

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 初始化类别字典，存储事件列表和数量
        event_data = {
            category: {
                'events': [],  # 存储事件列表
                'count': 0  # 事件数量统计
            } for category in CATEGORIES
        }
        current_category = None

        # 按行处理内容
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否为类别标题行（宽松匹配）
            # 处理可能包含的特殊字符（*等）并提取核心文本
            cleaned_line = line.strip('*').strip('#').strip('+').strip()  # 去除常见标记符号
            core_category = cleaned_line.split('（')[0].split('(')[0].strip()  # 去除括号及内部内容

            # 宽松匹配类别（忽略大小写）
            matched_category = None
            for cat in CATEGORIES:
                if core_category.lower() == cat.lower():
                    matched_category = cat
                    break

            if matched_category:
                current_category = matched_category
                continue
            # 检查是否是其他可能的标题格式（包含"件"字的标题）
            elif '件' in cleaned_line and any(cat.lower() in cleaned_line.lower() for cat in CATEGORIES):
                for cat in CATEGORIES:
                    if cat.lower() in cleaned_line.lower():
                        current_category = cat
                        break
                else:
                    current_category = "Other"
                continue

            # 处理事件行（非标题行且当前有活跃类别）
            if current_category:
                # 事件行特征：包含日期（YYYY-MM-DD）或不匹配标题格式
                event = line
                # 去除可能的序号（如数字+.开头）
                if event and event[0].isdigit() and ('.' in event[:5] or '、' in event[:5]):
                    event = event.split('. ', 1)[1] if '. ' in event else event.split('、', 1)[
                        1] if '、' in event else event

                event_data[current_category]['events'].append(event)
                event_data[current_category]['count'] += 1

        return event_data

    def standard_data(self,data,type):
        # 相似性检查合并+标准化
        # name
        # date
        # id
        # type
        print(data)
        #合理性校检：画像匹配度、现实合理性、日期、频率与间隔、相似事件
        prompt = template_check.format(persona=self.persona, content=data)
        res1 = llm_call(prompt, context, 1)
        print(res1)
        #基于合理性校检结果作修改、删除
        prompt = template_process.format(content=data)
        res1 = llm_call(prompt, context)
        print(res1)
        data1 = json.loads(res1)
        instruction = {
            "Career & Education": "工作内容是否都涉及到，工作可能会有什么长期项目或任务或成果",
            "Relationships": "思考已有人物关系是否有没有涉及的",
            "Living Situation": "思考生活，家庭相关事件",
            "Social & Lifestyle": "思考社交，爱好，出行等相关事件",
            "Finance": "思考资产、财务、买卖、消费等相关事件",
            "Self Satisfy/Care & Entertainment": "思考娱乐，自我满足，自我追求等相关事件",
            "Personal Growth": "更多样化的事件",
            "Health & Well-being": "更多样化的事件",
            "Unexpected Events": "更多样化的事件",
            "Other": "更多样化的事件"
        }
        #多样性新增事件，补充删除事件
        prompt = template_process_2.format(type=type, content=res1, persona=self.persona, instruction=instruction[type])
        res2 = llm_call(prompt, context)
        print(res2)
        data2 = json.loads(res2)
        data = data1 + data2
        print(data)

        def split_array(arr, chunk_size=20):
            # 列表推导式：从0开始，每30个元素取一次
            return [arr[i:i + chunk_size] for i in range(0, len(arr), chunk_size)]

        res = []
        for i in split_array(data):
            #标准化事件schema，填充participant和location。
            prompt = template_process_1.format(content=i, relation=self.relation)
            res1 = llm_call(prompt, context)
            print(res1)
            res1 = json.loads(res1)
            res = res + res1
        print(res)
        return res

    def main_gen_event(self):
        txt_file_path = self.file_path+"process/output.txt"
        if not os.path.exists(txt_file_path):
            res = self.genevent_yearterm(self.persona)#persona处理+三轮事件生成
            with open(txt_file_path, "w", encoding="utf-8") as file: #记录，防止丢失
                for s in res:
                    file.write(s + "\n")  # 每个字符串后加换行符，实现分行存储
        # 提取事件并生成字符串数组
        event_stats = self.extract_events_by_categories(txt_file_path)#从记录文件中提取事件
        result = []
        for category, data in event_stats.items():#逐类别做json格式标准化+合理性校检
            print(f"【{category}】（共{data['count']}件）")
            res = self.standard_data(data['events'],category)
            print(f"【{category}】（生成{len(res)}件）")
            result = result + res
            with open(self.file_path+"process/event_1.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        self.raw_events = result

    def extract_events_by_month(self,target_month):
        """
        提取目标月份（如2）及之前的事件
        :param target_month: 目标月份（整数，1-12）
        :return: (x月事件字典, x月之前事件字典)
        """
        month_events = {}  # x月事件
        before_events = {}  # x月之前事件

        for date_str, events in self.schedule.items():
            # 解析年份和月份
            year = int(date_str.split("-")[0])
            month = int(date_str.split("-")[1])

            # 仅处理2025年数据（与您的日程年份一致）
            if year != 2025:
                continue

            if month == target_month:
                month_events[date_str] = events
            elif month < target_month or month > target_month:
                before_events[date_str] = events

        return month_events, before_events
    def extract_events_by_month2(self,target_month):
        """
        提取目标月份（如2）的事件
        :param target_month: 目标月份（整数，1-12）
        :return: (x月事件字典)
        """
        month_events = {}  # x月事件
        before_events = {}  # x月之前事件
        after_events = {}
        for date_str, events in self.final_schedule.items():
            # 解析年份和月份
            year = int(date_str.split("-")[0])
            month = int(date_str.split("-")[1])

            # 仅处理2025年数据（与您的日程年份一致）
            if year != 2025:
                continue

            elif month == target_month-1:
                before_events[date_str] = events


        for date_str, events in self.schedule.items():
            # 解析年份和月份
            year = int(date_str.split("-")[0])
            month = int(date_str.split("-")[1])

            # 仅处理2025年数据（与您的日程年份一致）
            if year != 2025:
                continue

            elif month == target_month:
                month_events[date_str] = events
            elif month == target_month+1:
                after_events[date_str] = events
        return month_events, before_events,after_events\

    def add_event(self, event_name, time_ranges):
        """
        添加单个事件

        参数:
            event_name: 事件名称
            time_ranges: 时间范围数组，每个元素为"YYYY-MM-DD至YYYY-MM-DD"格式的字符串
        """
        # 保存原始事件信息
        self.raw_events.append({
            "主题事件": event_name,
            "起止时间": time_ranges.copy()
        })

        # 解析每个时间范围
        for time_range in time_ranges:
            start_str, end_str = time_range.split("至")
            start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d").date()

            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str not in self.schedule:
                    self.schedule[date_str] = []
                self.schedule[date_str].append(event_name)
                current_date += timedelta(days=1)

        self.schedule = dict(sorted(self.schedule.items()))

    def split_and_convert_events(self,events):
        """
        将包含多日期的事件拆分为独立事件，并转换date字段为start_time和end_time
        处理逻辑：
        - 若date是数组（如["2025-01-01", "2025-01-05至2025-01-06"]），每个元素对应一个独立事件
        - 单个日期（无"至"）：start_time = end_time
        - 日期范围（有"至"）：分割为start_time和end_time
        :param events: 原始事件列表（date为数组，元素为单日期或日期范围）
        :return: 拆分并转换后的事件列表（每个事件对应一次发生）
        """
        processed_events = []
        for event in events:
            # 遍历date数组中的每个发生日期/范围
            for date_item in event["date"]:
                # 复制原事件基础信息（避免修改原始数据）
                new_event = event.copy()
                # 移除原date字段（后续替换为start/end）
                del new_event["date"]
                # 处理当前日期项
                date_str = date_item.strip()
                # 单日期（无"至"）
                if "至" not in date_str:
                    new_event["start_time"] = date_str
                    new_event["end_time"] = date_str
                # 日期范围（有"至"）
                else:
                    parts = date_str.split("至")
                    new_event["start_time"] = parts[0].strip()
                    new_event["end_time"] = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                # 添加到结果列表
                processed_events.append(new_event)
        return processed_events

    def sort_and_add_event_id(self,events):
        import re

        def get_start_time(text):
            """
            从文本中提取XX-XX-XX格式的日期（支持年-月-日，年可2位或4位）
            匹配规则：
            - 月：01-12，日：01-31
            - 年：2位（如25-01-08）或4位（如2025-01-08）
            示例：从"时间：2025-01-08 会议"中提取"2025-01-08"
            :param text: 可能包含日期的文本字符串
            :return: 提取到的XX-XX-XX格式日期字符串；若无则返回空字符串
            """
            # 正则匹配XX-XX-XX：年（2或4位数字）-月（2位）-日（2位）
            date_pattern = r"\b(\d{2}|\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b"
            match = re.search(date_pattern, text)
            return match.group(0) if match else ""
        """
        按start_time（"YYYY-MM-DD"格式）升序排序，为每个事件添加event_id
        :param events: 经split_and_extract_events处理后的事件列表
        :return: 带event_id的排序后事件列表
        """
        # "YYYY-MM-DD"格式可直接按字符串排序（无需转datetime），效率高且结果准确
        sorted_events = sorted(events, key=lambda x: get_start_time(x["start_time"]))

        # 分配event_id（从1开始递增）
        for idx, event in enumerate(sorted_events, start=1):
            event["event_id"] = idx

        return sorted_events
    def filter_events_by_date(self,processed_events, target_date):
        """
        从拆分后的事件列表中，抽取时间范围包含目标日期的事件
        :param processed_events: 经split_and_convert_events处理后的事件列表
        :param target_date: 目标日期，格式为"YYYY-MM-DD"
        :return: 符合条件的事件列表
        """
        try:
            target = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("目标日期格式错误，请使用'YYYY-MM-DD'")

        filtered = []
        for event in processed_events:
            start = datetime.strptime(event["start_time"], "%Y-%m-%d")
            end = datetime.strptime(event["end_time"], "%Y-%m-%d")
            if start <= target <= end:
                filtered.append(event)
        return filtered

    def get_events_by_month(self,events, target_year, target_month):
        def extract_date(date_str):
            """从start_time/end_time中提取YYYY-MM-DD格式日期（兼容含文本描述的情况）"""
            # 正则匹配YYYY-MM-DD格式（优先提取完整日期）
            pattern = r"\b20\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b"
            match = re.search(pattern, date_str)
            if match:
                return match.group(0)
            # 若未找到完整日期，返回空（后续视为单日期事件处理）
            return ""
        """
        提取与目标月份（target_year年target_month月）有时间重叠的所有事件
        :param events: 事件列表（含start_time和end_time字段）
        :param target_year: 目标年份（如2025）
        :param target_month: 目标月份（如1表示1月，6表示6月）
        :return: 符合条件的事件列表
        """
        # 计算目标月份的第一天和最后一天（用于判断时间重叠）
        # 月份最后一天：若为12月则次年1月1日减1天，否则当月+1月的1日减1天
        if target_month == 12:
            next_month_first_day = datetime(target_year + 1, 1, 1)
        else:
            next_month_first_day = datetime(target_year, target_month + 1, 1)
        target_month_start = datetime(target_year, target_month, 1)
        target_month_end = next_month_first_day - timedelta(days=1)

        result = []
        for event in events:
            # 提取事件的起止日期（处理含文本的情况）
            start_str = extract_date(event["start_time"])
            end_str = extract_date(event["end_time"])

            # 处理无法提取日期的情况（默认视为单日期事件，取文本中的年份和月份）
            if not start_str:
                start_str = event["start_time"]  # 保留原始文本用于提取年份
            if not end_str:
                end_str = start_str  # 无结束日期则默认与开始日期相同

            # 尝试解析事件的起止日期（兼容纯文本，提取年份和月份）
            try:
                # 优先按YYYY-MM-DD解析
                event_start = datetime.strptime(start_str, "%Y-%m-%d")
                event_end = datetime.strptime(end_str, "%Y-%m-%d")
            except:
                # 若解析失败，提取年份和月份（默认当月1日至当月最后一天）
                # 从文本中提取年份（优先20xx）
                year_match = re.search(r"20\d{2}", start_str)
                event_year = int(year_match.group()) if year_match else target_year
                # 从文本中提取月份（若未找到则默认事件在目标月份）
                month_match = re.search(r"(0?[1-9]|1[0-2])", start_str)
                event_month = int(month_match.group()) if month_match else target_month
                # 构造事件的起止日期（当月1日至当月最后一天）
                event_start = datetime(event_year, event_month, 1)
                if event_month == 12:
                    event_end = datetime(event_year, 12, 31)
                else:
                    event_end = datetime(event_year, event_month + 1, 1) - timedelta(days=1)

            # 判断事件时间范围与目标月份是否有重叠
            # 重叠条件：事件开始时间 <= 目标月份结束 且 事件结束时间 >= 目标月份开始
            if event_start <= target_month_end and event_start >= target_month_start:
                result.append(event)

        return result

    def get_month_calendar(self,year, month):
        """
        生成指定年月的每日星期几和节日对照表
        :param year: 年份（如2025）
        :param month: 月份（如1-12）
        :return: 列表，每个元素为{"date": "YYYY-MM-DD", "weekday": "星期X", "holiday": "节日名称或空"}
        """
        # 初始化中国节假日数据集
        cn_holidays = holidays.China(years=year)

        # 获取当月第一天和最后一天
        first_day = datetime(year, month, 1)
        # 计算当月最后一天（下个月第一天减1天）
        if month == 12:
            next_month_first = datetime(year + 1, 1, 1)
        else:
            next_month_first = datetime(year, month + 1, 1)
        last_day = (next_month_first - timedelta(days=1)).day

        calendar = []
        for day in range(1, last_day + 1):
            current_date = datetime(year, month, day)
            date_str = current_date.strftime("%Y-%m-%d")

            # 转换星期几（0=周一，6=周日 → 调整为"星期一"至"星期日"）
            weekday_map = {0: "星期一", 1: "星期二", 2: "星期三", 3: "星期四",
                           4: "星期五", 5: "星期六", 6: "星期日"}
            weekday = weekday_map[current_date.weekday()]

            # 获取节日（优先法定节假日，再传统节日）
            holiday = cn_holidays.get(current_date, "")

            calendar.append({
                "date": date_str,
                "weekday": weekday,
                "holiday": holiday
            })

        return calendar

    def event_decomposer(self,events,file):
        def split_array(arr, chunk_size=30):
            # 列表推导式：从0开始，每30个元素取一次
            return [arr[i:i + chunk_size] for i in range(0, len(arr), chunk_size)]
        t = 0
        ans = []
        for i in split_array(events,5):
            #对其中的事件进行推理、扩展、分解，形成原子事件序列
            prompt = template_event_decomposer.format(content=i, persona=self.persona)
            res = self.llm_call_s(prompt,1)
            print(res)
            #结构化生成，形成树形结构。
            prompt = template_process_3.format()
            res = self.llm_call_sr(prompt)
            print(res)
            data = json.loads(res)
            ans += data
            #保存
            with open(file+"event_decompose.json", "w", encoding="utf-8") as f:
                json.dump(ans, f, ensure_ascii=False, indent=2)
        self.decompose_schedule = ans

    def event_schedule(self,data,month):
        prompt = template_process_4.format(content=data, persona=self.persona,calendar=self.get_month_calendar(2025,month))
        res = self.llm_call_sr(prompt)
        print(res)
        data = json.loads(res)
        return data

    def merge_events_events(self,events_data):
        """
        处理事件数据，保留event_id小于500且首次出现的事件

        参数:
            events_data (list): 原始事件列表，每个元素为包含event_id的字典

        返回:
            list: 处理后的事件列表（去重且event_id < 500）
        """
        seen_ids = set()  # 记录已出现的event_id
        processed_events = []

        for event in events_data:
            # 提取event_id，若不存在则跳过（容错处理）
            event_id = event.get("event_id")
            if event_id is None:
                continue

            # 筛选条件：event_id < 500 且 未出现过
            if event_id < 500 and event_id not in seen_ids:
                seen_ids.add(event_id)
                processed_events.append(event)

        return processed_events

    def main_schedule_event(self,data,file):
        data = self.split_and_convert_events(data)#将重复事件分解为单个事件
        data = self.sort_and_add_event_id(data)#按起始时间顺序为事件分配id
        res = []
        for i in range(1,13):
            rest = self.event_schedule(self.get_events_by_month(data,2025,i),i) #逐月规划主题事件
            res+=rest
            with open(file+"process/event_2.json", "w", encoding="utf-8") as f: #保存主题事件
                json.dump(res, f, ensure_ascii=False, indent=2)
        self.final_schedule = res
    def main_decompose_event(self,data,file):
        # res = read_json_file(file+"event.json")
        res = self.merge_events_events(data) #做预处理，防止主题事件文件出错
        res = self.split_and_convert_events(res)
        res = self.sort_and_add_event_id(res)
        #分解事件
        self.event_decomposer(res,file)


# 使用示例
if __name__ == "__main__":
    # 创建调度器实例
    scheduler = Scheduler()
    persona = '''
     {
            "name": "徐静",
            "birth": "1993-07-10",
            "age": 28,
            "nationality": "汉",
            "home_address": {
                "province": "上海市",
                "city": "上海市",
                "district": "浦东新区",
                "street_name": "张杨路",
                "street_number": "123号"
            },
            "birth_place": {
                "province": "上海市",
                "city": "上海市",
                "district": "浦东新区"
            },
            "gender": "女",
            "education": "普通高中",
            "job": "服装店销售主管",
            "occupation": "时尚服饰零售企业",
            "workplace": {
                "province": "上海市",
                "city": "上海市",
                "district": "浦东新区",
                "street_name": "世纪大道",
                "street_number": "88号"
            },
            "belief": "不信仰宗教",
            "salary": 100000.0,
            "body": {
                "height": 158,
                "weight": 62.5,
                "BMI": 25.04
            },
            "family": "未婚",
            "personality": {
                "mbti": "ESFJ",
            },
            "hobbies": [
                "逛街购物",
                "听音乐",
                "羽毛球",
                “收藏纪念币”
            ],
            "favorite_foods": [
                "上海小笼包",
                "抹茶拿铁",
                "草莓蛋糕"
            ],
            "memory_date": [
                "2012-06-15：第一份工作入职纪念日",
                "2020-08-20：晋升销售主管日"
            ],
            "healthy_desc": "个人整体健康状况良好，无慢性病史，不定期进行健康体检，每年就医几次主要是常规检查。保持每周三次的体育锻炼习惯，注重个人护理和作息规律。",
            "lifestyle_desc": "日常生活高度依赖互联网，尤其喜欢使用社交媒体和购物APP获取信息。休闲活动包括每周两到三次逛街购物、在家听流行音乐、以及参加瑜伽锻炼。每月与朋友聚餐或看电影一次，每年会有一到两次短途旅行探亲或度假，生活风格偏向现代都市休闲型。",
            "economic_desc": "家庭年收入约10万元，拥有1处房产和家用汽车，目前没有股票、基金等投资活动，消费习惯偏谨慎，注重基本生活保障。",
            "work_desc": "在家族经营的服装零售企业工作，每周工作48小时，担任销售主管职务，负责店面管理和客户服务工作，工作稳定且与家庭生活紧密结合。",
            "experience_desc": "徐静自出生起便生活在上海浦东新区，2012年高中毕业后加入家族经营的服装零售企业，从基层销售员做起，通过努力逐步晋升为销售主管，负责店面运营和团队管理。她的工作经历稳定，与家庭事业深度绑定，积累了丰富的客户服务经验。",
            "description": "徐静是一位28岁的上海本地女性，高中毕业后在家族服装零售企业工作，现任销售主管。作为ESFJ人格类型，她重视家庭关系和社会和谐，性格热情负责。日常生活中，她喜欢逛街购物、听音乐和体育锻炼，收藏纪念币是她的独特爱好。健康状况良好，注重规律作息。经济状况稳定，拥有房产和汽车，消费观念务实。工作与家庭生活紧密结合，未来计划开设自己的服装店并保持家庭旅行传统。她与家人关系密切，在工作中善于与客户沟通，生活中注重与朋友保持联系。",
            "relation": [
                [
                    {
                        "name": "徐明",
                        "relation": "父亲",
                        "social circle": "家庭圈",
                        "gender": "男",
                        "age": 58,
                        "birth_date": "1965-03-12",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "浦东新区",
                            "street_name": "张杨路",
                            "street_number": "123号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "黄浦区"
                        },
                        "personality": "ISTJ",
                        "economic_level": "中产",
                        "occupation": "服装零售企业主",
                        "organization": "明芳服饰有限公司",
                        "nickname": "老爸",
                        "relation_description": "徐静的父亲，与妻子共同经营家族服装企业。年轻时从裁缝学徒做起，1990年创办服装店并逐步发展成连锁企业。现在虽已半退休，仍会每周到店里巡视指导。与女儿关系亲密，每周至少三次家庭聚餐，经常一起讨论店铺经营。支持女儿开设分店的计划，时常传授商业经验。"
                    },
                    {
                        "name": "李芳",
                        "relation": "母亲",
                        "social circle": "家庭圈",
                        "gender": "女",
                        "age": 56,
                        "birth_date": "1967-08-25",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "浦东新区",
                            "street_name": "张杨路",
                            "street_number": "123号"
                        },
                        "birth_place": {
                            "province": "江苏省",
                            "city": "苏州市",
                            "district": "姑苏区"
                        },
                        "personality": "ISFJ",
                        "economic_level": "中产",
                        "occupation": "服装企业财务主管",
                        "organization": "明芳服饰有限公司",
                        "nickname": "妈妈",
                        "relation_description": "徐静的母亲，负责家族企业的财务管理工作。原籍苏州，年轻时来上海打工认识徐明后结婚。性格温柔细心，不仅管理公司账务，还包办全家饮食起居。每天都会为女儿准备午餐便当，周末常一起逛街选购新款服装。母女关系融洽，经常交流生活琐事和情感问题。"
                    },
                    {
                        "name": "徐强",
                        "relation": "哥哥",
                        "social circle": "家庭圈",
                        "gender": "男",
                        "age": 32,
                        "birth_date": "1991-11-03",
                        "home_address": {
                            "province": "浙江省",
                            "city": "杭州市",
                            "district": "西湖区",
                            "street_name": "文三路",
                            "street_number": "456号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "浦东新区"
                        },
                        "personality": "ENTJ",
                        "economic_level": "中产",
                        "occupation": "电商运营总监",
                        "organization": "杭州某电商平台",
                        "nickname": "强哥",
                        "relation_description": "徐静的哥哥，大学毕业后选择在杭州发展电商事业。虽然不在家族企业工作，但经常为妹妹提供线上销售建议。每月会回上海探望父母，与妹妹见面聚餐。兄妹关系良好，通过微信保持日常联系，主要讨论工作发展和家庭事务。徐静计划开设分店时也会征求哥哥的意见。"
                    }
                ],
                [
                    {
                        "name": "王丽",
                        "relation": "闺蜜",
                        "social circle": "高中同学圈",
                        "gender": "女",
                        "age": 28,
                        "birth_date": "1993-03-15",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "徐汇区",
                            "street_name": "淮海中路",
                            "street_number": "456号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "徐汇区"
                        },
                        "personality": "ENFP",
                        "economic_level": "中产",
                        "occupation": "市场专员",
                        "organization": "上海某广告公司",
                        "nickname": "丽丽",
                        "relation_description": "王丽是徐静高中时期的同桌，两人从学生时代就建立了深厚的友谊。现在同在上海工作，每周会约一次逛街或下午茶，经常分享工作和生活琐事。她们保持着密切的微信联系，节假日会一起聚餐或看电影，偶尔还会约上其他高中同学聚会。"
                    },
                    {
                        "name": "张婷",
                        "relation": "闺蜜",
                        "social circle": "高中同学圈",
                        "gender": "女",
                        "age": 29,
                        "birth_date": "1992-11-22",
                        "home_address": {
                            "province": "浙江省",
                            "city": "杭州市",
                            "district": "西湖区",
                            "street_name": "文三路",
                            "street_number": "789号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "静安区"
                        },
                        "personality": "ISFJ",
                        "economic_level": "中产",
                        "occupation": "小学教师",
                        "organization": "杭州市某实验小学",
                        "nickname": "婷婷",
                        "relation_description": "张婷是徐静高中时期的好友，大学毕业后选择到杭州发展。虽然分隔两地，但她们每月都会视频通话两到三次，分享各自的生活近况。每年春节张婷回上海探亲时，她们必定会见面聚餐，平时通过微信保持密切联系，互相支持对方的事业发展。"
                    },
                    {
                        "name": "赵小美",
                        "relation": "高中同学",
                        "social circle": "高中同学圈",
                        "gender": "女",
                        "age": 28,
                        "birth_date": "1993-09-08",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "闵行区",
                            "street_name": "虹梅路",
                            "street_number": "321号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "闵行区"
                        },
                        "personality": "ISTJ",
                        "economic_level": "小康",
                        "occupation": "会计",
                        "organization": "上海某会计师事务所",
                        "nickname": "小美",
                        "relation_description": "赵小美是徐静高中同学，现在同在上海工作。她们保持着每月一次的聚会频率，通常是在周末一起吃饭或逛街。作为高中同学圈的核心成员，赵小美经常组织同学聚会，与徐静及其他同学保持着稳定的联系，彼此在工作中也会互相提供建议和支持。"
                    },
                    {
                        "name": "钱多多",
                        "relation": "高中同学",
                        "social circle": "高中同学圈",
                        "gender": "女",
                        "age": 28,
                        "birth_date": "1993-12-03",
                        "home_address": {
                            "province": "广东省",
                            "city": "深圳市",
                            "district": "南山区",
                            "street_name": "科技园路",
                            "street_number": "654号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "黄浦区"
                        },
                        "personality": "ENTP",
                        "economic_level": "中产",
                        "occupation": "互联网产品经理",
                        "organization": "深圳某科技公司",
                        "nickname": "多多",
                        "relation_description": "钱多多是徐静的高中同学，大学毕业后选择到深圳发展。她们主要通过微信保持联系，每季度会视频通话一次。钱多多每年回上海探亲时会与徐静见面，平时在同学群里活跃互动。虽然距离较远，但她们仍保持着深厚的同学情谊，经常分享职场经验和生活趣事。"
                    }
                ],
                [
                    {
                        "name": "陈丽",
                        "relation": "同事",
                        "social circle": "工作圈",
                        "gender": "女",
                        "age": 26,
                        "birth_date": "1997-03-15",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "浦东新区",
                            "street_name": "金桥路",
                            "street_number": "456号"
                        },
                        "birth_place": {
                            "province": "江苏省",
                            "city": "南京市"
                        },
                        "personality": "ENFP",
                        "economic_level": "中等",
                        "occupation": "服装销售员",
                        "organization": "时尚服饰零售企业",
                        "nickname": "丽丽",
                        "relation_description": "陈丽是徐静在服装店的同事，两人相识于2019年工作期间。作为销售团队的核心成员，她们每天共同处理店面事务，配合默契。工作之余会一起在商场餐厅吃午餐，周末偶尔相约逛街淘货。两人居住在同一城区，保持每周5天的工作接触和每月1-2次的私人聚会。"
                    },
                    {
                        "name": "刘伟",
                        "relation": "同事",
                        "social circle": "工作圈",
                        "gender": "男",
                        "age": 30,
                        "birth_date": "1993-11-22",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "闵行区",
                            "street_name": "虹梅路",
                            "street_number": "789号"
                        },
                        "birth_place": {
                            "province": "浙江省",
                            "city": "杭州市"
                        },
                        "personality": "ISTJ",
                        "economic_level": "中等",
                        "occupation": "仓储管理员",
                        "organization": "时尚服饰零售企业",
                        "nickname": "伟哥",
                        "relation_description": "刘伟负责店铺的仓储管理工作，与徐静在工作中密切配合已有3年。他做事严谨认真，经常协助徐静处理货品调配和库存盘点。两人主要在工作场合交流，偶尔参加公司组织的团建活动。虽然私下交往不多，但工作关系稳定可靠，保持每天工作时间的常规互动。"
                    },
                    {
                        "name": "赵敏",
                        "relation": "同事",
                        "social circle": "工作圈",
                        "gender": "女",
                        "age": 29,
                        "birth_date": "1994-05-08",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "徐汇区",
                            "street_name": "淮海中路",
                            "street_number": "321号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市"
                        },
                        "personality": "ESFP",
                        "economic_level": "中等",
                        "occupation": "销售助理",
                        "organization": "时尚服饰零售企业",
                        "nickname": "敏敏",
                        "relation_description": "赵敏是徐静最亲密的同事之一，两人既是工作搭档也是朋友。她们经常一起讨论销售策略，下班后偶尔相约喝咖啡聊天。赵敏性格活泼开朗，与徐静在工作上形成良好互补。两人保持每周工作日的密切合作，每月会有2-3次私人聚会，关系融洽而稳定。"
                    },
                    {
                        "name": "孙老板",
                        "relation": "供应商",
                        "social circle": "工作圈",
                        "gender": "男",
                        "age": 45,
                        "birth_date": "1978-09-12",
                        "home_address": {
                            "province": "广东省",
                            "city": "广州市",
                            "district": "天河区",
                            "street_name": "体育西路",
                            "street_number": "668号"
                        },
                        "birth_place": {
                            "province": "广东省",
                            "city": "潮州市"
                        },
                        "personality": "ENTJ",
                        "economic_level": "富裕",
                        "occupation": "服装厂老板",
                        "organization": "广州时尚制衣厂",
                        "nickname": "孙总",
                        "relation_description": "孙老板是服装店的主要供应商，与徐静保持业务往来已有5年。他每季度会来上海考察市场，徐静负责接待和洽谈订单。两人主要通过电话和微信沟通业务，见面频率较低但合作稳定。孙老板注重产品质量和商业信誉，与徐静建立了相互信任的工作关系。"
                    },
                    {
                        "name": "周经理",
                        "relation": "商场经理",
                        "social circle": "工作圈",
                        "gender": "男",
                        "age": 38,
                        "birth_date": "1985-12-03",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "静安区",
                            "street_name": "南京西路",
                            "street_number": "1000号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市"
                        },
                        "personality": "ESTJ",
                        "economic_level": "中高",
                        "occupation": "商场运营经理",
                        "organization": "世纪商场管理公司",
                        "nickname": "周经理",
                        "relation_description": "周经理是店铺所在商场的运营负责人，与徐静在工作上有频繁的业务往来。他负责商场的日常管理和商户协调，徐静经常需要与他沟通店铺运营事宜。两人每月会有1-2次正式会议，平时通过商场内部系统保持联系。周经理处事专业严谨，与徐静保持着良好的工作关系。"
                    }
                ],
                [
                    {
                        "name": "孙秀英",
                        "relation": "邻居",
                        "social circle": "社区圈",
                        "gender": "女",
                        "age": 65,
                        "birth_date": "1959-03-22",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "浦东新区",
                            "street_name": "张杨路",
                            "street_number": "121号"
                        },
                        "birth_place": {
                            "province": "江苏省",
                            "city": "南通市"
                        },
                        "personality": "ISFJ",
                        "economic_level": "中等",
                        "occupation": "退休教师",
                        "organization": "浦东新区实验小学（已退休）",
                        "nickname": "孙阿姨",
                        "relation_description": "孙阿姨是徐静家对门的老邻居，退休前在附近小学任教。两人因社区活动相识，孙阿姨经常关心徐静的工作生活，会分享自己做的家常菜。现在主要通过微信保持联系，每周会碰面两三次，一起在小区散步或喝茶聊天。孙阿姨把徐静当作自家晚辈般照顾，逢年过节会互相赠送小礼物。"
                    }
                ],
                [
                    {
                        "name": "周晓雯",
                        "relation": "瑜伽教练",
                        "social circle": "瑜伽圈",
                        "gender": "女",
                        "age": 32,
                        "birth_date": "1991-03-15",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "徐汇区",
                            "street_name": "淮海中路",
                            "street_number": "356号"
                        },
                        "birth_place": {
                            "province": "浙江省",
                            "city": "杭州市"
                        },
                        "personality": "ENFJ",
                        "economic_level": "中产",
                        "occupation": "瑜伽馆",
                        "organization": "静心瑜伽工作室",
                        "nickname": "周老师",
                        "relation_description": "周晓雯是徐静在静心瑜伽工作室的专职教练，拥有8年瑜伽教学经验。两人通过2019年的团体课程相识，现在保持每周三次的私教课联系。上课时周教练会针对徐静的身体状况设计个性化训练方案，课后偶尔会交流健康饮食心得。虽然周教练住在徐汇区，但工作室距离徐静工作地点仅15分钟车程，教学关系稳定持续。"
                    },
                    {
                        "name": "李娜",
                        "relation": "瑜伽伙伴",
                        "social circle": "瑜伽圈",
                        "gender": "女",
                        "age": 29,
                        "birth_date": "1994-09-22",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "浦东新区",
                            "street_name": "陆家嘴环路",
                            "street_number": "188号"
                        },
                        "birth_place": {
                            "province": "江苏省",
                            "city": "苏州市"
                        },
                        "personality": "ISFP",
                        "economic_level": "中产",
                        "occupation": "银行职员",
                        "organization": "浦东发展银行",
                        "nickname": "娜娜",
                        "relation_description": "李娜是徐静在瑜伽课上认识的固定练习伙伴，同在周教练的早课班练习两年。作为银行柜员，李娜下班后常与徐静结伴练习瑜伽，周末偶尔一起逛商场喝下午茶。两人住在同一行政区，每月会约两三次课后聚餐，交流工作和生活近况。李娜性格内向但体贴，经常与徐静分享护肤心得，是瑜伽圈里最亲近的练习搭档。"
                    },
                    {
                        "name": "王芳",
                        "relation": "瑜伽伙伴",
                        "social circle": "瑜伽圈",
                        "gender": "女",
                        "age": 31,
                        "birth_date": "1992-12-05",
                        "home_address": {
                            "province": "江苏省",
                            "city": "南京市",
                            "district": "鼓楼区",
                            "street_name": "北京西路",
                            "street_number": "72号"
                        },
                        "birth_place": {
                            "province": "安徽省",
                            "city": "合肥市"
                        },
                        "personality": "ENTP",
                        "economic_level": "小康",
                        "occupation": "自由职业者",
                        "organization": "自媒体工作室",
                        "nickname": "芳芳",
                        "relation_description": "王芳原是上海工作的瑜伽同伴，2021年移居南京发展自媒体事业，但仍通过线上群组与徐静保持联系。两人在2018年瑜伽进修班相识，曾经常结伴参加周末瑜伽工作坊。现在主要通过微信群分享瑜伽视频和健康资讯，每年王芳回沪探亲时会与徐静、李娜小聚。虽然异地发展，但三人仍维持着瑜伽圈的友谊，经常互相关注彼此的生活动态。"
                    }
                ],
                [
                    {
                        "name": "张秀英",
                        "relation": "姨妈",
                        "social circle": "亲戚圈",
                        "gender": "女",
                        "age": 58,
                        "birth_date": "1965-03-22",
                        "home_address": {
                            "province": "江苏省",
                            "city": "南京市",
                            "district": "鼓楼区",
                            "street_name": "中山北路",
                            "street_number": "256号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "黄浦区"
                        },
                        "personality": "ISFJ",
                        "economic_level": "小康",
                        "occupation": "退休教师",
                        "organization": "南京市鼓楼区实验小学",
                        "nickname": "张阿姨",
                        "relation_description": "张秀英是徐静母亲的姐姐，退休前在南京担任小学教师。两人虽然分居上海和南京，但每月会通过视频通话联系两到三次，主要聊家常和健康话题。每年春节和国庆节徐静会去南京探望，一起逛夫子庙、品尝南京小吃。张秀英经常关心徐静的婚姻和工作情况，是徐静重要的长辈倾诉对象。"
                    },
                    {
                        "name": "刘建国",
                        "relation": "舅舅",
                        "social circle": "亲戚圈",
                        "gender": "男",
                        "age": 55,
                        "birth_date": "1968-09-15",
                        "home_address": {
                            "province": "浙江省",
                            "city": "杭州市",
                            "district": "西湖区",
                            "street_name": "文三路",
                            "street_number": "189号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "静安区"
                        },
                        "personality": "ESTP",
                        "economic_level": "富裕",
                        "occupation": "餐饮企业主",
                        "organization": "杭帮菜餐饮连锁集团",
                        "nickname": "刘叔叔",
                        "relation_description": "刘建国是徐静的舅舅，在杭州经营连锁餐饮企业。他性格开朗，经常给徐静提供创业建议。两人每季度通一次电话，主要讨论商业经营和市场趋势。每年徐静会专程到杭州品尝舅舅的新菜品，同时考察当地服装市场。刘建国曾资助徐静参加商业管理培训，是她在事业上的重要支持者。"
                    },
                    {
                        "name": "陈明",
                        "relation": "表弟",
                        "social circle": "亲戚圈",
                        "gender": "男",
                        "age": 25,
                        "birth_date": "1998-12-03",
                        "home_address": {
                            "province": "广东省",
                            "city": "深圳市",
                            "district": "南山区",
                            "street_name": "科技园路",
                            "street_number": "66号"
                        },
                        "birth_place": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "浦东新区"
                        },
                        "personality": "ENTJ",
                        "economic_level": "中产",
                        "occupation": "互联网产品经理",
                        "organization": "深圳某科技公司",
                        "nickname": "小明",
                        "relation_description": "陈明是徐静姑姑的儿子，目前在深圳从事互联网行业。两人从小一起在上海长大，现在主要通过微信保持联系，每周会分享生活趣事和工作心得。陈明经常给徐静推荐新的购物APP和时尚资讯，徐静则向他请教数字化营销知识。每年春节家庭聚会时见面，会一起逛商场、讨论最新的科技产品。"
                    }
                ],
                [
                    {
                        "name": "吴明远",
                        "relation": "家庭医生",
                        "social circle": "医疗圈",
                        "gender": "男",
                        "age": 45,
                        "birth_date": "1978-03-22",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "徐汇区",
                            "street_name": "淮海中路",
                            "street_number": "568号"
                        },
                        "birth_place": {
                            "province": "江苏省",
                            "city": "南京市",
                            "district": "鼓楼区"
                        },
                        "personality": "ISTJ",
                        "economic_level": "中产",
                        "occupation": "全科医生",
                        "organization": "浦东新区社区卫生服务中心",
                        "nickname": "吴医生",
                        "relation_description": "吴医生是徐静的家庭医生，五年前通过社区健康管理项目相识。他每月为徐静提供一次健康咨询，主要通过微信进行线上沟通，偶尔在社区卫生服务中心面诊。吴医生性格严谨负责，擅长慢性病管理和健康指导，与徐静保持着专业而友好的医患关系。"
                    }
                ],
                [
                    {
                        "name": "郑明辉",
                        "relation": "健身教练",
                        "social circle": "健身圈",
                        "gender": "男",
                        "age": 32,
                        "birth_date": "1992-03-15",
                        "home_address": {
                            "province": "上海市",
                            "city": "上海市",
                            "district": "徐汇区",
                            "street_name": "漕溪北路",
                            "street_number": "258号"
                        },
                        "birth_place": {
                            "province": "江苏省",
                            "city": "南京市",
                            "district": "鼓楼区"
                        },
                        "personality": "ESTP",
                        "economic_level": "中产",
                        "occupation": "健身教练",
                        "organization": "力健健身俱乐部",
                        "nickname": "郑教练",
                        "relation_description": "郑明辉是徐静在力健健身俱乐部的私人教练，两人通过健身课程相识已有两年。他擅长制定个性化训练计划，每周指导徐静进行三次力量训练和有氧运动。平时主要通过微信沟通训练安排和饮食建议，每月会组织会员户外拓展活动。郑教练性格开朗务实，注重训练效果的同时也会关心会员的生活状态。"
                    }
                ],
                [
                    {
                        "name": "王明远",
                        "relation": "纪念币藏友",
                        "social circle": "收藏圈",
                        "gender": "男",
                        "age": 45,
                        "birth_date": "1978-03-15",
                        "home_address": {
                            "province": "北京市",
                            "city": "北京市",
                            "district": "朝阳区",
                            "street_name": "建国门外大街",
                            "street_number": "88号"
                        },
                        "birth_place": {
                            "province": "北京市",
                            "city": "北京市"
                        },
                        "personality": "ISTJ",
                        "economic_level": "中产",
                        "occupation": "金融投资顾问",
                        "organization": "北京金融投资有限公司",
                        "nickname": "老王",
                        "relation_description": "王明远是徐静在纪念币收藏展会上认识的藏友，两人因共同爱好结缘。他目前在北京市从事金融投资工作，虽然分隔两地，但每月会通过线上交流收藏心得，偶尔会互相邮寄稀有纪念币。每年徐静去北京出差时会约见面，一起参观钱币博物馆或古玩市场。"
                    }
                ],
                [
                    {
                        "name": "李雪梅",
                        "relation": "同行朋友",
                        "social circle": "行业圈",
                        "gender": "女",
                        "age": 32,
                        "birth_date": "1991-03-15",
                        "home_address": {
                            "province": "浙江省",
                            "city": "杭州市",
                            "district": "西湖区",
                            "street_name": "文三路",
                            "street_number": "456号"
                        },
                        "birth_place": {
                            "province": "浙江省",
                            "city": "杭州市"
                        },
                        "personality": "ENTJ",
                        "economic_level": "中产",
                        "occupation": "区域运营经理",
                        "organization": "江南时尚集团",
                        "nickname": "雪梅姐",
                        "relation_description": "李雪梅是徐静在行业交流会上认识的同行朋友，两人因对服装零售业的共同兴趣而结缘。她们平时主要通过微信交流行业动态，每季度会在上海或杭州见面一次，通常选择在商圈咖啡馆讨论市场趋势和经营管理经验。虽然分处两地，但会互相推荐优质供应商和客户资源，去年还合作举办过跨区域促销活动。"
                    }
                ],
                [
                    {
                        "name": "张明远",
                        "relation": "熟客",
                        "social circle": "客户圈",
                        "gender": "男",
                        "age": 35,
                        "birth_date": "1988-03-15",
                        "home_address": {
                            "province": "浙江省",
                            "city": "杭州市",
                            "district": "西湖区",
                            "street_name": "文三路",
                            "street_number": "456号"
                        },
                        "birth_place": {
                            "province": "浙江省",
                            "city": "宁波市"
                        },
                        "personality": "ENTJ",
                        "economic_level": "中产",
                        "occupation": "互联网公司市场总监",
                        "organization": "杭州某科技股份有限公司",
                        "nickname": "张总",
                        "relation_description": "张明远是徐静服装店的长期客户，五年前因工作需要购买商务服装而结识。他每季度会从杭州来上海出差时到店选购，偏好简约商务风格。两人保持着专业的客户关系，主要通过微信沟通新款到货信息，平均每两月联系一次。见面时徐静会为他提供专业的穿搭建议，偶尔会聊及各自的工作近况。"
                    }
                ]
            ]
        }
    '''
    json_data = read_json_file('event_data/raw_event/event_final.json')
    scheduler.load_from_json(json_data,persona)
    scheduler.main_schedule_event(scheduler.raw_events,'event_data/raw_event/')
    scheduler.main_decompose_event(scheduler.final_schedule,'event_data/raw_event/')











