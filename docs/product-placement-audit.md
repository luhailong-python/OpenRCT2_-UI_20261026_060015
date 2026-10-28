# 实际产品整屏的控件位置与完整度复核

功能参考：OpenRCT2 `52a55c3e8da5972460642bdfed61d091fe9cabfd`。实际读取226张基础产品布局与120张补充产品布局，另有125张业务状态图。技术皮肤合同图不计入产品位置。

| 核验项目 | 数量 |
|---|---:|
| 确切源窗口作用域标识 | 1438 |
| 有可靠产品位置证据的标识（证明下限） | 820 |
| 产品位置未确认的标识 | 618 |
| 修正后的静态交互候选 | 957 |
| 有可靠产品位置证据的交互候选（证明下限） | 528 |
| 位置未确认的交互候选 | 429 |
| 实际产品完整布局 / 业务状态图 | 346 / 125 |
| 识别的具体重要操作美术缺口 / 已补齐 | 18 / 18 |
| 补充控件矩形证据异常 | 0 |

1438是当前源码中独立窗口作用域标识的确切数。旧943是带名称排除规则的启发式候选数；其中14个真实操作因名称含GROUP、TAB或CLOSE被误归结构。此报告按实际源类型修正为957，仍不等同于运行时所有控件实例总量。完整14项修正与源码行见JSON。

未确认不等于缺图：中文改写、动态内容、同语义复合控件需要独立明确映射。未按字段序号强行套ID，未用插图、提示文字或技术样式图冒充产品按钮。全部可靠证据保留具体PNG、布局哈希及矩形；补充稿的语义合并按各自清单说明。

## 已解决的具体重要操作美术缺口

| 来源 | 已补齐内容 | 实际补充产品图 |
|---|---|
| RideConstruction | 补画侧倾、前后段切换/删除，以及制动或推进速度、座椅旋转的条件变体。当前四稿以参数值显示为主，没有这些操作的完整位置合同。 | `designs/details/ride-construction/01-curves.png` |
| Footpath | 补画桥隧模式四方向、三坡度与移除控制；地面模式的禁用差异也要表达。 | `designs/details/footpath/01-ground.png` |
| Staff | 补画搬运、重命名、解雇入口；已有解雇弹窗不能代替员工详情中的操作入口。 | `designs/details/staff/01-overview.png` |
| Options | 补画显示帧数、多线程、全屏失焦与屏保行为选项。 | `designs/details/options/01-显示-01.png` |
| MapGen | 补画高度图已载入后的浏览、归一化、平滑与强度控件；不是只给“尚未选择高度图”提示。 | `designs/details/map-gen/03-image-unloaded.png` |
| TileInspector | 补画八种元素各自的属性与方向/碰撞/动画条件，不用相同五个字段代替所有类型；补齐剪贴板及元素操作入口。 | `designs/details/tile-inspector/00-element-list.png` |
| Ride | 补画设施总览管理动作、模拟入口、图表类型切换、同商品全园同价、测量页保存蓝图入口。 | `designs/details/ride-ops/01-overview-closed.png` |
| Guest | 补画游客搬运与重命名入口；定位/追踪已显示。 | `designs/details/guest-ops/01-guest-actions.png` |
| Park | 补画公园入口页购买土地权/建造权与公园重命名入口。 | `designs/details/park-ops/01-park-actions.png` |
| Scenery | 补画真实搜索框/清除、重涂、吸管、第三配色与编辑器限制按钮。当前提示文字不等于操作控件。 | `designs/details/management/scenery-complete-tools.png` |
| EditorObjectSelection | 补画对象来源筛选、文字搜索/清除、子分类与排序、轨道安装和对象重载操作。 | `designs/details/management/editor-object-complete-selection.png` |
| Themes | 补画按窗口逐行设置配色和透明的表格；分类页重复的三色表单没有表达具体窗口选择。 | `designs/details/management/themes-editors-1.png` |
| Cheats | 补画各类沙盒高级操作/开关的分组或分页，并注明适用性；现有七页是精选项预览。 | `designs/details/management/cheats-3-1.png` |
| NewRide | 搜索/清除、设施类型分组和研发详情/资金快捷入口。 | `designs/details/utility/newride-research-shortcuts.png` |
| GuestList | 姓名筛选、追踪过滤、地图高亮、行动/想法和分页。 | `designs/details/utility/guestlist-individual-tools.png` |
| RideList | 搜索/清除、列排序/类别、批量开关和快速拆除的条件入口。 | `designs/details/utility/ridelist-client.png` |
| LoadSave | 上一级/新建/默认/系统文件浏览、文件名输入、保存和列预览设置。 | `designs/details/utility/filebrowser-customise.png` |
| StaffList | 制服配色、雇用、快速解雇、巡逻/最近员工和地图高亮。 | `designs/details/utility/stafflist-entertainer.png` |

这18组均有实际产品控件与源ID绑定，当前没有观察到仍未补画的上述具体重要操作美术缺口。全部相关PNG与条件变体见JSON的`supplementFiles`，不能把表中第一张代表图理解为单图包含该组所有条件。

## 能够与不能够宣称的完成范围

79个已知原生窗口单元及聊天、控制台、插件三类机制已有产品设计对应，21类业务系统、226个页签/模式及125个状态合同均有图像范围。按这些系统和明确列出的重要操作范围，可以交付本阶段整套美术方案，供用户验收。

本报告没有证明1438个源标识都已逐一安放在产品图中，未确认项仍逐项列在JSON中。不能据此宣称原生全部控件布局100%还原、全部组合条件穷举、全部画面都已用户批准或已经在Unity运行验证。未知第三方插件只能交付共享控件与明确示例，不能穷举未提供的插件业务。

原作商业游戏对象、美术/音效数据不因源码克隆而取得；本套为原创风格UI方案及已声明的示例内容，不宣称交付原作完整对象库。动态图表、列表数据、实时视口、条件显示与Unity交互仍须下一阶段接入验证；本次实际发现的重要美术缺口已通过补图处理，未作为编程事项转移。

全部逐项证据、分窗口统计、输入文件哈希、旧候选规则修正、18组结果及四份补充清单位于 `docs/product-placement-audit.json`。
