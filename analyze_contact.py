import json
import os

def analyze_file(file_path):
    """
    分析JSON文件的结构和字段名
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) > 0:
            # 获取第一个对象的字段名
            fields = list(data[0].keys())
            print(f"文件 {os.path.basename(file_path)} 包含 {len(data)} 条记录")
            print(f"字段名列表: {fields}")
            return fields
        else:
            print(f"文件 {os.path.basename(file_path)} 为空或格式不正确")
            return []
    except Exception as e:
        print(f"分析文件 {file_path} 时出错: {str(e)}")
        return []

def rename_fields(file_path, field_mapping):
    """
    重命名JSON文件中的字段名
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            updated_data = []
            for item in data:
                new_item = {}
                for key, value in item.items():
                    new_key = field_mapping.get(key, key)
                    new_item[new_key] = value
                updated_data.append(new_item)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功更新文件 {os.path.basename(file_path)}")
            return True
        else:
            print(f"文件 {os.path.basename(file_path)} 格式不正确")
            return False
    except Exception as e:
        print(f"更新文件 {file_path} 时出错: {str(e)}")
        return False

if __name__ == "__main__":
    file_path = "D:\pyCharmProjects\pythonProject4\data\xujing\phone_data\contact.json"
    
    print("正在分析文件...")
    fields = analyze_file(file_path)
    
    if fields:
        print("\n联系人字段结构:")
        for field in fields:
            print(f"- {field}")
        
        # 示例：字段映射字典
        # field_mapping = {
        #     "name": "contact_name",
        #     "phoneNumber": "contact_phone"
        # }
        
        # 如需重命名字段，取消注释上述代码并运行 rename_fields(file_path, field_mapping)
        # rename_fields(file_path, field_mapping)