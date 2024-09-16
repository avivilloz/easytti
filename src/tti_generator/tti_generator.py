import os
import logging
from functools import wraps
from retry import retry
from time import time, sleep
from typing import Tuple, List, Optional
from contextlib import contextmanager
from .exceptions import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

LOG = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2
RETRY_BACKOFF = 2
DEFAULT_TIMEOUT = 10


@contextmanager
def managed_driver(options: Options):
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()


def validate_input(func):
    @wraps(func)
    def wrapper(
        dst_dir: str,
        image_description: str,
        bing_email: str,
        bing_password: str,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        if not dst_dir or not os.path.isdir(dst_dir):
            raise ValueError("Invalid destination directory")
        if not image_description:
            raise ValueError("Image description cannot be empty")
        if not bing_email or not bing_password:
            raise ValueError("Bing credentials cannot be empty")
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        return func(dst_dir, image_description, bing_email, bing_password, timeout)

    return wrapper


def create_chrome_options(download_dir: str) -> Options:
    LOG.info(f"Creating Chrome options for download directory: {download_dir}")
    chrome_options = Options()
    chrome_prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    return chrome_options


def elements_are_present(
    driver: webdriver.Chrome, by: str, value: str
) -> Optional[List[webdriver.remote.webelement.WebElement]]:
    elements = driver.find_elements(by, value)
    return elements if elements else None


@validate_input
def generate_images(
    download_dir: str,
    image_description: str,
    bing_email: str,
    bing_password: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Tuple[int, int]:
    """
    Generates up to 4 images
    """
    LOG.info(f"Starting image generation for prompt: '{image_description}'")

    chrome_options = create_chrome_options(download_dir)

    with managed_driver(chrome_options) as driver:
        wait = WebDriverWait(driver, timeout)
        login_to_bing(driver, wait, bing_email, bing_password)
        navigate_to_image_creation(driver)
        generate_and_wait_for_images(driver, wait, image_description)
        result = download_images(driver, wait, download_dir)
        LOG.info(f"Image generation complete for prompt: '{image_description}'")
        return result


def login_to_bing(
    driver: webdriver.Chrome, wait: WebDriverWait, email: str, password: str
) -> None:
    LOG.info("Navigating to Bing login page.")
    driver.get("https://login.live.com/")

    LOG.info("Entering email address.")
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "loginfmt")))
    email_input.send_keys(email)
    email_input.send_keys(Keys.RETURN)

    LOG.info("Entering password.")
    password_input = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)

    LOG.info("Successfully logged in to Bing.")


def navigate_to_image_creation(driver: webdriver.Chrome) -> None:
    LOG.info("Navigating to Bing image creation page.")
    driver.get("https://www.bing.com/images/create")


@retry(
    exceptions=ImageGenerationError,
    tries=MAX_RETRIES,
    delay=RETRY_DELAY,
    backoff=RETRY_BACKOFF,
    logger=LOG,
)
def generate_and_wait_for_images(
    driver: webdriver.Chrome, wait: WebDriverWait, image_description: str
) -> None:
    LOG.info(f"Generate Image Prompt: {image_description}")

    search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
    search_box.clear()
    search_box.send_keys(image_description)

    LOG.info("Clicking on the create button to generate images.")
    create_button = wait.until(EC.element_to_be_clickable((By.ID, "create_btn_c")))
    create_button.click()

    try:
        button = wait.until(EC.element_to_be_clickable((By.ID, "acceptButton")))
        LOG.info("Clicked on the accept button.")
        button.click()
    except TimeoutException:
        LOG.info("No accept button found, proceeding without it.")

    start_time = time()
    attempts = 0
    while True:
        LOG.info("Waiting for images to generate...")
        sleep(5)

        if elements := elements_are_present(
            driver, By.CSS_SELECTOR, "a.iusc, a.single-img-link"
        ):
            LOG.info("Images are ready for download.")
            break
        elif elements := elements_are_present(
            driver, By.CSS_SELECTOR, "div.gil_err_mt"
        ):
            reason = elements[0].text
            LOG.error(f"Error: {reason}")
            if reason == "You can't submit any more prompts":
                raise NoMorePrompts(reason)
            elif reason == "Unsafe image content detected":
                raise UnsafeImageContent(reason)
            elif reason == "Content warning":
                raise ContentWarning(reason)
            elif reason == "This prompt is being reviewed":
                raise ReviewRequired(reason)
            elif reason == "We're sorry — we've run into an issue.":
                handle_panda(driver=driver, wait=wait)


        if (time() - start_time) >= 60:
            if attempts == 0:
                LOG.info("Refreshing the page due to timeout.")
                driver.refresh()
                attempts += 1
                start_time = time()
            else:
                LOG.error("Failed to generate images after multiple attempts.")
                raise ImageGenerationError(
                    "Failed to generate images after multiple attempts"
                )


