import logging
from playwright.sync_api import Page, expect, TimeoutError, Locator

logger = logging.getLogger(__name__)


class BasePage:
    URL = "https://idream.pl/"

    def __init__(self, page: Page):
        self.page = page
        self.page.set_viewport_size({"width": 1920, "height": 1080})

    def open_page_and_handle_initial_popups(self):
        """
        Finalna, odporna metoda, która obsługuje aktualny stan strony idream.pl
        (cookies + nowy popup 'bhr').
        """
        logger.info(f"Navigating to {self.URL}...")
        self.page.goto(self.URL, wait_until="domcontentloaded", timeout=45000)
        logger.info("Page navigation complete and network is idle.")

        # KROK 1: Obsługa cookies
        cookie_btn = self.page.get_by_role("button", name="Zezwól na wszystkie")

        if cookie_btn.is_visible(timeout=5000):
            try:
                cookie_btn.click()
                logger.info("✅ Cookie consent handled.")
            except Exception:
                # Na wypadek, gdyby kliknięcie zostało przerwane
                logger.warning("Cookie click failed, but element was visible.")
        else:
            # To jest oczekiwany stan, jeśli cookies zostały już zaakceptowane.
            logger.info("Cookie banner not visible. Assuming consent already given.")

        # KROK 2: Obsługa NOWEGO popupa 'bhr'
        try:
            popup_container = self.page.locator("div.bhr-board__canvas.type--POPUP")

            logger.info("Checking for the 'bhr' popup...")
            if popup_container.is_visible(timeout=10000):
                logger.info("'bhr' popup found. Attempting to close it.")

                # Używamy get_by_title - jest bardzo czytelny i niezawodny
                close_button = self.page.get_by_title("Kliknij tutaj!")
                expect(close_button).to_be_enabled(timeout=2000)
                close_button.click()

                # Weryfikujemy, czy popup zniknął po kliknięciu
                expect(popup_container).not_to_be_visible(timeout=5000)
                logger.info("✅ 'bhr' popup handled successfully.")
            else:
                logger.info("'bhr' popup did not appear within the timeout. Continuing...")

        except Exception as e:
            logger.error(f"An unexpected error occurred while handling the 'bhr' popup: {e}")
            # Robimy zrzut ekranu, żeby zobaczyć, co poszło nie tak
            self.page.screenshot(path="error_bhr_popup.png")

        logger.info("--- Page is clean and ready for testing. ---")

    def _close_known_overlays(self):
        """
        Prywatna metoda pomocnicza, która próbuje zamknąć wszystkie znane,
        potencjalnie blokujące nakładki. Działa cicho, jeśli ich nie znajdzie.
        """
        logger.info("Auto-healing: Checking for known overlays to close...")

        # Używamy selektorów, które zidentyfikowałeś
        bhr_div_overlay = self.page.locator("#bhr-items div").first
        bhr_iframe_overlay = self.page.frame_locator("#bhr-items iframe").locator("div").nth(3)
        salesmanago_iframe_button = self.page.frame_locator(
            'iframe[title="salesmanago-consent-form-title"]'
        ).get_by_role("button", {"name": "Nie"})

        # Nowy overlay zidentyfikowany w analizie Gemini
        gemini_identified_overlay = self.page.locator("#wes-77605808-07d1-43c9-bace-421e2a2ddec8")

        overlays_to_check = [
            (bhr_div_overlay, "BHR Div Overlay"),
            (bhr_iframe_overlay, "BHR IFrame Div Overlay"),
            (salesmanago_iframe_button, "Salesmanago Consent Button"),
            (gemini_identified_overlay, "Gemini Analysis Identified Overlay (#wes-...)"),
        ]

        for overlay_locator, name in overlays_to_check:
            try:
                # Sprawdzamy, czy element jest widoczny, z bardzo krótkim timeoutem
                if overlay_locator.is_visible(timeout=500):
                    logger.warning(f"Found active overlay: '{name}'. Attempting to click it.")
                    overlay_locator.click(timeout=2000)
                    # Czekamy na zniknięcie po kliknięciu
                    expect(overlay_locator).not_to_be_visible(timeout=3000)
                    logger.info(f"✅ Successfully closed overlay: '{name}'.")
            except Exception:
                # Ignorujemy błędy, bo overlay mógł zniknąć w międzyczasie
                logger.debug(f"Could not interact with '{name}' (it might have already disappeared).")

    def safe_click(self, locator: Locator, **kwargs):
        """
        "Pancerna" wersja metody .click().
        Jeśli standardowe kliknięcie zawiedzie z powodu zasłonięcia elementu,
        uruchamia procedurę czyszczenia nakładek i ponawia próbę.
        """
        try:
            # Pierwsza, optymistyczna próba kliknięcia
            locator.click(**kwargs)
        except TimeoutError as e:
            # Sprawdzamy, czy błąd jest spowodowany zasłonięciem
            if "intercepts pointer events" in str(e):
                logger.warning(
                    "Click failed because the element is obscured. Initiating auto-healing..."
                )
                self._close_known_overlays()

                # Druga, ostateczna próba kliknięcia
                logger.info("Retrying the click after cleanup...")
                locator.click(**kwargs)
            else:
                # Jeśli błąd był inny (np. element nie został znaleziony), rzucamy go dalej
                raise e

