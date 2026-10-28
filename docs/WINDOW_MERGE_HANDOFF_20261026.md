# 重复窗口归并交接（2026-10-26）

## 窗口与目录

- 本窗口：`01a177a6-ab28-7732-aee8-f17747d127e1`。
- 本窗口现有制作目录：`E:\work\image\OpenRCT2_道家UI_20261026_060015`。
- 唯一继续负责窗口：`01a17806-e809-7b12-b899-99244e13d06b`。
- 归并主目录：`E:\work\image\OpenRCT2_UI_20261026_074555`。
- 协调窗口：`01a17b19-1946-72f3-997e-9162eccf9b31`。

按归并指令，本窗口已停止新增生成、补图、重排版和重复制作。本次仅在自身目录写此交接；未删除、搬移或改写其他当前有效成果，未写F盘、未操作Git、未向其他chat发送消息，也未实施跨目录合并。以下为可供主窗口挑选采用的现有成果，不表示已与主目录完成逐件去重或自动采用。

## 采用与预览入口

1. [本地完整预览](../index.html)：471张产品/状态图，可搜索、筛选、查看原图及布局/来源记录。离线HTML是稳定入口；历史`http://127.0.0.1:8769/index.html`仅是本地审阅服务，不保证仍在线。
2. [项目说明](../README.md)及[项目关联](../project.json)：本地根目录、功能/美术来源、暂定名称及阶段范围。
3. [合并产品清单](all-ui-production-manifest.json)：346张产品整屏（226基础页签/模式+120补充操作详页），另125张业务状态图；共471张。所有产品图及对应`.layout.json`、`.source.json`保留在`designs/`及`previews/states/`。
4. [正式资源清单](../assets/manifest.json)：130件独立PNG，包含28通用控件、64管理图标、16建设工具图标、21设施/人物插画和1园区背景；129件Sprite具有真实透明通道。清单含尺寸、SHA、Border L/B/R/T、Pivot、来源和已有使用映射。
5. [逐项功能与资源清单](UI功能与资源总清单.csv)、[Unity导入建议](unity-import-guide.md)、[下一阶段事项](next-unity-stage.md)。

采用时以清单及逐件哈希为准，连同布局/来源、字体许可和必要记录保留；不要只复制整屏PNG便宣称取得独立控件，也不要把本窗口数量直接累加到主窗口数量。功能研究克隆无需整体纳入成果仓库。

## 本窗口自有资源与文档

尚未与主目录做逐件比较，以下是本窗口实际制作、可供差异比对的候选成果。

### 7张已完成原生生成图

- `assets/backgrounds/park-day-native.png`：园区日景背景，1672×941。
- `assets/masters/surfaces-native.png`：面板母图，1254×1254。
- `assets/masters/controls-native.png`：控件母图，1024×1536。
- `assets/masters/icons-native.png`：64管理图标母图，1254×1254。
- `assets/masters/illustrations-native.png`：首批12设施/人物插画母图，1086×1448。
- `assets/masters/supplement-native.png`：9幅补充交通设施/店铺/服务插画，1254×1254。
- `assets/masters/tracktools-native.png`：16轨道建设工具图标母图，1254×1254。

上述每张均有`.png.generation.json`；全部调用已返回并完成本地保存。正式裁片位于`assets/common/`、`assets/icons/`、`assets/illustrations/`、`assets/construction-icons/`；专属切片清单和逐件`.source.json`记录原图、裁切矩形、透明处理及画布。原生母图是当前重切片所需输入，不是待清理拒稿。

两份随包原版OFL字体及许可证位于`assets/fonts/`，来源与哈希在`records/font-sources.json`；不是系统字体拷贝。

### 120张具体操作补充整屏

- `docs/detail-ui-production-manifest.json`：48张，轨道建设、步道、员工、设置、地图生成、地块检查等六组操作和条件变体。
- `docs/management-detail-manifest.json`：30张，景物、编辑器对象选择、主题、作弊、发明编辑等具体控件。
- `docs/operations-detail-manifest.json`：26张，设施状态/图表/全园同商品价格/保存蓝图，游客及公园操作。
- `docs/utility-detail-manifest.json`：16张，新建设施、游客/设施/员工列表、文件浏览的搜索/筛选/批量及条件操作。

文件位于`designs/details/`，均有源控件绑定与实际产品矩形证据。补图关闭的18组具体重要美术缺口及证据见`docs/product-placement-audit.md/.json`。

### 源码研究和验收资料

