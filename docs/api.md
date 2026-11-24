# 实验室设备巡检与故障记录平台 API 接口文档

> 版本：v0.2  
> 更新日期：2026-11-24  
> 适用项目：实验室设备巡检与故障记录平台  
> 技术栈：FastAPI + Vue 3 + SQLite  
> 说明：已吸收 C 同学在接口讨论中的意见。  
> 基础地址：`http://127.0.0.1:8000`  
> 业务接口前缀：`/api`

---

## 1. 通用约定

### 1.1 请求格式

- 请求体：`application/json`
- 响应体：`application/json`
- 时间格式：ISO 8601 字符串，例如 `2026-11-24T10:30:00+08:00`
- 本项目不要求登录，接口不需要鉴权。

### 1.2 MVP 范围约定

```text
1. 每台设备只保留一条“当前故障记录”，不做故障历史表。
2. 因此 device.fault_status 就是当前故障状态，不涉及“最新未解决故障”的选择。
3. 不做分页、不做设备新增/编辑/删除、不做用户登录。
4. 如果以后需要保留多条故障历史，再增加 faults 表，并把 device.fault_status
   改为“最新未解决故障”的派生字段。
```

### 1.3 成功响应

- 查询成功：HTTP `200`
- 创建成功：HTTP `201`
- 更新成功：HTTP `200`

### 1.4 错误响应

业务错误统一返回：

```json
{
  "detail": "错误说明"
}
```

常见状态码：

| 状态码 | 含义 | 示例 |
|---|---|---|
| `422` | 参数/字段校验失败 | 非法枚举、必填字段为空、note 超长 |
| `404` | 资源不存在 | 设备 ID 不存在 |
| `400` | 业务规则不允许 | 没有可解决的故障却请求 resolved |
| `500` | 服务器内部错误 | 未捕获异常 |

> 说明：FastAPI 默认的 422 响应中 `detail` 是数组。建议后端加统一异常处理，把 422 也转成 `{"detail": "参数校验失败"}`，前端只处理字符串。

---

## 2. 状态枚举

### 2.1 设备状态 `device.status`

| 值 | 含义 |
|---|---|
| `normal` | 正常 |
| `fault` | 故障 |

> 本 MVP 只保留 `normal` / `fault` 两种设备状态，避免和故障状态产生歧义。

### 2.2 故障状态 `device.fault_status`

| 值 | 含义 |
|---|---|
| `pending` | 待处理 |
| `processing` | 处理中 |
| `resolved` | 已解决 |
| `null` | 当前无故障记录 |

> 统一使用 `processing`，不要使用 `in_progress`。

### 2.3 巡检结果 `inspection.result`

| 值 | 含义 |
|---|---|
| `normal` | 正常 |
| `abnormal` | 异常 |

> 巡检结果统一使用 `abnormal`，不要使用 `fault`，避免和故障状态混淆。

---

## 3. 数据模型

### 3.1 设备 Device

