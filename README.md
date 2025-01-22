# AI4 AI4Fusion Literature Research

An LLM tool for crawling and analyzing AI-related papers in the field of fusion research. Currently supports paper crawling from the journal "Nuclear Fusion".

## Features

- Automatically crawl papers from specified years and months
- Use Qwen 2.5 model to intelligently identify AI-related papers
- Generate Chinese paper summaries automatically
- Extract publication dates and institutional information
- Export results to Excel format
- Support breakpoint resume and deduplication

## Requirements

- Python 3.8+ (tested on 3.12)
- Chrome browser (if using Selenium mode)

## Installation

1. Clone the repository:
   ```bash
   git clone [repository URL]
   cd [project directory]
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Modify the time range in `main.py`:
   ```python
   scraper = PaperScraper("Nuclear Fusion")
   scraper.scrape_papers(2020, 2021, 1, 12) # Crawl all issues from 2020-2021
   ```

2. Run `main.py`:
   ```bash
   python main.py
   ```

## Notes

1. **Hardware Requirements**:
   - Running Qwen 2.5 model requires at least 16GB GPU VRAM
   - Consider using a smaller model if GPU memory is insufficient

2. **Network Requirements**:
   - Stable network connection required
   - Automatic retry on network errors
   - Uses modelscope in China, consider switching to transformers outside China

3. **Storage Space**:
   - PDFs will be downloaded to the `Papers` folder
   - Ensure sufficient storage space

4. **Runtime**:
   - First run requires downloading the model (14GB), ensure stable network
   - AI analysis takes time for each paper
   - Tested on RTX 4090 with gigabit network: ~1s per paper analysis, 30-60s for PDF download
   - Recommended to crawl in batches

5. **Results**:
   - Results saved to `ai_fusion_papers.xlsx`
   - Supports resume from breakpoint
   - Automatic deduplication

## Output Format

Excel file contains the following fields:
- title: Paper title
- journal: Journal name
- volume_issue: Volume and issue number
- doi: Paper DOI
- first_institution: First author's institution
- second_institution: Second author's institution
- summary: Chinese content summary
- pub_date: Publication date

## Troubleshooting

1. Model loading errors:
   - Check GPU memory
   - Verify CUDA installation
   - Check modelscope installation

2. Network errors:
   - Check network connection
   - Consider using proxy
   - Program will retry automatically

3. Selenium mode:
   - Selenium mode is experimental
   - Set `use_selenium=True` in `PaperScraper` initialization
   - Ensure Chrome browser is installed
   - Ensure matching ChromeDriver version

## License

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

## Contact

[Harry Young](https://github.com/ZhenghaoYang19)

[中文文档](README_CN.md)
