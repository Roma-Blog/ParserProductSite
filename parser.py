import asyncio, aiohttp, csv
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
from tqdm import tqdm


class ProductParser:
    def __init__(self, base_url, pagination_param='page', max_pages=1,
                 card_selector='', title_selector='', link_selector=''):
        self.base_url = base_url
        self.pagination_param = pagination_param
        self.max_pages = max_pages
        self.card_selector = card_selector
        self.title_selector = title_selector
        self.link_selector = link_selector

    def build_url(self, page_num):
        parts = urlparse(self.base_url)
        query = parse_qs(parts.query)
        query[self.pagination_param] = [str(page_num)]
        new_query = urlencode(query, doseq=True)
        return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment))

    async def fetch(self, session, url):
        try:
            async with session.get(url, timeout=10) as resp:
                resp.raise_for_status()
                return await resp.text()
        except Exception as e:
            print(f"[Ошибка запроса] {url}: {e}")
            return ''

    def parse_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        for card in soup.select(self.card_selector):
            title_elem = card.select_one(self.title_selector)
            link_elem = card.select_one(self.link_selector)

            title = title_elem.get_text(strip=True) if title_elem else 'Нет названия'
            relative_link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
            full_link = urljoin(self.base_url, relative_link) if relative_link else 'Нет ссылки'

            products.append({
                'title': title,
                'url': full_link
            })

        return products

    async def fetch_and_parse(self, session, page_num):
        url = self.build_url(page_num)
        html = await self.fetch(session, url)
        return self.parse_html(html)

    async def parse_all(self):
        all_products = []
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_and_parse(session, page)
                     for page in range(1, self.max_pages + 1)]

            for coro in tqdm(asyncio.as_completed(tasks), total=self.max_pages, desc="Парсинг товаров"):
                result = await coro
                all_products.extend(result)
        return all_products


class ProductDetailParser:
    def __init__(self,
                 features_block_selector,
                 param_name_selector,
                 param_value_selector,
                 price_selector=None,
                 discount_price_selector=None,
                 image_selector=None):
        """
        :param features_block_selector: Селектор блока с характеристиками
        :param param_name_selector: Селектор названия характеристики
        :param param_value_selector: Селектор значения характеристики
        :param price_selector: Селектор обычной цены
        :param discount_price_selector: Селектор цены со скидкой (если есть)
        :param image_selector: Селектор изображения
        """
        self.features_block_selector = features_block_selector
        self.param_name_selector = param_name_selector
        self.param_value_selector = param_value_selector
        self.price_selector = price_selector
        self.discount_price_selector = discount_price_selector
        self.image_selector = image_selector

    async def fetch_html(self, session, url):
        try:
            async with session.get(url, timeout=10) as resp:
                resp.raise_for_status()
                return await resp.text()
        except Exception as e:
            print(f"[Ошибка при запросе] {url}: {e}")
            return ''

    def parse_features(self, soup):
        data = {}

        block = soup.select_one(self.features_block_selector)
        if not block:
            return data

        names = block.select(self.param_name_selector)
        values = block.select(self.param_value_selector)

        for name, value in zip(names, values):
            key = name.get_text(strip=True)
            val = value.get_text(strip=True)
            if key:
                data[key] = val

        return data

    def parse_prices(self, soup):
        """Извлекает обычную и скидочную цену (если есть)."""
        price = None
        discount_price = None

        if self.price_selector:
            price_elem = soup.select_one(self.price_selector)
            if price_elem:
                price = price_elem.get_text(strip=True)

        if self.discount_price_selector:
            discount_elem = soup.select_one(self.discount_price_selector)
            if discount_elem:
                discount_price = discount_elem.get_text(strip=True)

        return price, discount_price

    def parse_image(self, soup, base_url):
        if not self.image_selector:
            return None
        elem = soup.select_one(self.image_selector)
        if elem and 'src' in elem.attrs:
            return urljoin(base_url, elem['src'])
        return None

    async def parse_all_product_details(self, products):
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [self._parse_single(session, product) for product in products]

            for coro in tqdm(asyncio.as_completed(tasks), total=len(products), desc="Парсинг характеристик"):
                result = await coro
                results.append(result)
        return results

    async def _parse_single(self, session, product):
        html = await self.fetch_html(session, product['url'])
        soup = BeautifulSoup(html, 'html.parser')

        features = self.parse_features(soup)
        price, discount_price = self.parse_prices(soup)
        image = self.parse_image(soup, product['url'])

        return {
            **product,
            **features,
            'price': price,
            'discount_price': discount_price,
            'image': image
        }
    
class CSVExporter:
    def __init__(self, filename='output.csv'):
        self.filename = filename

    def export(self, data):
        if not data:
            print("[WARN] Нет данных для экспорта.")
            return

        fieldnames = sorted({key for item in data for key in item.keys()})

        try:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            print(f"[INFO] Данные успешно сохранены в {self.filename}")
        except Exception as e:
            print(f"[ERROR] Ошибка при записи CSV: {e}")