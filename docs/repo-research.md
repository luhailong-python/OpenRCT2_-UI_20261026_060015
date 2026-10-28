# OpenRCT2 功能与 UI 源码研究

核实日期：2026-10-26（America/New_York）。本文是制作依据；不代表已在运行的 OpenRCT2 或 Unity 中验收。

## 仓库身份与取得状态

- 功能参考远端：<https://github.com/OpenRCT2/OpenRCT2.git>。
- 本地：`reference/OpenRCT2`（相对本对话目录）。浅克隆 `--depth 1`。
- 分支：`develop`；固定提交：`52a55c3e8da5972460642bdfed61d091fe9cabfd`。
- 提交说明：`Remove unused variables (#27322)`；原提交时间 `2026-10-26T11:01:23+11:00`，等于纽约时间 2026-10-25 20:01:23。
- 本阶段没有向参考仓库提交、推送、改源码或安装游戏商业数据。
- `git lfs ls-files` 无输出；`.gitattributes` 无 LFS 过滤规则；源码文本扫描未发现 LFS 指针。`git submodule status` 无输出。任务所读源码、配置、仓库自带资源不是未下载的 LFS 指针。
- 克隆目录及其 E 盘各级父目录未发现 `AGENTS.md`。用户提供的本次项目规则仍适用；F 盘美术仓库规则由美术制作侧另行读取。

## 实际读取与交叉核实

完整读取 `readme.md`、`assets.json`、`.gitattributes`、`src/openrct2/readme.md`，读取 `distribution/scripting/scripting.md` 的插件入口/API说明、`docs/save-format.md` 的结构、场景目标与作者信息段和 `licence.txt` 开头。

扫描全部 **79 个** `src/openrct2-ui/windows/*.cpp` 的窗口定义、控件 ID、标签页、可见性/禁用条件与事件入口，生成可追溯清单。重点阅读 `TitleMenu.cpp`、`TopToolbar.cpp`、`NewRide.cpp`、`RideConstruction.cpp`、`Ride.cpp`、`Park.cpp`、`Finances.cpp`、`Guest.cpp`、`GuestList.cpp`、`Staff.cpp`、`StaffList.cpp`、`Research.cpp`、`Options.cpp`、`Map.cpp`、`MapGen.cpp`、`EditorObjectSelection.cpp`、`EditorScenarioOptions.cpp`、`Multiplayer.cpp`、`ServerList.cpp`、`ServerStart.cpp`、`LoadSave.cpp`、`News.cpp`、`ObjectLoadError.cpp`、`TileInspector.cpp`、`TrackDesignManage.cpp`。

另读 `src/openrct2-ui/WindowManager.cpp` 的窗口路由，以及位于窗口目录外的 `interface/Chat.cpp`、`interface/InGameConsole.cpp`、`scripting/CustomWindow.cpp`，因此没有把“窗口 cpp 文件个数”等同于全部 UI 功能个数。

玩法条件交叉依据：`actions/ride/RideSetStatusAction.cpp` 的关闭/开放/测试/模拟校验；`actions/track/TrackPlaceAction.cpp` 的越界、未拥有土地、无效高度/特殊段限制；`actions/GameActionRunner.cpp:191` 的资金不足结果；`management/Research.cpp` 的研究阶段与四档预算；`scenario/Scenario.cpp:638` 起的目标成功/失败判断；`ride/Ride.cpp:2037` 起的入口出口可达性提醒；`windows/NetworkStatus.cpp:175` 的服务器密码输入。

清单每项的 `sourceEvidence` 保存确切路径、一基行号和短源码片段；`controlIds` 保存其实际控件 ID；`tabSourceLabels` 保存源码中提取出的标签页字符串 ID。该文件的全部行号固定在上述提交，不以远端未来的 develop 行号替代。

## 游戏类型、核心循环与系统关系

OpenRCT2 是游乐园建造经营模拟。README 明确说明场景模式、沙盒以及协作多人。玩家负责设施、商店、服务设施、地形步道景观、员工和财务，使游客满意并达到场景目标。美术改编使用临时道家游园主题，但核心规则按源码保留。

1. 标题主菜单 → 选择场景（来源或难度、目标、完成记录）/读取公园/加入或创建多人服务器/创作工具。
2. 进入公园 → 主视口与工具栏 → 调整土地水域 → 修建普通步道和排队步道 → 选择设施/蓝图或分段建造轨道 → 放置入口出口并连路。
3. 设施 → 车辆与运行参数 → 模拟或测试 → 三项评级与曲线 → 定价及开放 → 客流、等待时间、收入、维护检查和故障处理。
4. 公园 → 门票与开闭园、评分、客流、面积资产、场景目标和奖项；游客需求/消费/想法反馈经营问题；员工职责与巡逻区保障运行。
5. 财务 → 现金/贷款/收支与价值/利润趋势 → 营销活动 → 研究预算与优先类别 → 新设施/景观解锁。
6. 编辑器 → 选择对象 → 地形/入口/出生点/土地权 → 发明研究顺序 → 场景目标、初始条件与限制 → 场景保存。
7. 多人 → 服务器列表、收藏或地址 → 版本/密码/同步 → 玩家与权限组 → 协作操作、聊天、网络错误/不同步反馈。

