# Unity 图片导入与排版建议

本文件属于美术交付合同。参考画布为 **1920×1080、桌面横屏、16:9**；暂定项目名称必须保持“暂定”标记。当前未建立 Unity 工程、未制作 Prefab/C#、未实际导入或运行验证，以下均为后续接入建议。

## 资源入口与尺寸依据

- 正式独立资源：`../assets/`。逐件文件名、像素尺寸、SHA-256、Alpha、所属界面、来源和九宫格边距以 [assets/manifest.json](../assets/manifest.json) 为准；该清单生成前不能视为文件已交付。
- 整屏视觉稿：`../designs/`；状态与流程预览：`../previews/`。整屏是布局及效果参考，不能直接当作带交互的窗口底图。
- 每张 AI 原图保留逐图生成记录；机械裁切、缩放、九宫格拼装及文字合成输出关联 `derivedFrom` 和 `operation`。**1920×1080 是排版/导出尺寸，不自动等于模型原生尺寸。** 图标从母板裁出时，其可用细节受单格原生像素约束。
- 新版文件使用稳定语义名称，并在清单中列明实际采用版本。禁止仅按文件名或旧报告认定当前像素已通过。

## 建议导入设置

| 项目 | 本阶段建议 | 后续核实 |
|---|---|---|
| Texture Type | Sprite (2D and UI) | 与目标Unity版本和渲染方案核对 |
| Sprite Mode | 独立PNG用Single；确需合图才用Multiple并采用明确矩形映射 | 不按透明内容自动重排裁片 |
| Mesh Type | Full Rect | 稳定UI边界及九宫格 |
| Pixels Per Unit | 100 | 与Canvas像素参考及显示比例统一 |
| Filter Mode | Bilinear | 1920参考画布下检查小字旁边缘与缩放 |
| Wrap Mode | Clamp | 纸纹若声明可平铺，再单独核实Repeat |
| Generate Mip Maps | 关闭 | UI一般不需要Mipmap |
| Alpha Source / Alpha Is Transparency | 输入Alpha；有透明资源启用Alpha Is Transparency | 确认不是画出来的棋盘格/白底 |
| Compression | 首次验收Uncompressed，保留原始PNG | 后续平台压缩必须另做实机边缘检查 |
| sRGB | 色彩图建议启用 | 特殊数据贴图按用途另定 |
| Max Size | 不小于实际PNG；常用2048，确有大图时4096 | 保证导入器未静默缩小正式图 |
| Pivot | 普通UI建议中心(0.5,0.5) | 非中心装饰/锚点以逐件manifest为准 |
| Read/Write | 默认关闭 | 仅具体运行需求确需读像素时启用 |

透明资源检查实际Alpha通道中同时存在透明/不透明像素；内容本体如纸面可保持不透明。四角透明留白属于图像画布，不必全算作点击范围。按钮各状态必须共用画布尺寸、Pivot、Border、内容区与定位点。

## 九宫格和状态

边距统一采用原PNG像素 **Left、Bottom、Right、Top** 顺序（`borderLeftBottomRightTop`，或manifest明确的同义字段），例如 `[L,B,R,T]`。不得误当成L/T/R/B或在缩小导出后继续使用未换算的原母图边距。

1. 按清单设置Sprite Border并使用Sliced。固定角饰和边条保持原比例，中心只在允许方向伸展。
2. `L+R < width`、`B+T < height`；目标控件尺寸不小于固定边框总和。若清单给出更大的minimum size，采用更严格者。
3. 主面板可按合同双向拉伸；带侧边固定图标的按钮/页签若仅允许横向拉伸，保持原高度或整体等比缩放。
4. 圆徽章、头像、游乐设施插图、装饰、地图预览不做九宫格。装饰应独立叠加，避免跟随纸面拉长。
5. 普通/按下/选中/禁用/锁定的命名与语义以清单为准。选中、禁用与锁定分别表达；缺少某状态时不得仅换文件名宣称齐全。
6. Alpha边缘分别在浅色、深色、玉绿背景上检查；检查九宫格三种代表尺寸及原生尺寸，确认角饰没有切断、重复或拉伸。

## 动态文字与图层

标题、设施名称、游客/员工名称、现金、人数、价格、日期、统计、列表、工具提示和业务文案原则上用独立文字层。背景、面板、按钮和页签底图不带这些动态内容。整屏预览中的演示文字是排版样例，不能作为真实经营数据或硬编码业务规则。

建议图层顺序：场景/背景 → HUD → 主窗口 → 子窗口/详情 → 模态遮罩 → 模态窗口 → Tooltip/Toast。模态、工具提示和键盘焦点的实际阻挡/恢复留待下一阶段实现。工具栏保留园区观察空间，避免经营弹窗遮住建造预览的关键区域。

