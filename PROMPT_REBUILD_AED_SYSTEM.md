# 可直接用于重新生成完整 AED Operations Control System 的 Prompt

你是一名资深 Python、Streamlit、Pandas、OpenPyXL、Microsoft Graph 和业务系统架构师。你的任务不是修改、补丁式修复、复制或逐行改写现有代码，而是把给定的旧项目仅作为“功能与视觉参考”，从空目录开始重新实现一个完整、可运行、可部署的 AED Operations Control System。

最终项目必须在功能、数据行为、页面效果、导航、视觉层级、跨页面联动、Excel 写回安全、OneDrive 同步、审计历史和响应式表现上，与参考项目保持等价。代码结构、函数内部实现和启动架构必须重新设计；不得把旧文件原样复制进新项目。必须输出完整项目文件，而不是 diff、代码片段或“请自行补充”的骨架。

---

## 一、交付目标

生成一个完整 Streamlit 项目，项目根目录只能有一个可执行入口：

```text
streamlit_app.py
```

不得存在 `app.py`，也不得要求用户把 `app.py` 内容复制到 `streamlit_app.py`。Streamlit Cloud 的 Main file path 必须直接设置为 `streamlit_app.py`。

项目至少包含：

```text
streamlit_app.py
config.py
requirements.txt
.streamlit/config.toml
.streamlit/secrets.toml.example
application/
services/
ui/
views/
views/map_modules/
utils/
data/
external_data/
tests/
```

要求将启动配置、会话、运行合同检查、存储初始化、侧边栏控制、云端刷新、页面路由拆分清楚；业务服务与页面渲染不得全部塞进单个文件。

技术栈：

```text
Python 3.11+
streamlit >= 1.51, < 2.0
pandas >= 2.0, < 3.0
openpyxl >= 3.1, < 4.0
folium >= 0.16, < 1.0
streamlit-folium >= 0.20, < 1.0
requests >= 2.31, < 3.0
```

不得使用已废弃的 `use_container_width`；统一改用 `width="stretch"` 或 `width="content"`。

---

## 二、整体视觉与排版合同

保持参考系统的整体视觉语言，但重新编写 CSS：

- 左侧为深海军蓝/深石板色固定侧边栏，主工作区为浅色背景。
- 品牌区显示闪电图标、`AED Operations` 和副标题 `CONTROL · SERVICE · TRACE`。
- 导航按小写字距较大的分组标题排列。
- 主页面使用宽布局、白色卡片、细边框、柔和阴影、圆角、清晰的标题层级。
- 页面顶部使用带 eyebrow、标题、说明和 chip 的 hero 区。
- KPI 卡片数值突出，说明文字较小。
- 表格必须支持完整文本换行，不得裁切重要字段。
- Profile 统计卡在桌面端为 4 列，在窄屏变成 2 × 2。
- Profile 顶部按钮和分段导航必须允许横向换行，不得被裁切。
- 所有主要操作按钮在窄屏仍能完整显示。
- 必须包含 `@media (max-width: 680px)` 的响应式规则。
- 所有页面应共享同一套视觉 token、按钮、卡片、表格、hero 和空状态样式。

不要改变原系统的主要英文 UI 文案，避免用户重新学习。

---

## 三、侧边栏与路由

可见导航必须严格按以下分组：

```text
OVERVIEW
- Operations Control

WORK MANAGEMENT
- PM Planning
- PM Checklist
- Report Issue
- Issues (显示当前 open issue 数量)

ASSET CONTROL
- AED Management
- AED Map

RECORDS
- Service Records
```

内部页面名：

```text
Operations Dashboard
PM Planning
PM Checklist
Report Issue
Issues
AED Management
AED Map
Service Records
```

保留隐藏兼容路由：

```text
AED Master Table
AED Master Data
```

旧路由进入时，不显示第二个侧边栏入口，而是重定向到 `AED Management` 的 `Direct Edit` 模式。

侧边栏底部显示：

- Open issue 数量摘要。
- 当前 Build ID。
- Operator Identity：可选择审计用户名，并显示当前 session ID 前 8 位。
- Data Source：显示 Excel 文件名、worksheet、Local/OneDrive 模式、同步状态、锁状态、Refresh now。
- OneDrive 已启用时显示连接账户和 Sign out。

