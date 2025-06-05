from parser import CatalogScraper, URLExtractor, CharacteristicsParser, ImagePreviewParser, ProductDataMerger
from selenium_parser import PageDownloader

if __name__ == "__main__":
    #Парсинг каталога настройка селекторов
    scraper = CatalogScraper(
        url_template="https://erstvak.com/industrial/vintovye-kompressory/?PAGEN_1={page}",
        total_pages=23,
        product_selector=".prods__pitem",
        name_selector=".pitem__title",
        link_selector=".prods__pitem a",
        price_selector=".price_value",
        delay=1
    )

    catalog_items = scraper.run()

    #Сбор урл из словаря
    extractor = URLExtractor(catalog_items)
    product_urls = extractor.extract_urls()

    #Парсинг с поддгрузкой JS страниц товаров
    downloader = PageDownloader(product_urls, timeout=30, headless=True)
    downloader.download_pages()

    parser = CharacteristicsParser(downloader.html_pages, ".pdetail__char-l", ".pdetail__char-v")
    result = parser.parse_all()

    parser = ImagePreviewParser(downloader.html_pages, ".pdetail__im img")
    images = parser.parse_all()

    merger = ProductDataMerger(catalog_items, result, images)
    merged_data = merger.merge()
    merger.save_to_csv("products.csv")

    downloader.quit()
