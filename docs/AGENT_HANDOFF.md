# Agent Handoff

本文件用于后续 Agent / 维护者衔接上下文。用户文档只保留面向使用者的信息。

## 仓库与当前状态

- 英文名称：Selected Dimensions；用户确定的中文名称：显示选中物体尺寸。中文 README 使用该中文标题；英文名称、插件标识和仓库名保持不变。
- GitHub：hendasheng/selected-dimensions-blender-addon。
- 唯一版本来源：selected_dimensions/blender_manifest.toml 的 version。
- 当前版本：0.2.0，迁移为 Blender Extension。0.1.0 为历史 Legacy Add-on。
- main 与 v0.2.0 标签均已推送；GitHub 自动发布完成，已确认 0.2.0 安装包下载返回 HTTP 200。历史 v0.1.0 标签保持不动。
- 头图来自用户提供的中英文图片，已放入 docs/images/ 并分别引用。
- 本地仓库目录名称必须保持 selected-dimensions-blender-addon，不再创建带 -git 后缀的并行副本。

## 已确认的产品需求

- 运行或安装后默认不显示尺寸，用户点击 Show Dimensions 才启用。
- 只标注当前选中物体；多选分别标注；取消选择隐藏对应标注。
- 支持集合实例，以选中实例整体作为测量对象。
- 默认世界坐标，可切换物体自身坐标。
- 单位及单位比例跟随场景；界面语言跟随 Blender，提供英文和简体中文翻译。
- 标注是视图叠加，不增加场景文字/线条，不参与渲染。
- 字号、小数位、重算间隔可配置。模型变化时重算，旋转视图时复用缓存。
- 打开文件、重复开关、卸载插件时正确移除回调，避免残留或 null handler 错误。

## 文档规则与历史问题

- README_CN.md 为中文源文档；每次同步维护英文 README.md，结构和含义一致。
- 用户下载指引不得写死某个版本或 ZIP 完整文件名。统一指向 Releases，描述 selected_dimensions- 开头的安装包。
- 不引导用户下载 GitHub 自动生成的 Source code ZIP。
- 兼容声明统一为 Blender 5+；实测版本另记在本文件，不混为全版本验证。
- 构建、发布、实现细节、回调历史问题和 Agent 上下文不放入 README。
- 类似易过期信息（版本、标签、构建文件名、本机路径、测试记录）集中于版本元数据或本文件；不得在用户文档多处重复维护。
- 提交前同时检查两份 README 是否有写死版本、失效图片引用、中英文不对齐及面向维护者的内容。

## 文件结构

- selected_dimensions/__init__.py：插件、界面、翻译、尺寸计算和回调管理。
- scripts/build.py：仅依赖标准库的构建脚本，从 blender_manifest.toml 读取版本并验证标签。
- scripts/test_blender.py：Blender 后台功能验证。
- .github/workflows/release.yml：版本标签或手动触发的自动打包流程。
- docs/images/：用户提供的文档头图。
- LICENSE：参照用户现有 Batch Asset Export 项目，采用 MIT；作者 HenDaSheng。

## 构建与发布

本地构建：

    python scripts/build.py

输出为 dist/selected_dimensions-<version>.zip。ZIP 根目录包含 blender_manifest.toml、__init__.py 及 LICENSE（不再包含外层 selected_dimensions/ 目录），不包含缓存、测试或文档图片。

发布前：修改 blender_manifest.toml 的 version，执行测试与构建，提交并推送 main，再推送与版本一致的 v<version> 标签。不要移动既有发布标签。纯文档变更不需要修改插件版本或重发安装包。

GitHub Actions 校验标签版本，上传工作流构建产物，并创建/更新相应 Release 的插件 ZIP。workflow_dispatch 手动运行会生成构建产物，只有标签运行会发布 Release。

## 验证记录与边界

- 已在本机 Blender 5.0.0 和 5.2.0 LTS 后台验证：注册/卸载、重复显示/关闭、打开文件前清理、默认关闭/世界坐标、选择变化、旋转缩放模型、集合实例、物体/世界坐标切换、公英制和单位比例、中英文切换。
- 测试命令：blender --background --factory-startup --python scripts/test_blender.py。
- 本地构建及 ZIP 结构已验证。兼容目标为 Blender 5+，不表示已测试每个 5.x 版本。
- GitHub 连接器曾出现 transport 错误，本地 Git 可用；API 查询曾受代理访问限制。最终发布状态需重新确认，不能用成功推送标签代替发布成功。
- 复杂实例更新仍可能有计算成本；缓存减少视图交互时的重复开销。
- 世界坐标模式目前将普通对象的局部包围盒变换到世界后再求轴对齐范围；对旋转的不规则几何体，它可能比直接按所有顶点求世界范围更大。若继续修复实测精度，需要增加旋转不规则网格回归测试并权衡性能。

## Extension 迁移（0.2.0）

- 使用 selected_dimensions/blender_manifest.toml 作为唯一元数据和版本来源；移除 bl_info。
- 清单声明 maintainer=HenDaSheng、仓库网站、最低 Blender 5.0.0 及沿用的 MIT 许可证，不申请网络或文件权限。
- 翻译注册使用 __package__，支持 bl_ext.<repository>.selected_dimensions 命名空间。
- build.py 使用 Python 3.11+ tomllib，生成根目录清单格式的 Extension 安装包。
- README 中英文同步迁移安装步骤，提醒先卸载旧式版本；不要写死版本号。
- 发布前运行 Blender 官方 extension validate，且在隔离的扩展仓库中安装 ZIP、启用、测试、卸载。不能只用普通 import 替代扩展安装验证。
- 当前工作目录已迁移到 Documents/ChatGPT/Blender；旧 Codex 工作目录仅为历史副本，不继续写入。

## 0.2.0 验证记录

- Blender 5.0.0、5.2.0 LTS：官方 extension validate 校验通过。
- 在各自隔离的本地扩展仓库中，使用 package_install_files 安装 ZIP、启用 bl_ext.sd_extension_test.selected_dimensions、执行功能测试并卸载，全部通过。
- 测试覆盖清单版本/网站/维护者、命名空间、中英文、坐标、单位、实例、默认状态和重复启停。
- scripts/test_package.py 验证 ZIP 根结构、清单与源码一致及错误标签拒绝；已通过。
- 自动发布工作流新增包结构验证；已推送 v0.2.0 并确认 Release 安装包可下载。
