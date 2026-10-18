# 简历

当前简历页面、所需字体、PDF 和工具集中存放在此目录，可整体复制使用，不依赖首页目录的资源。此次整理没有修改简历内容或重新生成已有 PDF。

## 文件结构

```text
resume/
├── index.html            # 简历页面
├── assets/
│   └── fonts/            # 当前使用的 3 套字体及许可证
├── output/pdf/           # 导出的 PDF
├── scripts/
│   ├── export-resume-pdf.sh
│   └── check-resume-pdf.sh
└── tmp/                  # 工具运行时生成，Git 忽略
```

## 查看

直接打开 `index.html`，或在仓库本地服务器运行时访问 `http://127.0.0.1:4173/resume/`。页面字体均从本目录加载。

## 导出 PDF

需要 Chrome/Chromium、Python 3 和 Poppler（`pdfinfo`、`pdffonts`、`pdftotext`）。以下命令在 `resume/` 目录执行：

```bash
./scripts/export-resume-pdf.sh
```

默认保存到 `output/pdf/YanxiaoZhao-yymmdd.pdf`，日期为导出当天。相同日期的导出会替换同名 PDF。

可用 `RESUME_DATE` 指定日期，用 `CHROME_BIN` 指定浏览器可执行文件；也可以传入输出路径：

```bash
RESUME_DATE=261019 ./scripts/export-resume-pdf.sh ./output/pdf/YanxiaoZhao-261019.pdf
```

## 检查 PDF

```bash
./scripts/check-resume-pdf.sh ./output/pdf/YanxiaoZhao-260823.pdf
```

检查包括单页 A4、文档标签、字体嵌入、文本顺序和文件体积。检查脚本中的必需文本与当前简历内容对应；以后修改简历内容时，也应同步维护这些检查项。

这里使用独立字体副本，许可证位于 `assets/fonts/`。未引用的备用字体、照片和校徽已移至仓库的 `archive/resume/assets/`；恢复清单见 `archive/manifest.json`。