---

## 四、核心页面与功能

### 1. Operations Control

这是 manager/boss-facing 主页。

顶部显示系统状态、数据源状态和全局工具栏。视图只保留：

```text
PM
Issues
Unit Profiles
```

不要出现旧的 `Overview` scope，也不要出现 `Asset readiness` 文案。

PM/Issues 视图需要：

- KPI row。
- Unified work queue。
- 按 period、view、assignee、keyword 过滤。
- Critical/High 优先级先显示。
- 左侧工作队列，右侧选中项详情。
- PM summary、issue summary。
- Recent operational activity。
- Source/data health。
- Quick actions。

Unit Profiles 视图需要：

- 可直接按 Serial Number、Model、Location、Postal Code 部分文本搜索。
- Selectbox 选择具体 AED。
- `Open selected profile`。
- `Browse all profiles`。
- 完整 Unit Profile 功能必须与 AED Management 中一致。

### 2. AED Management

这是统一的资产浏览、电子档案和 Master Table 编辑工作区。

页面顶部显示 4 个 management KPI，随后立即显示一个全宽搜索/过滤区。

只能存在一套搜索与联动过滤器：

- Partial keyword search。
- Serial Number、Model、Zone、Location、Postal Code、Job Type 等 linked filters。
- Date filters。
- Sorting。
- Reset 后必须同时清空表格结果和所有控件选择。

工作模式：

```text
Browse Units
Direct Edit
```

#### Browse Units

- 显示过滤后的 AED 表格。
- 行选择使用单行点击。
- 点击某行后按 `Serial Number` 打开完整 Unit Profile。
- 返回列表时保留原搜索词和过滤条件。

#### Direct Edit

保留完整 Master Table 能力：

- 直接多行 cell editing。
- 使用 Serial Number 作为稳定 identity。
- 日期字段使用日期编辑器。
- 不允许增加或删除 editor 内的行。
- 生成 Before/After 变化清单。
- 明确 Review Changes。
- 用户确认后才写 Excel。
- same-field conflict detection。
- batch update 必须 all-or-nothing。
- 支持 full-details editor。
- 支持 Add AED。
- 支持 Deactivate AED，不删除 Excel 原始行，只写 lifecycle status/history。
- 显示 Audit、Conflict、Transaction、Excel write 和 Lifecycle history。

#### Unit Profile

必须包含：

```text
Overview
Edit Details
Service History
Add Service
Issues
```

Overview：

- 显示当前 IB List/cache 中所有字段，而不是只显示摘要字段。
- 按 Basic Information、Location、Adult Pads、Pediatric Pads、Battery、PM and Service、Other Details 分组。
- 显示状态、open issue、PM 等 2 × 2 响应式统计。
- 显示 Recent Activity。

Edit Details：

- 正式字段编辑。
- Before/After review。
- `Confirm and update Excel` 后调用受保护 Excel transaction。
- Postal Code 改变时清空旧 Latitude、Longitude，并把 Geocoding Status 改为 pending。

Add Service：

- 创建独立 structured manual service record。
- 不得把新记录追加到公司原有 `Remarks`。
- 支持 Completed、Pending、Follow-up 等状态。
- 只有 Completed service 才可选择更新 master latest-service fields 和 PM dates。
- 可更新 Battery Replacement History。
- 可完成 linked PM Plan。
- 必须先显示 `Review new service record`，确认后保存。
- 保存后同时出现在 Unit Profile Service History 和 Service Records。

Service History 合并：

- PM Checklist responses。
- Issue resolution attempts。
- Manual service records。
- Current master latest service fields。
- Legacy Remarks。

Issues：

- 显示该 Serial Number 关联的所有 issue。

快捷操作必须包含：

```text
Fill PM Checklist
Report Issue
Open in Table Edit
View Service Records
Open AED Map
```

### 3. PM Planning

支持：