```json
{
  "id": 1,
  "name": "示波器",
  "location": "A101",
  "model": "Tektronix TBS2000",
  "status": "normal",
  "fault_status": null,
  "fault_description": null,
  "last_inspection_at": "2026-11-24T10:00:00+08:00",
  "created_at": "2026-11-01T09:00:00+08:00",
  "updated_at": "2026-11-24T10:00:00+08:00"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 设备 ID |
| `name` | string | 设备名称 |
| `location` | string | 存放位置 |
| `model` | string | 设备型号 |
| `status` | string | `normal` / `fault` |
| `fault_status` | string \| null | `pending` / `processing` / `resolved` / `null` |
| `fault_description` | string \| null | 当前故障描述 |
| `last_inspection_at` | string \| null | 最近一次巡检时间 |
| `created_at` | string | 创建时间 |
| `updated_at` | string | 更新时间 |

### 3.2 巡检记录 Inspection

```json
{
  "id": 10,
  "device_id": 1,
  "result": "normal",
  "note": "运行正常，无异常声音",
  "created_at": "2026-11-24T10:00:00+08:00"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 巡检记录 ID |
| `device_id` | int | 所属设备 ID |
| `result` | string | `normal` / `abnormal` |
| `note` | string | 巡检备注，1–500 字 |
| `created_at` | string | 巡检时间 |

### 3.3 首页统计 Stats

```json
{
  "total_devices": 10,
  "normal_devices": 6,
  "fault_devices": 3,
  "pending_faults": 2,
  "processing_faults": 1,
  "resolved_faults": 1,
  "total_inspections": 26
}
```

---

## 4. 接口清单

| 方法 | 路径 | 用途 | 负责人 |
|---|---|---|---|
| GET | `/api/health` | 健康检查 | A |
| GET | `/api/devices` | 设备列表、搜索、筛选 | A/C |
| GET | `/api/devices/{device_id}` | 设备详情 | A |
| GET | `/api/devices/{device_id}/inspections` | 巡检记录列表 | A |
| POST | `/api/devices/{device_id}/inspections` | 新增巡检记录 | A |
| PATCH | `/api/devices/{device_id}/fault` | 更新当前故障状态 | A |
| GET | `/api/stats` | 首页统计 | C |

---

## 5. 接口详情

### 5.1 健康检查

```http
GET /api/health
```

响应 `200`：

```json
{
  "status": "ok"
}
```

---

### 5.2 设备列表

```http
GET /api/devices?keyword=&status=&fault_status=
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 否 | **只按设备名称 name 模糊搜索**，忽略大小写，自动去首尾空格 |
| `status` | string | 否 | 设备状态：`normal` / `fault` |
| `fault_status` | string | 否 | 故障状态：`pending` / `processing` / `resolved` |

规则：

- `keyword` 为空时不过滤。
- `status` 和 `fault_status` 同时传时，按 **AND** 组合。
- 没有结果时返回 `200` 和空列表，不返回 404。
- 非法枚举返回 `422`。
- 默认按 `id` 升序。

响应 `200`：

```json
{
  "items": [
    {
      "id": 1,
      "name": "示波器",
      "location": "A101",
      "model": "Tektronix TBS2000",
      "status": "normal",
      "fault_status": null,
      "fault_description": null,
      "last_inspection_at": "2026-11-24T10:00:00+08:00",
      "created_at": "2026-11-01T09:00:00+08:00",
      "updated_at": "2026-11-24T10:00:00+08:00"
    }
  ],
  "total": 1
}
```

错误示例：

```json
{
  "detail": "status 必须是 normal 或 fault"
}
```

---

### 5.3 设备详情

```http
GET /api/devices/{device_id}
```

响应 `200`：返回单个 Device 对象。

不存在返回 `404`：

```json
{
  "detail": "设备不存在"
}
```

---

### 5.4 巡检记录列表

```http
GET /api/devices/{device_id}/inspections
```

响应 `200`：

```json
{
  "items": [
    {
      "id": 10,
      "device_id": 1,
      "result": "normal",
      "note": "运行正常，无异常声音",
      "created_at": "2026-11-24T10:00:00+08:00"
    }
  ],
  "total": 1
}
```

规则：

- 按 `created_at` 倒序，最新在前。
- 设备不存在返回 `404`。
- 没有记录返回空列表。

---

### 5.5 新增巡检记录

```http
POST /api/devices/{device_id}/inspections
```

请求体：

```json
{
  "result": "normal",
  "note": "运行正常，无异常声音"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `result` | string | 是 | `normal` / `abnormal` |
| `note` | string | 是 | 1–500 字 |

响应 `201`：返回新增的 Inspection 对象。

业务规则：

1. 新增成功后，更新设备的 `last_inspection_at`。
2. 如果 `result=abnormal`：
   - 设备当前没有故障（`fault_status` 为 `null` 或 `resolved`）时，
     自动创建当前故障：
     ```text
     fault_status = pending
     fault_description = note
     status = fault
     ```
   - 设备已有 `pending` / `processing` 故障时，**不重复创建**，保留原故障状态和描述。
3. 如果 `result=normal`：只更新 `last_inspection_at`，不改变故障状态。
4. 前端提交成功后，建议重新请求设备详情和巡检列表，刷新页面状态。

错误：

- 设备不存在：`404`
- `result` 非法、`note` 为空或超过 500 字：`422`

```json
{
  "detail": "巡检结果必须是 normal 或 abnormal"
}
```

---

### 5.6 更新当前故障状态

```http
PATCH /api/devices/{device_id}/fault
```

请求体：

```json
{
  "fault_status": "processing",
  "fault_description": "设备无法正常开机，已联系维修"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fault_status` | string | 是 | `pending` / `processing` / `resolved` |
| `fault_description` | string | 否 | 故障描述，最多 500 字 |

规则：

- `pending` / `processing`：
  - 如果当前没有故障或故障已解决，创建/覆盖为当前故障；
  - 如果已有故障，更新状态和描述；
  - 同步 `device.status = fault`。
- `resolved`：
  - 如果当前有 `pending` / `processing` 故障，改为 `resolved`；
  - 同步 `device.status = normal`；
  - 如果当前没有故障，返回 `400`：`当前没有可解决的故障`。
- `fault_description` 不传时保留原描述。
- 响应 `200`：返回更新后的 Device 对象。

错误：

- 设备不存在：`404`
- `fault_status` 非法：`422`
- 没有故障却请求 `resolved`：`400`

---

### 5.7 首页统计

```http
GET /api/stats
```

响应 `200`：

```json
{
  "total_devices": 10,
  "normal_devices": 6,
  "fault_devices": 3,
  "pending_faults": 2,
  "processing_faults": 1,
  "resolved_faults": 1,
  "total_inspections": 26
}
```

统计口径（按 C 的约定）：

| 字段 | 口径 |
|---|---|
| `total_devices` | 全部设备数 |
| `normal_devices` | `status=normal` 的设备数 |
| `fault_devices` | 存在 `pending` / `processing` 故障的设备数（按设备去重） |
| `pending_faults` | `fault_status=pending` 的故障记录数 |
| `processing_faults` | `fault_status=processing` 的故障记录数 |
| `resolved_faults` | `fault_status=resolved` 的故障记录数 |
| `total_inspections` | 巡检记录总数 |

> 本 MVP 中每台设备只有一条当前故障记录，所以 `fault_devices`、`pending_faults`、`processing_faults`、`resolved_faults` 都等价于对应设备数。后续如果增加故障历史表，再按“设备去重 / 故障记录数”分别统计。

---

## 6. 前端页面与接口对应

| 页面/操作 | 使用接口 |
|---|---|
| 首页统计卡片 | `GET /api/stats` |
| 设备列表 | `GET /api/devices` |
| 名称搜索 | `GET /api/devices?keyword=...` |
| 设备状态筛选 | `GET /api/devices?status=...` |
| 故障状态筛选 | `GET /api/devices?fault_status=...` |
| 设备详情 | `GET /api/devices/{id}` |
| 巡检记录列表 | `GET /api/devices/{id}/inspections` |
| 提交巡检 | `POST /api/devices/{id}/inspections` |
| 更新故障状态 | `PATCH /api/devices/{id}/fault` |
| 后端在线检查 | `GET /api/health` |

---

## 7. 数据初始化与测试约定

### 7.1 Seed 数据

- A 提供 `seed.py` 或 `seed.sql`，插入约 10 台示例设备。
- 至少包含：

```text
3 台正常设备
2 台待处理故障设备
1 台处理中故障设备
1 台已解决故障设备
若干巡检记录
```

- 测试和联调共用 A 的 seed。
- 测试使用临时数据库，测试结束后删除。
- **不要提交 `*.db`、`*.sqlite`、`*.sqlite3` 文件。**

### 7.2 测试覆盖

C 负责至少覆盖：

```text
[ ] 设备列表空数据
[ ] keyword 搜索无结果 -> 200 空列表
[ ] 非法 status -> 422
[ ] 非法 fault_status -> 422
[ ] 设备详情 404
[ ] 新增巡检 note 为空 -> 422
[ ] 新增巡检 result 非法 -> 422
[ ] 巡检 abnormal 且无故障 -> 自动 pending
[ ] 巡检 abnormal 且已有 pending -> 不重复创建
[ ] PATCH 非法 fault_status -> 422
[ ] PATCH resolved -> status 变 normal
[ ] 没有故障时 PATCH resolved -> 400
[ ] 统计数字与 seed 数据一致
```

### 7.3 README 分工

| 负责人 | 内容 |
|---|---|
| A | 后端启动、seed、接口说明 |
| B | 前端启动、页面操作说明 |
| C | 测试、验收记录、汇总 |

### 7.4 联调缺陷

- C 记录缺陷和复验结果。
- A/B 修复后回填各自负责部分。
- 每个缺陷写清楚：现象、复现步骤、期望结果、修复提交。

---

## 8. 前端开发约定

### 8.1 Vite 代理

```js
server: {
  proxy: {
    '/api': 'http://127.0.0.1:8000'
  }
}
```

前端请求 `/api/...`，代理到后端。

### 8.2 必须处理的状态

```text
loading   加载中
empty     没有数据
success   操作成功
error     接口失败
```

### 8.3 Mock 数据

- 后端未完成前，前端按本文件字段做 mock。
- 建议 `src/api/mock.js` + `VITE_USE_MOCK=true`。
- 后端完成后切换为真实请求，不改页面字段。

### 8.4 不要提交

```text
node_modules/
dist/
.env
.idea/
*.db
```

---

## 9. 已确认的讨论结论

| 编号 | 结论 |
|---|---|
| 1 | `keyword` 只搜 `name`；空值不过滤；无结果返回 200 空列表 |
| 2 | `status` 与 `fault_status` 同时传按 AND；非法枚举统一 422 |
| 3 | 统计按第 5.7 节口径；MVP 一设备一条当前故障 |
| 4 | 测试覆盖空列表、无结果、非法状态、404、note 为空、统计和状态流转 |
| 5 | 测试/联调共用 A 的 seed；测试用临时数据库；不提交 db 文件 |
| 6 | README 由 C 汇总，A/B 补各自部分 |
| 7 | 联调缺陷由 C 记录和复验，A/B 修复并回填 |
| 8 | 巡检结果用 `abnormal`，不用 `fault`；`abnormal` 且无 active 故障时自动 pending |
| 9 | 设备列表的 `fault_status` 直接取当前故障状态；MVP 不做“最新未解决”匹配 |

---

## 10. 变更记录

| 日期 | 版本 | 修改人 | 说明 |
|---|---|---|---|
| 2026-11-23 | v0.1 | B | 初稿 |
| 2026-11-24 | v0.2 | B | 吸收 C 的评审意见：422、统计口径、巡检异常自动 pending、测试与 README 分工 |
