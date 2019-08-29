import scrapy


class SeleniumRequest(scrapy.Request):
    """
    @wait_until:
        see specify condition in selenium download middleware

    @just_cookies:
        browser just set cookies to request
        not return the page
    """

    def __init__(self, url, callback=None, wait_until=None, wait_time=10, script=None, just_cookies=False, **kwargs):
        self.wait_until = wait_until
        self.script = script
        self.wait_time = wait_time
        self.just_cookies = just_cookies
        super().__init__(url, callback, **kwargs)