- Planning Month。
- Planning Year。
- Scope：`Due in selected month`。
- Scope：`Due by selected month (includes overdue)`。
- 可选包含没有 usable PM due date 的 AED。
- 若 Next PM Date 缺失，可根据 PM Completed Date + PM Interval Months 推算。
- 显示 Total AED Units、Due count、Without Usable PM Due Date。
- 候选表可选择 unit、Assigned To、Planned Date、Loaner、Color Override。
- 保存 persistent monthly plan。
- Plan ID 格式类似 `PM-YYYY-MM`。
- 已保存 plan 可重新显示、编辑、导出。
- 可批量更新 Next PM Date，但必须走正式 Excel review/conflict/transaction。
- PM Checklist 完成后自动更新对应 plan 为 Completed，并写 Completion Record ID、Operation ID、Completed Date、Completed By。

### 4. PM Checklist

搜索必须支持 Serial Number、Location、Postal Code 的部分文本匹配，多结果时选择正确 AED。

支持从 AED Map 或 PM Plan deep-link 预填目标 AED。

表单至少包含：

- Service Date。
- Technician。
- Service Type。
- Service Report e-SR。
- Service Notes。
- Customer / Location。
- Loaner Unit。
- Postal Code。
- Lift Lobby。
- AED Serial Number。
- AED Model。
- Battery Replaced。
- Battery Expiry Date。
- Adult Pads Expiry Date 和 Lot Number。
- Pediatric Pads Expiry Date 和 Lot Number。
- Cabinet Inspection。
- Cabinet Alarm。
- AED Physical Condition。
- Self Test Result。
- AED Cover。
- Adult Pads Within Expiry Date。
- Pediatric Pads Within Expiry Date。
- AED Signage。
- Final Check。

Service Type 顺序必须保留：

```text
第 2 个选项：PM
第 3 个选项：Commissioning
最后三个：PM+batt、PM+glass、PM +batt +glass
```

正式提交前必须：

- Validate required fields。
- 显示 Confirm PM Submission。
- 显示完整 summary。
- 显示 failed checklist items。
- 用户勾选确认后才提交。

提交事务必须：

1. 先持久化 PM response，即使 Excel 已经无需改变也不得丢失记录。
2. 更新 official Excel/cache 的 latest PM/service、pads、battery、e-SR、job type 等字段。
3. 更新 linked PM plan。
4. 每个 failed checklist field 创建独立 issue。
5. Issue 保存 PM Response ID、Source Field、Source Value、Serial、Location snapshot、Loaner status。
6. 记录 Submission Status、Excel Update Status、Master Data Updated、Created Issue IDs 和 Operation ID。

### 5. Report Issue

- 可搜索并选中 AED，也可从 Map/Profile 预填。
- 可手动修正 reported AED information。
- 保存 Reported By、Serial、Model、Location、Postal Code、Lift Lobby、Loaner、Source。
- Issue Type 支持多选。
- Priority。
- Detailed Description。
- 支持多张照片，写入 issue-specific 文件夹并创建 attachment rows。
- 正式创建前必须显示 Confirm Issue Report。
- 创建后提供 Open Issue Management。

### 6. Issues / Resolution / Verification

页面采用左侧 issue list、右侧 workspace 的结构，并支持窄屏。

过滤条件：

- Keyword。
- Month。
- Issue Type。
- Status。
- Reported By。
- Assigned By。
- Assigned To。
- Started By。
- Resolution By。
- Verified By。
- Date type + From/To date。
- Reset Filters。

列表：

- 默认按 Reported At 最新优先。
- 分页。
- 显示 priority、status、serial、location、reported time、next action。

详情 tabs：

```text
Details
Evidence & Resolution
Activity
```

详情必须显示：

- Original issue fields。
- Source and Record Linkage。
- Source。
- Source Record ID。
- Source Field。
- Source Value。
- Is Loaner。
- Review/assignment notes。
- Photos。
- Full history。
- Resolution attempts。

状态工作流：

```text
Reported
Assigned
In Progress
Pending Verification
Closed
Reopened / In Progress（验证失败）
```

操作：

- Review and Assign。
- Start Work。
- Add Progress Update。
- Submit Resolution。
- Verify Submitted Resolution。

Resolution submission 保存：

- Attempt Number。
- Submitted By/At。
- Action Taken。
- Root Cause。
- Parts Replaced。
- Test Performed。
- Test Result。
- Resolution Notes。
- Completion evidence/photos。

Verify/Close：

