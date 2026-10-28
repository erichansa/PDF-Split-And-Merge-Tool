# PDF 拆分 · 合并 · 瘦身工具箱 (PDF Split & Merge Tool)

[![GitHub Pages](https://img.shields.io/badge/Web%20App-Online%20Ready-blue)](https://erichansa.github.io/PDF-Split-And-Merge-Tool/)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Windows%20%7C%20Android-green)](#)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Client--Side-brightgreen)](#)

一款纯前端、100% 离线隐私安全的现代化 PDF 工具箱。支持 **PDF 拆分**（单页/自定义区间）、**多文件合并**（统一 A4 画板、解决页面忽大忽小）、**单文件智能体积瘦身**。

> 🔒 **100% 本地运算隐私保障**：所有 PDF 的解析、渲染、拆分与合并操作全部在用户本地设备（浏览器或客户端）内存中执行，**绝不向任何云端服务器上传 1 个字节**，处理商业合同、财务发票与个人证件万无一失。

---

## 🌟 核心功能

### 1. ✂️ PDF 拆分 (Split)
- **逐页拆分**：将多页 PDF 的每一页导出为单独的 PDF，并一键打包为 `.zip` 下载。
- **自定义区间提取**：支持 `1-3, 5, 7-10` 灵活提取，支持中英文逗号与分号。

### 2. 📑 PDF 合并 (Merge)
- **多文件批量拖拽**：支持文件多选、拖拽调整合并先后顺序。
- **画板尺寸自适应统一**：
  - 🌟 **统一为标准 A4（默认推荐）**：无论原图是超大扫描件还是手机拍摄图片，自动等比缩放并居中自适应，排版统一平整。
  - **以首页尺寸对齐** 或 **保留原始大小**。
- **体积智能瘦身**：合并同时对大图进行视觉无损压缩，防止合并后体积暴涨。

### 3. 🗜️ 单文件瘦身 (Compress)
- **独立单文件处理**：专门针对单个体积过大的 PDF 瘦身。
- **多档压缩强度**：
  - 🌟 **智能高清瘦身**：大图重采样至 150 DPI 优质 JPEG，体积缩减 70%~90% 以上。
  - 🚀 **极限压缩瘦身**：优化至 100 DPI，适合作为邮件附件或严格限制文件上传大小的场景。
  - 🎨 **轻度无损精简**：仅清理未引用对象和流压缩。
- **同步 A4 规范化**：可选一键修复偏大偏小的页面。

---

## 💻 运行与使用方式

### 🌐 1. 在线网页版 (Web)
直接通过浏览器访问 GitHub Pages 在线体验：
👉 **https://erichansa.github.io/PDF-Split-And-Merge-Tool/**

或者本地双击打开 [`index.html`](file:///C:/Dokumente/Tools/PDF拆分合并工具/index.html) 即可完全离线在浏览器中使用。

### 🖥️ 2. Windows 桌面客户端 (Python / GUI)
- 双击 [`启动_PDF拆分合并工具.cmd`](file:///C:/Dokumente/Tools/PDF拆分合并工具/启动_PDF拆分合并工具.cmd)
- 或运行命令：
  ```bash
  python main.py
  ```

### 📱 3. Android 安卓应用 (.apk)
通过项目配套的 Capacitor 编译流程生成安卓安装包，在手机与平板上随时随地离线使用。

---

## 📁 项目结构

```text
├── index.html                 # 纯前端 Web 单页应用
├── libs/                      # 离线核心 JS 依赖 (pdf-lib, jszip, pdf.js)
├── main.py                    # Windows 桌面客户端主程序
├── gui.py                     # PySide6 桌面界面
├── pdf_processor.py           # Python 底层处理核心
├── config.json                # 桌面客户端配置文件
├── 启动_PDF拆分合并工具.cmd     # Windows 双击启动器
└── README.md                  # 项目中英文说明文档
```

---

## 📄 License
MIT License. 欢迎 Fork 与自由使用。
