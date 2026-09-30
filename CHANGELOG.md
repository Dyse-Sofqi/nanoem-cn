# 更新日志

本分支沿用上游 nanoem 版本号并追加 `-cn` 序号，例如 `v34.10.0-cn3` 表示基于上游 v34.10.0 的第 3 个中文版本。

## v34.10.0-cn3（2026-10-01）

首个 GitHub Release，包含此前 cn1–cn2 的汉化与 Windows 适配成果，以及本轮的效果（MME）渲染修复。

### 修复

- **使用光照色的效果（如 G_Shader）渲染为全黑**：对象绘制 pass 传给效果的 `LightDiffuse`
  （`DIFFUSE <string Object = "Light">`）恒为 0，导致效果里 `MaterialDiffuse * LightDiffuse`
  之类的写法输出为 0。现改为写入光照颜色。（`emapp/src/Effect.cc`）
- **带 `#include` 的效果编译失败**：fx9 计算 include 基目录时只识别 `/`，遇到混用分隔符的路径
  （如 `.../08_MOON\G_Shader.fx`）会丢掉最后一级目录，导致 `_GSCommon.fxsub` 等公共文件找不到、
  效果编译失败、模型不渲染。现同时识别 `/` 与 `\`。（`dependencies/fx9/src/Parser.cc`）
- **挂上效果后模型完全消失（连轮廓都没有）**：效果声明的资源贴图在加载/解码失败时，会用空数据
  创建纹理并得到非法图片，绑定后渲染后端会直接丢弃整次绘制。现在非法图片统一回退到内置备用贴图，
  绘制不再中断；覆写贴图同样处理。这也是 G_Shader 此前完全不可见的真正原因。
  （`emapp/src/Effect.cc`）
- **未声明渲染状态的效果按 MMD 语义处理**：效果 pass 未声明 `AlphaBlendEnable` / `ZWriteEnable` 时，
  改为继承材质状态（不透明材质不混合、开启深度写入），与 MMD + MME 行为一致。
- 效果编译失败时，错误对话框首行显示出错的**效果文件完整路径**（原先只显示被包含的文件，难以定位）。

### 新增

- **模型名显示语言**（偏好设置 → 项目）：界面保持中文的同时，可单独把骨骼、变形、材质等名称显示为
  「跟随界面语言 / 日语 / 英语 / 中文（词典）」。
- **中文词典**：内置约 150 条 MMD 标准骨骼、常用表情与常见材质的日译中词条；未收录的名称保持原文。
  可在 `%APPDATA%\nanoem\model_names_user.tsv` 中补充或覆盖词条（修改后重启生效）。

### 工具与文档

- 新增 `scripts/gen-translations-pb.py`：由 `translations.yml` 重新生成 `translations.pb`
  （Windows 构建树中缺少 `yaml2pb` 工具时的替代方案）。
- 新增诊断脚本：`scripts/gen-diag-project.py`（生成用于复现问题的 nanoem 工程文件）、
  `scripts/_pmx_dump.py`、`scripts/_pmx_uv_alpha.py`（解析 PMX 材质与贴图 alpha）。
- 调试构建支持环境变量 `NANOEM_LOG_FILE` 输出文件日志。
- `KNOWN_ISSUES.md` 记录上述问题的现象、原因与修复，以及 `.fxsub` 误挂载、命令行参数格式等使用注意。

### 一并包含的既有工作（cn1–cn2）

- 简体中文界面（1180+ 条翻译）与使用手册全文汉化、内置离线文档、中文字体（Noto Sans SC）。
- Windows 高分辨率（DPI）适配：Per-Monitor V2 感知、UI 文字按缩放率高清渲染、3D 视口原生分辨率渲染、
  非整数缩放（125%/150%/175%）坐标取整修正。
- 相机操作改为 MMD 习惯的「抓取式」方向（右键拖拽旋转、中键拖拽平移、滚轮向上拉近）。