`WindowManager.cpp` 显示这些窗口共用原作的窗口系统。道家版整屏是重新组织后的视觉设计，不把原作 640 像素宽的独立窗口尺寸当作新的 1920×1080 整屏合同。

## UI 覆盖边界与非适用系统

| 用户通用项 | 本游戏实际对应 |
|---|---|
| 启动、更新、登录 | 主菜单、版本更新提示与更新日志。游戏内无普通账号登录、角色创建与职业选择；外部 launcher 自动更新不属于本仓库游戏内下载更新流程。 |
| 服务器选择 | 协作服务器列表、收藏、地址输入、旁观和创建服务器；不是 MMORPG 分区服/永久角色。 |
| 角色、属性、成长 | 游客需求消费想法与员工职责统计；不增加玩家等级/技能树/战斗装备。 |
| 背包、仓库、物品 | 游客携带商品详情和商店商品/价格；没有玩家背包仓库整理/强化装备系统。 |
| 任务、奖励 | 场景目标进度、成功/失败、高分名字和公园奖项；没有日常任务领取奖励邮件。 |
| 地图、传送 | 公园地图、图例、相机定位、额外视口、透明与裁切；没有世界地图传送。 |
| 战斗、结算 | 无战斗；设施模拟测试、运营事故、场景目标结算按经营逻辑设计。 |
| 商店购买出售货币 | 玩家作为经营者建商店、设商品价格、查看成本和利润；资金贷款与营销，游客作为消费者。 |
| 活动签到成就排行 | 营销活动、公园奖项、场景完成高分；没有签到、抽奖、付费商城、战力榜。 |
| 好友聊天邮件组队 | 已有多人聊天、玩家权限组、合作服务器；未发现好友/邮件/战斗队伍系统，不机械加入。 |
| 设置帮助引导 | 8页设置、快捷键、主题、自定义币制、资源包、关于和悬浮说明；新手步骤说明可作为“建议补充”，不冒称原作独立教程页。 |
| 放置收益、派遣、部队 | 不适用；本任务不增加这些类型玩法。 |

## 清单结构与状态真值

`repo-ui-inventory.json` 共 **82 项**：79 个窗口源码单元，外加聊天、控制台、插件自定义窗口。当前包含 **226 个** 页签/操作模式/预览分组；这不等于226个原作固定窗口。全部226个预览分组均有 `tabDetails`，提供字段、排版样例、主动作和推荐布局；其中55个核心分页有分别编写的专门参数，其余共用所属功能的字段，并标明当前分组。目录类另外提供 `catalogItems`。

- `scope: existing` 指该系统在源码中存在。道家命名、铜钱、样例公园/设施/人名和示例统计值属于本项目的视觉改编与排版样例。
- `tabInterpretation` 区分源码实际分页/类别与本项目安排的状态预览分组。只有 `tabSourceLabels` 与源码证据能支持原作实际固定标签页名称。
- 状态词汇共30种，当前426个系统↔状态映射；其中 normal/focused/disabled 是跨系统共享控件状态。不能将426个映射直接当成426个独立业务页面，也不能用一张通用弹窗掩盖设施故障或目标失败等上下文差异。
- `states` 是美术覆盖合同。普通、聚焦、禁用等是共享控件状态；空列表、无搜索结果、重试等统一外观合理补齐，不表示原作各有独立同名页面。
- 资金不足、无土地权、建造冲突、轨道不完整/入口出口不连通、设施未测试/故障/事故、未研究、目标成功/失败、密码/版本/网络问题应按实际触发场景展示，不将所有状态强加给所有功能。
- “已领取”不适用于自动结算的场景目标；用“目标达成/记录成绩”表达。没有手动领取按钮的系统不新增领取流程。
- 插件自定义窗口的具体业务由外部插件决定。本包能交付公共皮肤、通用控件与一个明确示例，无法穷举所有未安装第三方插件。
- `productionStatus`、`acceptanceStatus`、`screenPaths`、`assetPaths` 起始为 planned/not-produced/空；制作协调者按真实产物回填，不能由源代码覆盖率推断美术完成率。

## 外部素材与运行证据限制

README 明确要求原版 RCT2 数据才能运行完整游戏。这些商业数据没有因克隆源码而取得。`assets.json` 还列出独立 objects、OpenMusic、OpenSoundEffects、title-sequences、replays 下载包；本轮研究没有把这些未下载 ZIP 计为已取得资源。当前 UI 美术重新创作，不直接打包原版游戏图像或音频。

研究使用实际源码/配置，没有伪造运行游戏截图、功能可点击验收或 Unity 结果。运行兼容性、场景可玩性、联机认证、真实数值和 Unity 导入效果都留待后续实现与运行验证。`docs/save-format.md` 是仓库内现有格式说明，未据此承诺未来 Unity 存档与 OpenRCT2 二进制格式兼容。

## 关联与后续提交

功能参考、美术参考、成果目标远端分别管理：功能参考为上述 OpenRCT2 URL；美术参考为 `F:/work/image` 指定成图；成果位于本对话目录；成果 GitHub 账号/地址待用户提供。克隆的完整参考仓库不纳入将来的美术成果提交包。
