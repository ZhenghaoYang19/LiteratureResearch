from scraper import PaperScraper
import traceback

def main():
    try:

        scraper = PaperScraper("Nuclear Fusion")
        scraper.scrape_papers(2020, 2021, 1, 12) # 2020-2021年, 1-12月
        # scraper.scrape_papers(2021, 2021, 9, 9)
        scraper.save_to_excel()
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 