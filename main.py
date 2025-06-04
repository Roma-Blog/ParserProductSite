from parser import CatalogScraper, URLExtractor
from selenium_parser import PageDownloader

if __name__ == "__main__":
    #Парсинг каталога настройка селекторов
    scraper = CatalogScraper(
        url_template="https://air-vint.ru/catalog/kompressory/vintovye_kompressory/filter/brand-is-triumph/apply/?PAGEN_1={page}",
        total_pages=1,
        product_selector=".catalog_item",
        name_selector=".item-title span",
        link_selector=".item-title a",
        price_selector=".price_value",
        delay=1
    )

    catalog_items = scraper.run()

    #Сбор урл из словаря
    extractor = URLExtractor(catalog_items)
    product_urls = extractor.extract_urls()

    #Парсинг с поддгрузкой JS страниц товаров
    downloader = PageDownloader(product_urls, wait_selector=".product-title", timeout=15, headless=True)
    downloader.download_pages()

    # Сохраняем в файлы с именами по номеру
    for i, (url, html) in enumerate(downloader.html_pages.items(), 1):
        with open(f"page_{i}.html", "w", encoding="utf-8") as f:
            f.write(html)

    downloader.quit()