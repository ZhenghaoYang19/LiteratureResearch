import pdfplumber
import re
from datetime import datetime

class PDFExtractor:
    def __init__(self):
        self.metadata = {}
    
    def extract_pub_data(self, pdf_path):
        """
        从PDF中提取发布日期
        返回格式: YYYY/MM/DD
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[1].extract_text() or ''
                # 查找发布日期的常见模式
                # 例如: "Published 30 Octorber 2019"
                date_patterns = [
                    r'Published\s*(\d{1,2}\s*[A-Za-z]+\s*\d{4})',  
                    # r'Accepted\s*(\d{1,2}\s*[A-Za-z]+\s*\d{4})',
                    # r'Received\s*(\d{1,2}\s*[A-Za-z]+\s*\d{4})'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, first_page)
                    if match:
                        date_str = match.group(1)
                        return self._format_date(date_str)
                return ''
                
        except Exception as e:
            print(f"Error extracting publication date: {e}")
            return ''
    
    def _format_date(self, date_str):
        """
        将日期字符串转换为标准格式 (YYYY/MM/DD)
        """
        try:
            # 移除所有空格后重新插入单个空格
            date_str = ' '.join(re.findall(r'\d+|[A-Za-z]+', date_str))
            # 月份映射
            month_map = {
                'January': '01', 'February': '02', 'March': '03', 'April': '04',
                'May': '05', 'June': '06', 'July': '07', 'August': '08',
                'September': '09', 'October': '10', 'November': '11', 'December': '12'
            }
            
            # 解析日期字符串，例如 " 30 Octorber 2019 "
            day, month, year = date_str.split()
            day = day.zfill(2)  # 确保日期是两位数
            month = month_map.get(month, '01')
            return f"{year}/{month}/{day}"
            
        except Exception as e:
            print(f"Error formatting date '{date_str}': {e}")
            return ''

    def extract_affiliations(self, pdf_path):
        """
        从PDF中提取第一作者单位和第二作者单位
        返回: (first_institution, second_institution)
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                second_page = pdf.pages[1].extract_text() if len(pdf.pages) > 1 else ''
                text = second_page
                
                # 机构关键词（支持多语言）
                institution_keywords = (
                    # 英语
                    r'University|Institute|Laboratory|Center|Centre|Department|School|Physics|Consortium|' 
                    # 德语
                    r'Universität|Institut|Zentrum|Abteilung|Schule|'
                    # 法语
                    r'Université|Institut|Laboratoire|Centre|École|'
                    # 中文
                    r'大学|研究所|实验室|中心|学院|研究院|物理|'
                    # 日语
                    r'大学|研究所|実験室|センター|'
                    # 俄语
                    r'Университет|Институт|Лаборатория|Центр|'
                    # 西班牙语
                    r'Universidad|Instituto|Laboratorio|Centro|Facultad|Departamento|Escuela|'
                    # 葡萄牙语
                    r'Universidade|Instituto|Laboratório|Centro|Faculdade|Departamento|Escola|'
                    # 意大利语
                    r'Università|Istituto|Laboratorio|Centro|Dipartimento|Scuola|Consorzio'
                )
                
                # 方法1：匹配编号的机构
                # 1. 使用 (?m) 开启多行模式
                # 2. 使用 \s* 来处理可能缺失的空格
                # 3. 使用 [^\n]* 来匹配除换行外的所有字符
                affiliation_pattern = fr'(?m)^(\d)\s*([^\n]*?(?:{institution_keywords})[^\n]*?)(?=\n\d|\n\s*$|$)'
                matches = list(re.finditer(affiliation_pattern, text))
                
                # 直接存储匹配结果
                affiliation_dict = {}
                for match in matches:
                    number = int(match.group(1))  # 第一个捕获组是数字
                    institution = self._clean_affiliation(match.group(2))  # 第二个捕获组是机构名称
                    if institution:  # 只保存非空的机构名称
                        affiliation_dict[number] = institution
                        print(f"Found institution {number}: {institution}")  # 调试信息
                
                # 按序号排序获取机构列表
                affiliations = [affiliation_dict[i] for i in sorted(affiliation_dict.keys()) if i in affiliation_dict]
                
                # 如果方法1失败，使用方法2
                if not affiliations:
                    print("Method 1 failed, trying method 2...")  # 调试用
                    lines = text.split('\n')
                    for line in lines:
                        if any(keyword in line for keyword in institution_keywords.split('|')):
                            clean_line = self._clean_affiliation(line)
                            if clean_line and clean_line not in affiliations:
                                affiliations.append(clean_line)
                
                # 返回前两个机构（如果存在）
                first_institution = affiliations[0] if affiliations else ''
                second_institution = affiliations[1] if len(affiliations) > 1 else ''
                
                return first_institution, second_institution
                
        except Exception as e:
            print(f"Error extracting affiliations: {e}")
            import traceback
            print(traceback.format_exc())  # 打印完整错误信息
            return '', ''
    
    def _clean_affiliation(self, text):
        """清理机构文本"""
        if not text:
            return ''
        
        # 移除开头的数字和空格
        text = re.sub(r'^\d+\s*', '', text)
        
        # 移除邮箱地址
        text = re.sub(r'\S+@\S+', '', text)
        
        # 移除多余的空格和换行，但保留一个空格
        text = ' '.join(text.split())
        
        # 保留所有Unicode字符、数字、空格和常用标点符号
        text = re.sub(r'[^\w\s,.()\'"/-àáâãäçèéêëìíîïñòóôõöùúûüýÀÁÂÃÄÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ]', '', text)
        
        # 移除孤立的数字，但保留邮政编码和门牌号
        text = re.sub(r'(?<!\d)\b\d+\b(?!\d)', '', text)
        
        # 移除前后空格
        text = text.strip()
        
        # 如果清理后文本太短，可能不是有效的机构名
        if len(text) < 10:  # 可以调整这个阈值
            return ''
        
        return text
    
    def extract_metadata(self, pdf_path):
        """
        提取PDF的元数据（卷刊号、DOI和发布日期）
        返回: dict包含volume_issue、doi和pub_date
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0].extract_text() or ''
                
                # 提取DOI
                doi_match = re.search(r'https://doi.org/([\S]+)', first_page)
                if doi_match:
                    self.metadata['doi'] = doi_match.group(1)
                
                # 提取卷刊号
                volume_match = re.search(r'Nucl.\s*Fusion\s*(\d+)\s*\((\d+)\)', first_page)
                if volume_match:
                    volume = volume_match.group(1)
                    issue = volume_match.group(2)
                    self.metadata['volume_issue'] = f"{volume} {issue}"
                
                # 提取发布日期
                self.metadata['pub_date'] = self.extract_pub_data(pdf_path)
                
                return self.metadata
                
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
    
    def extract_text_from_page(self, pdf_path, page_number):
        """
        提取指定页面的文本
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if 0 <= page_number < len(pdf.pages):
                    return pdf.pages[page_number].extract_text() or ''
                return ''
        except Exception as e:
            print(f"Error extracting text from page {page_number}: {e}")
            return '' 