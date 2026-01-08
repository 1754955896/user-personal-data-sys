import json
import os
import csv
from rename_phone_data_fields import rename_fields_in_file

# 创建测试JSON文件
test_data = [
    {"name": "张三", "age": 30, "city": "北京"}
]

test_file_path = "D:\pyCharmProjects\pythonProject4\test_duplicate_fields.json"

# 写入测试数据
with open(test_file_path, 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

# 定义字段映射（包含重复的新增字段）
field_mapping = {
    "name": "full_name",  # 正常字段映射
    "age": "age",  # 正常字段映射（保持原名）
    "+1": "city",  # 新增字段，与原字段名重复
    "+2": "age",  # 新增字段，与正常映射值重复
    "+3": "country"  # 新增字段，无重复
}

print("测试字段映射:")
print(field_mapping)
print("\n开始处理...")

# 调用函数
success = rename_fields_in_file(test_file_path, field_mapping)

if success:
    print("\n处理成功！")
    print("\n查看生成的CSV文件内容:")
    csv_file_path = test_file_path.replace('.json', '.csv')
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("\n处理失败！")

# 清理测试文件
if os.path.exists(test_file_path):
    os.remove(test_file_path)
    print(f"\n已删除测试JSON文件: {test_file_path}")

if os.path.exists(csv_file_path):
    os.remove(csv_file_path)
    print(f"已删除测试CSV文件: {csv_file_path}")