import json
import os
import csv

def extract_data_by_type(source_file, target_file, type_value):
    """
    从源JSON文件中提取指定类型的数据到目标JSON文件，并从源文件中删除这些数据
    
    参数:
    source_file: 源JSON文件路径
    target_file: 目标JSON文件路径
    type_value: 要提取的数据类型
    
    返回:
    bool: 提取是否成功
    """
    try:
        # 检查目标文件是否已存在
        if os.path.exists(target_file):
            print(f"目标文件 {os.path.basename(target_file)} 已存在，跳过提取")
            return False
        
        # 读取源JSON文件
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        if not isinstance(source_data, list):
            print(f"源文件 {os.path.basename(source_file)} 不是JSON数组格式，跳过提取")
            return False
        
        # 分离数据：提取符合条件的数据，保留不符合条件的数据
        extracted_data = []
        remaining_data = []
        
        for item in source_data:
            if item.get('type') == type_value:
                extracted_data.append(item)
            else:
                remaining_data.append(item)
        
        if not extracted_data:
            print(f"在 {os.path.basename(source_file)} 中未找到类型为 {type_value} 的数据，跳过提取")
            return False
        
        # 将提取的数据保存到目标文件
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        # 将剩余的数据写回源文件（即删除了提取的数据）
        with open(source_file, 'w', encoding='utf-8') as f:
            json.dump(remaining_data, f, ensure_ascii=False, indent=2)
        
        print(f"成功从 {os.path.basename(source_file)} 提取 {len(extracted_data)} 条类型为 {type_value} 的数据到 {os.path.basename(target_file)}")
        print(f"源文件 {os.path.basename(source_file)} 中剩余 {len(remaining_data)} 条数据")
        return True
        
    except Exception as e:
        print(f"提取数据时出错: {str(e)}")
        return False

