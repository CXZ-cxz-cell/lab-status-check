# 实验室设备巡检与故障记录平台 API 接口文档

> 版本：v0.1（草案）  
> 适用项目：实验室设备巡检与故障记录平台  
> 技术栈：FastAPI + Vue 3 + SQLite  
> 说明：本文档由前端起草，需由成员 A、B、C 共同确认后再开始联调。  
> 基础地址：`http://127.0.0.1:8000`  
> 所有业务接口前缀：`/api`

---

## 1. 通用约定

### 1.1 请求格式

- 请求体：`application/json`
- 响应体：`application/json`
- 时间格式：ISO 8601 字符串，例如 `2026-11-23T10:30:00+08:00`
- 本项目不要求登录，因此接口不需要鉴权。

### 1.2 成功响应

- 查询成功：HTTP `200`
- 创建成功：HTTP `201`
- 删除成功：HTTP `200` 或 `204`（本项目暂不涉及删除）

### 1.3 错误响应

业务错误统一返回：

```json
{
  "detail": "错误说明"
}
```

常见状态码：

| 状态码 | 含义 |
|---|---|
| 400 | 参数不合法，例如状态枚举错误、必填字段为空 |
| 404 | 资源不存在，例如设备 ID 不存在 |
| 422 | 请求体字段类型错误（FastAPI 默认校验） |
| 500 | 服务器内部错误 |

> 前端处理建议：优先展示 `detail`；如果 `detail` 是数组，说明是 422 字段校验错误，展示“请求参数不正确”。

---

## 2. 状态枚举

### 2.1 设备状态 `device.status`

| 值 | 含义 |
|---|---|
| `normal` | 正常 |
| `fault` | 故障 |
| `offline` | 离线/停用 |

### 2.2 故障状态 `device.fault_status`

| 值 | 含义 |
|---|---|
| `pending` | 待处理 |
| `processing` | 处理中 |
| `resolved` | 已解决 |
| `null` | 当前无故障记录 |

### 2.3 巡检结果 `inspection.result`

| 值 | 含义 |
|---|---|
| `normal` | 正常 |
| `abnormal` | 异常 |

> 所有枚举值前后端必须保持一致，不能出现 `Pending`、`待处理`、`PROCESSING` 等混用。

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
  "last_inspection_at": "2026-11-23T10:00:00+08:00",
  "created_at": "2026-11-01T09:00:00+08:00",
  "updated_at": "2026-11-23T10:00:00+08:00"
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 设备 ID |
| `name` | string | 设备名称 |
| `location` | string | 存放位置 |
| `model` | string | 设备型号 |
| `status` | string | 设备状态：`normal` / `fault` / `offline` |
| `fault_status` | string \| null | 故障状态：`pending` / `processing` / `resolved` / `null` |
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
  "created_at": "2026-11-23T10:00:00+08:00"
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 巡检记录 ID |
| `device_id` | int | 所属设备 ID |
| `result` | string | `normal` / `abnormal` |
| `note` | string | 巡检备注 |
| `created_at` | string | 巡检时间 |

### 3.3 首页统计 Stats

```json
{
  "total_devices": 10,
  "normal_devices": 6,
  "fault_devices": 3,
  "offline_devices": 1,
  "pending_faults": 2,
  "processing_faults": 1,
  "resolved_faults": 5,
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
| PATCH | `/api/devices/{device_id}/fault` | 更新故障状态 | A |
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

用途：前端启动时检查后端是否在线。

---

### 5.2 设备列表

```http
GET /api/devices?keyword=&status=&fault_status=
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 否 | 按设备名称模糊搜索，忽略大小写，自动去首尾空格 |
| `status` | string | 否 | 设备状态：`normal` / `fault` / `offline` |
| `fault_status` | string | 否 | 故障状态：`pending` / `processing` / `resolved` |

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
      "last_inspection_at": "2026-11-23T10:00:00+08:00",
      "created_at": "2026-11-01T09:00:00+08:00",
      "updated_at": "2026-11-23T10:00:00+08:00"
    }
  ],
  "total": 1
}
```

规则：

- 默认按 `id` 升序。
- 没有结果时返回 `items: []`、`total: 0`，不要返回 404。
- `status` 或 `fault_status` 不在枚举内时返回 `400`。

错误示例：

```json
{
  "detail": "status 必须是 normal、fault 或 offline"
}
```

---

### 5.3 设备详情

```http
GET /api/devices/{device_id}
```

响应 `200`：返回单个 Device 对象。

不存在时返回 `404`：

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
      "created_at": "2026-11-23T10:00:00+08:00"
    }
  ],
  "total": 1
}
```

规则：

- 按 `created_at` 倒序，最新的在前。
- 设备不存在返回 `404`。
- 没有记录返回 `items: []`、`total: 0`。

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

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `result` | string | 是 | `normal` / `abnormal` |
| `note` | string | 是 | 巡检备注，1–500 字 |

