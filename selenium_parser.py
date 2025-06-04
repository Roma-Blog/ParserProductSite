from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class PageDownloader:
    def __init__(self, urls, wait_selector=None, timeout=15, headless=True):
        self.urls = urls
        self.wait_selector = wait_selector
        self.timeout = timeout
        self.html_pages = {}  # Словарь: {url: html}

        # Настройки Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # Инициализация драйвера
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

    def wait_for_page_ready(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def download_pages(self):
        for idx, url in enumerate(self.urls, start=1):
            print(f"📄 Парсинг страницы {idx}: {url}")
            self.driver.get(url)

            # Ждём полной загрузки документа
            self.wait_for_page_ready()

            # Ждём нужный элемент (если задан)
            if self.wait_selector:
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, self.wait_selector))
                    )
                except Exception as e:
                    print(f"⚠️ Элемент '{self.wait_selector}' не найден или не видим: {e}")

            # Сохраняем в словарь: url -> html
            self.html_pages[url] = self.driver.page_source

    def quit(self):
        self.driver.quit()