- 必须确认 evidence 已检查。
- 支持 Accept and close 或 Reject and return to work。
- 保存 Verification Result、Verified By/At、Verification Notes。
- 关闭前检查同一 AED 是否仍有其他 unresolved issue。
- Map 状态只能在没有未解决 issue 后恢复为绿色。

### 7. AED Map

使用 Folium + streamlit-folium。

Map Type：

```text
All Units Map
Monthly PM Map
```

过滤器必须联动：

- Plan Month。
- Search。
- Model。
- Assigned To。
- Status card。
- Reset。

地图要求：

- 只显示具有有效 Latitude/Longitude 的记录。
- 明确提示缺坐标的数量。
- 点击 marker 后在右侧显示 selected AED panel。
- Marker tooltip 返回 Serial Number 以更新当前选择。
- 右侧提供 PM Checklist 和 Report Issue deep-link。

状态系统：

- 至少 15 种可选 marker colours，包括 Blue、Green、Red、Yellow、Purple、Pink、Teal、Black。
- Status Name、Definition/Meaning、Marker Color、Active、Display Order、Workflow Role 可编辑。
- 保留用户已有自定义 status；只追加缺失的系统 workflow roles，不覆盖已有定义。
- Planning Color Override 不属于 official IB List，单独保存在 system state。
- Planning colour 改变后直接 auto-save，不需要 Save/Confirm。
- Open Issue 强制 red。
- Pending Verification 强制 yellow。
- 无 unresolved issue 后才可恢复 green。

### 8. Service Records

统一合并：

- PM Checklist responses。
- Unit Profile manual service records。
- Issue resolution submissions。

记录必须归一化为统一显示字段，同时保留 Record Source 和原始业务详情。

页面顶部提供 clickable Record Scope：

```text
All Records
Matched
Mismatch
Loaner
```

Matched/Mismatch 依据 record Postal Code 与当前 Master Table 中 Serial Number ↔ Postal Code 的关系判断。

不得为了显示 mismatch 而额外添加重复的：

```text
Record Postal Code
Master Postal Code
Mismatch Reason
```

但内部可以计算 `Record Match`。

同时提供 linked `Loaner Unit` filter。

其他过滤器：

- Keyword。
- Service date range。
- Service Month，必须以 `Service Date` 为准，不以 Submitted At 为准。
- Service Type。
- Technician。
- Serial Number。
- Model。
- Location。
- Record Status。
- Record Source。
- Linked Plan ID 等。
- Reset 后清空全部控件状态。

Month options 必须 unique、newest first。

支持 CSV export 和详细 record selector。详情应显示：

- Record ID。
- Source。
- Service Date/Submitted At。
- Serial、Model、Location、Postal、Lift Lobby、Loaner。
- Technician、Service Type、Reference、Status。
- Master update flags。
- Full PM checklist 或 resolution evidence。
- Notes/details。

---

## 五、官方 AED Master 数据合同

内部 cache 使用以下列，必须保留列名和 round-trip 能力：

```text
Serial Number
Installation Date
Model
Installed Phase / Month
PO Number
Zone
Block / Locations
Street Name
Location
Postal Code
Level
Lift Lobby
Adult Pads Replacement Date
Adult Pads Expiry Date
Adult Pads Lot Number
Pediatric Pads Replacement Date
Pediatric Pads Expiry Date
Pediatric Pads Lot Number
Battery Replacement History
Battery Expiry Date
PM Completed Date
Next PM Date
PM Interval Months
Job Type
Last Done By
Service Report e-SR
Remarks
Patrol Schedule
PM Schedule (H1)
PM Schedule (H2)
Repaired?
Latitude
Longitude
OneMap Address
Geocoding Status
```

日期在 CSV/UI 中统一为 `DD-MM-YYYY`；Excel 中写为真正日期单元格并使用 `dd/mm/yyyy` number format。

Postal Code 必须保持前导 0，Excel cell number format 使用 text。

Location 可由 Block / Locations + Street Name 重新组合，但不能无意覆盖用户输入。

Excel 导入需要兼容真实 IB List 的 merged cells、continuation rows、continuation remarks 和非标准标题映射。

---

## 六、Excel 写回与并发安全

所有正式写入 official workbook 的操作必须走同一个事务层：

