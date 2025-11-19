import json
import re
from utils.llm_call import llm_call, llm_call_reason
from persona.gen_utils.template import template, template_refine, template_relation_1, template_person
from utils.random_ref import JSONRandomSelector, convert_list_to_string


class PersonaGenerator:
    def __init__(self, ref_json_file_path="../data_persona/profile_ref.json"):
        """初始化个人画像生成器"""
        self.selector = JSONRandomSelector(ref_json_file_path)
        self.example_relation = '''
        [
          {"name":"","relation":""，“social circle”：“”},
          {"name":"","relation":""，“social circle”：“”}
        ]
            - **name**：该联系人的姓名。
            - **relation**：联系人与个体之间的关系。
            - **social circle**：该联系人所属社交圈。
        '''
        self.example_person = '''
        {
                "name": "韩海生",
                "relation": "父亲",
                "social circle":"家庭圈",
                "gender": "男",
                "age": 52,
                "birth_date": "1973-11-06",
                "home_address": {
                  "province": "甘肃省",
                  "city": "临夏回族自治州",
                  "district": "临夏市",
                  "street_name": "红园街道民丰路",
                  "street_number": "127号"
                },
                "birth_place": {
                  "province": "陕西省",
                  "city": "咸阳市"
                },
                "personality": "ESTJ",
                "economic_level": "小康",
                "occupation": "汽车整车制造人员",
                "organization": "临夏民族汽车配件厂",
                "nickname": "老爸",
                "relation_description":""
              }
        '''

    def refer_const(self):
        """生成参考数据"""
        hobby = self.selector.random_select("兴趣", 12)
        aim = self.selector.random_select("目标规划", 6)
        value = self.selector.random_select("价值观", 6)

        ref = ""
        ref += f"\"hobbies\":{convert_list_to_string(hobby)} ，选取4-6个符合用户特征的合理爱好，同时根据上下文补充一个其他爱好；\n"
        ref += f"\"aim\":{convert_list_to_string(aim)}，可选取一到两个目标并具体化（若无合理目标可不选）；\n"
        ref += f"\"traits\":{convert_list_to_string(value)}，可选取2-4个合理且符合该用户的价值观；\n"
        return ref

    def generate_profile(self, profile_str):
        """生成基础个人画像"""
        result = template.format(JSON=profile_str, Ref=self.refer_const())
        result = llm_call(result)
        print(result)
        return result

    def generate_refine(self, profile):
        """优化个人画像"""
        result = template_refine.format(JSON=profile)
        result = llm_call_reason(result)
        print(result)
        return result

    def generate_relation(self, profile):
        """生成人际关系"""
        result = template_relation_1.format(JSON=profile, example=self.example_relation)
        result = llm_call(result)
        print(result)
        return result

    def generate_people(self, profile, circle):
        """生成具体人物信息"""
        result = template_person.format(
            JSON=circle,
            example=self.example_person,
            profile=profile
        )
        result = llm_call(result)
        print(result)
        return result

    def group_by_social_circle(self, data):
        """按社交圈分组"""
        groups = {}
        for person in data:
            circle = person["social circle"]
            if circle not in groups:
                groups[circle] = []
            groups[circle].append(person)
        return groups

    def generate_person(self, profile, profile_rl, index):
        """生成人物关系详情"""
        json_data = []
        relation_list = json.loads(profile_rl)
        grouped_data = self.group_by_social_circle(relation_list)

        person_str = profile
        for circle, people in grouped_data.items():
            relation_str = json.dumps(people, ensure_ascii=False, indent=2)
            llm_str = self.generate_people(person_str, relation_str)
            try:
                json_data.append(self.parse_llm_json_response(llm_str))
                # print(f"已处理第{index + 1}条数据_person")
            except json.JSONDecodeError as e:
                print(f"第{index + 1}条数据JSON转换失败_person：", e)
        return json_data

    def parse_llm_json_response(self, llm_response):
        """解析LLM返回的JSON数据"""
        pattern = r'```json\s*(.*?)\s*```'
        match = re.search(pattern, llm_response, re.DOTALL)

        if not match:
            return json.loads(llm_response)

        json_str = match.group(1)
        return json.loads(json_str)

    def gen_profile(self, start_id, end_id,in_file_path,out_file_path):
        """生成完整个人画像数据"""
        json_data = []
        try:
            with open(in_file_path, 'r', encoding='utf-8') as f:
                people_list = json.load(f)


            for i, person in enumerate(people_list):
                if i < start_id:
                    continue
                if i >= end_id:
                    break

                person_str = json.dumps(person, ensure_ascii=False, indent=2)
                llm_str = self.generate_profile(person_str)
                llm_str = self.generate_refine(llm_str)
                rl = self.generate_relation(llm_str)
                rl_data = self.generate_person(llm_str, rl, i)

                data = self.parse_llm_json_response(llm_str)
                if 'note' in data:
                    del data['note']
                data['relation'] = rl_data

                try:
                    json_data.append(data)
                    print(f"已处理第{i + 1}条数据")
                except json.JSONDecodeError as e:
                    print(f"第{i + 1}条数据JSON转换失败：", e)

            with open(out_file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            return json_data

        except Exception as e:
            print("处理过程出错，错误原因：", e)
            return None
        finally:
            # 无论是否出错，都尝试写入已收集的数据
            if json_data:
                with open(out_file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                print(f"已保存部分数据到 {out_file_path}")



# 使用示例
if __name__ == "__main__":
    generator = PersonaGenerator()
    generator.gen_profile(start_id=0, end_id=1)