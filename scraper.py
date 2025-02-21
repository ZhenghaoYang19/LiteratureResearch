import requests
from bs4 import BeautifulSoup
import pandas as pd
from modelscope import AutoModelForCausalLM, AutoTokenizer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from random import uniform, choice
import torch
import os
from PDFExtractor.pdf_extractor import PDFExtractor
import time


class PaperScraper:
    def __init__(self, journal, use_selenium=False):
        """
        Args:
            journal: 期刊名称
            use_selenium: 是否使用selenium下载PDF，默认False使用requests
        """
        self.journal = journal
        # 初始化Qwen模型
        self.model_name = "Qwen/Qwen2.5-7B-Instruct"
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        print(f"Model device: {next(self.model.parameters()).device}")
        
        self.papers = []
        
        # 是否使用selenium
        self.use_selenium = use_selenium
        if use_selenium:
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # 无头模式
            self.driver = webdriver.Chrome(options=chrome_options)
            print("Using Selenium")
        else:
            print("Using Requests")
        
        self.min_interval = 5  # 最小请求间隔（秒）
        self.last_request_time = 0  # 上次请求时间
        
        # 添加 headers 相关的属性
        self.current_headers = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        self.accept_languages = [
            'en-US,en;q=0.9',
            'en-GB,en;q=0.9',
            'en-CA,en;q=0.9',
            'en-AU,en;q=0.9',
            'en,zh-CN;q=0.9,zh;q=0.8'
        ]
        
    def get_headers(self, force_new=False):
        """获取请求头，force_new为True时强制生成新的headers"""
        if self.current_headers is None or force_new:
            self.current_headers = {
                'User-Agent': choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': choice(self.accept_languages),
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1'
            }
        return self.current_headers

    def get_page_content(self, volume, issue, force_new_headers=False):
        """获取指定卷期的页面内容"""
        if self.journal == "Nuclear Fusion":
            url = f"https://iopscience.iop.org/issue/0029-5515/{volume}/{issue}"
        else:
            print(f"Unsupported journal: {self.journal}")
            return None

        headers = self.get_headers(force_new=force_new_headers)
        
        try:
            session = requests.Session()
            # 添加随机延迟
            sleep(uniform(1, 3))
            response = session.get(url, headers=headers, timeout=30)
            
            # 检查是否被重定向到登录页面或错误页面
            if 'login' in response.url.lower() or response.status_code != 200:
                print(f"Access denied or redirected. Status code: {response.status_code}")
                return None
            
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
        
    def format_pub_date(self, date_str):
        """将发表日期转换为标准格式 (YYYY/MM/DD)"""
        if not date_str:
            return ''
        
        # 移除"Published"前缀
        date_str = date_str.replace('Published', '').strip()
        
        # 月份映射
        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        
        try:
            # 解析日期字符串，例如 "30 October 2019"
            day, month, year = date_str.split()
            day = day.zfill(2)  # 确保日期是两位数
            month = month_map.get(month, '01')
            print(f"{year}/{month}/{day}")
            return f"{year}/{month}/{day}"
        except Exception as e:
            print(f"Error formatting date '{date_str}': {e}")
            return date_str

    def parse_paper_info(self, html, volume):
        """解析网页提取论文信息"""
        soup = BeautifulSoup(html, 'html.parser')
        papers_info = []
        
        # 查找所有论文条目
        for paper in soup.find_all('div', class_='art-list-item'):
            paper_info = {
                'title': '',
                'journal': '',
                'volume_issue': '',
                'doi': '',
                'first_institution': '',
                'second_institution': '',
                'summary': '',
                'pub_date': ''
            }
            try:
                # 提取标题
                title_elem = paper.find('a', class_='art-list-item-title')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                paper_info['title'] = title
                
                # 提取摘要
                abstract_elem = paper.find('div', class_='article-text wd-jnl-art-abstract cf')
                abstract = ''
                if abstract_elem and abstract_elem.find('p'):
                    abstract = abstract_elem.find('p').text.strip()
                if not abstract:
                    continue
                
                print(f"Processing paper: {title}")
                # 提取DOI
                doi_elem = paper.find('a', href=lambda x: x and 'doi.org' in x)
                if doi_elem:
                    doi = doi_elem.text.strip()
                    if doi.startswith('https://doi.org/'):
                        doi = doi.replace('https://doi.org/', '')
                    paper_info['doi'] = doi
                
                # 提取卷期号
                indexer = paper.find('div', class_='indexer')
                if indexer:
                    paper_info['volume_issue'] = f"{volume} {indexer.text.strip()}"
                
                # 使用模型判断是否为AI相关论文并生成内容简介
                if self.is_ai_related(title, abstract):
                    # 生成内容简介
                    summary = self.generate_summary(title, abstract)
                    paper_info['summary'] = summary
                    paper_info['journal'] = self.journal
                    
                    # 下载PDF并提取pub_data, affiliations
                    if paper_info['doi']:
                        path = self.download_pdf(doi, title)
                        if path:
                            extractor = PDFExtractor()
                            pub_date = extractor.extract_pub_data(path)
                            first_institution, second_institution = extractor.extract_affiliations(path)
                            paper_info['pub_date'] = pub_date
                            paper_info['first_institution'] = first_institution
                            paper_info['second_institution'] = second_institution
                    
                    papers_info.append(paper_info)
                    print(f"Found AI-related paper: {title}")
            
            except Exception as e:
                print(f"Error parsing paper: {e}")
                import traceback
                print(traceback.format_exc())
                continue
        
        return papers_info

    def generate_summary(self, title, abstract):
        """生成中文内容简介"""
        prompt = f"""
        请根据以下论文的标题和摘要，生成一段中文内容简介（150字左右），如果文章有这些相关信息，则重点说明：
        1. 研究目的和方法
        2. 使用的AI技术
        3. 主要发现和结论
        4. 应用场景和实验装置
        如果文章没有这些相关信息，则不用提及。
        
        标题：{title}
        摘要：{abstract}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的核聚变领域专家。'disruption', 'stellarator', 'renormalization'分别翻译为'破裂', '仿星器', '重整化'。'SOL', 'ITER'则不用翻译。"},
            {"role": "user", "content": prompt}
        ]
        
        with torch.no_grad():
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            input_length = model_inputs.input_ids.shape[1]
            
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=300,
                do_sample=True,
                temperature=0.7
            )
            
            summary = self.tokenizer.batch_decode(
                generated_ids[:, input_length:],
                skip_special_tokens=True
            )[0]
        
        return summary.strip()

    def is_ai_related(self, title, abstract):
        """使用Qwen模型判断论文是否与AI相关"""
        # print(f"Abstract preview: {abstract[:200]}...")
        
        prompt = f"""
        请判断以下论文是否与人工智能和磁约束核聚变相关。
        判断标准：
        1. 论文涉及机器学习、深度学习、神经网络等AI技术，
        2. 论文应用于磁约束核聚变领域
        3. 如果只是普通的数值模拟或者物理分析，不算是AI相关
        
        标题：{title}
        摘要：{abstract}
        
        请分析后回答"True"或"False"，并用中文简要说明原因。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的核聚变领域专家。'disruption', 'stellarator', 'renormalization'分别翻译为'破裂', '仿星器', '重整化'。'SOL', 'ITER'则不用翻译。"},
            {"role": "user", "content": prompt}
        ]
        
        with torch.no_grad():
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            input_length = model_inputs.input_ids.shape[1]  # 获取输入长度
            
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=50, # 经过测试的合适值
                do_sample=True
            )
            
            # 只获取新生成的部分（最后一次回答）
            response = self.tokenizer.batch_decode(
                generated_ids[:, input_length:], 
                skip_special_tokens=True
            )[0]
        
        if "True" in response:
            print(f"AI analysis result: {response}")  # 打印分析结果
            return True
        else:
            return False

    def scrape_papers(self, start_year, end_year, start_month, end_month):
        """爬取指定年份和月份的期刊论文"""
        if self.journal == "Nuclear Fusion":
            start_volume = start_year - 1960
            end_volume = end_year - 1960
        else:
            print(f"Unsupported journal: {self.journal}")
            return
        
        for volume in range(start_volume, end_volume + 1):  
            for month in range(start_month, end_month + 1):  
                print(f"\nProcessing volume {volume}, month {month}")
                
                html = self.get_page_content_with_retry(volume, month)
                # # 将HTML内容保存到文件中
                # filename = f"debug_html_v{volume}_i{issue}.html"
                # with open(filename, "w", encoding="utf-8") as f:
                #     f.write(html)
                # print(f"HTML content saved to {filename}")
                if html:
                    paper_info = self.parse_paper_info(html, volume)
                    print(f"Found {len(paper_info)} AI-related papers in volume {volume}, month {month}")
                    if paper_info:
                        print("Papers found in this issue:")
                        for paper in paper_info:
                            print(f"- {paper['title']}")
                    self.papers.extend(paper_info)
                else:
                    print(f"Failed to get content for volume {volume}, month {month}")
                
                sleep(uniform(2, 5))  # 随机延迟
    
    def save_to_excel(self, filename="ai_fusion_papers.xlsx"):
        """将结果保存为Excel文件"""
        # 定义列顺序
        columns_order = [
            'title', 'journal', 'volume_issue', 'doi', 'first_institution', 
            'second_institution', 'summary', 'pub_date'
        ]
        
        # 创建新数据的DataFrame
        new_df = pd.DataFrame(self.papers)
        
        # 确保所有列都存在
        for col in columns_order:
            if col not in new_df.columns:
                new_df[col] = ''
        
        # 按指定顺序排列列
        new_df = new_df[columns_order]
        
        try:
            # 如果文件存在，读取现有数据并追加新数据
            if os.path.exists(filename):
                existing_df = pd.read_excel(filename)
                # 合并现有数据和新数据
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # 分别对标题和DOI去重，保留最新的记录
                combined_df = combined_df.drop_duplicates(subset=['title'], keep='last')
                combined_df = combined_df.drop_duplicates(subset=['doi'], keep='last')
                
                print(f"Updated {len(new_df)} new papers to existing file")
                combined_df.to_excel(filename, index=False)
            else:
                # 如果文件不存在，直接保存新数据
                print(f"Creating new file with {len(new_df)} papers")
                new_df.to_excel(filename, index=False)
            
            print(f"Total papers in file: {len(pd.read_excel(filename))}")
            print(f"\nResults saved to {filename}")
        except Exception as e:
            print(f"Error saving to Excel: {e}")
            # 如果保存失败，创建带时间戳的备份文件
            from datetime import datetime
            backup_filename = f"ai_fusion_papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            new_df.to_excel(backup_filename, index=False)
            print(f"Backup saved to {backup_filename}")

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'driver') and self.use_selenium:
            self.driver.quit()

    def get_page_content_with_retry(self, volume, issue, max_retries=3):
        """带重试机制的页面获取"""
        for attempt in range(max_retries):
            try:
                # 第三次重试时更换headers
                force_new_headers = (attempt == 2)
                if force_new_headers:
                    print("Changing headers for final retry...")
                
                content = self.get_page_content(volume, issue, force_new_headers=force_new_headers)
                if content and "We apologize for the inconvenience" not in content:
                    return content
                
                # 指数退避策略
                sleep_time = (2 ** attempt) * uniform(2, 5)
                print(f"Retry {attempt + 1}/{max_retries}, waiting {sleep_time:.1f}s...")
                sleep(sleep_time)
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                sleep_time = (2 ** attempt) * uniform(2, 5)
                sleep(sleep_time)
        
        return None

    def download_pdf(self, doi, title):
        """下载论文PDF并保存到Papers文件夹"""
        os.makedirs('Papers', exist_ok=True)
        
        # 构造文件名（使用标题的前30个字符）
        safe_title = "".join(x for x in title[:30] if x.isalnum() or x in (' ', '-', '_')).strip()
        filename = f"Papers/{safe_title}.pdf"
        
        # 如果文件已存在，跳过下载
        if os.path.exists(filename):
            print(f"PDF already exists: {filename}")
            return filename

        pdf_url = f"https://iopscience.iop.org/article/{doi}/pdf"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://iopscience.iop.org/article/{doi}'
        }
        
        try:
            if not self.use_selenium:
                # 使用requests下载
                response = requests.get(pdf_url, headers=headers)
                if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('application/pdf'):
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"PDF downloaded: {filename}")
                    return filename
                else:
                    print(f"Requests download failed: {response.status_code}")
                    print(f"Content-Type: {response.headers.get('Content-Type')}")
                    return None
                
            if self.use_selenium:
                # 使用selenium下载
                try:
                    self.driver.get(pdf_url)
                    sleep(5)  # 等待PDF加载
                    
                    response = requests.get(self.driver.current_url, headers=headers)
                    if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('application/pdf'):
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        print(f"PDF downloaded via selenium: {filename}")
                        return filename
                    else:
                        print(f"Selenium download failed: {response.status_code}")
                except Exception as e:
                    print(f"Selenium download error: {e}")
                    return None
                
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return None
        
    def wait_for_next_request(self):
        """控制请求频率"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            sleep(sleep_time)
        self.last_request_time = time.time()


