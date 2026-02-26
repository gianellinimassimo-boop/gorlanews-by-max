import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://comune.gorlaminore.va.it"
HOME_URL = BASE_URL          # home
NOVITA_URL = BASE_URL + "/novita"  # elenco novità

MAX_NEWS = 100


def parse_date(text):
    """
    Prova a convertire una data tipo '20/02/2026' o '20 febbraio 2026' in ISO.
    Se fallisce, restituisce None.
    """
    text = (text or "").strip().lower()

    # Prova formato europeo semplice
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.isoformat()
        except ValueError:
            pass

    # Se proprio non si riesce, None
    return None


def scrape_page(url, origine_default):
    """
    Scarica una pagina (home o novità) e restituisce una lista di dict:
    {titolo, url, dataPubblicazione, origine, categoria, immagine}

    NB: i selettori CSS sotto sono generici e andranno affinati
    in base alla struttura reale del sito.
    """
    print(f"Scarico {url} per origine {origine_default}...")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    items = []

    # Selettori GENERICI: da adattare alla struttura reale del sito
    # Prova a trovare blocchi notizia comuni (article, li, card, ecc.)
    candidates = soup.select("article, li, div.card, div.novita-item")

    for el in candidates:
        # Titolo
        title_el = el.select_one("a, h2, h3")
        if not title_el:
            continue
        titolo = title_el.get_text(strip=True)
        if not titolo:
            continue

        # Link
        href = title_el.get("href") or ""
        url_assoluto = urljoin(BASE_URL, href)

        # Data (se presente)
        data_el = el.select_one("time, .data, .date")
        data_iso = None
        if data_el:
            data_iso = parse_date(data_el.get_text(strip=True))

        # Categoria (se c'è un'etichetta)
        cat_el = el.select_one(".categoria, .tag, .badge")
        categoria = None
        if cat_el:
            categoria = cat_el.get_text(strip=True)
        else:
            # fallback semplice: in base all'origine
            categoria = "Avviso" if origine_default == "home" else "Informativa"

        # Immagine (se presente)
        img_el = el.select_one("img")
        immagine = None
        if img_el and img_el.get("src"):
            immagine = urljoin(BASE_URL, img_el["src"])

        items.append({
            "titolo": titolo,
            "url": url_assoluto,
            "dataPubblicazione": data_iso or datetime.utcnow().isoformat(),
            "origine": origine_default,
            "categoria": categoria,
            "immagine": immagine or ""
        })

    print(f"Trovate {len(items)} notizie da {url}.")
    return items


def main():
    # 1) Notizie dalla home -> origine "home"
    news_home = scrape_page(HOME_URL, "home")

    # 2) Notizie dalla sezione Novità -> origine "novita"
    news_novita = scrape_page(NOVITA_URL, "novita")

    all_news = news_home + news_novita

    # Ordina per data decrescente (se c'è)
    def sort_key(item):
        try:
            return datetime.fromisoformat(item["dataPubblicazione"])
        except Exception:
            return datetime.min

    all_news.sort(key=sort_key, reverse=True)

    # Limita a MAX_NEWS
    all_news = all_news[:MAX_NEWS]

    # Aggiungi id numerico progressivo come stringa
    for idx, item in enumerate(all_news, start=1):
        item["id"] = str(idx)

    # Scrivi news.json
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"Salvate {len(all_news)} notizie in news.json")


if __name__ == "__main__":
    main()