1. 校验 Changed By。
2. 获取原子 operation lock。
3. 创建原始 workbook backup。
4. 读取最新 workbook snapshot。
5. 依据 original/current/desired 做 same-field conflict detection。
6. 已被其他用户以相同 desired value 写入的字段视为 already applied，不冲突。
7. 不同字段的并发改变可以安全 merge。
8. Batch 任意一个 field conflict 时整批不写。
9. 在临时副本中修改。
10. 可使用 `__STAGING_UPDATE__` 临时 sheet，但成功或失败后必须清理。
11. 原子替换源文件。
12. 刷新 CSV cache。
13. 写 transaction、audit、conflict、Excel write history。
14. 删除 operation lock 和 active transaction marker。

必须保留：

- 其他 worksheet。
- merged ranges。
- cell styles。
- continuation rows。
- 旧 Remarks，除非用户在正式 full-details editor 中明确修改。

支持崩溃恢复：如果 workbook 已替换但 cache 未刷新，启动时自动完成 cache refresh 并记录 Recovered。

Deactivate 只写 lifecycle history，不删除 Excel row。

---

## 七、OneDrive 与系统状态分离

浏览器 Microsoft sign-in，使用 delegated `Files.ReadWrite`。

远程必须使用两个独立文件：

```text
/AED System/IB_list_TEST.xlsx
/AED System/AED_System_State.zip
```

- Excel 是 official master data。
- ZIP 是 issues、PM records、manual service records、map states、histories 和 photos。
- System-state archive 绝不能包含 official workbook cache 或 Excel 文件。

下载/上传要求：

- 使用 Microsoft Graph metadata、content endpoint。
- Workbook upload 使用 ETag / If-Match 冲突保护。
- 约每 10 秒检查 cloud changes。
- 当用户处于 PM Planning、PM Checklist、Report Issue、Issues、AED Map、Master Table edit/review、Profile Edit Details/Add Service 时，暂停远程下载，防止覆盖未保存输入。
- 编辑期间仍可安全上传本地 system-state changes。
- Manual `Refresh now` 始终保留。
- 云端不可用时保留 local workbook + CSV fallback。

不得在代码中硬编码真实 client secret、OneMap 邮箱或密码。只提供 `.streamlit/secrets.toml.example` 占位符。

---

## 八、OneMap 坐标

- 根据 Postal Code 查询坐标。
- 只补充缺失或需要重新查询的记录。
- 保存 Latitude、Longitude、OneMap Address、Geocoding Status。
- Postal Code 变化后自动清理旧坐标。
- AED CSV 文件签名发生改变后自动检查缺失坐标。
- 查询失败不得阻止系统其他页面运行，应显示 warning。

---

## 九、持久化 CSV Schema

必须创建并自动修复缺失文件与缺失列。至少包含：

### PM Plan

```text
Operation ID, Plan ID, Plan Month, Planned Date, Serial Number, Assigned To,
PM Status, Completed Date, Completed By, Completion Record ID,
Completion Operation ID, Is Loaner, Color Override, Location Snapshot,
Postal Code Snapshot, Latitude Snapshot, Longitude Snapshot, Created At
```

### PM Responses

```text
Operation ID, Submission Status, Excel Update Status, Submitted By,
Service Date, Technician, Service Type, Service Report e-SR, Service Notes,
Postal Code, Lift Lobby, AED Serial Number, AED Model, Battery Replaced,
Battery Expiry Date, Adult Pads Expiry Date, Pediatric Pads Expiry Date,
Adult Pads Lot Number, Pediatric Pads Lot Number, AED Location,
PM Response ID, Original Serial Number, Customer / Location, Loaner Unit,
Cabinet Inspection, Cabinet Alarm, AED Physical Condition, Self Test Result,
AED Cover, Adult Pads Within Expiry Date, Pediatric Pads Within Expiry Date,
AED Signage, Final Check, Linked Plan ID, Failed Checklist Fields,
Created Issue IDs, Master Data Updated, Submitted At
```

### Issue Records

保留 source linkage、assignment、work、resolution、verification、legacy compatibility 字段。至少包括：

