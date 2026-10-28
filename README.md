# 云游仙苑（暂名）· OpenRCT2 道家 Q 版 UI 美术

本对话制作目录：`E:\work\image\OpenRCT2_道家UI_20261026_060015`。本阶段交付静态 UI 图片、独立资源、状态和流程说明；暂定名称、桌面1920×1080参考画布及演示数据均为设计约定。

直接打开 [整套图片预览](index.html)，可按系统、页面和状态搜索，打开原图以及逐图文案/布局/来源。网页仅用于本地审阅。

## 已制作内容

| 内容 | 数量与位置 |
|---|---|
| 产品整屏 | 346张：226张基础页签/模式，加120张具体操作与条件变体；`designs/` |
| 业务状态 | 21系统125张；`previews/states/` |
| 独立PNG | 130件：28通用控件、64管理图标、16建设工具图标、21设施/人物插画、1园区背景；`assets/manifest.json` |
| 流程关系 | 4张；`previews/flows/index.html` |
| 源码控件皮肤合同 | 121张核对板，1,438个窗口作用域源标识；不是额外产品整屏 |
| 字体 | 2份原版OFL字体及许可证；`assets/fonts/` |

[功能与资源总清单](docs/UI功能与资源总清单.md)、[逐项CSV](docs/UI功能与资源总清单.csv)、[正式资源清单](assets/manifest.json)、[验收结果和限制](docs/acceptance-results.md)、[Unity导入建议](docs/unity-import-guide.md)、[下一阶段接入事项](docs/next-unity-stage.md)。

## 功能与美术来源

- 功能参考为 [OpenRCT2](https://github.com/OpenRCT2/OpenRCT2.git)，固定提交 `52a55c3e8da5972460642bdfed61d091fe9cabfd`；本地克隆为 `reference/OpenRCT2`。实际研究源码、窗口、模式、状态和操作条件，见 [研究记录](docs/repo-research.md)、[流程](docs/workflows.md) 与 [源码清单](docs/repo-ui-inventory.json)。游戏类型是游乐园建设经营，含场景、沙盒、编辑器和合作联机；未叠加角色养成、战斗或抽卡等不适用系统。
- 美术参考为 `F:\work\image`；主要使用 `designs/mail-ui-v1/01-mail-event.png` 和 `designs/team-ui-v2/team-ui-v2.png`，实际查看并附入本批生成调用。两份参考副本位于 `reference-art/`。已读资料及同功能参考见 [美术核对](docs/art-audit.md)。`qdao_ui_redesign_v5/UI_SPEC.md` 实际缺失，未从历史恢复。
- 遵照后续只读指令，F盘仓库保持只读；本项目当前关联记录位于 [image-reference-associations.md](docs/image-reference-associations.md)。历史关联操作证据保留在 `records/project-associations.json`，不冒称当前仍向F盘写入。
- 成果GitHub账号和远端待用户提供；当前未对本项目或参考仓库提交、推送或发布。后续成果提交应排除克隆的参考仓库。

## 生成和处理证据

7张原生生成母图及逐图记录保存在 `assets/backgrounds/`、`assets/masters/`。统一配置目标是 `gpt-image-2.5-sunburst / max`；使用内置图像入口，该入口未提供型号/质量选择器或相应返回元数据，因此实际型号和质量均标为未确认。详见 [模型核对](records/model-verification.md)、[逐图索引](records/generation-index.json) 与 [全部图片来源索引](records/image-provenance-index.json)。

整屏通过正式手绘资源、独立文字和数据形状合成；裁切、补透明画布、排版及预览缩放均有处理记录。1920×1080是整屏排版导出尺寸，不代表每张图片由模型原生生成到该分辨率，也不代表原生4K。母图保留为当前切片与复现所必需的源文件。

## 核验边界

全部82项源码界面单元已有设计对应，已识别的18组重要美术缺口已补齐。离线检查覆盖图片解码/尺寸/哈希、真实Alpha、边距、状态画布和预览文件；实际目视检查采用代表屏及联系表，具体记录见验收结果。

1,438个源码标识中，820项具有明确产品矩形证据，618项位置仍未确认；未确认项不能自动判为缺图，也不能声称全部控件位置已100%验证。技术样式板只证明皮肤合同。外部任意插件、所有条件组合、商业原作对象库不在本包穷举范围内。

没有建立或运行Unity工程；Prefab、场景、C#、接口、业务/网络逻辑与实机验证均为下一阶段。园区背景与设施卡面是UI素材，不能替代可操作世界地图、完整轨道精灵或碰撞资源。

## 目录与复现

`assets/`为正式图片与必要母图/字体，`designs/`为产品整屏，`previews/`为状态/流程/审阅图，`docs/`为功能和资源合同，`records/`为生成及验收证据，`tools/`为静态排版与切片工具，`reference/`为只读功能研究克隆。

现有图片无需安装工具即可审阅。重新排版需Python 3及Pillow；脚本按自身路径寻找项目，不依赖F盘写入。`tools/render_screens.py`生成基础稿；四份`render_*details.py`生成补充稿；`tools/build_delivery.py`汇总清单与本地预览。`tools/check_gallery.cjs`是可选的Playwright本地审阅器检查，其运行时路径需按新电脑调整。重新运行会更新本项目派生稿和验收时间，应重新验收并刷新来源哈希。
