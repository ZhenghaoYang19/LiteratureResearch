from pdf_extractor import PDFExtractor
import argparse

test_pdf_path_1 = 'Papers/A disruption predictor based o.pdf'
test_pdf_path_2 = 'Papers/Scaling laws of the energy con.pdf'
test_pdf_path_3 = 'Papers/Physics-guided machine learnin.pdf'
parser = argparse.ArgumentParser(description='Extract publication date and affiliations from a PDF file')
# 可选择pdf_path
parser.add_argument('--pdf_path', '-p', help='Path to the PDF file', default=test_pdf_path_1)
args = parser.parse_args()

extractor = PDFExtractor()

pub_date = extractor.extract_pub_data(args.pdf_path)
print(pub_date)

first_institution, second_institution = extractor.extract_affiliations(args.pdf_path)
print(first_institution)
print(second_institution)

