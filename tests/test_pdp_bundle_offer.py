import logging

import pytest
from playwright.sync_api import Page, expect

from pages.product_page import ProductPage

logger = logging.getLogger(__name__)


# Parametryzacja testu dla 3 różnych stron PDP (tu można dodawać kolejne URL-e).
PRODUCT_URLS = [
    "https://idream.pl/iphone/apple-iphone-15/apple-iphone-15-128gb-niebieski.html",
    "https://idream.pl/iphone/apple-iphone-15/apple-iphone-15-128gb-niebieski.html",
    "https://idream.pl/ipad/ipad-air/apple-ipad-air-13-m2-128gb-wi-fi-cellular-6.gen-gwiezdna-szarosc-2024.html",
    "https://idream.pl/apple-watch/apple-watch-ultra-2/apple-watch-ultra-2-gps-cellular-49mm-tytan-naturalny-z-bransoleta-mediolanska-w-kolorze-naturalnym-s.html",
    "https://idream.pl/iphone/apple-iphone-16/apple-iphone-16-128gb-bialy.html",
    "https://idream.pl/ipad/ipad-air/apple-ipad-air-11-m3-256gb-wi-fi-7-gen-gwiezdna-szarosc-2025.html",
]


@pytest.mark.parametrize("product_url", PRODUCT_URLS)
def test_pdp_bundle_offer_presence(page: Page, product_url: str):
    """
    TC_PDP_BUNDLE_001: Sprawdza obecność oferty zestawu na stronie PDP produktu.
    Weryfikuje:
      1. Widoczność kontenera zestawu (div.ab__bt_box)
      2. Widoczność i klikalność przycisku "Dodaj zestaw do koszyka"
    Test UPADA jeśli sekcja zestawu nie istnieje na stronie.
    """
    logger.info(f"Test PDP Bundle dla URL: {product_url}")
    product_page = ProductPage(page)

    # 1. Przejdź na stronę i obsłuż popupy (cookies, BHR itp.)
    product_page.open_specific_product_and_handle_popups(product_url)

    # 2. Upewniamy się, że strona została w całości załadowana
    page.wait_for_load_state("networkidle", timeout=30000)

    # 3. Lekkie przewinięcie, żeby aktywować lazy-loading dla sekcji niżej na stronie.
    page.evaluate("window.scrollTo(0, 1000)")
    page.wait_for_timeout(1000)

    # 4. Definicja lokatorów
    bundle_box_locator = page.locator("div.ab__bt_box")
    bundle_add_btn_locator = page.locator("div.cm-ab__bt-submit")

    # 5. Asercje
    logger.info("Sprawdzam widoczność sekcji ab__bt_box...")
    expect(bundle_box_locator).to_be_visible(timeout=10000)

    # Przewijamy do tej sekcji, żeby Playwright "widział" przycisk w widoku.
    bundle_box_locator.scroll_into_view_if_needed()

    logger.info("Sprawdzam obecność przycisku 'Dodaj zestaw do koszyka'...")
    expect(bundle_add_btn_locator).to_be_visible(timeout=5000)
    expect(bundle_add_btn_locator).to_be_enabled(timeout=5000)
    expect(bundle_add_btn_locator).to_contain_text("Dodaj zestaw do koszyka")

    logger.info(f"✅ Przycisk 'Dodaj zestaw do koszyka' widoczny i aktywny dla {product_url}")

