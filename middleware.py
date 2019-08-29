import logging

from scrapy import signals
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# rewrite import path here
from lzz.utils.selenium import SeleniumRequest

logger = logging.getLogger(__name__)


class SeleniumDownloadMiddleWare(object):
    """
    For selenium & chrome driver
    
    @driver_path
        driver's path settings

    注意：
        缓存cookies需要浏览器User-Agent请求头版本与设置脚本(或Request)中的默认请求头保持一致
        否则某些网站可能会对此做验证 导致cookies无效
    """
    WAIT_CONDITION_MAP = {
        'id': By.ID,
        'class_name': By.CLASS_NAME,
        'xpath': By.XPATH,
        'css': By.CSS_SELECTOR,
        'tag': By.TAG_NAME
    }

    def __init__(self, driver_path, headless):
        if headless:
            options = webdriver.ChromeOptions()
            options.headless = headless
        else:
            options = None
        self._options = options
        self._driver_path = driver_path
        self._driver = None
        self._cached_cookies = {}

    @property
    def driver(self):
        if self._driver is None:
            self._driver = webdriver.Chrome(executable_path=self._driver_path, options=self._options)
        return self._driver

    @classmethod
    def from_crawler(cls, crawler):
        driver_path = crawler.settings['SELENIUM_DRIVER_PATH']
        headless = crawler.settings.getbool('SELENIUM_HEADLESS', True)

        dm = cls(driver_path, headless)
        crawler.signals.connect(dm.closed, signal=signals.spider_closed)

        return dm

    def check_cached_cookies(self, request):
        for domain, cookies in self._cached_cookies.items():
            if domain in request.url:
                return cookies

    def process_request(self, request, spider):
        if not isinstance(request, SeleniumRequest):
            return

        if request.just_cookies:
            cookies = self.check_cached_cookies(request)
            if cookies:
                request.cookies = cookies
                return

        self.driver.get(request.url)

        if request.wait_until:
            for k, v in request.wait_until.items():
                k = self.WAIT_CONDITION_MAP.get(k)
                if not k:
                    logger.warning('Ignored an unexpected wait condition {}'.format(k))
                    continue
                condition = EC.presence_of_element_located((k, v))
                WebDriverWait(self.driver, request.wait_time).until(
                    condition
                )

        if request.script:
            # execute javascript code and save the result to meta
            result = self.driver.execute_script(request.script)
            if result is not None:
                request.meta['js_result'] = result

        for cookie_name, cookie_value in request.cookies.items():
            self.driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': cookie_value
                }
            )
        request.cookies = self.driver.get_cookies()
        request.meta['browser'] = self.driver

        if request.just_cookies:
            domain = request.url.split('://')[1].split('/')[0]
            self._cached_cookies[domain] = request.cookies
        else:
            body = str.encode(self.driver.page_source)
            return HtmlResponse(
                self.driver.current_url,
                body=body,
                encoding='utf-8',
                request=request
            )

    def closed(self):
        if not self._driver is None:
            self._driver.close()
            logger.debug('Selenium closed')
