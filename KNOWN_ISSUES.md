# Windows 兼容性说明

## 已测试的 Windows 版本

| 版本 | 构建号 | 状态 |
|------|--------|------|
| Windows 10 RTM | 10240 | **有问题** — 鼠标捕获未释放，子窗口点不动 |
| Windows 10 22H2 | 19045 | ✅ 测试通过，使用正常 |
| Windows 11 | — | 未测试 |

## 已知问题

### 鼠标交互异常（仅限 Windows 10 10240 及更早版本）

在 Windows 10 10240 (RTM) 上，打开子窗口（如偏好设置、导出对话框）后，内容区域鼠标点击无效，无法切换选项卡，菜单无法点击。

**原因：** 该系统版本存在鼠标捕获（SetCapture）释放机制与 nanoem 代码交互不兼容的问题。Windows 10 22H2+ 中 DWM 已优化此行为，不再出现该问题。

**解决方案：** 升级到 Windows 10 22H2+ 或 Windows 11。

## 高分屏（DPI 缩放）适配说明

自 v34.10.0-cn2 起，Windows 版完成高分屏适配：

- **Per-Monitor V2 DPI 感知**：多显示器混合 DPI 环境下，窗口拖动到不同缩放率的显示器时自动切换渲染分辨率（WM_DPICHANGED 处理）。
- **UI 文字高清渲染**：ImGui 字体图集按显示器缩放率（100%/125%/150%/175%/200%…）原生光栅化，界面文字锐利不发虚。
- **3D 视口按原生分辨率渲染**：默认 Auto 模式下，独立显卡设备直接以屏幕原生分辨率渲染预览画面；仅核显设备自动回退到 1x 以保证性能（也可在「偏好设置 → 通用 → 视口渲染模式」中手动指定）。
- **非整数缩放修正**：125%/150%/175% 下窗口尺寸、鼠标坐标换算改用四舍五入，消除了此前的底部/右侧留白与光标抖动问题。

如需强制视口以 1x 分辨率渲染（提升低配设备流畅度），可在偏好设置中将「视口渲染模式」设为禁用。

## 相机操作方向说明

自 v34.10.0-cn2 起，相机操作采用与 MMD 一致的「抓取式」方向约定（上游 nanoem 为 FPS 式视线跟随，两者方向相反）：

| 操作 | 本分支（MMD 风格） | 上游（FPS 风格） |
|------|--------------------|------------------|
| 右键拖拽旋转 | 画面内容跟随鼠标方向转动 | 视线转向鼠标方向 |
| 中键拖拽平移 | 画面内容跟随鼠标方向移动 | 注视点跟随鼠标移动 |
| 滚轮缩放 | 向上滚 = 拉近 | 向上滚 = 拉远 |

## 效果导致模型全黑/透明（已修复，含两个原因）

现象：给模型挂上效果后模型变黑或透出背景；不挂效果正常。用分层最小效果（只输出纯色 / 只输出材质色 /
只输出光照色 / 只输出贴图）实测定位，发现是两个独立问题。

### 原因一：对象 pass 的 LightDiffuse 被写成 0

`Effect::setLightParameters` 在对象绘制 pass 使用的分支里把 `LightDiffuse`（语义
`DIFFUSE <string Object = "Light">`）写成 0。模型的所有绘制 pass 都走该分支，于是效果中
`DiffuseColor = MaterialDiffuse * float4(LightDiffuse, 1)` 之类的写法恒为 0 → 全黑。
实测对照：只输出光照色的最小效果全黑，其余三项正常。
修复：该分支改为写入光照颜色（与标准管线、与 MMD 行为一致）。

### 原因二：效果 `#include` 的基目录推导不识别反斜杠

fx9 计算 include 基目录时只查找 `'/'`（`dependencies/fx9/src/Parser.cc` 的
`ParserContext::execute`）。当传入效果的路径混用分隔符（例如
`.../01_G_Shader_v1.01/08_MOON\G_Shader_08_S1.fx`）时，基目录会丢掉最后一级目录
（`08_MOON`），于是 `#include "_GSCommon.fxsub"` 解析失败、效果编译失败、模型不渲染；
若误命中同名的其它版本文件，还会表现为「被包含文件里的变量未知」。
修复：基目录推导同时识别 `'/'` 与 `''`。本地用 10 个 G_Shader 变体验证：修复前 10 个全部编译失败，
修复后 10 个全部加载成功。

### 已排除的方向

float3 声明被拒（fx9 对向量一律按 float4 上报，相关改动为空操作已回退）、贴图解码、效果图片覆写指针、
面剔除、CONTROLOBJECT 缺省值、未声明渲染状态的默认值（混合/深度写入，按 MMD 语义改写后现象不变，
改动已回退）。

## 效果声明的资源贴图加载失败会导致模型完全不渲染（已修复）

现象：挂上 G_Shader 这类效果后模型完全消失（连轮廓都没有，只剩背景和网格），而简单效果正常。
用二分测试（逐个简化着色器）确认：**与着色器的代码内容无关**——把顶点着色器简化成只算位置、
像素着色器直接返回常量，依然完全不渲染。

原因：效果里用 `texture X < string ResourceName = ...; >;` 声明的资源贴图在加载/解码失败时，
nanoem 仍会用空数据创建纹理（日志中的 `VALIDATE_IMAGEDATA_NODATA` / `DATA_SIZE` 校验错误），
得到一个 state 为 FAILED 的图片；该图片被绑定到采样器后，**sokol 会直接丢弃整次绘制**，
于是模型一个像素都不写（看起来就是全透明）。

（G_Shader 的 `Sphere2nd` 使用宏 `SPHERE_2ND_PATH` 作为 ResourceName 值，其 `tex/ref1.png`
为调色板 PNG，在此构建下解码失败，正好命中该问题。）

修复：`Effect::registerImageResource` 中检查图片状态，非 VALID 时回退到项目内置备用贴图并记录日志，
保证绘制不被中断。本地验证：该采样器的图片状态由 FAILED(3) 变为 VALID(2)。

## 把 .fxsub 当成效果挂载会编译失败（使用注意）

`_GSCommon.fxsub` 之类被主效果文件 `#include` 的公共文件里**只有 technique 和着色器代码**，
参数声明都在主 `.fx` 里。把它直接作为效果挂到模型材质上时会报一屏「未知变量」并导致模型不渲染，例如：

```
_GSCommon.fxsub:433: 'SphereMapIn' : unknown variable
_GSCommon.fxsub:433: 'constructor' : can't convert
_GSCommon.fxsub:433: ' temp 3-component vector of float' : cannot construct with these arguments
.../_GSCommon.fxsub near at 433:39
```

正确做法是挂同目录下的主效果文件（如 `G_Shader_08_S1_SkinON.fx`），不要挂 `.fxsub`。

效果编译失败时，错误提示第一行现在会以 `Effect: <效果文件完整路径>` 开头（fx9 的原始报错只会提到
被包含的文件，看不出是哪个效果失败）；配合 `NANOEM_LOG_FILE` 的调试构建日志可进一步定位。

## 命令行参数格式（开发者）

`--bootstrap-project` / `--recovery-from` 等参数由 bx::CommandLine 解析，只支持
`--name <value>`（空格分隔）写法，`--name=<value>` 不会被识别。这些参数仅在启用
`NANOEM_ENABLE_DEBUG_LABEL` 的构建中生效。调试构建另支持环境变量 `NANOEM_LOG_FILE=<path>`
输出文件日志。
