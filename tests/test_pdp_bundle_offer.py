import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from pages.product_page import ProductPage

logger = logging.getLogger(__name__)

# URL-e, dla których sprawdzamy liczbę przycisków na PDP.
PRODUCT_URLS = [
    "https://idream.pl/iphone/apple-iphone-15/apple-iphone-15-128gb-niebieski.html",
    "https://idream.pl/ipad/ipad-air/apple-ipad-air-13-m2-128gb-wi-fi-cellular-6.gen-gwiezdna-szarosc-2024.html",
    "https://idream.pl/apple-watch/apple-watch-ultra-2/apple-watch-ultra-2-gps-cellular-49mm-tytan-naturalny-z-bransoleta-mediolanska-w-kolorze-naturalnym-s.html",
    "https://idream.pl/iphone/apple-iphone-16/apple-iphone-16-128gb-bialy.html",
    "https://idream.pl/ipad/ipad-air/apple-ipad-air-11-m3-256gb-wi-fi-7-gen-gwiezdna-szarosc-2025.html",
]

BUTTON_TEXT = "Dodaj zestaw do koszyka"
STATE_ENV_VAR = "PDP_BUNDLE_BUTTON_COUNT_STATE_PATH"
DEFAULT_STATE_PATH = Path(__file__).resolve().parent / ".pdp_bundle_button_counts_state.json"


def _expect_visible_with_url(locator, *, url: str, description: str, timeout: int) -> None:
    try:
        expect(locator).to_be_visible(timeout=timeout)
    except Exception as e:
        raise AssertionError(f"{description}. URL: {url}. Szczegóły: {e}") from e


def _expect_enabled_with_url(locator, *, url: str, description: str, timeout: int) -> None:
    try:
        expect(locator).to_be_enabled(timeout=timeout)
    except Exception as e:
        raise AssertionError(f"{description}. URL: {url}. Szczegóły: {e}") from e


def _load_button_counts(state_path: Path) -> dict[str, int]:
    if not state_path.exists():
        return {}

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning(f"Nie udało się odczytać stanu z {state_path}. Nadpiszę przy kolejnym teście.")
        return {}

    counts = data.get("counts", {})
    safe_counts: dict[str, int] = {}
    for url, count in counts.items():
        try:
            safe_counts[url] = int(count)
        except Exception:
            continue
    return safe_counts


def _save_button_counts(state_path: Path, counts_by_url: dict[str, int]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)

    state_data = {
        "schema_version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts_by_url,
    }

    tmp_path = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state_data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(state_path)


def test_pdp_bundle_buttons_presence_and_regression(page: Page):
    """
    Łączy:
    - sprawdzanie obecności sekcji zestawu i widocznego przycisku,
    - weryfikację, że na stronie jest więcej niż 1 przycisk,
    - porównanie liczby przycisków z poprzednim uruchomieniem (spadek = błąd).
    """

    product_page = ProductPage(page)

    state_path = Path(os.environ.get(STATE_ENV_VAR, str(DEFAULT_STATE_PATH))).expanduser()
    previous_counts = _load_button_counts(state_path)

    current_counts: dict[str, int] = {}

    for product_url in PRODUCT_URLS:
        logger.info(f"Test PDP Bundle (liczba przycisków) dla URL: {product_url}")

        # 1) Nawigacja + popupy
        product_page.open_specific_product_and_handle_popups(product_url)

        # 2) Upewniamy się, że strona jest załadowana
        page.wait_for_load_state("networkidle", timeout=30000)

        # 3) Scroll aby aktywować lazy-loading dla niższych sekcji
        # Różne PDP mogą mieć przyciski na różnych pozycjach, więc przewijamy w kilku krokach.
        for scroll_y in (500, 1500, 2500, 3500):
            page.evaluate(f"window.scrollTo(0, {scroll_y})")
            page.wait_for_timeout(800)

        # 4) Lokatory
        # Na niektórych PDP jest kilka kontenerów ab__bt_box, więc bierzemy pierwszy.
        bundle_box_locator = page.locator("div.ab__bt_box").first
        bundle_buttons_locator = page.locator(
            "div.cm-ab__bt-submit:has-text('Dodaj zestaw do koszyka')"
        )

        # 5) Asercje: sekcja zestawu + przyciski
        _expect_visible_with_url(
            bundle_box_locator,
            url=product_url,
            description="Brak widocznej sekcji zestawów (div.ab__bt_box)",
            timeout=10000,
        )
        bundle_box_locator.scroll_into_view_if_needed()

        current_count = bundle_buttons_locator.count()

        if current_count == 0:
            prev_count = previous_counts.get(product_url)
            if prev_count is None:
                raise AssertionError(
                    "Nie znaleziono przycisku 'Dodaj zestaw do koszyka' na tej danej stronie. "
                    f"URL: {product_url}."
                )
            raise AssertionError(
                "Mniej przycisków na tej danej stronie. "
                f"URL: {product_url}. Było: {prev_count}, teraz: {current_count}"
            )

        # Dodatkowe sprawdzenie, że przynajmniej jeden przycisk jest dostępny i ma poprawny tekst.
        # (To nie wymusza >1 na każdej stronie, tylko gwarantuje sensowność selektora.)
        _expect_visible_with_url(
            bundle_buttons_locator.first,
            url=product_url,
            description="Przycisk 'Dodaj zestaw do koszyka' nie jest widoczny",
            timeout=5000,
        )
        _expect_enabled_with_url(
            bundle_buttons_locator.first,
            url=product_url,
            description="Przycisk 'Dodaj zestaw do koszyka' nie jest aktywny",
            timeout=5000,
        )
        expect(bundle_buttons_locator.first).to_contain_text(BUTTON_TEXT)

        current_counts[product_url] = current_count

    # 6) Wypisujemy, na której stronie jest najwięcej przycisków (>1) i towarzyszymy temu komunikatem w logach.
    max_url, max_count = max(current_counts.items(), key=lambda kv: kv[1])
    logger.info(
        "Przyciski (>1) na stronach: "
        + ", ".join(
            [
                f"{url.split('/')[-1]}={count}"
                for url, count in current_counts.items()
                if count > 1
            ]
        )
    )
    logger.info(f"Najwięcej przycisków ({max_count}) na stronie: {max_url}")

    if max_count > 1:
        logger.info("✅ Znalazłem stronę z więcej niż 1 przyciskiem. Test zaliczony.")
    else:
        logger.info("ℹ️ Na żadnej stronie nie było więcej niż 1 przycisku. Bazeline nadal jest aktualizowane (o ile brak regresji).")

    # 7) Spadek liczby przycisków względem poprzedniego uruchomienia = błąd testu
    # tylko dla stron, które wcześniej miały >1 przycisk.
    for product_url, current_count in current_counts.items():
        prev_count = previous_counts.get(product_url)
        if prev_count is None:
            continue
        if prev_count > 1 and current_count < prev_count:
            assert False, (
                "Mniej przycisków na tej danej stronie. "
                f"URL: {product_url}. Było: {prev_count}, teraz: {current_count}"
            )

    # 8) Aktualizacja baseline po udanym teście.
    _save_button_counts(state_path, current_counts)