@retry(
    (ElementError, StaleElementReferenceException, TimeoutException),
    tries=MAX_RETRIES,
    delay=RETRY_DELAY,
    backoff=RETRY_BACKOFF,
    logger=LOG,
)
def get_href_with_retry(element, wait):
    LOG.info("Attempting to get href attribute.")
    href = wait.until(lambda d: element.get_attribute("href"))
    if not href:
        LOG.warning("Failed to get href attribute. Raising ElementError.")
        raise ElementError("Failed to get href")
    LOG.info(f"Successfully retrieved href: {href}")
    return href


def wait_for_download(
    download_dir: str, initial_file_count: int, timeout: int = 30
) -> bool:
    LOG.info(f"Waiting for file to download in {download_dir}")
    start_time = time()
    while time() - start_time < timeout:
        current_file_count = len(os.listdir(download_dir))
        if current_file_count > initial_file_count:
            LOG.info("New file detected in download directory")
            return True
        sleep(0.5)
    LOG.warning(f"Download timeout after {timeout} seconds")
    return False


@retry(
    (ElementError, TimeoutException, NoSuchElementException),
    tries=MAX_RETRIES,
    delay=RETRY_DELAY,
    backoff=RETRY_BACKOFF,
    logger=LOG,
)
def download_images(driver: webdriver.Chrome, wait: WebDriverWait, download_dir: str):
    elements = driver.find_elements(By.CSS_SELECTOR, "a.iusc, a.single-img-link")
    total_images = len(elements)
    successful_downloads = 0
    original_window = driver.current_window_handle

    LOG.info(f"Starting download process for {total_images} images.")

    for index, element in enumerate(elements, 1):
        try:
            href = get_href_with_retry(element, wait)
            LOG.info(f"Processing image {index}/{total_images}: {href}")

            driver.execute_script("window.open();")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(href)

            download_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.action.dld.nofocus"))
            )

            initial_file_count = len(os.listdir(download_dir))

            download_button.click()
            LOG.info(f"Clicked download button for image {index}/{total_images}")

            if wait_for_download(download_dir, initial_file_count):
                successful_downloads += 1
                LOG.info(f"Successfully downloaded image {index}/{total_images}")
            else:
                LOG.warning(
                    f"Download may have failed for image {index}/{total_images}"
                )

        except (ElementError, TimeoutException, NoSuchElementException) as e:
            error_type = type(e).__name__
            LOG.error(
                f"{error_type} while processing image {index}/{total_images}: {e}",
                exc_info=True,
            )
            raise
        finally:
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(original_window)

    LOG.info(
        f"Download complete. Successfully downloaded {successful_downloads}/{total_images} images."
    )

    return successful_downloads, total_images


def handle_panda(driver: webdriver.Chrome, wait: WebDriverWait):
    original_tab = driver.current_window_handle

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get("https://www.bing.com/account/general")

    element = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "a[href*='setlang=en'][h='ID=SERP,5024.1']")
        )
    )
    element.click()

    driver.close()

    driver.switch_to.window(original_tab)

    driver.refresh()
