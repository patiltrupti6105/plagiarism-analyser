"""
Stable Selenium Tests (Error-Free Version)
Run: pytest test_selenium.py -v
"""

import os
import sys
import time
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Selenium imports ──────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


BASE_URL = os.environ.get("APP_URL", "http://localhost:5000")

pytestmark = pytest.mark.skipif(
    not SELENIUM_AVAILABLE,
    reason="selenium not installed"
)


# ───────────────── Helpers ─────────────────

def make_txt_file(content: str):
    f = tempfile.NamedTemporaryFile(
        suffix=".txt", mode="w", encoding="utf-8", delete=False
    )
    f.write(content)
    f.close()
    return f.name


SOURCE_CONTENT = "This is a test document for plagiarism detection."
REFERENCE_CONTENT = "This is another test document for comparison."


# ───────────────── Driver ─────────────────

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1400,900")

    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=options)
    drv.implicitly_wait(5)
    yield drv
    drv.quit()


# ───────────────── Tests ─────────────────

class TestPageLoad:

    def test_page_loads(self, driver):
        driver.get(BASE_URL)
        title = driver.title.lower()
        assert "plagiarism" in title or "plagiaguard" in title

    def test_upload_section_present(self, driver):
        driver.get(BASE_URL)
        assert driver.find_element(By.ID, "sourceInput")
        assert driver.find_element(By.ID, "refInput")

    def test_analyze_button_present(self, driver):
        driver.get(BASE_URL)
        btn = driver.find_element(By.ID, "analyzeBtn")
        assert btn is not None

    def test_analyze_button_disabled_initially(self, driver):
        driver.get(BASE_URL)
        btn = driver.find_element(By.ID, "analyzeBtn")
        assert btn.get_attribute("disabled") is not None


class TestFileUpload:

    def test_upload_enables_button(self, driver):
        driver.get(BASE_URL)

        src = make_txt_file(SOURCE_CONTENT)
        ref = make_txt_file(REFERENCE_CONTENT)

        try:
            driver.find_element(By.ID, "sourceInput").send_keys(src)
            time.sleep(0.5)

            driver.find_element(By.ID, "refInput").send_keys(ref)
            time.sleep(0.5)

            btn = driver.find_element(By.ID, "analyzeBtn")
            assert btn.get_attribute("disabled") is None

        finally:
            os.unlink(src)
            os.unlink(ref)

    def test_source_preview_visible(self, driver):
        driver.get(BASE_URL)

        src = make_txt_file(SOURCE_CONTENT)

        try:
            driver.find_element(By.ID, "sourceInput").send_keys(src)
            time.sleep(0.5)

            preview = driver.find_element(By.ID, "sourcePreview")
            assert preview.is_displayed()

        finally:
            os.unlink(src)

    def test_reference_list_updates(self, driver):
        driver.get(BASE_URL)

        ref = make_txt_file(REFERENCE_CONTENT)

        try:
            driver.find_element(By.ID, "refInput").send_keys(ref)
            time.sleep(0.5)

            items = driver.find_elements(By.CLASS_NAME, "ref-preview-item")
            assert len(items) >= 1

        finally:
            os.unlink(ref)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])