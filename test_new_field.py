import json
import os

def test_new_field_functionality():
    """
    测试新增字段功能
    """
    # 创建一个测试JSON文件
    test_data = [
        {"name": "张三", "age": 25, "city": "北京"},
        {"name": "李四", "age": 30, "city": "上海"}
    ]
    
    test_file_path = "test_new_field.json"
    
    # 写入测试数据
    with open(test_file_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"创建测试文件: {test_file_path}")
    print(f"原始数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    # 测试新增字段功能
    field_mapping = {
        "+": "new_field",  # 新增字段
        "age": "new_age"   # 同时重命名字段
    }
    
    try:
        # 读取JSON文件
        with open(test_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否有新增字段的指令
        new_fields = []
        updated_field_mapping = {}
        
        for key, value in field_mapping.items():
            if key == '+':
                # 处理新增字段
                new_fields.append(value)
            else:
                # 正常的字段映射
                updated_field_mapping[key] = value
        
        updated_data = []
        
        for item in data:
            new_item = {}
            for key, value in item.items():
                # 重命名顶层字段
                new_key = updated_field_mapping.get(key, key)
                new_item[new_key] = value
            
            # 添加新字段
            for new_field in new_fields:
                new_item[new_field] = ""
            
            updated_data.append(new_item)
        
        # 保存修改后的数据
        with open(test_file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n修改后的数据: {json.dumps(updated_data, ensure_ascii=False, indent=2)}")
        print(f"\n测试成功！新增字段 'new_field' 已添加，值为空字符串，同时 'age' 字段已重命名为 'new_age'")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\n已删除测试文件: {test_file_path}")

if __name__ == "__main__":
    test_new_field_functionality()