# AI4 AI4Fusion Literature Research

这是一个用于爬取和分析核聚变领域中AI相关论文的Python工具。目前支持从《Nuclear Fusion》期刊爬取论文信息。

## 功能特点

- 自动爬取指定年份和月份的论文
- 使用Qwen 2.5模型智能识别AI相关论文
- 自动生成中文论文总结
- 提取论文发布日期和机构信息
- 支持结果导出为Excel格式
- 支持断点续传和去重

## 环境要求

- Python 3.8+ (在3.12上测试通过)
- Chrome浏览器（如果使用Selenium模式）

## 安装步骤

1. 克隆仓库：
   bash
   git clone [仓库地址]
   cd [项目目录]

2. 安装依赖：
   bash
   pip install -r requirements.txt

## 使用方法

1. 修改`main.py`中的时间范围：

   ```python
   scraper = PaperScraper("Nuclear Fusion")
   scraper.scrape_papers(2020, 2021, 1, 12) # 爬取2020-2021年的所有期刊
   ```

2. 运行`main.py`：

   ```bash
   python main.py

## 注意事项

1. **硬件要求**：
   - 运行Qwen 2.5模型需要至少16GB显存的GPU
   - 如果GPU显存不足，可能需要更换较小的模型

2. **网络要求**：
   - 需要稳定的网络连接
   - 如遇到网络错误会自动重试
   - 国内使用modelscope下载模型，如果在国外需要自行更换为transformers

3. **存储空间**：
   - 会下载论文PDF到`Papers`文件夹
   - 请确保有足够的存储空间

4. **运行时间**：
   - 第一次运行需要下载模型，耗时较长，Qwen 2.5模型大小14G，请确保网络畅通且有充足空间
   - 由于需要进行AI分析，处理每篇论文需要一定时间
   - 在台式4090显卡和千兆网速环境下测试，处理1篇论文耗时1s左右，但是下载PDF需要30~60s
   - 建议分批次爬取，避免一次爬取时间过长

5. **结果保存**：
   - 结果保存在`ai_fusion_papers.xlsx`
   - 程序支持断点续传，可以多次运行
   - 重复论文会自动去重

## 输出说明

Excel文件包含以下字段：
- title: 论文标题
- journal: 期刊名称
- volume_issue: 卷期号
- doi: 论文DOI
- first_institution: 第一作者单位
- second_institution: 第二作者单位
- summary: 中文内容简介
- pub_date: 发布日期

## 常见问题

1. 如果遇到模型加载错误，请检查：
   - GPU显存是否足够
   - CUDA是否正确安装
   - modelscope是否正确安装

2. 如果遇到网络错误：
   - 检查网络连接
   - 考虑使用代理
   - 程序会自动重试失败的请求

3. 如果需要使用Selenium模式：
   - Selenium模式未开发完全，欢迎贡献
   - 修改`PaperScraper`初始化参数：`use_selenium=True`
   - 确保已安装Chrome浏览器
   - 确保已安装对应版本的ChromeDriver

## 许可证

Copyright 2024 [Harry Young](https://github.com/ZhenghaoYang19)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## 联系方式

[Harry Young](https://github.com/ZhenghaoYang19)
