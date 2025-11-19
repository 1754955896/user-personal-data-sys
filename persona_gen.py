from persona.persona_gen import *
#输入：profile_ref.json参考数据库、processed_features.json从问卷数据预处理出的格式化基础数据
#输出：persona_list.json
file_path = 'data/persona/'
start = 0
end = 1 #用于控制从基础数据processed_features.json选择哪些people生成


#数据库json地址
generator = PersonaGenerator(file_path+'profile_ref.json')
generator.gen_profile(start_id=start, end_id=end,in_file_path=file_path+'processed_features.json',out_file_path=file_path+'persona_list.json')