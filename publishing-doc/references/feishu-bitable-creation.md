# 飞书多维表格（Bitable）创建与操作

## 创建多维表格

```bash
# 1. 创建应用
curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"表格名称"}'
# 返回 app_token

# 2. 获取默认table_id
curl -s "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables" \
  -H "Authorization: Bearer $TOKEN"
# 返回 table_id

# 3. 添加字段
# type: 1=文本, 2=数字, 3=单选, 5=日期, 7=复选框, 15=URL
curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/fields" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field_name":"字段名","type":1}'

# 4. 删除默认无用字段
curl -s -X DELETE "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/fields/$FIELD_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## 记录CRUD

```bash
# 添加单条记录
curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"字段1":"值1","字段2":"值2"}}'

# 批量添加
curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/records/batch_create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"records":[{"fields":{"字段":"值"}},{"fields":{"字段":"值"}}]}'

# 更新记录
curl -s -X PUT "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/records/$RECORD_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"字段":"新值"}}'

# 查询记录
curl -s "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/records" \
  -H "Authorization: Bearer $TOKEN"
```

## URL字段格式

URL类型字段需要传对象，不是纯字符串：
```json
{"fields": {"文章链接": {"link": "https://...", "text": "显示文本"}}}
```

## 日期字段格式

日期类型字段传Unix时间戳（毫秒）：
```json
{"fields": {"发布日期": 1750867200000}}
```

## 坑位

- 主字段（第一列）无法删除/重命名，创建时默认叫"文本"
- 删除字段时需要先获取fields列表找到field_id
- token有效期2小时，过期需重新获取
- 批量创建最多500条/次