```text
Issue ID, Reported At, Source, Source Record ID, Source Field, Source Value,
Reported By, Technician, Serial Number, Model, Location, Postal Code,
Lift Lobby, Is Loaner, Issue Type, Detailed Description, Priority, Status,
Reviewed By, Reviewed At, Review Notes, Assigned By, Current Assignee,
Due Date, Assignment Notes, Started By, Started At, Last Updated At,
Latest Submission ID, Resolution Submitted By, Resolution Submitted At,
Closed By, Closed At, Photo Paths
```

### Issue History

```text
History ID, Issue ID, From Status, To Status, Action, Action By, Action At, Comments
```

### Resolution Submissions

```text
Submission ID, Issue ID, Attempt Number, Submitted By, Submitted At,
Action Taken, Root Cause, Parts Replaced, Test Performed, Test Result,
Resolution Notes, Verification Result, Verified By, Verified At,
Verification Notes
```

### Manual Service Records

```text
Service Record ID, Created At, Created By, AED Serial Number, AED Model,
AED Location, Postal Code, Lift Lobby, Service Date, Service Type,
Technician, Reference, Status, Details, Master Data Updated, PM Dates Updated,
Battery Replaced, Battery History Updated, PM Interval Months Used,
Linked Plan ID, Master Operation ID, Source
```

### Audit/Transaction/Conflict/Lifecycle

建立独立、append-only 的 CSV 历史，不覆盖旧记录。

---

## 十、质量、错误处理与兼容性

- 所有 CSV read 使用 `dtype=str`、`keep_default_na=False`，避免 Serial/Postal 变形。
- 所有写入使用 UTF-8 with BOM，兼容 Excel。
- 对空文件、缺列、无数据、文件占用、重复 Serial、非法日期、缺 required field 提供清晰错误。
- Add AED 必须检查 Serial 唯一。
- Next PM Date 不得早于 PM Completed Date。
- 1930 等明显不合理年份不应进入 readiness queue。
- Dashboard 对空数据源也必须返回稳定空 DataFrame，而不是异常。
- 不得出现 import cycle。
- 不得使用 `from config import` 于主入口；主入口应先 `import config as config` 并完成 compatibility defaults，再导入业务模块。
- 主入口导入 runtime services 时优先使用 module import，避免某个新增 symbol 缺失导致启动链式失败。
- 启动时执行 runtime contract validation，缺模块时给出一个清晰部署错误，而不是连续 ImportError。
- 不修改参考数据文件中的真实业务记录。
- 保留旧 bookmarked routes 和 session-state keys 的兼容性。

---

## 十一、自动化验收

必须编写 pytest，覆盖并通过以下合同：

- 所有 Python 文件 compile。
- 单一 `streamlit_app.py` 入口，无 `app.py`。
- AED clean/load/save/date calculation。
- Table editor identity、changes、validation、grouping。
- Excel sync：真实 IB layout、continuation rows、dates、postal、coordinates。
- Safe Excel write：backup、styles、merged cells、other worksheets、staging cleanup、locks。
- Same-field conflict、different-field merge、all-or-nothing batch。
- Add/Deactivate/full detail update。
- Recovery。
- PM response、failed items、plan completion、issue creation。
- Issue assign/start/progress/resolution/verify transitions。
- Unit profile manual service history。
- Dashboard queues、summaries、activity、filters、data exceptions。
- Service Records matched/mismatch/loaner/month filter。
- System-state archive exclusion of official workbook/cache。
- OneDrive URL and ETag behavior。
- Responsive CSS selectors。
- Unified AED Management route and profile actions。

最终至少执行：

```bash
python -m compileall -q .
pytest -q
```

若任何测试失败，继续修改直到全部通过。

---

## 十二、输出格式

输出一个完整可下载的 ZIP 项目，并同时提供：

```text
README.md
REBUILD_VALIDATION.md
requirements.txt
.streamlit/secrets.toml.example
```

README 必须说明：

- 如何本地运行。
- 如何部署 Streamlit Cloud。
- Main file path 是 `streamlit_app.py`。
- 本地 Excel 和 OneDrive 两种模式。
- Secrets 配置。
- 数据文件的作用。

不要只输出解释、伪代码、部分页面或 TODO。不要要求用户继续说“下一步”。一次性生成完整项目。
