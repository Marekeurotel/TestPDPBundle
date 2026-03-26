import logging
from playwright.sync_api import Page, Locator, expect

from .base_page import BasePage

logger = logging.getLogger(__name__)


class ProductPage(BasePage):
    # Możesz zdefiniować URL dla konkretnego produktu lub przyjmować go w metodzie
    URL = "https://idream.pl/ipad/apple-ipad-11-wi-fi-128gb-11-gen-niebieski.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self._init_locators()

    def _init_locators(self):
        self.add_to_cart_button_locator = self.page.locator("button:has-text('Do koszyka')").first
        self.continue_shopping_button_locator = self.page.locator(
            "a.ty-btn.ty-btn__secondary.cm-notification-close:has-text('Kontynuuj zakupy')"
        ).first

        # Selektory dla szczegółów produktu
        self.product_name_locator = self.page.locator("h1").first
        self.product_price_locator = self.page.locator(".ty-price-num")
        self.price_element: Locator = self.page.locator(".ty-price-num").first
        self.description_accordion: Locator = self.page.locator(
            ".idr-accordion-title", has_text="Skrócony opis"
        )
        self.specification_tab: Locator = self.page.locator(".ty-tabs__a", has_text="Dane techniczne")

    def open_specific_product(self, product_url: str):
        self.page.goto(product_url)

    def open_specific_product_and_handle_popups(self, product_url: str):
        """Otwiera konkretną stronę produktu i obsługuje początkowe popupy."""
        logger.info(f"Otwieranie strony produktu: {product_url}")
        self.page.goto(product_url, wait_until="domcontentloaded", timeout=45000)

        # KROK 1: Obsługa cookies
        cookie_btn = self.page.get_by_role("button", name="Zezwól na wszystkie")
        if cookie_btn.is_visible(timeout=5000):
            try:
                cookie_btn.click()
                logger.info("✅ Cookies zaakceptowane.")
            except Exception:
                logger.warning("Nie udało się kliknąć cookies.")

        # KROK 2: Obsługa bhr popup
        try:
            popup_container = self.page.locator("div.bhr-board__canvas.type--POPUP")
            if popup_container.is_visible(timeout=5000):
                close_button = self.page.get_by_title("Kliknij tutaj!")
                close_button.click()
                logger.info("✅ 'bhr' popup zamknięty.")
        except Exception as e:
            logger.error(f"Błąd podczas zamykania bhr popup: {e}")

    def add_product_to_cart(self):
        logger.info("Attempting to add product to cart.")
        expect(self.add_to_cart_button_locator).to_be_visible(timeout=10000)
        expect(self.add_to_cart_button_locator).to_be_enabled(timeout=5000)
        self.add_to_cart_button_locator.click()
        logger.info("Clicked 'Do koszyka' button.")
        self.page.wait_for_timeout(2000)
        expect(self.continue_shopping_button_locator).to_be_visible(timeout=10000)
        expect(self.continue_shopping_button_locator).to_be_enabled(timeout=5000)
        self.continue_shopping_button_locator.click()
        self.page.wait_for_timeout(1000)
        logger.info("Clicked 'Kontynuuj zakupy' button.")

    def get_product_name(self) -> str:
        return self.product_name_locator.inner_text().strip()

    def get_product_price(self) -> str:
        expect(self.product_price_locator).to_be_visible()
        return self.product_price_locator.inner_text().strip()

    def open_product_page(self):
        """Otwiera stronę produktu i obsługuje początkowe popupy."""
        self.page.goto(self.URL)
        self.open_page_and_handle_initial_popups()
        logger.info("Product page opened and initial popups handled.")

    def verify_product_details_displayed(self):
        """Sprawdza, czy kluczowe szczegóły produktu są widoczne i nie są puste."""
        logger.info("Verifying product details are displayed...")

        expect(self.price_element).to_be_visible()
        expect(self.description_accordion).to_be_visible()
        expect(self.specification_tab).to_be_visible()

        expect(self.price_element).not_to_have_text("")
        expect(self.description_accordion).not_to_have_text("")
        expect(self.specification_tab).not_to_have_text("")

        logger.info("✅ All key product details are visible and have content.")

