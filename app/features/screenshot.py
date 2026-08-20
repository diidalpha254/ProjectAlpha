"""
Screenshot Module
Captures screenshots of the dashboard for reporting.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import io
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image

from core.logger import get_logger


logger = get_logger(__name__)


class ScreenshotCapture:
    """
    Captures screenshots of the dashboard.
    Supports full-page and component captures.
    """
    
    def __init__(self):
        """Initialize the screenshot capture."""
        self._driver: Optional[webdriver.Chrome] = None
        self._initialized = False
        logger.info("ScreenshotCapture initialized")
    
    def _initialize_driver(self):
        """Initialize the WebDriver for screenshot capture."""
        if self._initialized:
            return
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            self._driver = webdriver.Chrome(options=options)
            self._initialized = True
            logger.info("WebDriver initialized")
            
        except Exception as e:
            logger.error(f"Error initializing WebDriver: {e}")
            self._initialized = False
    
    def capture_page(self, url: str, output_path: Optional[str] = None) -> Optional[bytes]:
        """
        Capture screenshot of a page.
        
        Args:
            url: URL to capture
            output_path: Optional output file path
            
        Returns:
            Optional[bytes]: Screenshot data
        """
        try:
            self._initialize_driver()
            if not self._initialized:
                return None
            
            self._driver.get(url)
            
            # Wait for page to load
            self._driver.implicitly_wait(5)
            
            # Capture screenshot
            screenshot = self._driver.get_screenshot_as_png()
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(screenshot)
            
            logger.info(f"Page screenshot captured from {url}")
            return screenshot
            
        except Exception as e:
            logger.error(f"Error capturing page screenshot: {e}")
            return None
    
    def capture_element(self, element_selector: str, url: str) -> Optional[bytes]:
        """
        Capture screenshot of a specific element.
        
        Args:
            element_selector: CSS selector for the element
            url: URL to load
            
        Returns:
            Optional[bytes]: Screenshot data
        """
        try:
            self._initialize_driver()
            if not self._initialized:
                return None
            
            self._driver.get(url)
            self._driver.implicitly_wait(5)
            
            # Find element
            element = self._driver.find_element_by_css_selector(element_selector)
            
            # Capture element screenshot
            screenshot = element.screenshot_as_png
            
            logger.info(f"Element screenshot captured: {element_selector}")
            return screenshot
            
        except Exception as e:
            logger.error(f"Error capturing element screenshot: {e}")
            return None
    
    def capture_streamlit_dashboard(self, streamlit_url: str = "http://localhost:8501") -> Optional[bytes]:
        """
        Capture screenshot of the Streamlit dashboard.
        
        Args:
            streamlit_url: URL of the Streamlit app
            
        Returns:
            Optional[bytes]: Screenshot data
        """
        return self.capture_page(streamlit_url)
    
    def save_screenshot(self, screenshot_data: bytes, filename: Optional[str] = None) -> str:
        """
        Save screenshot data to file.
        
        Args:
            screenshot_data: Screenshot bytes
            filename: Optional filename
            
        Returns:
            str: Saved filename
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{timestamp}.png"
        
        with open(filename, 'wb') as f:
            f.write(screenshot_data)
        
        logger.info(f"Screenshot saved to {filename}")
        return filename
    
    def screenshot_to_base64(self, screenshot_data: bytes) -> str:
        """
        Convert screenshot to base64 string.
        
        Args:
            screenshot_data: Screenshot bytes
            
        Returns:
            str: Base64 encoded string
        """
        return base64.b64encode(screenshot_data).decode('utf-8')
    
    def close(self):
        """Close the WebDriver."""
        if self._driver:
            self._driver.quit()
            self._driver = None
            self._initialized = False
            logger.info("WebDriver closed")
