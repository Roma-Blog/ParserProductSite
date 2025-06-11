from parser import CatalogScraper, URLExtractor, CharacteristicsParser, ImagePreviewParser, ProductDataMerger
from selenium_parser import PageDownloader

if __name__ == "__main__":
    #Парсинг каталога настройка селекторов
    scraper = CatalogScraper(
        url_template="https://ctt-stroy.ru/product/peredvizhnye-kompressory/filter/brand-is-liugong/apply/?PAGEN_2={page}",
        total_pages=3,
        product_selector=".catalog-block__wrapper",
        name_selector="a.switcher-title span",
        link_selector="a.switcher-title",
        price_selector=".price__new-val",
        num_start_page = 1,
        delay=1
    )

    catalog_items = scraper.run()

    #Сбор урл из словаря
    extractor = URLExtractor(catalog_items)
    product_urls = extractor.extract_urls()

    #Парсинг с поддгрузкой JS страниц товаров
    downloader = PageDownloader(product_urls, timeout=30, headless=True)
    downloader.download_pages()

    parser = CharacteristicsParser(downloader.html_pages, ".props_item.js-prop-title span", ".char_value.js-prop-value span")
    result = parser.parse_all()

    parser = ImagePreviewParser(downloader.html_pages, "img.catalog-detail__gallery__picture")
    images = parser.parse_all()

    merger = ProductDataMerger(catalog_items, result, images)
    merged_data = merger.merge()
    merger.save_to_csv("products.csv")

    downloader.quit()
