import requests, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv

#Парсим каталог товаров
class CatalogScraper:
    def __init__(self, url_template, total_pages, product_selector, name_selector, link_selector, price_selector, delay=1, num_start_page = 1):
        """
        :param url_template: Строка с шаблоном URL, например: "https://site.com/catalog?page={page}"
        :param total_pages: Количество страниц для парсинга
        :param product_selector: CSS-селектор карточки товара
        :param name_selector: CSS-селектор названия товара внутри карточки
        :param link_selector: CSS-селектор ссылки на товар внутри карточки
        :param price_selector: CSS-селектор цены внутри карточки
        :param delay: Задержка между запросами (секунды)
        :param num_start_page: номер страницы каталога с которого начинается парсинг
        """
        self.url_template = url_template
        self.total_pages = total_pages
        self.product_selector = product_selector
        self.name_selector = name_selector
        self.link_selector = link_selector
        self.price_selector = price_selector
        self.delay = delay
        self.num_start_page = num_start_page
        self.base_url = "{0.scheme}://{0.netloc}".format(requests.utils.urlparse(url_template))

    def _fetch_page(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def _parse_products(self, html):
        soup = BeautifulSoup(html, "lxml")
        products = []

        for card in soup.select(self.product_selector):
            try:
                name_elem = card.select_one(self.name_selector)
                link_elem = card.select_one(self.link_selector)
                price_elem = card.select_one(self.price_selector)

                if not (name_elem and link_elem):
                    print("Проьлема с элементами: " + name_elem + " | " + link_elem)
                    continue

                name = name_elem.get_text(strip=True)
                rel_link = link_elem.get("href")
                link = urljoin(self.base_url, rel_link)

                price = "Цена по запросу"
                if price_elem is not None:
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

        for page in range(self.num_start_page, self.total_pages + 1):
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
    


class CharacteristicsParser:
    def __init__(self, html_dict, name_selector, value_selector):
        """
        :param html_dict: словарь {url: html_content}
        :param name_selector: CSS-селектор для названий характеристик
        :param value_selector: CSS-селектор для значений характеристик
        """
        self.html_dict = html_dict
        self.name_selector = name_selector
        self.value_selector = value_selector
        self.parsed_data = {}

    def parse_all(self):
        for url, html in self.html_dict.items():
            print(f"🔍 Парсинг характеристик с {url}")
            soup = BeautifulSoup(html, "lxml")

            names = soup.select(self.name_selector)
            values = soup.select(self.value_selector)

            if len(names) != len(values):
                print(f"⚠️ Несовпадение количества названий и значений на {url}")
                count = min(len(names), len(values))
            else:
                count = len(names)

            characteristics = {}
            for i in range(count):
                name = names[i].get_text(strip=True)
                value = values[i].get_text(strip=True)
                if name and value:
                    characteristics[name] = value

            self.parsed_data[url] = characteristics

        return self.parsed_data
    
class ImagePreviewParser:
    def __init__(self, html_dict, img_selector):
        """
        :param html_dict: словарь {url: html_content}
        :param img_selector: CSS-селектор для поиска изображений (например, "img.product-preview")
        """
        self.html_dict = html_dict
        self.img_selector = img_selector
        self.result = {}

    def parse_all(self):
        for url, html in self.html_dict.items():
            print(f"🖼 Парсинг изображения с {url}")
            soup = BeautifulSoup(html, "lxml")
            img_tag = soup.select_one(self.img_selector)

            if img_tag and img_tag.has_attr("src"):
                img_url = img_tag["src"]
                full_img_url = urljoin(url, img_url)
                self.result[url] = full_img_url
            else:
                print(f"⚠️ Изображение не найдено на {url}")
                self.result[url] = None

        return self.result
    
class ProductDataMerger:
    def __init__(self, catalog_data, characteristics, images):
        """
        :param catalog_data: список словарей [{'name': ..., 'url': ..., 'price': ...}, ...]
        :param characteristics: словарь {url: {характеристика: значение}}
        :param images: словарь {url: ссылка_на_изображение}
        """
        self.catalog_data = catalog_data
        self.characteristics = characteristics
        self.images = images
        self.result = []

    def merge(self):
        for item in self.catalog_data:
            url = item.get("url")
            merged_item = {
                "URL": url,
                "Название": item.get("name"),
                "Цена": item.get("price"),
                "Изображение": self.images.get(url),
            }

            # Добавляем характеристики, если они есть
            specs = self.characteristics.get(url, {})
            merged_item.update(specs)

            self.result.append(merged_item)

        return self.result

    def save_to_csv(self, filepath="products.csv"):
        if not self.result:
            print("⚠️ Нет данных для сохранения.")
            return

        # Собираем все возможные заголовки
        all_keys = set()
        for item in self.result:
            all_keys.update(item.keys())

        fieldnames = sorted(all_keys)

        with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.result)

        print(f"✅ Данные сохранены в файл: {filepath}")