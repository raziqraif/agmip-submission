import logging
from pathlib import Path
import sys

import pytest
from selenium import webdriver
import selenium
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

# Add project directory to PATH so system can find scripts/ pkg
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils import CSS
from scripts.utils import Notification
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


class presence_of_class_name:
    """Class to emulate a callback in Selenium's expected_conditions"""

    def __init__(self, locator: tuple, class_name: str):
        self.locator = locator
        self.class_name = class_name

    def __call__(self, driver: WebDriver):
        try:
            element: WebElement = driver.find_element(*self.locator)
            class_names: str = element.get_attribute("class")  # html attribute 'class'
            return self.class_name in class_names
        except:
            return False


class TestFileUploadSuite:
    def setup_method(self, method):
        # Note: With the current CI environment, chrome needs to be in headless mode before pushing to github
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1440, 1440")
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)  # Set explicit wait time to X seconds
        self.driver.implicitly_wait(15)  # Set implicit wait time to X seconds
        self.driver.get(nb_url())
        self._run_notebook()

    def teardown_method(self, method):
        self.driver.quit()

    def _run_notebook(self):
        """Run our Jupyter notebook"""
        # Clear output and run all cells
        self.driver.find_element_by_id("kernellink").click()
        self.driver.find_element_by_link_text("Restart & Run All").click()
        try:
            confirmation_button_locator = (By.CLASS_NAME, "btn-danger")
            self.wait.until(expected_conditions.visibility_of_element_located(confirmation_button_locator))
            self.driver.find_element(*confirmation_button_locator).click()
        except (NoSuchElementException, TimeoutException) as e:
            logger = logging.getLogger()
            logger.error(str(e), exc_info=True)

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
        self.driver.find_element_by_class_name(CSS.UA__FILE_UPLOADER).send_keys(sample_file_spath)
        # Wait until file name snackbar IS visible
        filename_snackbar_locator = (By.CLASS_NAME, CSS.FILENAME_SNACKBAR)
        self.wait.until(expected_conditions.visibility_of_element_located(filename_snackbar_locator))
        # Make sure that file name is showing correctly on the page
        snackbar_label_locator = (
            By.XPATH,
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div[1]/div[1]/div[3]/div[2]/div'
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
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div[1]/div[1]/div[3]/div[2]/button'
        )
        remove_file_button.click()
        self._test_snackbar_invisible()
        self._test_valid_upload(sample_file_spath)

    def test_2(self, invalid_file_ext_spath: str) -> None:
        """Test case: upload file with invalid extension > click next"""
        # Upload file
        self.driver.find_element_by_class_name(CSS.UA__FILE_UPLOADER).send_keys(invalid_file_ext_spath)
        self._test_notification_appear_correctly(Notification.INVALID_FILE_FORMAT)
        next_button: WebElement = self.driver.find_element_by_xpath(
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div/div[2]/button'
        )
        next_button.click()
        self._test_notification_appear_correctly(Notification.PLEASE_UPLOAD)
        # Verify that we're still on the file upload page
        download_button: WebElement = self.driver.find_element_by_xpath(
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div[1]/div[1]/div[1]/div[2]/div/a'
        )
        assert download_button.is_displayed()

    def test_3(self, sample_file_spath: str) -> None:
        """Test case: upload > next"""
        self._test_valid_upload(sample_file_spath)
        first_project_option: WebElement = self.driver.find_element_by_xpath(
            '/html/body/div[4]/div/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div[1]/div[1]/div[5]/select/option'
        )
        first_project_option.click()
        next_button: WebElement = self.driver.find_element_by_xpath(
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[2]/div[1]/div[2]/button'
        )
        next_button.click()
        # Check if we switched page
        self.wait.until(expected_conditions.invisibility_of_element((By.CLASS_NAME, CSS.UA__BACKGROUND)))
        # Check if stepper element changes color appropriately
        page_1_stepper_element = (
            By.XPATH,
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[1]/div[1]'
        )
        page_2_stepper_element = (
            By.XPATH,
            '//*[@id="notebook-container"]/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[3]/div[1]/div[2]',
        )
        self.wait.until(presence_of_class_name(page_1_stepper_element, CSS.STEPPER_EL__ACTIVE))
        self.wait.until(presence_of_class_name(page_2_stepper_element, CSS.STEPPER_EL__CURRENT))