def rename_fields_in_file(file_path, field_mapping, nested_mappings=None, output_dir=None):
    """
    重命名JSON文件中的字段名，支持嵌套字段和新增字段，并将结果保存为CSV格式
    
    参数:
    file_path: JSON文件路径
    field_mapping: 字段映射字典，键为原字段名，值为新字段名；
                  支持 "+":"new_key" 格式添加新字段
    nested_mappings: 嵌套字段映射字典，如 {"location": {"province": "new_province"}}
    output_dir: 输出CSV文件的目录路径，默认为源文件目录
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
            if "+" in key:
                # 处理新增字段
                new_fields.append(value)
            else:
                # 正常的字段映射
                updated_field_mapping[key] = value
        
        # 检查并移除与正常字段映射值重复的新增字段
        normal_mapped_fields = set(updated_field_mapping.values())
        unique_new_fields = []
        for field in new_fields:
            if field not in normal_mapped_fields:
                unique_new_fields.append(field)
            else:
                print(f"警告: 新增字段 '{field}' 与正常字段映射值重复，已移除")
        new_fields = unique_new_fields

        print(new_fields)
        # 重命名数据中的字段
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
        
        # 生成CSV文件路径
        if output_dir:
            # 如果指定了输出目录，将CSV文件保存到该目录
            filename = os.path.basename(file_path)
            csv_filename = os.path.splitext(filename)[0] + '.csv'
            csv_file_path = os.path.join(output_dir, csv_filename)
        else:
            # 否则保存到源文件目录
            csv_file_path = os.path.splitext(file_path)[0] + '.csv'
        
        # 确定CSV的列名（从所有数据项中提取所有唯一的键）
        fieldnames = set()
        for item in updated_data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)  # 排序以确保列顺序一致
        print(fieldnames)
        # 将嵌套字典转换为扁平化表示
        flat_data = []
        for item in updated_data:
            flat_item = {}
            for key, value in item.items():
                if isinstance(value, dict):
                    # 扁平化嵌套字典，如 {'location': {'province': '北京'}} -> {'location_province': '北京'}
                    for nested_key, nested_value in value.items():
                        flat_item[f"{key}_{nested_key}"] = nested_value
                else:
                    flat_item[key] = value
            flat_data.append(flat_item)
        
        # 重新确定扁平化后的列名
        flat_fieldnames = set()
        for item in flat_data:
            flat_fieldnames.update(item.keys())
        flat_fieldnames = sorted(flat_fieldnames)

        # 保存为CSV文件
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=flat_fieldnames)
            writer.writeheader()  # 写入表头
            for item in flat_data:
                writer.writerow(item)
        
        print(f"成功将文件转换为CSV格式: {os.path.basename(csv_file_path)}")
        return True
        
    except Exception as e:
        print(f"处理文件 {os.path.basename(file_path)} 时出错: {str(e)}")
        return False

def main():
    # 主数据目录
    main_data_dir = "D:\pyCharmProjects\pythonProject4\data"
    
    # 获取所有用户文件夹
    user_folders = [f for f in os.listdir(main_data_dir) if os.path.isdir(os.path.join(main_data_dir, f)) and f != "phone_data_csv"]
    
    print(f"发现 {len(user_folders)} 个用户文件夹:")
    for folder in user_folders:
        print(f"- {folder}")
    
    # 询问用户是否要继续
    confirm = input("\n是否确认执行数据提取和字段名更改？(y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 遍历所有用户文件夹
    for user_folder in user_folders:
        print(f"\n\n===== 处理用户: {user_folder} =====")
        
        # 用户的phone_data目录
        phone_data_dir = os.path.join(main_data_dir, user_folder, "phone_data")
        
        # 检查phone_data目录是否存在
        if not os.path.exists(phone_data_dir):
            print(f"  未找到phone_data目录，跳过该用户")
            continue
        
        print(f"  正在处理phone_data目录")
        
        # 为当前用户创建输出CSV文件的目录（与phone_data同级）
        user_dir = os.path.join(main_data_dir, user_folder)
        output_csv_dir = os.path.join(user_dir, "phone_data_csv")
        
        # 创建输出目录
        if not os.path.exists(output_csv_dir):
            os.makedirs(output_csv_dir)
        
        print(f"  CSV文件将保存到: {output_csv_dir}")
        
        # 执行数据提取操作
        print("  开始执行数据提取操作...")
        
        # 从event_call.json提取type为"sms"的数据到event_sms.json
        call_file = os.path.join(phone_data_dir, "event_call.json")
        sms_file = os.path.join(phone_data_dir, "event_sms.json")
        extract_data_by_type(call_file, sms_file, "sms")
        
        # 从event_note.json提取type为"calendar"的数据到event_calendar.json
        note_file = os.path.join(phone_data_dir, "event_note.json")
        calendar_file = os.path.join(phone_data_dir, "event_calendar.json")
        extract_data_by_type(note_file, calendar_file, "calendar")
        
        # 获取要处理的文件列表（排除event_fitness_health.json）
        json_files = [f for f in os.listdir(phone_data_dir) if f.endswith('.json') and f != 'event_fitness_health.json']
        
        print(f"  以下文件将被处理字段名更改:")
        for file in json_files:
            print(f"  - {file}")
    
    # 定义按文件区分的字段映射
    # 格式: {"文件名": {"原字段名": "新字段名", ...}}
    file_mappings = {
        # contact.json 字段映射
        "contact.json": {
            # 一、直接匹配字段：JSON字段 → CSV字段（直接取值，含基础处理）
            "name": "name",  # JSON联系人姓名 → CSV的name字段（修正原匹配senderName错误，直接对应name字段）
            "relation": "relationShip",  # JSON亲属关系 → CSV的relationShip字段（如“父亲”“朋友”）
            "nickname": "nickname",  # JSON昵称 → CSV的nickname字段（当前无数据，有值时直接使用）

            # 二、需拆解匹配字段：JSON字段 → CSV字段（CSV为集合类型，需拆解）
            "phoneNumber": "phoneNumbers",
            # JSON单个手机号 → CSV的phoneNumbers字段（多手机号集合，需提取单个值，如["13807123456"]→"13807123456"）
            "personalEmail": "emails",
            # JSON个人邮箱 → CSV的emails字段（多邮箱集合，需筛选个人邮箱，如["fengjianguo_wh@163.com"]→"fengjianguo_wh@163.com"）
            "workEmail": "emails_2",
            # JSON工作邮箱 → CSV的emails字段（多邮箱集合，需筛选工作邮箱，如["fengjianguo@whtlj.com"]→"fengjianguo@whtlj.com"）

            # 四、JSON需新增字段：CSV有但JSON无（用"+"标注，补充到JSON）
            "+1": "dataSource",  # CSV数据来源 → JSON需新增
            "+2": "extra",  # CSV扩展信息 → JSON需新增
            "+3": "uid",  # CSV用户标识 → JSON需新增
            "+4": "udid",  # CSV设备唯一标识 → JSON需新增
            "+5": "timestamp",  # CSV时间戳 → JSON需新增
            "+6": "source",  # CSV数据来源标识 → JSON需新增
            "+7": "senderName",  # CSV发送者名称 → JSON需新增
            "+8": "entityId",  # CSV实体唯一标识 → JSON需新增
            "+9": "entityName",  # CSV实体名称 → JSON需新增
            "+10": "entityGroupId",  # CSV实体组ID → JSON需新增
            "+11": "dataName",  # CSV数据名称 → JSON需新增
            "+12": "riskContentId",  # CSV风险内容ID → JSON需新增
            "+13": "riskState",  # CSV风险状态 → JSON需新增
            "+14": "namePinyin",  # CSV姓名拼音 → JSON需新增
            "+15": "organization",  # CSV所属机构 → JSON需新增
            "+16": "position",  # CSV职位 → JSON需新增
            "+17": "icon",  # CSV头像标识 → JSON需新增
            "+18": "phoneNumberCount",  # CSV手机号数量 → JSON需新增
            "+19": "note",  # CSV联系人备注 → JSON需新增
            "+20": "familyAddress",  # CSV家庭地址 → JSON需新增
            "+21": "imInfo",  # CSV即时通讯信息 → JSON需新增
            "+22": "groupName",  # CSV所属分组 → JSON需新增
            "+23": "meeTimeUri",  # CSV会议链接 → JSON需新增
            "+24": "hicall",  # CSV高清通话标识 → JSON需新增
            "+25": "isDeleted",  # CSV是否删除（0/1）→ JSON需新增
            "+26": "isUploadAllowed",  # CSV是否允许上传（0/1）→ JSON需新增
            "+27": "deviceType",  # CSV设备类型 → JSON需新增
            "+28": "updateTime",  # CSV更新时间 → JSON需新增
            "+29": "extras",  # CSV额外信息 → JSON需新增
            "+30": "iconUrl",  # CSV头像URL → JSON需新增
            "+31": "iconData",  # CSV头像数据 → JSON需新增
            "+32": "extension",  # CSV扩展字段 → JSON需新增
            "+33": "accessToken",  # CSV访问令牌 → JSON需新增
            "+34": "dataSyncState",  # CSV数据同步状态 → JSON需新增
            "+35": "syncUploadStatus",  # CSV同步上传状态 → JSON需新增
            "+36": "meeTimeCapabilities",  # CSV会议功能标识 → JSON需新增
            "+37": "huaweiAccountId",  # CSV华为账号ID → JSON需新增
            "+38": "phoneNumbersCapability",  # CSV手机号功能标识 → JSON需新增
            "+39": "contactCount",  # CSV手机号同步状态 → JSON需新增
            "+40": "lastContactTime",  # CSV手机号同步状态 → JSON需新增
            "+41": "primaryContact",  # CSV手机号同步状态 → JSON需新增
            "+42": "importantDay" # CSV手机号同步状态 → JSON需新增
        },
        
        # event_call.json 字段映射
        "event_call.json": {
            # 一、核心匹配字段：JSON字段 → CSV字段（直接对应，含格式处理）
            "event_id": "entityId",                 # JSON通话事件ID → CSV实体唯一标识（建议格式："call_"+entityId）
            "phoneNumber": "phoneNumber",           # JSON电话号码 → CSV电话号码（需补充"+86"前缀，如13981839301→+8613981839301）
            "contactName": "contactName",           # JSON联系人姓名 → CSV联系人姓名（直接使用，如"陈德红"、"妈"）
            "direction": "callDirection",           # JSON通话方向（1=呼出/0=呼入）→ CSV通话方向字段（需确认编码映射）

            # 二、固定值/推断字段：JSON有，CSV无直接对应
            "type": "entityName",                         # JSON通话类型标识 → CSV无对应，固定值"call"
            "start_time": "contactTime",              # JSON通话开始时间 → 暂用CSV的timestamp（13位时间戳转标准格式，如1760000000000→2025-10-09 08:53:20）
            "call_result": "answerState",           # JSON通话结果（接通/未接通）→ CSV接听状态字段（需映射，如1=接通、0=未接通）
            "end_time": "talkDuration",              # JSON通话结束时间 → 暂用CSV的timestamp（13位时间戳转标准格式，如1760000000000→2025-10-09 08:53:20）
            # 三、JSON需新增字段：CSV有但JSON无（用"+"标注，补充到JSON）
            "+1": "dataSource",                      # CSV数据来源（如"ArkData"）→ JSON需新增
            "+2": "extra",                           # CSV扩展信息（含格式化号码等）→ JSON需新增
            "+3": "udid",                            # CSV设备唯一标识 → JSON需新增
            "+4": "uid",                             # CSV用户标识（如3.01e+16）→ JSON需新增
            "+5": "source",                          # CSV数据来源标识 → JSON需新增
            "+6": "senderName",                      # CSV发送应用（如"com.ohos.contactsdataability"）→ JSON需新增
            "+7": "dataName",                        # CSV数据名称（如"action.InsightIntent"）→ JSON需新增
            "+8": "riskContentId",                   # CSV风险内容ID → JSON需新增
            "+9": "riskState",                       # CSV风险状态（如0）→ JSON需新增
            "+10": "entityGroupId",                   # CSV实体组ID → JSON需新增
            "+11": "slotId",                          # CSV卡槽ID → JSON需新增
            "+12": "ringDuration",                    # CSV响铃时长 → JSON需新增
            "+13": "numberLocation",                  # CSV号码归属地 → JSON需新增
            "+14": "isRead",                          # CSV是否已读（0/1）→ JSON需新增
            "+15": "updateTime",                      # CSV更新时间戳 → JSON需新增
            "+16": "accessToken",                     # CSV访问令牌 → JSON需新增
            "+17": "dataSyncState",                   # CSV数据同步状态 → JSON需新增
            "+18": "timestamp",
        },
        
        # event_gallery.json 字段映射
        "event_gallery.json": {
            # 一、核心匹配字段：JSON字段（含嵌套）→ CSV字段（直接/间接对应）
            # 基础信息字段
            "type": "entityName",  # JSON图片类型（固定"photo"）→ CSV无对应，需手动新增
            "title": "title",  # JSON图片标题 → CSV图片标题/文件名
            "datetime": "date",  # JSON拍摄时间 → CSV时间戳字段（需转标准格式）
            "ocrText": "ocrText",  # JSON文字识别结果 → CSV文字识别字段

            # 地理位置嵌套字段（拆解JSON嵌套结构）
            "location.province": "localAdminArea",  # JSON省份 → CSV省级行政区域
            "location.city": "localLocality",  # JSON城市 → CSV市级行政区域
            "location.district": "localSubLocality",  # JSON区县 → CSV区县级行政区域
            "location.streetName": "localThoroughfare",  # JSON街道名 → CSV街道名称
            "location.streetNumber": "localSubThoroughfare",  # JSON门牌号 → CSV门牌号
            "location.poi": "poi",  # JSON兴趣点 → CSV兴趣点字段

            # 图片特征字段
            "faceRecognition": "peopleName",  # JSON人脸识别列表 → CSV人脸名称（需转列表格式）
            "shoot_mode": "shootingMode",  # JSON拍摄模式 → CSV拍摄模式（如"普通"→"正常拍照"）
            "image_size": "size",  # JSON图片尺寸 → 由CSV"width+height"拼接（需组合生成）
            "imageTag":"tagFirstType",

            # 二、JSON需新增字段：CSV有但JSON无（用"+"标注）
            "+1": "timestamp",  # CSV时间戳（与takenDate区分）→ JSON需新增
            "+2": "albumName",  # CSV相册名称 → JSON需新增
            "+4": "holiday",  # CSV节假日标识 → JSON需新增
            "+5": "year",  # CSV年份 → JSON需新增
            "+6": "month",  # CSV月份 → JSON需新增
            "+7": "day",  # CSV日期 → JSON需新增
            "+8": "localCountryName",  # CSV国家名称 → JSON需新增
            "+9": "localSubAdminArea",
            "+10": "localSubLocality",
            "+11": "comment",
            "+12": "tagSecondType",  # CSV二级标签 → JSON需新增（可补充到imageTag）
            "+13": "tagThirdType",  # CSV三级标签 → JSON需新增（可补充到imageTag）
            "+14": "peopleTagId",  # CSV人脸标签ID → JSON需新增（可补充到faceRecognition）
            "+15": "sourceAppName",  # CSV拍摄应用名称 → JSON需新增
            "+16": "sourceAppNameKey",  # CSV应用标识 → JSON需新增
            "+17": "shootingModeKey",  # CSV拍摄模式编码 → JSON需新增
            "+18": "width",  # CSV图片宽度 → JSON需新增（可用于计算image_size）
            "+19": "height",  # CSV图片高度 → JSON需新增（可用于计算image_size）
            "+20": "size",  # CSV图片文件大小 → JSON需新增
            "+21": "latitude",  # CSV纬度 → JSON需新增
            "+22": "longitude",  # CSV经度 → JSON需新增（需注意精度）
            "+23": "aoi",  # CSV区域标识 → JSON需新增（如"10000000000000000000000000000000"）
            "+25": "faceRecognitionResult",  # CSV人脸识别结果 → JSON需新增（需解析JSON列表）
            "+26": "aestheticsScore",  # CSV图片美学评分 → JSON需新增（需注意范围）
            "+27": "filterTagName",  # CSV滤镜标签 → JSON需新增
            "+28": "duration",  # CSV时长（视频类）→ JSON需新增
            "+29": "picVector",  # CSV图片向量 → JSON需新增
            "+30": "entityId"
        },
        
        # event_note.json 字段映射
        "event_note.json": {
            # 一、核心匹配字段：JSON字段 → CSV字段（直接对应/格式转换）
            "title": "title",  # JSON笔记标题 → CSV笔记标题（直接使用，如"我爸的名字叫李四"）
            "content": "content",  # JSON笔记内容 → CSV笔记内容字段（修正初步匹配错误，直接对应）
            "datetime": "createdDate",  # JSON时间 → CSV时间戳（13位时间戳需转"YYYY-MM-DD HH:MM:SS"）

            # 二、固定值字段：JSON有但CSV无，需手动设置
            "type": "entityName",  # JSON笔记类型 → CSV无对应字段，固定值"note"

            # 三、JSON需新增字段：CSV有但JSON无（用"+"标注，补充到JSON）
            "+1": "dataSource",  # CSV数据来源（如"ArkData"）→ JSON需新增
            "+2": "extra",  # CSV扩展信息 → JSON需新增
            "+3": "odid",  # CSV设备标识 → JSON需新增
            "+4": "uid",  # CSV用户标识（如"default"）→ JSON需新增
            "+5": "timestamp",  # CSV时间戳（与datetime区分）→ JSON需新增
            "+6": "source",  # CSV数据来源标识 → JSON需新增
            "+7": "senderName",  # CSV发送应用（如"com.huawei.hmos.notepad"）→ JSON需新增
            "+8": "dataName",  # CSV数据名称（如"action.InsightIntent"）→ JSON需新增
            "+9": "riskContentId",  # CSV风险内容ID → JSON需新增
            "+10": "riskState",  # CSV风险状态 → JSON需新增
            "+11": "entityId",  # CSV实体名称 → JSON需新增
            "+12": "attachmentNames",  # CSV附件名称 → JSON需新增
            "+13": "folder",  # CSV笔记所属文件夹 → JSON需新增
            "+14": "isFavorite",  # CSV是否收藏（0/1）→ JSON需新增
            "+15": "modifiedDate",  # CSV修改时间戳 → JSON需新增（可转标准时间）
            "+16": "isLocked",  # CSV是否锁定（0/1）→ JSON需新增
            "+17": "isDeleted",  # CSV是否删除（0/1）→ JSON需新增
            "+18": "accessToken",  # CSV访问令牌 → JSON需新增
            "+19": "dataSyncState",  # CSV数据同步状态 → JSON需新增
        },
        
        # event_push.json 字段映射
        "event_push.json": {
            # "event_id": "事件ID",
            # "type": "事件类型",
            # "title": "通知标题",
            # "content": "通知内容",
            # "datetime": "推送时间",
            # "source": "来源",
            # "push_status": "状态",
            # "jump_path": "跳转路径",
        },
        
        # event_sms.json 字段映射 (从event_call.json提取)
        "event_sms.json": {
            # 一、核心匹配字段：JSON字段 → CSV字段（直接对应，无需额外处理）
            "type": "entityName",  # JSON消息类型（sms）→ CSV消息类型编码
            "message_content": "content",  # JSON消息内容 → CSV消息内容
            "contactName": "contactName",  # JSON联系人姓名 → CSV联系人姓名
            "contact_phone_number": "phoneNumber",  # JSON联系电话 → CSV电话号码
            "timestamp": "createDate",  # JSON时间戳 → CSV时间戳
            "message_type": "direction",  # JSON收发类型（发送/接收）→ CSV方向标识

            # 二、JSON需新增字段：CSV有但JSON无（用"+"标注，补充JSON字段）
            "+1": "timestamp",  # CSV电话号码字段，JSON需新增该字段
            "+4": "contactId",  # CSV联系人ID字段，JSON需新增该字段
            "+5": "state",  # CSV消息状态字段，JSON需新增该字段
            "+6": "sessionId",  # CSV会话ID字段，JSON需新增该字段
            "+7": "isCollect",  # CSV是否收藏字段，JSON需新增该字段
            "+8": "isDeleted",  # CSV是否删除字段，JSON需新增该字段
            "+9": "sessionName",  # CSV会话名称字段，JSON需新增该字段
            "+10": "accessToken",  # CSV访问令牌字段，JSON需新增该字段
            "+11": "dataSyncState",  # CSV数据同步状态字段，JSON需新增该字段
            "+12": "entityId",  # CSV数据来源字段，JSON需新增该字段
        },
        
        # event_calendar.json 字段映射 (从event_note.json提取)
        "event_calendar.json": {
            # 一、核心字段映射：CSV字段名 -> 目标JSON字段名（与原始JSON字段对应）
            "title": "title",              # CSV的事件标题 → JSON的title
            "description": "description",  # CSV的事件描述 → JSON的description
            "start_time":"dtStart",       # CSV的开始时间戳 → JSON的start_time
            "end_time":"dtEnd",           # CSV的结束时间戳 → JSON的end_time
            "type":"entityName",
            # 二、CSV新增字段：CSV特有字段，以"+"标识（原始JSON样例中无对应字段）
            "+1": "eventCreateTimestamp",   # CSV特有：事件创建时间戳
            "+2": "eventContent",           # CSV特有：事件内容补充
            "+3": "eventLocation",          # CSV特有：事件地点
            "+4": "isAllDay",               # CSV特有：是否全天事件（1=全天，0=非全天）
            "+5": "remindTime",             # CSV特有：提醒时间
            "+6": "oneClickServiceType",    # CSV特有：一键服务类型
            "+7": "timeZone",               # CSV特有：时区信息
            "+8": "timeCount",              # CSV特有：时间计数
            "+9": "importantEventType",     # CSV特有：重要事件类型
            "+10": "timestamp",              # CSV特有：时间戳（与dtStart/end区分）
            "+11": "source",                 # CSV特有：事件来源（如铁路12306）
            "+12": "visible",                # CSV特有：可见性设置
            "+13": "duration",               # CSV特有：事件时长
            "+14": "participants",           # CSV特有：参与者信息
            "+15": "participantEmails",      # CSV特有：参与者邮箱
            "+16": "important",               # CSV特有：是否重要事件
            "+17": "repeatType"
        }
    }
    
    # 定义按文件区分的嵌套字段映射
    # 格式: {"文件名": {"嵌套字段名": {"原字段名": "新字段名", ...}}}
    file_nested_mappings = {
        # 示例：
        "event_gallery.json": {
            "location": {
                "province": "localAdminArea",
                "city": "localLocality",
                "district": "localThoroughfare",
                "streetName": "localSubThoroughfare",
                "streetNumber": "localFeatureName"
            }
        }
        # 
        # "event_sms.json": {
        #     # 可以为event_sms.json添加嵌套字段映射
        # },
        # 
        # "event_calendar.json": {
        #     # 可以为event_calendar.json添加嵌套字段映射
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
    total_success_count = 0
    total_files = 0
    
    for user_folder in user_folders:
        phone_data_dir = os.path.join(main_data_dir, user_folder, "phone_data")
        
        if not os.path.exists(phone_data_dir):
            continue
        
        # 为当前用户创建输出CSV文件的目录（与phone_data同级）
        user_dir = os.path.join(main_data_dir, user_folder)
        output_csv_dir = os.path.join(user_dir, "phone_data_csv")
        
        # 创建输出目录
        if not os.path.exists(output_csv_dir):
            os.makedirs(output_csv_dir)
        
        # 获取要处理的文件列表（排除event_fitness_health.json）
        json_files = [f for f in os.listdir(phone_data_dir) if f.endswith('.json') and f != 'event_fitness_health.json']
        
        user_success_count = 0
        
        for file_name in json_files:
            file_path = os.path.join(phone_data_dir, file_name)
            
            # 获取当前文件的字段映射（如果没有定义则使用空映射）
            current_mapping = file_mappings.get(file_name, {})
            
            # 获取当前文件的嵌套字段映射（如果没有定义则使用空映射）
            current_nested_mapping = file_nested_mappings.get(file_name, {})
            
            # 只有当有映射定义时才处理文件
            if current_mapping:
                print(f"\n处理 {user_folder}/{file_name}...")
                if rename_fields_in_file(file_path, current_mapping, current_nested_mapping, output_csv_dir):
                    user_success_count += 1
            else:
                print(f"文件 {file_name} 没有定义字段映射，跳过处理")
        
        total_success_count += user_success_count
        total_files += len(json_files)
        print(f"\n用户 {user_folder} 处理完成！成功更新 {user_success_count} / {len(json_files)} 个文件")
        print(f"  CSV文件已保存到: {output_csv_dir}")
    
    print(f"\n\n===== 全部处理完成！=====")
    print(f"成功更新 {total_success_count} / {total_files} 个文件")

if __name__ == "__main__":
    main()