建议Canvas参考1920×1080并使用Scale With Screen Size；宽高匹配权重可先试0.5，再按目标显示器核实。整屏纯插画保持比例；窄屏/超宽屏不要整体非等比拉伸。桌面外的平台规格尚未确认，不能把桌面导出称为移动端已适配。

## 文字、色彩与内容区

| 用途 | 1920画布初始建议 | 颜色/对齐 |
|---|---|---|
| 页面主标题 | 42–48px，国风书写气质 | 玉绿标题牌上用象牙白，水平居中 |
| 分区/弹窗标题 | 28–34px | 浅底深玉绿；按区域居中或左对齐 |
| 正文、按钮、表单 | 22–26px | 正文左对齐，按钮居中 |
| 紧凑表格、辅助说明 | 18–21px | 深色文字，保留足够行高 |
| 关键资源数值 | 26–32px | 数字列右对齐，单位位置一致 |

这些是初始排版建议；实际字号、坐标、矩形、对齐和文案以每屏布局记录为准。建议正文深玉绿 `#173E35`，米白字 `#FFF5D8`，主玉绿 `#226C55`，纸面 `#F5EAD2`，暖金 `#C7A365`，告警朱砂 `#A93C30`，辅助文字 `#6F705D`；具体图片取色和实际对比仍需视觉验收。

本包已取得两份未经修改的原版OFL字体，位于 `assets/fonts/`，无需依赖或复制Windows字体：

| 用途 | 实际随包文件 | 已核实来源与版本 |
|---|---|---|
| 正文、按钮、表格、数字及缺字回退 | [NotoSansCJKsc-Regular.otf](../assets/fonts/NotoSansCJKsc-Regular.otf) | 官方 `notofonts/noto-cjk`；Noto Sans CJK SC Regular，版本2.004，16,437,364字节 |
| 国风短标题 | [MaShanZheng-Regular.ttf](../assets/fonts/MaShanZheng-Regular.ttf) | 官方 `google/fonts`；Ma Shan Zheng Regular，版本2.003，5,857,936字节 |

两者均采用SIL Open Font License 1.1。原许可和版权通知分别保存在 [Noto许可证](../assets/fonts/NotoSansCJK-LICENSE.txt)、[马善政许可证](../assets/fonts/MaShanZheng-OFL.txt) 和 [NOTICE](../assets/fonts/NOTICE.txt)。官方原许可可直接核对：[Noto](https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE)、[Ma Shan Zheng](https://raw.githubusercontent.com/google/fonts/main/ofl/mashanzheng/OFL.txt)。后续分发保留这些原许可和版权信息，不把字体作为独立商品销售；本次未修改、子集化或安装到系统。

[字体来源和字形核验](../records/font-sources.json) 记录官方仓库固定提交、下载路径、SHA-256、Git blob一致性、SFNT name/cmap信息，以及实际检查的功能总清单/状态文案文件哈希。两字体均覆盖原两份文案文件中的872个中文及其中非ASCII字符；**这不等于覆盖所有Unicode或运行时拼接文字**。后续针对实际布局文本的FreeType逐字检查发现Ma Shan Zheng缺少中点 `·`（U+00B7），会画成缺字框；短标题分隔符须改用空格或对该字使用Noto回退。记录中列出实际布局文字探测的范围和其他缺字结果，新增文案仍须复查。

Pillow/FreeType已成功加载两字体；这些是本地字体文件/字形核验，**不是Unity/TMP字体资源或动态字库验证**。标题中不受Ma Shan Zheng支持的字回退Noto Sans CJK SC，正文继续采用Noto保持小字号可读性。

后续可从随包原字体创建目标Unity版本的字体/TMP资源，并按业务文本建立静态字符集或动态回退；这属于下一阶段。若以后修改或子集化字体，另记录来源、操作和适用许可，不将本次原版文件的哈希/版本证据直接套到修改版。预览中的其他系统字体只可视为历史排版输入；本交付不含Windows字体文件。

## 图集建议与接入验证

建议按通用控件、工具图标、设施卡面、装饰分组图集，常用2048×2048；确需时使用4096×4096。窗口/背景大图可独立纹理，避免把一张背景塞满通用图集。建议Padding至少4px并保留边缘外扩；UI图集先关闭旋转与Tight Packing以方便九宫格和矩形映射核验。图集构建尺寸不是单件原生分辨率提升。

下一阶段需在目标Unity版本中逐项核实：Sprite加载、哈希与Max Size、Border/Pivot、Sliced三种尺寸、透明边缘、文本溢出与长名称、表格/列表滚动、分辨率与安全区、模态遮挡/焦点、按钮状态切换、建造预览与HUD共存。验收截图和引擎实际结果应单独记录，不能沿用F盘旧项目的测试或历史Unity报告。
