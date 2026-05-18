from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

_DEFAULT_WAIT = 20


class E2EBaseTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        cls.driver = webdriver.Chrome(options=opts)
        cls.driver.implicitly_wait(_DEFAULT_WAIT)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def wait(self, timeout=_DEFAULT_WAIT):
        return WebDriverWait(self.driver, timeout)

    def create_user(self, username="testuser", password="testpass123"):
        return User.objects.create_user(username=username, password=password)

    def login_via_ui(self, username="testuser", password="testpass123"):
        self.driver.get(f"{self.live_server_url}/accounts/login/")
        self.wait().until(EC.presence_of_element_located((By.ID, "id_username")))
        self.driver.find_element(By.ID, "id_username").clear()
        self.driver.find_element(By.ID, "id_username").send_keys(username)
        self.driver.find_element(By.ID, "id_password").clear()
        self.driver.find_element(By.ID, "id_password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, ".btn-login").click()
        login_url = f"{self.live_server_url}/accounts/login/"
        self.wait(timeout=40).until(EC.url_changes(login_url))
        self.wait(timeout=20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def goto(self, reverse_name, **kwargs):
        url = self.live_server_url + reverse(reverse_name, **kwargs)
        self.driver.get(url)
        return url
