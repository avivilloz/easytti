import os
import logging
import retry
from time import time, sleep
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .exceptions import *

LOG = logging.getLogger(__name__)


def elements_are_present(driver, by, value):
    elements = driver.find_elements(by, value)
    if elements:
        return elements
    else:
        return False


def create_chrome_options(download_directory):
    chrome_options = Options()
    chrome_prefs = {
        "download.default_directory": download_directory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    return chrome_options


def generate_images(
    dst_dir: str, image_description: str, bing_email: str, bing_password: str
):
    """
    Generates up to 4 images
    """
    os.makedirs(dst_dir, exist_ok=True)

    chrome_options = create_chrome_options(dst_dir)
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    driver.get("https://login.live.com/")

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "loginfmt")))
    email_input.send_keys(bing_email)
    email_input.send_keys(Keys.RETURN)

    password_input = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))
    password_input.send_keys(bing_password)
    password_input.send_keys(Keys.RETURN)

    driver.get("https://www.bing.com/images/create")

    is_ready = False
    while not is_ready:
        LOG.info(f"Generate Image Prompt: {image_description}")

        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        search_box.clear()
        search_box.send_keys(image_description)

        create_button = wait.until(EC.element_to_be_clickable((By.ID, "create_btn_c")))
        create_button.click()

        try:
            button = wait.until(EC.element_to_be_clickable((By.ID, "acceptButton")))
            button.click()
        except TimeoutException:
            pass

        elements = None
        start = time()
        attempts = 0

        while not elements:
            sleep(5)

            if elements := elements_are_present(
                driver, By.CSS_SELECTOR, "a.iusc, a.single-img-link"
            ):
                is_ready = True
            elif elements := elements_are_present(
                driver, By.CSS_SELECTOR, "div.gil_err_mt"
            ):
                reason = elements[0].text
                LOG.error(f"Error: {reason}")
                if reason == "You can't submit any more prompts":
                    raise NoMorePrompts
                elif reason == "Unsafe image content detected":
                    raise UnsafeImageContent
                elif reason == "Content warning":
                    raise ContentWarning

            if not elements and ((time.time() - start) >= 60):
                if attempts == 0:
                    driver.refresh()
                    attempts += 1
                else:
                    elements = True
                start = time()

    # elements = driver.find_elements(by, value)

    total_images = len(elements)
    hrefs = []
    original_window = driver.current_window_handle
    for element in elements:
        href = None
        try:
            href = wait.until(lambda d: element.get_attribute("href"))
            time.sleep(5)
            href = element.get_attribute("href")

            original_handles = driver.window_handles
            driver.execute_script(f"window.open('{href}', '_blank');")
            wait.until(EC.new_window_is_opened(original_handles))
            time.sleep(5)
            driver.switch_to.window(driver.window_handles[-1])

            download_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.action.dld.nofocus"))
            )
            download_button.click()
            time.sleep(5)

            driver.close()
            driver.switch_to.window(original_window)

        except Exception as e:
            total_images -= 1
            hrefs.append(href)
            LOG.error(f"Error processing href {href}: {e}")

    try:
        driver.quit()
    finally:
        if total_images == 0:
            raise Exception(f"Error processing hrefs: {hrefs}")


@retry(exceptions=Exception, tries=3, delay=2)
def download_images():
    total_images = len(elements)
    hrefs = []
    original_window = driver.current_window_handle
    for element in elements:
        href = None
        try:
            href = wait.until(lambda d: element.get_attribute("href"))
            time.sleep(5)
            href = element.get_attribute("href")

            original_handles = driver.window_handles
            driver.execute_script(f"window.open('{href}', '_blank');")
            wait.until(EC.new_window_is_opened(original_handles))
            time.sleep(5)
            driver.switch_to.window(driver.window_handles[-1])

            download_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.action.dld.nofocus"))
            )
            download_button.click()
            time.sleep(5)

            driver.close()
            driver.switch_to.window(original_window)

        except Exception as e:
            total_images -= 1
            hrefs.append(href)
            LOG.error(f"Error processing href {href}: {e}")
