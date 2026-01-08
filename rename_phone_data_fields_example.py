import json
import os

def rename_fields_in_file(file_path, field_mapping, nested_mappings=None):
    """
    重命名JSON文件中的字段名，支持嵌套字段和新增字段
    
    参数:
    file_path: JSON文件路径
    field_mapping: 字段映射字典，键为原字段名，值为新字段名；
                  支持 "+":"new_key" 格式添加新字段
    nested_mappings: 嵌套字段映射字典，如 {"location": {"province": "new_province"}}
    """
    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"文件 {os.path.basename(file_path)} 不是JSON数组格式，跳过处理")
            return False
        
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
                
                # 处理嵌套字段（如location）
                if isinstance(value, dict) and nested_mappings and key in nested_mappings:
                    updated_nested = {}
                    for nested_key, nested_value in value.items():
                        updated_nested[nested_mappings[key].get(nested_key, nested_key)] = nested_value
                    new_item[new_key] = updated_nested
                else:
                    new_item[new_key] = value
            
            # 添加新字段
            for new_field in new_fields:
                new_item[new_field] = ""
            
            updated_data.append(new_item)
        
        # 保存更新后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        print(f"成功更新文件: {os.path.basename(file_path)}")
        return True
        
    except Exception as e:
        print(f"处理文件 {os.path.basename(file_path)} 时出错: {str(e)}")
        return False

def main():
    # 目标文件夹路径
    target_directory = "D:\pyCharmProjects\pythonProject4\data\xujing\phone_data"
    
    # 获取要处理的文件列表（排除event_fitness_health.json）
    json_files = [f for f in os.listdir(target_directory) if f.endswith('.json') and f != 'event_fitness_health.json']
    
    print("以下文件将被处理:")
    for file in json_files:
        print(f"- {file}")
    
    # 定义按文件区分的字段映射（中文示例）
    # 格式: {"文件名": {"原字段名": "新字段名", ...}}
    file_mappings = {
        # contact.json 字段映射
        "contact.json": {
            "name": "联系人姓名",
            "phoneNumber": "电话号码",
            "relation": "关系",
            "gender": "性别",
            "personalEmail": "个人邮箱",
            "workEmail": "工作邮箱",
            "address": "地址",
            "birthdate": "出生日期",
            "company": "公司",
            "jobTitle": "职位",
            "category": "分类",
            # "+": "新增字段名"  # 新增字段示例
        },
        
        # event_call.json 字段映射
        "event_call.json": {
            "event_id": "事件ID",
            "type": "类型",
            "phoneNumber": "电话号码",
            "start_time": "开始时间",
            "end_time": "结束时间",
            "duration": "通话时长",
            "call_type": "通话类型",
            "message_content": "短信内容",
            "status": "状态",
            "datetime": "时间",
        },
        
        # event_gallery.json 字段映射
        "event_gallery.json": {
            "event_id": "事件ID",
            "type": "类型",
            "caption": "照片说明",
            "datetime": "拍摄时间",
            "location": "拍摄地点",
        },
        
        # event_note.json 字段映射
        "event_note.json": {
            "event_id": "事件ID",
            "type": "类型",
            "title": "标题",
            "content": "内容",
            "datetime": "时间",
            "description": "描述",
        },
        
        # event_push.json 字段映射
        "event_push.json": {
            "event_id": "事件ID",
            "type": "类型",
            "title": "通知标题",
            "content": "通知内容",
            "datetime": "推送时间",
            "source": "来源",
            "push_status": "推送状态",
            "jump_path": "跳转路径",
        },
    }
    
    # 定义按文件区分的嵌套字段映射
    # 格式: {"文件名": {"嵌套字段名": {"原字段名": "新字段名", ...}}}
    file_nested_mappings = {
        "event_gallery.json": {
            "location": {
                "province": "省份",
                "city": "城市",
                "district": "区县",
                "streetName": "街道名称",
                "streetNumber": "街道编号"
            }
        },
        
        # 可以为其他文件添加嵌套映射
        # "contact.json": {
        #     "address": {
        #         "province": "省份",
        #         "city": "城市"
        #     }
        # }
    }
    
    # 检查是否有任何字段映射被定义
    has_mappings = False
    for mappings in file_mappings.values():
        if mappings:
            has_mappings = True
            break
    
    if not has_mappings:
        print("\n错误: 请在脚本中为至少一个文件定义字段映射关系！")
        return
    
    # 询问用户是否要继续
    confirm = input("\n是否确认执行字段名更改？(y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 处理所有文件
    print("\n开始处理文件...")
    success_count = 0
    
    for file_name in json_files:
        file_path = os.path.join(target_directory, file_name)
        
        # 获取当前文件的字段映射（如果没有定义则使用空映射）
        current_mapping = file_mappings.get(file_name, {})
        
        # 获取当前文件的嵌套字段映射（如果没有定义则使用空映射）
        current_nested_mapping = file_nested_mappings.get(file_name, {})
        
        # 只有当有映射定义时才处理文件
        if current_mapping:
            if rename_fields_in_file(file_path, current_mapping, current_nested_mapping):
                success_count += 1
        else:
            print(f"文件 {file_name} 没有定义字段映射，跳过处理")
    
    print(f"\n处理完成！成功更新 {success_count} / {len(json_files)} 个文件")

if __name__ == "__main__":
    main()