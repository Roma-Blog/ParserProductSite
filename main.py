from parser import CatalogScraper, URLExtractor, CharacteristicsParser, ImagePreviewParser, ProductDataMerger
from selenium_parser import PageDownloader

if __name__ == "__main__":
    #Парсинг каталога настройка селекторов
    scraper = CatalogScraper(
        url_template="https://habe.com.ru/catalog/vintovye_kompressory/?page-{page}",
        total_pages=1,
        product_selector=".list_item",
        name_selector="a.js-notice-block__title span",
        link_selector="a.js-notice-block__title",
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

    parser = CharacteristicsParser(downloader.html_pages, ".properties-group__name", ".properties-group__value")
    result = parser.parse_all()

    parser = ImagePreviewParser(downloader.html_pages, "img.detail-gallery-big__picture")
    images = parser.parse_all()

    merger = ProductDataMerger(catalog_items, result, images)
    merged_data = merger.merge()
    merger.save_to_csv("products.csv")

    downloader.quit()
