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
            def get_all_fields(obj, parent_key=''):
                fields = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        full_key = f"{parent_key}.{key}" if parent_key else key
                        fields.append(full_key)
                        if isinstance(value, (dict, list)):
                            fields.extend(get_all_fields(value, full_key))
                elif isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], (dict, list)):
                    fields.extend(get_all_fields(obj[0], parent_key))
                return fields
            
            all_fields = get_all_fields(data[0])
            print(f"文件 {os.path.basename(file_path)} 包含 {len(data)} 条记录")
            print(f"所有字段名 (包含嵌套字段):")
            for field in all_fields:
                print(f"- {field}")
            
            return all_fields
        else:
            print(f"文件 {os.path.basename(file_path)} 为空或格式不正确")
            return []
    except Exception as e:
        print(f"分析文件 {file_path} 时出错: {str(e)}")
        return []

def rename_fields(file_path, field_mapping, nested_mappings=None):
    """
    重命名JSON文件中的字段名，支持嵌套字段
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            updated_data = []
            
            for item in data:
                new_item = {}
                for key, value in item.items():
                    # 重命名顶层字段
                    new_key = field_mapping.get(key, key)
                    
                    # 处理嵌套字段（如location）
                    if isinstance(value, dict) and nested_mappings and key in nested_mappings:
                        updated_nested = {}
                        for nested_key, nested_value in value.items():
                            updated_nested[nested_mappings[key].get(nested_key, nested_key)] = nested_value
                        new_item[new_key] = updated_nested
                    else:
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
    file_path = "D:\pyCharmProjects\pythonProject4\data\xujing\phone_data\event_gallery.json"
    
    print("正在分析文件...")
    fields = analyze_file(file_path)
    
    # 示例：字段映射字典
    # field_mapping = {
    #     "event_id": "gallery_event_id",
    #     "title": "photo_title",
    #     "datetime": "photo_time"
    # }
    
    # 示例：嵌套字段映射
    # nested_mappings = {
    #     "location": {
    #         "province": "photo_province",
    #         "city": "photo_city"
    #     }
    # }
    
    # 如需重命名字段，取消注释上述代码并运行 rename_fields(file_path, field_mapping, nested_mappings)
    # rename_fields(file_path, field_mapping, nested_mappings)