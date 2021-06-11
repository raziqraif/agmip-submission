from pathlib import Path
import sys

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

# Add project directory to PATH so system can find scripts/ pkg
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.view import CSS
from scripts.view import Notification
from .test_nbserver import nb_url


INPUT_DIRPATH = Path(__file__).parent / "input"  # <TESTS_DIR>/input/


@pytest.fixture
def sample_file_spath() -> str:
    """Return the str path to the sampe file"""
    return str(INPUT_DIRPATH / Path("SampleData.csv"))


@pytest.fixture
def invalid_file_ext_spath() -> str:
    """Return str path to a file with an invalid extension"""
    return str(INPUT_DIRPATH / Path("InvalidExtension.wxyz"))


class TestFileUploadSuite:
    def setup_method(self, method):
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)  # Set explicit wait time to 10 seconds
        self.driver.implicitly_wait(10)  # Set implicit wait time to 10 seconds
        self.driver.get(nb_url())
        self._run_notebook()

    def teardown_method(self, method):
        self.driver.quit()

    def _run_notebook(self):
        """Run our Jupyter notebook"""
        # Clear output and run all cells
        self.driver.find_element_by_id("kernellink").click()
        self.driver.find_element_by_link_text("Restart & Run All").click()
        self.driver.find_element_by_class_name("btn-danger").click()

    def _test_notification_appear_correctly(self, content: str):
        """Test case: <no action>"""
        notification_locator = (By.CLASS_NAME, CSS.NOTIFICATION)
        self.wait.until(expected_conditions.visibility_of_element_located(notification_locator))
        notification_label_locator = (
            By.XPATH,
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[1]/div[2]',
        )
        self.wait.until(expected_conditions.text_to_be_present_in_element(notification_label_locator, content))

    def _test_click_removes_notification(self):
        """Test case: random click"""
        app: WebElement = self.driver.find_element_by_class_name(CSS.APP)
        app.click()
        notification_locator = (By.CLASS_NAME, CSS.NOTIFICATION)
        short_wait = WebDriverWait(self.driver, 1)
        short_wait.until(expected_conditions.invisibility_of_element(notification_locator))

    def _test_snackbar_invisible(self):
        """Test case: <no action>"""
        filename_snackbar_locator = (By.CLASS_NAME, CSS.FILENAME_SNACKBAR)
        self.wait.until(expected_conditions.invisibility_of_element_located(filename_snackbar_locator))

    def _test_valid_upload(self, sample_file_spath: str):
        """Test case: upload"""
        # Upload a file
        self.driver.find_element_by_class_name(CSS.UA_FILE_UPLOADER).send_keys(sample_file_spath)
        # Wait until file name snackbar IS visible
        filename_snackbar_locator = (By.CLASS_NAME, CSS.FILENAME_SNACKBAR)
        self.wait.until(expected_conditions.visibility_of_element_located(filename_snackbar_locator))
        # Make sure that file name is showing correctly on the page
        snackbar_label_locator = (
            By.XPATH,
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div/div[1]/div[3]/div[2]/div[2]/div',
        )
        self.wait.until(
            expected_conditions.text_to_be_present_in_element(snackbar_label_locator, Path(sample_file_spath).name)
        )
        # Make sure that notification text is showing correctly
        self._test_notification_appear_correctly(Notification.FILE_UPLOAD_SUCCESS)

    def test_1(self, sample_file_spath: str) -> None:
        """Test case: upload > upload > remove > upload"""
        self._test_snackbar_invisible()
        self._test_valid_upload(sample_file_spath)
        self._test_click_removes_notification()
        self._test_valid_upload(sample_file_spath)
        self._test_click_removes_notification()
        remove_file_button: WebElement = self.driver.find_element_by_xpath(
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div/div[1]/div[3]/div[2]/div[2]/button'
        )
        remove_file_button.click()
        self._test_snackbar_invisible()
        self._test_valid_upload(sample_file_spath)

    def test_2(self, invalid_file_ext_spath: str) -> None:
        """Test case: upload file with invalid extension > click next"""
        # Upload file
        self.driver.find_element_by_class_name(CSS.UA_FILE_UPLOADER).send_keys(invalid_file_ext_spath)
        self._test_notification_appear_correctly(Notification.INVALID_FILE_FORMAT)
        next_button: WebElement = self.driver.find_element_by_xpath(
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div/div[2]/button'
        )
        next_button.click()
        self._test_notification_appear_correctly(Notification.PLEASE_UPLOAD)
        # Verify that we're still on the file upload page
        download_button: WebElement = self.driver.find_element_by_link_text("Download")
        assert download_button.is_displayed()
