import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

#Парсим каталог товаров
class CatalogScraper:
    def __init__(self, url_template, total_pages, product_selector, name_selector, link_selector, price_selector, delay=1):
        """
        :param url_template: Строка с шаблоном URL, например: "https://example.com/catalog?page={page}"
        :param total_pages: Количество страниц для парсинга
        :param product_selector: CSS-селектор карточки товара
        :param name_selector: CSS-селектор названия товара внутри карточки
        :param link_selector: CSS-селектор ссылки на товар внутри карточки
        :param price_selector: CSS-селектор цены внутри карточки
        :param delay: Задержка между запросами (секунды)
        """
        self.url_template = url_template
        self.total_pages = total_pages
        self.product_selector = product_selector
        self.name_selector = name_selector
        self.link_selector = link_selector
        self.price_selector = price_selector
        self.delay = delay
        self.base_url = "{0.scheme}://{0.netloc}".format(requests.utils.urlparse(url_template))

    def _fetch_page(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def _parse_products(self, html):
        soup = BeautifulSoup(html, "html.parser")
        products = []

        for card in soup.select(self.product_selector):
            try:
                name_elem = card.select_one(self.name_selector)
                link_elem = card.select_one(self.link_selector)
                price_elem = card.select_one(self.price_selector)

                if not (name_elem and link_elem and price_elem):
                    continue

                name = name_elem.get_text(strip=True)
                rel_link = link_elem.get("href")
                link = urljoin(self.base_url, rel_link)
                price = price_elem.get_text(strip=True)

                products.append({
                    "name": name,
                    "url": link,
                    "price": price
                })
            except Exception as e:
                print(f"⚠️ Ошибка при парсинге товара: {e}")
        return products

    def run(self):
        all_products = []

        for page in range(1, self.total_pages + 1):
            page_url = self.url_template.format(page=page)
            print(f"📄 Парсинг страницы {page}: {page_url}")

            try:
                html = self._fetch_page(page_url)
                products = self._parse_products(html)
                all_products.extend(products)
            except Exception as e:
                print(f"❌ Ошибка при обработке страницы {page}: {e}")

            time.sleep(self.delay)

        return all_products


#Получаем ссылки на товары из структуры 
class URLExtractor:
    def __init__(self, data):
        self.data = data

    def extract_urls(self):
        return [item['url'] for item in self.data if 'url' in item]