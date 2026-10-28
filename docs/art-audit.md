# 美术参考实读与实看审计

核实日期：2026-10-26（America/New_York）。审计范围为 `F:\work\image` 现存素材；未恢复旧 Git、未修改参考仓库或操作其 Git。

## 规则与缺失

- 已完整读取根 `AGENTS.md`。
- `qdao_ui_redesign_v5/UI_SPEC.md` 当前不存在。`rg --files -g UI_SPEC.md` 只找到 `designs/mail-ui-v1/UI_SPEC.md` 与 `designs/social-ui-v1/UI_SPEC.md`；本审计没有将它们冒称为缺失的全局规范。
- 两张用户指定主图均存在，已用 `view_image` 实际查看；designs 索引中关于邮件图缺失的历史文字不适用于本次磁盘状态。
- 本任务继续采用用户本次明确规范和根 AGENTS：深玉绿、象牙纸面、暖金细边、圆润云纹、少量太极葫芦和流苏；其他游戏仅参考功能与布局。

## 已实际阅读的同功能文件

| 参考仓库相对路径 | 本次读取内容与用途 |
|---|---|
| `designs/mail-ui-v1/README.md`、`UI_SPEC.md`、`unity-slices/README.md` | 双栏信息层级、原生动态文字、独立无字横幅、领取与阅读分离、真实Alpha及导入边界。README中部分历史验收不代表当前新增主题全验收。 |
| `designs/team-ui-v2/README.md`、`unity-slices/README.md`、`unity-slices/manifest.json` | 同时呈现两栏、成员行、空态、申请操作及状态；独立无字控件。manifest 边距字段为 `borderLeftBottomRightTop`，不是 `border`。 |
| `designs/ui-completion-20261021/README.md` | 八张静态成图、商城与活动层级；该包本身未含透明切片和九宫格。 |
| `designs/gameplay-ui/README.md`、`exact-20261022/README.md` | 列表、背包、活动、状态条与勾选标记的同源精确切图规则。 |
| `designs/social-ui-v1/README.md` | 聊天频道、输入区和消息滚动留白，原生文字与独立位图组合。 |
| `designs/equipment-ui-20261009/README.md` | 完整长内容不截断、不合并重复字段；详情纸板真实Alpha与来源、导出区别。 |
| `designs/scene-select-ui-v1/README.md` | 多项选择、当前项与底部确认/取消，模型实际证据不足时明确未确认。 |
| `qdao_ui_redesign_v5/README.md`、`components/README.md` | 登录、加载、通用39套控件及横向/双向九宫格、原生与导出尺寸区别。 |
| `qdao_ui_redesign_v5/fidelity-20261016/login-revision-20261017/README.md` | 公告、设置弹窗用玉纸控件；静态原稿不等于实际账号流程，历史客户端验收不可移用于新项目。 |
| `designs/attribute-panels/v2-painted/unity-slices/README.md` | 当前31张v10切片、无字底板、独立固定标题、Alpha与Sprite导入合同。 |

## 已用 view_image 实际查看的现图

| 相对路径 | 核实用途 |
|---|---|
| `designs/mail-ui-v1/01-mail-event.png` | 首要风格图。1931×814；清楚纸面、大标题玉牌、选中行和主次按钮。 |
| `designs/team-ui-v2/team-ui-v2.png` | 首要风格图。1931×814；双栏与卡片、头像和状态留白。 |
| `designs/ui-completion-20261021/04-item-shop.png` | 商店同功能参考；两列商品、右侧数量/货币/购买、明确主按钮。 |
| `designs/social-ui-v1/02-world.png` | 多人聊天同功能层级；左频道、右消息、固定输入和发送区。 |
| `qdao_ui_redesign_v5/01_login_2560x1080.png` | 启动入口层级与Q版画法。画面上的“五行奇谈”、服务器和角色不属于OpenRCT2新项目。 |
| `qdao_ui_redesign_v5/06_battle_entry_loading_2560x1080.png` | 加载插画同功能参考，进度与提示应另行排版。 |
| `docs/ui-fidelity-20261016/native/login-revision/03-settings_1920x1080.png` | 当前现存设置预览截图：玉纸弹窗、滑杆和开关层级；这是历史Unity截图而非新任务成图。 |
| `qdao_ui_redesign_v5/fidelity-20261016/login-revision-20261017/client/Assets/Resources/UI/Ugui/CoreFidelity20261016/login_settings_original.png` | 实际只含设置入口徽标，不是设置弹窗；不要误用文件名推断内容。 |
| `designs/equipment-ui-20261009/sprites/tooltip_panel.png` | 448×930竖纸板，深玉绿标题、太极及云纹，内容区安静。 |

## 可选独立控件及采用前要求

- 优先让本任务新生成的无字统一控件承接同一画法。所有F盘资源只在实际复制/改造后于 [本项目美术来源关联](image-reference-associations.md) 登记对应关系，审计本身不等于已复用。
- `designs/attribute-panels/v2-painted/unity-slices/png/` 提供窗框、纸纹、标题牌、按钮、页签、滑杆、数值框；原manifest可提供边距。该包当前图仍应逐件视觉核验，不仅引用旧通过报告。
- `designs/team-ui-v2/unity-slices/png/` 提供行、卡、圆头像圈、关闭、空位与状态点；同目录manifest明确尺寸和L/B/R/T。例：member_row 851×97、application_card 631×198、primary 225×66、secondary 220×66。九宫格只按实际保留角饰的尺寸使用。
- 重要已知缺陷：[DaoSurvivors 的美术来源关联](../../DaoSurvivors/docs/image-reference-associations.md) 保留了2026-10-26的组队切片检查：`main_frame.png`、`title_plate.png` 存在拼接接缝、拉伸填块及残字，已由干净属性切片替换。不能仅凭历史通过记录直接采用这两件。
- `qdao_ui_redesign_v5/components/png/` 的39套控件均为位图（对应SVG是内嵌位图包装），不是无限精度矢量。带勾/锁/放大镜的三态件和摘要条仅横向九宫格、固定高度；圆徽标等比显示。
- `designs/equipment-ui-20261009/sprites/tooltip_panel.png` 已实际查看。448×930，L/B/R/T=48/80/48/160；透明边缘与中间不透明纸面各有用途；导出来源为1024×1536母图，不能声称448×930是新原生AI细节。

## OpenRCT2新项目约束

仅承接画法与控件层级，不复制旧游戏业务。财务/设施/地图/多人协作等应按OpenRCT2实际系统设计；角色养成、战斗、邮件奖励、充值和会员不应因参考稿存在而机械加入。固定图标可绘入位图，动态标题/数量/名称/列表和操作文案应独立。每张新图保留配置目标、真实提交/返回、时间及源图证据；裁切、缩放和组合记录为派生操作。全部Unity设置在本阶段只能标为导入建议或待验证。

本项目两段来源关联现已迁回 [本项目美术来源关联](image-reference-associations.md)，F 盘对应 README 中的新增段已移除；原来源与执行证据继续保留为历史记录。
