import logging
from playwright.sync_api import Page, expect
from pages.product_page import ProductPage

logger = logging.getLogger(__name__)

def test_three_bundle_buttons_on_specific_page(page: Page):
    """
    Sprawdza, czy na stronie konkretnego produktu są dokładnie 3 przyciski 'Dodaj zestaw do koszyka'.
    """
    url = "https://idream.pl/iphone/apple-iphone-16/apple-iphone-16-128gb-bialy.html"
    logger.info(f"Test weryfikacji 3 przycisków na stronie: {url}")
    
    product_page = ProductPage(page)

    # 1. Przejdź na stronę i obsłuż popupy
    product_page.open_specific_product_and_handle_popups(url)

    # 2. Upewniamy się, że strona została załadowana (zwykle domcontentloaded jest bezpieczniejsze niż networkidle)
    page.wait_for_load_state("domcontentloaded", timeout=30000)

    # 3. Przewijanie dla wywołania lazy-loadingu (kilkuetapowe, aby załadować wszystkie zestawy)
    page.evaluate("window.scrollTo(0, 500)")
    page.wait_for_timeout(1000)
    page.evaluate("window.scrollTo(0, 1500)")
    page.wait_for_timeout(1000)
    page.evaluate("window.scrollTo(0, 2500)")
    page.wait_for_timeout(1000)

    # 4. Szukamy przycisków
    # Możemy szukać po tekście lub po klasie (jak w istniejących testach)
    # Zakładając klasę wziętą z test_pdp_bundle_offer.py
    bundle_add_btn_locator = page.locator("div.cm-ab__bt-submit:has-text('Dodaj zestaw do koszyka')")
    
    # 5. Asercja: ilość elementów to dokładnie 3
    logger.info("Sprawdzam ilość przycisków 'Dodaj zestaw do koszyka'...")
    expect(bundle_add_btn_locator).to_have_count(3, timeout=10000)

    logger.info("✅ Znaleziono dokładnie 3 przyciski 'Dodaj zestaw do koszyka' na stronie")
