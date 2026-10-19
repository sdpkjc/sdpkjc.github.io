# 历史归档

整理日期：2026-10-19。这里保存当前首页、简历不再使用的 38 个旧文件/版本，没有删除历史内容。其中 5 个来自已停用的 SVG 首页生成方案。

## 存放规则

保留原目录结构：原来的 `assets/logos/ucas.svg` 移至 `archive/assets/logos/ucas.svg`。文件内容不变。

`manifest.json` 记录原路径、归档路径、文件字节数、SHA-256 和整理前的 Git 提交，便于核对和恢复。

## 归档内容

| 类别 | 文件 | 归档原因 |
| --- | --- | --- |
| 旧页面和片段 | `a.html`、`x.html`、`x` | 不再作为当前页面入口 |
| 旧动画与字体工具 | `typed.js`、`my_subset.txt`、`mysubsetfont.woff2` | 当前首页无打字动画，直接使用本地字体和 HTML |
| 旧字体副本 | 根目录的 Smiley Sans、`assets/fonts/Monaspace-*` | 首页已不使用；简历在自身目录保留独立副本及许可证 |
| 双人头像 | `adam_wenxin.svg`、`adam_wenxin_dark.svg` | 当前页面不再展示头像动画；单人头像仍用于 favicon，未归档 |
| 旧项目图片 | `cleanrl_pr344.jpg`、`snapshotrl.svg`、`social_media_card*.svg` | 旧项目展示区已移除 |
| 公司和学校标识 | `assets/logos/` 下的 6 个 SVG | 当前页面没有使用这些标识 |
| 备用社交图标 | `assets/social/` 下的 6 个 SVG | 当前链接栏未采用；旧邮件图标已替换为独立的描边版本 |
| 简历备用素材 | `resume/assets/` 下的霞鹜文楷、思源宋体及许可证，照片和校徽 | 当前简历页面未引用 |
| SVG 首页方案 | `index.html`、`assets/profile.svg`、`scripts/` 下的 3 个生成文件 | 当前首页已改为直接编辑的 HTML，不再需要生成步骤 |

## 保留在工作目录的文件

- 首页：`index.html`、`adam.svg`、`adam_dark.svg`。
- 首页资源：本地字体及许可证、5 个实际使用的社交 SVG。无需构建工具。
- 简历：`resume/index.html`、实际使用的 3 套字体及许可证、已有 PDF、导出和检查脚本。

## 恢复与注意事项

根据 `manifest.json` 将需要的文件从 `archive/原路径` 移回 `原路径`，再恢复对应页面引用即可。恢复时先确认原路径没有新文件，避免覆盖；尤其不要直接覆盖当前的 HTML 首页。

归档中的 `scripts/build-profile.py` 必须恢复到原目录、配齐所需字体与图标后才能使用，不应直接在归档位置运行。当前首页只需编辑根目录 `index.html`。

这是资料归档，不是可独立运行的旧网站快照。旧页面中的链接保持原样：例如 `x.html` 的相对头像引用和 `x` 中的根路径图片链接在归档位置可能失效；`a.html` 引用的 `avatar.svg` 在整理前就不存在。需要完整旧版网站时，应从 Git 历史恢复。

归档会改变这些文件原来的本地/网站路径；当前页面不引用旧路径。此目录本身不是访问控制，直接发布整个仓库时仍需根据部署方式决定是否排除 `archive/`。