响应 `201`：

```json
{
  "id": 10,
  "device_id": 1,
  "result": "normal",
  "note": "运行正常，无异常声音",
  "created_at": "2026-11-23T10:00:00+08:00"
}
```

业务规则：

- 新增成功后，后端更新设备的 `last_inspection_at`。
- 本项目约定：**巡检提交不自动改变故障状态**；如果巡检异常，用户再通过 5.6 更新故障状态。
- 设备不存在返回 `404`。
- `result` 非法、`note` 为空或过长时返回 `400`。

错误示例：

```json
{
  "detail": "巡检结果必须是 normal 或 abnormal"
}
```

---

### 5.6 更新故障状态

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

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fault_status` | string | 是 | `pending` / `processing` / `resolved` |
| `fault_description` | string | 否 | 故障描述，最多 500 字 |

响应 `200`：返回更新后的 Device 对象。

业务规则：

- 更新 `fault_status` 和 `fault_description`。
- 本项目约定：**该接口只更新故障状态，不自动修改设备 `status`**；前端分别展示设备状态和故障状态。
- 如果希望“故障解决后设备自动变为正常”，需要全组确认后再改规则。
- 设备不存在返回 `404`。
- `fault_status` 非法返回 `400`。

错误示例：

```json
{
  "detail": "fault_status 必须是 pending、processing 或 resolved"
}
```

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
  "offline_devices": 1,
  "pending_faults": 2,
  "processing_faults": 1,
  "resolved_faults": 5,
  "total_inspections": 26
}
```

统计口径：

- `total_devices`：设备总数
- `normal_devices`：`status=normal` 的设备数
- `fault_devices`：`status=fault` 的设备数
- `offline_devices`：`status=offline` 的设备数
- `pending_faults`：`fault_status=pending` 的设备数
- `processing_faults`：`fault_status=processing` 的设备数
- `resolved_faults`：`fault_status=resolved` 的设备数
- `total_inspections`：巡检记录总数

---

## 6. 前端页面与接口对应

| 页面/操作 | 使用接口 |
|---|---|
| 首页统计卡片 | `GET /api/stats` |
| 设备列表 | `GET /api/devices` |
| 名称搜索 | `GET /api/devices?keyword=...` |
| 状态筛选 | `GET /api/devices?status=...` |
| 故障状态筛选 | `GET /api/devices?fault_status=...` |
| 设备详情 | `GET /api/devices/{id}` |
| 巡检记录列表 | `GET /api/devices/{id}/inspections` |
| 提交巡检 | `POST /api/devices/{id}/inspections` |
| 更新故障状态 | `PATCH /api/devices/{id}/fault` |
| 后端在线检查 | `GET /api/health` |

---

## 7. 建议联调顺序

1. `GET /api/health`：确认后端能访问。
2. `GET /api/devices`：打通设备列表。
3. `GET /api/devices/{id}`：打通详情。
4. `GET /api/devices/{id}/inspections`：打通巡检列表。
5. `POST /api/devices/{id}/inspections`：打通新增巡检。
6. `PATCH /api/devices/{id}/fault`：打通故障更新。
7. `GET /api/stats`：打通首页统计。
8. 最后测试错误情况：404、400、空列表、接口失败。

---

## 8. 前端开发约定

### 8.1 Vite 代理

前端开发地址：

```text
http://localhost:5173
```

后端地址：

```text
http://127.0.0.1:8000
```

`vite.config.js` 建议配置：

```js
server: {
  proxy: {
    '/api': 'http://127.0.0.1:8000'
  }
}
```

这样前端请求 `/api/devices` 会被代理到后端，不需要处理 CORS。

### 8.2 前端必须处理的状态

```text
loading   加载中
empty     没有数据
success   操作成功
error     接口失败
```

### 8.3 不要提交的文件

```text
node_modules/
dist/
.env
.idea/
```

---

## 9. 待全组确认的事项

- [ ] 设备字段是否就是上面这些，是否需要增加 `fault_description`
- [ ] 巡检记录是否需要记录巡检人姓名
- [ ] 巡检结果为 `abnormal` 时，是否自动把设备标记为故障
- [ ] 更新故障状态时，是否同步修改设备 `status`
- [ ] 设备状态是否只保留 `normal` / `fault` / `offline`
- [ ] 是否需要分页（当前按小数据量设计，不分页）
- [ ] 后端端口是否使用 `8000`
- [ ] 前端端口是否使用 `5173`
- [ ] 初始设备数据由谁准备
- [ ] 是否需要在首页增加“最近巡检记录”列表

---

## 10. 变更记录

| 日期 | 版本 | 修改人 | 说明 |
|---|---|---|---|
| 2026-11-23 | v0.1 | B | 初稿，待 A/C 确认 |
