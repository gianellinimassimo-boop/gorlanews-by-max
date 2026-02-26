import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://comune.gorlaminore.va.it"
NOVITA_URL = BASE_URL + "/novita"  # elenco novità

MAX_NEWS = 100        # quante notizie totali salvare
HOME_COUNT = 10       # quante notizie marcare come "home"


def parse_date(text):
    """
    Prova a convertire una data tipo '20/02/2026' o '24 feb 2026' in ISO.
    Se fallisce, restituisce None.
    """
    if not text:
        return None
    text = text.strip().lower()

    # Prova formato europeo semplice
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.isoformat()
        except ValueError:
            pass

    # TODO: si può aggiungere parsing per '24 feb 2026' con mapping mesi
    return None


def scrape_novita():
    """
    Scarica la pagina /novita e restituisce una lista di dict:
    {titolo, url, dataPubblicazione, categoria, immagine}
    Tutte le notizie qui sono considerate 'novita' come origine base.
    """
    print(f"Scarico {NOVITA_URL} ...")
    resp = requests.get(NOVITA_URL, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    items = []

    # OGNI notizia è un <a title="Leggi di più"> con dentro un <h3> titolo
    candidates = soup.select("a[title='Leggi di più']")

    for el in candidates:
        titolo = ""
        href = ""

        # el è direttamente l'<a title="Leggi di più">
        href = el.get("href") or ""
        title_el = el.select_one("h3, h2")
        if title_el:
            titolo = title_el.get_text(strip=True)

        if not titolo or not href:
            continue

        url_assoluto = urljoin(BASE_URL, href)

        # Data: proviamo a risalire al contenitore più vicino che ha una data
        container = el.find_parent(["div", "li", "article"])
        data_el = None
        if container:
            data_el = container.select_one("time, .data, .date")

        data_iso = None
        if data_el:
            data_iso = parse_date(data_el.get_text(strip=True))

        # Categoria: proviamo a cercare argomento o badge
        categoria = "Informativa"
        if container:
            cat_el = container.select_one(".categoria, .tag, .badge, .argomenti .chip-label")
            if cat_el:
                categoria = cat_el.get_text(strip=True)

        # Immagine (se presente)
        immagine = ""
        if container:
            img_el = container.select_one("img")
            if img_el and img_el.get("src"):
                immagine = urljoin(BASE_URL, img_el["src"])

        items.append({
            "titolo": titolo,
            "url": url_assoluto,
            "dataPubblicazione": data_iso or datetime.utcnow().isoformat(),
            "categoria": categoria,
            "immagine": immagine
        })

    print(f"Trovate {len(items)} novità da /novita.")
    return items


def main():
    # 1) Notizie dalla sezione Novità
    all_news = scrape_novita()

    if not all_news:
        print("Nessuna notizia trovata su /novita.")
        return

    # Ordina per data decrescente
    def sort_key(item):
        try:
            return datetime.fromisoformat(item["dataPubblicazione"])
        except Exception:
            return datetime.min

    all_news.sort(key=sort_key, reverse=True)

    # Limita a MAX_NEWS totali
    all_news = all_news[:MAX_NEWS]

    # 2) Imposta origine:
    #    - prime HOME_COUNT come "home"
    #    - tutte comunque "novita"
    for idx, item in enumerate(all_news):
        if idx < HOME_COUNT:
            item["origine"] = "home"
        else:
            item["origine"] = "novita"

    # 3) Aggiungi id numerico progressivo come stringa
    for idx, item in enumerate(all_news, start=1):
        item["id"] = str(idx)

    # 4) Scrivi news.json
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"Salvate {len(all_news)} notizie in news.json")


if __name__ == "__main__":
    main()