- `docs/repo-ui-inventory.json`：82项界面单元（79原生窗口及聊天、控制台、插件机制），226基础页签/模式，附源码依据。
- `docs/state-contracts.json`及`workflows.md`：21系统125业务状态与流程依据。
- `docs/control-resource-mapping.json`：1,438个窗口作用域源标识的类型、文案、资源及条件说明。
- `previews/control-contracts/`及`docs/control-display-evidence.json`：121张皮肤合同图。只能证明样式合同，不能当成121张产品页面或全部产品位置验证。
- `previews/flows/`：4张流程图、布局/来源与索引。
- `docs/acceptance-results.md`、`final-independent-audit.md`、`detail-visual-qa.json`、`operations-visual-qa.json`、`sprite-qa.md`、`records/visual-review.json`及`records/nine-slice-qa.json`：检查方法、实际目视样本、哈希与边界。
- `tools/`：本项目静态排版、切片、预览汇总与检查脚本；归并交接不要求运行。不要恢复旧版向F盘写关联的脚本，现有`register_associations.py`已改为本地记录的只读验证。

## 来源记录

- 功能参考：`https://github.com/OpenRCT2/OpenRCT2.git`，固定提交`52a55c3e8da5972460642bdfed61d091fe9cabfd`；本地`reference/OpenRCT2`。未向参考仓库提交或推送。无LFS指针待下载；商业原作数据并未因源码克隆而取得。
- 美术参考：`F:\work\image`，主要为`designs/mail-ui-v1/01-mail-event.png`、`designs/team-ui-v2/team-ui-v2.png`。两图实际查看并附入全部本批生成调用；本项目副本在`reference-art/`。F盘按后续指令只读。
- 本项目关联：`docs/image-reference-associations.md`；历史关联动作证据在`records/project-associations.json`，不是重新写F盘的授权。
- 逐图索引：`records/generation-index.json`、`records/image-provenance-index.json`，原始提示/调用/回执为`records/*-prompt.txt`、`*-job.json`、`*-receipt.json`。
- 配置目标为`gpt-image-2.5-sunburst / max`；内置入口未暴露可提交的型号/质量选择器或相应返回值，实际型号/质量为未确认，不能据此锁定API分支。配置快照与官方核对分别在`records/image-config.snapshot.json`和`model-verification.md`。
- 整屏是正式手绘资源与独立文字的静态合成。裁切、缩放和1920×1080排版不冒称新模型原生高清；来源链已保留。
- 成果GitHub账号/仓库仍未提供，本窗口没有Git提交、推送、发布或共享Git HEAD/index/refs操作。

## 验收状态与待办

最后汇总核验时间为2026-10-26 09:34（America/New_York），见`records/final-delivery-check.json`：471张预览、130正式资源、471缩略图、1228张来源索引图像；入口链接缺失0，离线交付机器失败0，本地浏览器检查通过。用户最终验收尚未发生。

重要限制继续保留：

- 1,438个源标识中820项有可靠产品位置证据，618项位置未逐项确认；957个静态交互候选中528项有证据、429项未确认。未确认不自动等于缺图，也不能声称全部源控件布局100%验收。逐项未确认表在`product-placement-audit.json`。
- 实际目视检查为带哈希的代表样本及联系表，未声称逐张逐字人工看完全部471张图。18组已识别具体美术缺口已补图，无新增已观察到的阻塞美术问题。
- Unity工程、Prefab、C#、场景、业务/网络接口和运行验证均未开展。背景/卡面不等于完整世界轨道精灵、可交互地图或商业对象库。移动端未适配；外部未知插件不能穷举。
- `F:\work\image\qdao_ui_redesign_v5\UI_SPEC.md`读取时缺失，未从旧Git恢复。既有主参考与其他可得规范已实际读取，见`docs/art-audit.md`。

归并主窗口下一步应先比对清单/哈希与来源，选择可复用成图/控件/文档；随后统一去重、采用记录、未确认位置映射及用户验收。上述为交接建议，本窗口不再继续生产或代替主窗口进行合并。

## 在途与子工停止状态

- 新增生成/渲染/切片：已停止；本轮未启动任何此类任务。
- 图像调用：无在途，7张原生结果均已保存。
- 子工：本轮`collaboration.list_agents`只返回`/root`运行，无活动子工，无需中断未完成调用。此前子工均已完成并保存资料。
- 本机任务进程：交接检查未发现命令行指向本目录或历史`http.server 8769`的Python/Node进程；没有观察到在途写入。
- 本文件保存完成后，本窗口结束本轮，等待协调者归档；不自动恢复制作。
