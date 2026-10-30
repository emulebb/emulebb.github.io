#!/usr/bin/env python3
"""Render the static eMuleBB pages from Jinja2 templates and structured copy."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import posixpath
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


SITE_BASE_URL = "https://emulebb.github.io"
DOCS_SITE_URL = "https://emulebb.github.io/emulebb-tooling"
PICO_CDN = "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css"
GA_MEASUREMENT_ID = "G-8G02C2WFEB"
RUST_RELEASES_URL = "https://github.com/emulebb/emulebb-rust/releases"
RUST_REPOSITORY_URL = "https://github.com/emulebb/emulebb-rust"
DEFAULT_PUBLIC_PRESENCE_CONTRACT = (
    Path(__file__).resolve().parents[2] / "emulebb-tooling" / "manifests" / "public-presence.v1.json"
)
STATIC_SITE_PATHS = (
    Path("assets"),
    Path("install.ps1"),
    Path("install.ps1.sha256"),
    Path("robots.txt"),
    Path("styles.css"),
    Path("suite-manifest.json"),
)
LOCALIZED_DYNAMIC_RELEASE_PATTERN = re.compile(
    r"\bBeta\s*[23]\b|\b\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?\b|nightl",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PageSpec:
    """Static routing metadata for one generated page."""

    key: str
    hreflang: str
    html_lang: str
    directory: str
    priority: str
    language_label: str

    @property
    def output_path(self) -> Path:
        if self.directory:
            return Path(self.directory) / "index.html"
        return Path("index.html")

    @property
    def url(self) -> str:
        if self.directory:
            return f"{SITE_BASE_URL}/{self.directory}/"
        return f"{SITE_BASE_URL}/"

    @property
    def stylesheet_href(self) -> str:
        return f"{relative_prefix(self)}styles.css"

    @property
    def favicon_href(self) -> str:
        return f"{relative_prefix(self)}assets/brand/emulebb-favicon.ico"


def relative_prefix(page: PageSpec) -> str:
    """Return the relative URL prefix from a generated page to the site root."""

    if not page.directory:
        return ""
    return f"{posixpath.relpath('.', page.directory)}/"


PAGES = (
    PageSpec("en", "en", "en", "", "1.0", "English"),
    PageSpec("ar_ae", "ar-AE", "ar-AE", "ar-ae", "0.8", "العربية"),
    PageSpec("eu", "eu", "eu", "eu", "0.8", "Euskara"),
    PageSpec("bg", "bg", "bg", "bg", "0.8", "Български"),
    PageSpec("ca", "ca", "ca", "ca", "0.8", "Català"),
    PageSpec("cs", "cs", "cs", "cs", "0.8", "Čeština"),
    PageSpec("da", "da", "da", "da", "0.8", "Dansk"),
    PageSpec("el", "el", "el", "el", "0.8", "Ελληνικά"),
    PageSpec("es", "es", "es", "es", "0.8", "Español"),
    PageSpec("ast", "ast", "ast", "ast", "0.8", "Asturianu"),
    PageSpec("et", "et", "et", "et", "0.8", "Eesti"),
    PageSpec("fa", "fa", "fa", "fa", "0.8", "فارسی"),
    PageSpec("fi", "fi", "fi", "fi", "0.8", "Suomi"),
    PageSpec("br", "br", "br", "br", "0.8", "Brezhoneg"),
    PageSpec("pt_br", "pt-BR", "pt-BR", "pt-br", "0.8", "Português (Brasil)"),
    PageSpec("pt_pt", "pt-PT", "pt-PT", "pt-pt", "0.8", "Português (Portugal)"),
    PageSpec("gl", "gl", "gl", "gl", "0.8", "Galego"),
    PageSpec("he", "he", "he", "he", "0.8", "עברית"),
    PageSpec("hu", "hu", "hu", "hu", "0.8", "Magyar"),
    PageSpec("it", "it", "it", "it", "0.8", "Italiano"),
    PageSpec("ja", "ja", "ja", "ja", "0.8", "日本語"),
    PageSpec("ko", "ko", "ko", "ko", "0.8", "한국어"),
    PageSpec("lt", "lt", "lt", "lt", "0.8", "Lietuvių"),
    PageSpec("lv", "lv", "lv", "lv", "0.8", "Latviešu"),
    PageSpec("mt", "mt", "mt", "mt", "0.8", "Malti"),
    PageSpec("nb", "nb", "nb", "nb", "0.8", "Norsk bokmål"),
    PageSpec("ru", "ru", "ru", "ru", "0.8", "Русский"),
    PageSpec("de", "de", "de", "de", "0.8", "Deutsch"),
    PageSpec("fr", "fr", "fr", "fr", "0.8", "Français"),
    PageSpec("pl", "pl", "pl", "pl", "0.8", "Polski"),
    PageSpec("nl", "nl", "nl", "nl", "0.8", "Nederlands"),
    PageSpec("nn", "nn", "nn", "nn", "0.8", "Norsk nynorsk"),
    PageSpec("ro", "ro", "ro", "ro", "0.8", "Română"),
    PageSpec("sl", "sl", "sl", "sl", "0.8", "Slovenščina"),
    PageSpec("sq", "sq", "sq", "sq", "0.8", "Shqip"),
    PageSpec("sv", "sv", "sv", "sv", "0.8", "Svenska"),
    PageSpec("tr", "tr", "tr", "tr", "0.8", "Türkçe"),
    PageSpec("uk", "uk", "uk", "uk", "0.8", "Українська"),
    PageSpec("ug_cn", "ug-CN", "ug-CN", "ug-cn", "0.8", "ئۇيغۇرچە"),
    PageSpec("ca_valencia", "ca-ES-valencia", "ca-ES-valencia", "ca-valencia", "0.8", "Valencià"),
    PageSpec("ca_valencia_racv", "ca-ES-valencia-x-racv", "ca-ES-valencia-x-racv", "ca-valencia-racv", "0.8", "Valencià RACV"),
    PageSpec("vi", "vi", "vi", "vi", "0.8", "Tiếng Việt"),
    PageSpec("zh_cn", "zh-CN", "zh-CN", "zh-cn", "0.8", "简体中文"),
    PageSpec("zh_tw", "zh-TW", "zh-TW", "zh-tw", "0.8", "繁體中文"),
)
LANGUAGE_PAGE = PageSpec("languages", "en", "en", "languages", "0.7", "Languages")
RUST_REDIRECT_PATH = Path("rust") / "index.html"
FAQ_LOCALE_KEYS = ("en", "it", "es", "pt_br", "pt_pt", "fr", "de", "pl", "nl", "ru", "tr", "uk", "ko", "ar_ae", "zh_cn", "ja")
FAQ_PAGE_BY_KEY = {
    page.key: PageSpec(
        page.key,
        page.hreflang,
        page.html_lang,
        "faq" if page.key == "en" else f"{page.directory}/faq",
        "0.8",
        page.language_label,
    )
    for page in PAGES
    if page.key in FAQ_LOCALE_KEYS
}
FAQ_PAGES = tuple(FAQ_PAGE_BY_KEY[key] for key in FAQ_LOCALE_KEYS)
ENGLISH_FAQ_PAGE = FAQ_PAGE_BY_KEY["en"]

STOCK_LOCALE_TEXT_FILE = Path("content") / "stock-locales.json"
LOCALIZED_COPY_FILE = Path("content") / "locales.json"
LANGUAGE_GROUPS = (
    ("English", ("en",)),
    (
        "Europe",
        (
            "eu",
            "bg",
            "ca",
            "cs",
            "da",
            "de",
            "el",
            "es",
            "ast",
            "et",
            "fi",
            "br",
            "fr",
            "gl",
            "hu",
            "it",
            "lt",
            "lv",
            "mt",
            "nb",
            "nl",
            "nn",
            "pl",
            "pt_br",
            "pt_pt",
            "ro",
            "ru",
            "sl",
            "sq",
            "sv",
            "tr",
            "uk",
            "ca_valencia",
            "ca_valencia_racv",
        ),
    ),
    ("Middle East", ("ar_ae", "fa", "he")),
    ("Asia", ("ja", "ko", "ug_cn", "vi", "zh_cn", "zh_tw")),
)


def c(span: str, h3: str, p: str) -> dict[str, str]:
    """Make a content card."""

    return {"span": span, "h3": h3, "p": p}


def s(eyebrow: str, h2: str, p: str = "") -> dict[str, Any]:
    """Make a section heading."""

    return {"eyebrow": eyebrow, "h2": h2, "p": p}


CONTENT: dict[str, dict[str, Any]] = {
    "en": {
        "title": "eMuleBB Rust | Active eD2K/Kad beta",
        "meta_description": "eMuleBB Rust is the active eD2K/Kad beta.",
        "og_title": "eMuleBB Rust | Active eD2K/Kad beta",
        "og_description": "Get the newest dated eMuleBB Rust nightly.",
        "structured_description": "eMuleBB Rust is the active eD2K/Kad beta.",
        "nav_label": "Primary navigation",
        "project_links_label": "Project links",
        "product_summary_label": "eMuleBB product summary",
        "footer_links_label": "Footer links",
    }
}


DOC_SECTION_COPY = {'en': ('Documentation', 'Guides, API, and release notes')}


MENU_COPY = {'en': {'label': 'Menu', 'open_label': 'Open primary navigation', 'close_label': 'Close primary navigation'}}


LANGUAGE_LINK_COPY = {'en': 'Languages'}


FAQ_LINKS = {
    "network": f"{DOCS_SITE_URL}/reference/GUIDE-NETWORK/",
    "sharing": f"{DOCS_SITE_URL}/reference/GUIDE-SHARING/",
    "downloads": f"{DOCS_SITE_URL}/reference/GUIDE-DOWNLOADS-SEARCH/",
    "controllers": f"{DOCS_SITE_URL}/reference/GUIDE-CONTROLLERS-REST/",
    "product": f"{DOCS_SITE_URL}/reference/GUIDE-EMULEBB/",
}

FAQ_TESTING_ANSWERS = {
    "en": "Choose the newest dated eMuleBB Rust nightly from GitHub Releases for current testing. Beta 3 is expected after a few more weeks of implementation and stabilization.",
    "it": "Per i download di eMuleBB Rust, consulta la pagina GitHub Releases.",
    "es": "Para descargar eMuleBB Rust, consulta la página GitHub Releases.",
    "pt_br": "Para baixar o eMuleBB Rust, consulte a página GitHub Releases.",
    "pt_pt": "Para transferir o eMuleBB Rust, consulte a página GitHub Releases.",
    "fr": "Pour télécharger eMuleBB Rust, consultez la page GitHub Releases.",
    "de": "Downloads für eMuleBB Rust findest du auf der GitHub-Releases-Seite.",
    "pl": "Pliki eMuleBB Rust są dostępne na stronie GitHub Releases.",
    "nl": "Downloads voor eMuleBB Rust staan op de GitHub Releases-pagina.",
    "ru": "Загрузки eMuleBB Rust доступны на странице GitHub Releases.",
    "tr": "eMuleBB Rust indirmeleri GitHub Releases sayfasındadır.",
    "uk": "Завантаження eMuleBB Rust доступні на сторінці GitHub Releases.",
    "ko": "eMuleBB Rust 다운로드는 GitHub Releases 페이지에서 확인하세요.",
    "ar_ae": "تتوفر تنزيلات eMuleBB Rust في صفحة GitHub Releases.",
    "zh_cn": "eMuleBB Rust 下载位于 GitHub Releases 页面。",
    "ja": "eMuleBB Rust のダウンロードは GitHub Releases ページにあります。",
}


def faq_item(question: str, answer: str, doc_title: str, doc_href: str) -> dict[str, str]:
    """Make a FAQ entry."""

    return {"question": question, "answer": answer, "doc_title": doc_title, "doc_href": doc_href}


FAQ_CONTENT: dict[str, dict[str, Any]] = {
    "en": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Short answers for eMule users who want to try eMuleBB for binding, sharing, upload slots, Kad, REST, and stable 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Quick eMuleBB answers for eMule users moving to the broadband edition.",
        "nav_label": "FAQ navigation",
        "eyebrow": "FAQ",
        "h1": "Common eMule questions, answered for eMuleBB",
        "lead": "Short answers for users who want the classic eMule workflow with better broadband control, safer networking, and clearer release proof.",
        "home_label": "Home",
        "docs_label": "Docs",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Languages",
        "read_more": "Read more",
        "items": [
            faq_item("How do I bind eMule to an interface or VPN?", "eMuleBB can bind P2P traffic to a named interface or local address, and it can block startup when the target is missing. Keep your VPN kill switch, firewall, and WebServer/REST bind policy separate.", "Network guide", FAQ_LINKS["network"]),
            faq_item("How do I share my library in eMule?", "eMuleBB keeps the familiar Shared Files model: add curated roots, keep Temp out of shares, use stable paths, and let hashing finish before scaling up.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("How do I limit upload slots in eMule?", "eMuleBB adds a finite broadband upload-slot target, weak-slot recycling, and practical diagnostics so fast lines stay useful without flooding the queue.", "Downloads and search guide", FAQ_LINKS["downloads"]),
            faq_item("Is eMuleBB a protocol fork of eMule?", "No. eMuleBB keeps stock-compatible eD2K and Kad behavior as the default, then improves local limits, automation, diagnostics, and release discipline around it.", "Product guide", FAQ_LINKS["product"]),
            faq_item("Which eMule release should I use for testing?", FAQ_TESTING_ANSWERS["en"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("How do I keep eMule WebServer or REST safe?", "eMuleBB treats WebServer and REST as trusted-controller surfaces. Enable them only when needed, bind deliberately, use an API key, and avoid broad exposure.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("How do I use eMule with Kad and servers?", "eMuleBB keeps classic server, global, and Kad search workflows. Start with trusted server lists, bootstrap Kad deliberately, and diagnose Low ID or firewalled Kad before changing many settings.", "Network guide", FAQ_LINKS["network"]),
            faq_item("How do I handle large shared libraries in eMule?", "eMuleBB is built for large libraries: add roots gradually, use long-path capable Windows setups, review share-ignore rules, and let startup cache work settle.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Can I automate eMule with external tools?", "Yes. eMuleBB exposes an authenticated JSON REST API for trusted local controllers while keeping native transfer and sharing semantics in the desktop app.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
    "it": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Risposte brevi per utenti eMule che vogliono provare eMuleBB per binding, condivisione, slot di upload, Kad, REST e test 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Risposte rapide eMuleBB per utenti eMule.",
        "nav_label": "Navigazione FAQ",
        "eyebrow": "FAQ",
        "h1": "Domande comuni su eMule, risposte per eMuleBB",
        "lead": "Risposte brevi per chi vuole il flusso classico di eMule con migliore controllo broadband, rete piu sicura e prove di rilascio chiare.",
        "home_label": "Home",
        "docs_label": "Documentazione",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Lingue",
        "read_more": "Approfondisci",
        "items": [
            faq_item("Come collego eMule a un'interfaccia o a una VPN?", "eMuleBB puo vincolare il traffico P2P a un'interfaccia o indirizzo locale e bloccare l'avvio se il target manca. Tieni separati kill switch VPN, firewall e binding WebServer/REST.", "Guida rete", FAQ_LINKS["network"]),
            faq_item("Come condivido la mia libreria in eMule?", "eMuleBB conserva il modello Shared Files: aggiungi radici curate, tieni Temp fuori dalle condivisioni, usa percorsi stabili e lascia finire l'hashing.", "Guida condivisione", FAQ_LINKS["sharing"]),
            faq_item("Come limito gli slot di upload in eMule?", "eMuleBB aggiunge un target finito di slot upload, riciclo degli slot deboli e diagnostica utile per sfruttare linee veloci senza saturare la coda.", "Guida download e ricerca", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB e un fork di protocollo di eMule?", "No. eMuleBB mantiene compatibili eD2K e Kad stock, migliorando limiti locali, automazione, diagnostica e disciplina di rilascio.", "Guida prodotto", FAQ_LINKS["product"]),
            faq_item("Quale release di eMule dovrei usare per i test?", FAQ_TESTING_ANSWERS["it"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Come tengo sicuri WebServer o REST di eMule?", "eMuleBB tratta WebServer e REST come superfici per controller fidati. Abilitali solo quando servono, configura il bind, usa una API key ed evita esposizione ampia.", "Guida controller e REST", FAQ_LINKS["controllers"]),
            faq_item("Come uso eMule con Kad e server?", "eMuleBB conserva server, ricerca globale e Kad. Parti da liste server fidate, avvia Kad con cura e diagnostica Low ID o Kad firewalled prima di cambiare troppe opzioni.", "Guida rete", FAQ_LINKS["network"]),
            faq_item("Come gestisco grandi librerie condivise in eMule?", "eMuleBB e pensato per grandi librerie: aggiungi radici gradualmente, usa Windows con long paths, rivedi share-ignore e lascia stabilizzare la cache di avvio.", "Guida condivisione", FAQ_LINKS["sharing"]),
            faq_item("Posso automatizzare eMule con strumenti esterni?", "Si. eMuleBB espone una REST API JSON autenticata per controller locali fidati, mantenendo semantica nativa di trasferimenti e condivisioni nell'app desktop.", "Guida controller e REST", FAQ_LINKS["controllers"]),
        ],
    },
    "es": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Respuestas breves para usuarios de eMule que quieren probar eMuleBB con binding, biblioteca compartida, slots de subida, Kad, REST y 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Respuestas rapidas de eMuleBB para usuarios de eMule.",
        "nav_label": "Navegacion FAQ",
        "eyebrow": "FAQ",
        "h1": "Preguntas comunes de eMule, respondidas para eMuleBB",
        "lead": "Respuestas breves para usar el flujo clasico de eMule con mejor control de banda ancha, red mas segura y pruebas de release claras.",
        "home_label": "Inicio",
        "docs_label": "Documentacion",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Idiomas",
        "read_more": "Leer mas",
        "items": [
            faq_item("Como vinculo eMule a una interfaz o VPN?", "eMuleBB puede vincular el trafico P2P a una interfaz o direccion local y bloquear el arranque si falta el destino. Mantén aparte el kill switch VPN, firewall y bind de WebServer/REST.", "Guia de red", FAQ_LINKS["network"]),
            faq_item("Como comparto mi biblioteca en eMule?", "eMuleBB conserva el modelo Shared Files: agrega raices cuidadas, deja Temp fuera de las compartidas, usa rutas estables y espera a que termine el hashing.", "Guia de comparticion", FAQ_LINKS["sharing"]),
            faq_item("Como limito los slots de subida en eMule?", "eMuleBB agrega un objetivo finito de slots de subida, reciclaje de slots debiles y diagnostico practico para aprovechar lineas rapidas sin inundar la cola.", "Guia de descargas y busqueda", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB es un fork de protocolo de eMule?", "No. eMuleBB mantiene eD2K y Kad compatibles con el comportamiento stock, y mejora limites locales, automatizacion, diagnostico y disciplina de release.", "Guia del producto", FAQ_LINKS["product"]),
            faq_item("Que release de eMule debo usar para pruebas?", FAQ_TESTING_ANSWERS["es"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Como mantengo seguro WebServer o REST de eMule?", "eMuleBB trata WebServer y REST como superficies para controladores confiables. Activalos solo cuando haga falta, configura el bind, usa API key y evita exponerlos ampliamente.", "Guia de controladores y REST", FAQ_LINKS["controllers"]),
            faq_item("Como uso eMule con Kad y servidores?", "eMuleBB conserva servidores, busqueda global y Kad. Empieza con listas confiables, arranca Kad con cuidado y diagnostica Low ID o Kad firewalled antes de tocar muchas opciones.", "Guia de red", FAQ_LINKS["network"]),
            faq_item("Como manejo bibliotecas compartidas grandes en eMule?", "eMuleBB esta preparado para bibliotecas grandes: agrega raices gradualmente, usa Windows con long paths, revisa share-ignore y deja asentarse la cache de inicio.", "Guia de comparticion", FAQ_LINKS["sharing"]),
            faq_item("Puedo automatizar eMule con herramientas externas?", "Si. eMuleBB ofrece una REST API JSON autenticada para controladores locales confiables, manteniendo la semantica nativa de transferencias y comparticion en la app desktop.", "Guia de controladores y REST", FAQ_LINKS["controllers"]),
        ],
    },
    "pt_br": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Respostas curtas para usuarios do eMule que querem testar o eMuleBB com binding, compartilhamento, slots de upload, Kad, REST e 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Respostas rapidas do eMuleBB para usuarios do eMule.",
        "nav_label": "Navegacao FAQ",
        "eyebrow": "FAQ",
        "h1": "Perguntas comuns sobre eMule, respondidas para eMuleBB",
        "lead": "Respostas curtas para usar o fluxo classico do eMule com melhor controle de banda larga, rede mais segura e provas de release claras.",
        "home_label": "Inicio",
        "docs_label": "Docs",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Idiomas",
        "read_more": "Leia mais",
        "items": [
            faq_item("Como vinculo o eMule a uma interface ou VPN?", "O eMuleBB pode vincular o trafego P2P a uma interface ou endereco local e bloquear a inicializacao quando o alvo falta. Mantenha kill switch VPN, firewall e bind WebServer/REST separados.", "Guia de rede", FAQ_LINKS["network"]),
            faq_item("Como compartilho minha biblioteca no eMule?", "O eMuleBB mantem o modelo Shared Files: adicione raizes selecionadas, deixe Temp fora do compartilhamento, use caminhos estaveis e espere o hashing terminar.", "Guia de compartilhamento", FAQ_LINKS["sharing"]),
            faq_item("Como limito os slots de upload no eMule?", "O eMuleBB adiciona alvo finito de slots de upload, reciclagem de slots fracos e diagnosticos praticos para aproveitar links rapidos sem lotar a fila.", "Guia de downloads e busca", FAQ_LINKS["downloads"]),
            faq_item("O eMuleBB e um fork de protocolo do eMule?", "Nao. O eMuleBB mantem eD2K e Kad compativeis com o comportamento stock e melhora limites locais, automacao, diagnosticos e disciplina de release.", "Guia do produto", FAQ_LINKS["product"]),
            faq_item("Qual release do eMule devo usar para testes?", FAQ_TESTING_ANSWERS["pt_br"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Como mantenho seguros WebServer ou REST do eMule?", "O eMuleBB trata WebServer e REST como superficies para controladores confiaveis. Ative apenas quando precisar, configure bind, use API key e evite exposicao ampla.", "Guia de controladores e REST", FAQ_LINKS["controllers"]),
            faq_item("Como uso eMule com Kad e servidores?", "O eMuleBB mantem servidores, busca global e Kad. Comece com listas confiaveis, inicialize Kad com cuidado e diagnostique Low ID ou Kad firewalled antes de mudar muita coisa.", "Guia de rede", FAQ_LINKS["network"]),
            faq_item("Como lidar com grandes bibliotecas compartilhadas no eMule?", "O eMuleBB foi feito para bibliotecas grandes: adicione raizes aos poucos, use Windows com long paths, revise share-ignore e deixe a cache de inicio estabilizar.", "Guia de compartilhamento", FAQ_LINKS["sharing"]),
            faq_item("Posso automatizar o eMule com ferramentas externas?", "Sim. O eMuleBB expoe uma REST API JSON autenticada para controladores locais confiaveis, mantendo a semantica nativa de transferencias e compartilhamento no app desktop.", "Guia de controladores e REST", FAQ_LINKS["controllers"]),
        ],
    },
    "fr": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Reponses courtes pour les utilisateurs eMule qui veulent essayer eMuleBB: binding, partage, slots d'upload, Kad, REST et 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Reponses rapides eMuleBB pour utilisateurs eMule.",
        "nav_label": "Navigation FAQ",
        "eyebrow": "FAQ",
        "h1": "Questions courantes eMule, reponses pour eMuleBB",
        "lead": "Des reponses courtes pour garder le flux eMule classique avec un meilleur controle broadband, une exposition reseau plus claire et des preuves de release.",
        "home_label": "Accueil",
        "docs_label": "Docs",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Langues",
        "read_more": "Lire la suite",
        "items": [
            faq_item("Comment lier eMule a une interface ou a un VPN?", "eMuleBB peut lier le trafic P2P a une interface ou adresse locale et bloquer le demarrage si la cible manque. Gardez kill switch VPN, pare-feu et bind WebServer/REST separes.", "Guide reseau", FAQ_LINKS["network"]),
            faq_item("Comment partager ma bibliotheque dans eMule?", "eMuleBB garde le modele Shared Files: ajoutez des racines choisies, gardez Temp hors des partages, utilisez des chemins stables et laissez le hachage finir.", "Guide partage", FAQ_LINKS["sharing"]),
            faq_item("Comment limiter les slots d'upload dans eMule?", "eMuleBB ajoute une cible finie de slots d'upload, le recyclage des slots faibles et des diagnostics utiles pour exploiter les lignes rapides sans noyer la file.", "Guide telechargements et recherche", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB est-il un fork de protocole d'eMule?", "Non. eMuleBB garde eD2K et Kad compatibles avec le comportement stock, puis ameliore limites locales, automatisation, diagnostics et discipline de release.", "Guide produit", FAQ_LINKS["product"]),
            faq_item("Quelle release eMule utiliser pour tester?", FAQ_TESTING_ANSWERS["fr"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Comment securiser WebServer ou REST d'eMule?", "eMuleBB traite WebServer et REST comme des surfaces pour controleurs de confiance. Activez-les seulement si besoin, liez-les explicitement, utilisez une API key et evitez l'exposition large.", "Guide controleurs et REST", FAQ_LINKS["controllers"]),
            faq_item("Comment utiliser eMule avec Kad et les serveurs?", "eMuleBB conserve serveurs, recherche globale et Kad. Commencez avec des listes fiables, amorcez Kad proprement et diagnostiquez Low ID ou Kad firewalled avant de trop changer.", "Guide reseau", FAQ_LINKS["network"]),
            faq_item("Comment gerer de grandes bibliotheques partagees dans eMule?", "eMuleBB vise les grandes bibliotheques: ajoutez les racines graduellement, utilisez Windows avec long paths, revoyez share-ignore et laissez la cache de demarrage se stabiliser.", "Guide partage", FAQ_LINKS["sharing"]),
            faq_item("Puis-je automatiser eMule avec des outils externes?", "Oui. eMuleBB expose une REST API JSON authentifiee pour des controleurs locaux de confiance, tout en gardant la semantique native dans l'app desktop.", "Guide controleurs et REST", FAQ_LINKS["controllers"]),
        ],
    },
    "de": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Kurze Antworten fuer eMule-Nutzer, die eMuleBB fuer Binding, Shares, Upload-Slots, Kad, REST und 0.7.3 testen wollen.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Schnelle eMuleBB-Antworten fuer eMule-Nutzer.",
        "nav_label": "FAQ-Navigation",
        "eyebrow": "FAQ",
        "h1": "Haeufige eMule-Fragen, beantwortet fuer eMuleBB",
        "lead": "Kurze Antworten fuer den klassischen eMule-Workflow mit besserer Breitbandkontrolle, klarer Netzwerkexposition und nachvollziehbarer Release-Pruefung.",
        "home_label": "Start",
        "docs_label": "Doku",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Sprachen",
        "read_more": "Mehr lesen",
        "items": [
            faq_item("Wie binde ich eMule an ein Interface oder VPN?", "eMuleBB kann P2P-Verkehr an ein Interface oder eine lokale Adresse binden und den Start blockieren, wenn das Ziel fehlt. VPN-Kill-Switch, Firewall und WebServer/REST-Bind bleiben getrennt.", "Network Guide", FAQ_LINKS["network"]),
            faq_item("Wie teile ich meine Bibliothek in eMule?", "eMuleBB behaelt das bekannte Shared-Files-Modell: kuratierte Wurzeln hinzufuegen, Temp nicht teilen, stabile Pfade nutzen und Hashing auslaufen lassen.", "Sharing Guide", FAQ_LINKS["sharing"]),
            faq_item("Wie begrenze ich Upload-Slots in eMule?", "eMuleBB fuegt ein endliches Upload-Slot-Ziel, Recycling schwacher Slots und praktische Diagnose hinzu, damit schnelle Leitungen nutzbar bleiben ohne die Queue zu fluten.", "Downloads and Search Guide", FAQ_LINKS["downloads"]),
            faq_item("Ist eMuleBB ein Protokoll-Fork von eMule?", "Nein. eMuleBB haelt eD2K und Kad stock-kompatibel und verbessert darum herum lokale Limits, Automatisierung, Diagnose und Release-Disziplin.", "Product Guide", FAQ_LINKS["product"]),
            faq_item("Welche eMule-Release soll ich testen?", FAQ_TESTING_ANSWERS["de"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Wie halte ich eMule WebServer oder REST sicher?", "eMuleBB behandelt WebServer und REST als Oberflaechen fuer vertrauenswuerdige Controller. Nur bei Bedarf aktivieren, bewusst binden, API key nutzen und breite Exposition vermeiden.", "Controllers and REST Guide", FAQ_LINKS["controllers"]),
            faq_item("Wie nutze ich eMule mit Kad und Servern?", "eMuleBB behaelt Server, globale Suche und Kad. Starte mit vertrauenswuerdigen Serverlisten, bootstrappe Kad bewusst und diagnostiziere Low ID oder Kad firewalled vor grossen Aenderungen.", "Network Guide", FAQ_LINKS["network"]),
            faq_item("Wie betreibe ich grosse Freigabe-Bibliotheken in eMule?", "eMuleBB ist fuer grosse Bibliotheken gedacht: Wurzeln schrittweise hinzufuegen, Windows mit long paths nutzen, share-ignore pruefen und Startup-Cache stabilisieren lassen.", "Sharing Guide", FAQ_LINKS["sharing"]),
            faq_item("Kann ich eMule mit externen Tools automatisieren?", "Ja. eMuleBB bietet eine authentifizierte JSON REST API fuer vertrauenswuerdige lokale Controller und behaelt native Transfer- und Share-Semantik in der Desktop-App.", "Controllers and REST Guide", FAQ_LINKS["controllers"]),
        ],
    },
    "pl": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Krotkie odpowiedzi dla uzytkownikow eMule, ktorzy chca wyprobowac eMuleBB: binding, udostepnianie, sloty uploadu, Kad, REST i 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Szybkie odpowiedzi eMuleBB dla uzytkownikow eMule.",
        "nav_label": "Nawigacja FAQ",
        "eyebrow": "FAQ",
        "h1": "Popularne pytania o eMule, odpowiedzi dla eMuleBB",
        "lead": "Krotkie odpowiedzi dla osob, ktore chca klasycznego eMule z lepsza kontrola lacza, bezpieczniejsza siecia i jasnym procesem wydania.",
        "home_label": "Start",
        "docs_label": "Dokumentacja",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Jezyki",
        "read_more": "Czytaj wiecej",
        "items": [
            faq_item("Jak przypiac eMule do interfejsu albo VPN?", "eMuleBB moze przypiac ruch P2P do interfejsu lub lokalnego adresu i zablokowac start, gdy cel znika. Kill switch VPN, firewall i bind WebServer/REST trzymaj osobno.", "Przewodnik sieciowy", FAQ_LINKS["network"]),
            faq_item("Jak udostepnic biblioteke w eMule?", "eMuleBB zachowuje model Shared Files: dodawaj wybrane katalogi, trzymaj Temp poza udostepnianiem, uzywaj stalych sciezek i poczekaj na zakonczenie hashowania.", "Przewodnik udostepniania", FAQ_LINKS["sharing"]),
            faq_item("Jak ograniczyc sloty uploadu w eMule?", "eMuleBB dodaje skonczony cel slotow uploadu, odzyskiwanie slabych slotow i praktyczna diagnostyke, aby szybkie lacza pomagaly bez zalewania kolejki.", "Przewodnik pobierania i wyszukiwania", FAQ_LINKS["downloads"]),
            faq_item("Czy eMuleBB jest forkiem protokolu eMule?", "Nie. eMuleBB zachowuje zgodne eD2K i Kad, a dookola nich poprawia lokalne limity, automatyzacje, diagnostyke i dyscypline wydan.", "Przewodnik produktu", FAQ_LINKS["product"]),
            faq_item("Ktore wydanie eMule wybrac do testow?", FAQ_TESTING_ANSWERS["pl"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Jak zabezpieczyc WebServer albo REST w eMule?", "eMuleBB traktuje WebServer i REST jako powierzchnie dla zaufanych kontrolerow. Wlaczaj je tylko w razie potrzeby, ustaw bind, uzyj API key i unikaj szerokiej ekspozycji.", "Przewodnik kontrolerow i REST", FAQ_LINKS["controllers"]),
            faq_item("Jak uzywac eMule z Kad i serwerami?", "eMuleBB zachowuje serwery, wyszukiwanie globalne i Kad. Zacznij od zaufanych list, ostroznie bootstrapuj Kad i diagnozuj Low ID lub Kad firewalled przed duzymi zmianami.", "Przewodnik sieciowy", FAQ_LINKS["network"]),
            faq_item("Jak obslugiwac duze biblioteki udostepniane w eMule?", "eMuleBB jest przygotowany na duze biblioteki: dodawaj katalogi stopniowo, uzywaj Windows z long paths, sprawdz share-ignore i pozwol ustabilizowac cache startowy.", "Przewodnik udostepniania", FAQ_LINKS["sharing"]),
            faq_item("Czy moge automatyzowac eMule zewnetrznymi narzedziami?", "Tak. eMuleBB udostepnia uwierzytelniona JSON REST API dla zaufanych lokalnych kontrolerow, zachowujac natywna semantyke transferow i udostepniania w aplikacji desktop.", "Przewodnik kontrolerow i REST", FAQ_LINKS["controllers"]),
        ],
    },
    "nl": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Korte antwoorden voor eMule-gebruikers die eMuleBB willen proberen voor binding, delen, uploadslots, Kad, REST en 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Snelle eMuleBB-antwoorden voor eMule-gebruikers.",
        "nav_label": "FAQ-navigatie",
        "eyebrow": "FAQ",
        "h1": "Veelgestelde eMule-vragen, beantwoord voor eMuleBB",
        "lead": "Korte antwoorden voor de klassieke eMule-werkwijze met betere breedbandcontrole, duidelijkere netwerkgrenzen en releasebewijs.",
        "home_label": "Home",
        "docs_label": "Docs",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Talen",
        "read_more": "Lees meer",
        "items": [
            faq_item("Hoe bind ik eMule aan een interface of VPN?", "eMuleBB kan P2P-verkeer aan een interface of lokaal adres binden en starten blokkeren als het doel ontbreekt. Houd VPN kill switch, firewall en WebServer/REST-bind apart.", "Netwerkgids", FAQ_LINKS["network"]),
            faq_item("Hoe deel ik mijn bibliotheek in eMule?", "eMuleBB houdt het bekende Shared Files-model: voeg gekozen roots toe, houd Temp buiten shares, gebruik stabiele paden en laat hashing afronden.", "Deelgids", FAQ_LINKS["sharing"]),
            faq_item("Hoe beperk ik uploadslots in eMule?", "eMuleBB voegt een eindig uploadslotdoel, recycling van zwakke slots en praktische diagnostiek toe zodat snelle lijnen nuttig blijven zonder de wachtrij te overspoelen.", "Downloads en zoekgids", FAQ_LINKS["downloads"]),
            faq_item("Is eMuleBB een protocolfork van eMule?", "Nee. eMuleBB houdt eD2K en Kad stock-compatibel en verbetert daaromheen lokale limieten, automatisering, diagnostiek en release-discipline.", "Productgids", FAQ_LINKS["product"]),
            faq_item("Welke eMule-release moet ik testen?", FAQ_TESTING_ANSWERS["nl"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Hoe houd ik eMule WebServer of REST veilig?", "eMuleBB behandelt WebServer en REST als oppervlakken voor vertrouwde controllers. Zet ze alleen aan wanneer nodig, bind bewust, gebruik een API key en voorkom brede blootstelling.", "Controllers en REST-gids", FAQ_LINKS["controllers"]),
            faq_item("Hoe gebruik ik eMule met Kad en servers?", "eMuleBB houdt servers, globale zoekactie en Kad. Begin met vertrouwde serverlijsten, bootstrap Kad bewust en diagnoseer Low ID of Kad firewalled voordat je veel wijzigt.", "Netwerkgids", FAQ_LINKS["network"]),
            faq_item("Hoe beheer ik grote gedeelde bibliotheken in eMule?", "eMuleBB is gemaakt voor grote bibliotheken: voeg roots geleidelijk toe, gebruik Windows met long paths, controleer share-ignore en laat de startcache stabiliseren.", "Deelgids", FAQ_LINKS["sharing"]),
            faq_item("Kan ik eMule automatiseren met externe tools?", "Ja. eMuleBB biedt een geauthenticeerde JSON REST API voor vertrouwde lokale controllers en houdt native transfer- en deelgedrag in de desktop-app.", "Controllers en REST-gids", FAQ_LINKS["controllers"]),
        ],
    },
    "ru": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Короткие ответы для пользователей eMule, которые хотят попробовать eMuleBB: binding, общие папки, upload slots, Kad, REST и 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Быстрые ответы eMuleBB для пользователей eMule.",
        "nav_label": "Навигация FAQ",
        "eyebrow": "FAQ",
        "h1": "Частые вопросы по eMule, ответы для eMuleBB",
        "lead": "Короткие ответы для тех, кто хочет классический рабочий процесс eMule с лучшим broadband-контролем, понятной сетью и проверяемыми релизами.",
        "home_label": "Главная",
        "docs_label": "Документация",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Языки",
        "read_more": "Подробнее",
        "items": [
            faq_item("Как привязать eMule к интерфейсу или VPN?", "eMuleBB может привязать P2P-трафик к интерфейсу или локальному адресу и заблокировать старт, если цель недоступна. VPN kill switch, firewall и WebServer/REST bind держите отдельно.", "Network guide", FAQ_LINKS["network"]),
            faq_item("Как расшарить библиотеку в eMule?", "eMuleBB сохраняет модель Shared Files: добавляйте выбранные корни, не шарьте Temp, используйте стабильные пути и дождитесь окончания hashing.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Как ограничить upload slots в eMule?", "eMuleBB добавляет конечную цель upload slots, переработку слабых слотов и полезную диагностику, чтобы быстрый канал не превращался в хаос очереди.", "Downloads and search guide", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB является protocol fork eMule?", "Нет. eMuleBB сохраняет совместимое поведение eD2K и Kad, а вокруг него улучшает локальные лимиты, automation, диагностику и дисциплину релизов.", "Product guide", FAQ_LINKS["product"]),
            faq_item("Какой релиз eMule использовать для тестов?", FAQ_TESTING_ANSWERS["ru"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Как безопасно включить eMule WebServer или REST?", "eMuleBB считает WebServer и REST поверхностями для доверенных контроллеров. Включайте их только при необходимости, задавайте bind, используйте API key и не открывайте широко.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("Как использовать eMule с Kad и серверами?", "eMuleBB сохраняет серверы, global search и Kad. Начните с доверенных списков серверов, аккуратно bootstrap Kad и диагностируйте Low ID или Kad firewalled до массовых изменений.", "Network guide", FAQ_LINKS["network"]),
            faq_item("Как работать с большой общей библиотекой в eMule?", "eMuleBB рассчитан на большие библиотеки: добавляйте корни постепенно, используйте Windows с long paths, проверяйте share-ignore и дайте startup cache стабилизироваться.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Можно ли автоматизировать eMule внешними инструментами?", "Да. eMuleBB предоставляет authenticated JSON REST API для доверенных локальных контроллеров, сохраняя native transfer и sharing semantics в desktop app.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
    "uk": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Короткі відповіді для користувачів eMule, які хочуть спробувати eMuleBB: binding, спільні бібліотеки, upload slots, Kad, REST і 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Швидкі відповіді eMuleBB для користувачів eMule.",
        "nav_label": "Навігація FAQ",
        "eyebrow": "FAQ",
        "h1": "Поширені питання про eMule, відповіді для eMuleBB",
        "lead": "Короткі відповіді для тих, хто хоче класичний процес eMule з кращим broadband-контролем, чіткішою мережею та перевіреними релізами.",
        "home_label": "Головна",
        "docs_label": "Документація",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Мови",
        "read_more": "Докладніше",
        "items": [
            faq_item("Як прив'язати eMule до інтерфейсу або VPN?", "eMuleBB може прив'язати P2P-трафік до інтерфейсу або локальної адреси й заблокувати старт, якщо ціль недоступна. VPN kill switch, firewall і WebServer/REST bind тримайте окремо.", "Network guide", FAQ_LINKS["network"]),
            faq_item("Як поділитися бібліотекою в eMule?", "eMuleBB зберігає модель Shared Files: додавайте вибрані корені, не діліться Temp, використовуйте стабільні шляхи й дочекайтеся завершення hashing.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Як обмежити upload slots в eMule?", "eMuleBB додає скінченну ціль upload slots, переробку слабких слотів і корисну діагностику, щоб швидкий канал не перевантажував чергу.", "Downloads and search guide", FAQ_LINKS["downloads"]),
            faq_item("Чи є eMuleBB protocol fork від eMule?", "Ні. eMuleBB зберігає сумісну поведінку eD2K і Kad, а навколо неї покращує локальні ліміти, automation, діагностику та дисципліну релізів.", "Product guide", FAQ_LINKS["product"]),
            faq_item("Який реліз eMule використовувати для тестів?", FAQ_TESTING_ANSWERS["uk"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Як безпечно використовувати eMule WebServer або REST?", "eMuleBB розглядає WebServer і REST як поверхні для довірених контролерів. Увімкніть лише за потреби, задайте bind, використовуйте API key і не відкривайте широко.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("Як використовувати eMule з Kad і серверами?", "eMuleBB зберігає сервери, global search і Kad. Почніть із довірених списків серверів, обережно bootstrap Kad і діагностуйте Low ID або Kad firewalled перед масовими змінами.", "Network guide", FAQ_LINKS["network"]),
            faq_item("Як працювати з великою спільною бібліотекою в eMule?", "eMuleBB розрахований на великі бібліотеки: додавайте корені поступово, використовуйте Windows з long paths, перевіряйте share-ignore і дайте startup cache стабілізуватися.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Чи можна автоматизувати eMule зовнішніми інструментами?", "Так. eMuleBB надає authenticated JSON REST API для довірених локальних контролерів, зберігаючи native transfer і sharing semantics у desktop app.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
    "zh_cn": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "面向 eMule 用户的简短问答：用 eMuleBB 处理绑定、共享库、上传槽、Kad、REST 和 0.7.3 测试。",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "面向 eMule 用户的 eMuleBB 快速问答。",
        "nav_label": "FAQ 导航",
        "eyebrow": "FAQ",
        "h1": "常见 eMule 问题，按 eMuleBB 来回答",
        "lead": "给想保留经典 eMule 工作流、同时获得更好宽带控制、更清晰网络边界和发布证据的用户。",
        "home_label": "首页",
        "docs_label": "文档",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "语言",
        "read_more": "阅读更多",
        "items": [
            faq_item("如何把 eMule 绑定到接口或 VPN?", "eMuleBB 可以把 P2P 流量绑定到指定接口或本地地址，也可以在目标缺失时阻止启动。VPN kill switch、防火墙和 WebServer/REST bind 应单独配置。", "网络指南", FAQ_LINKS["network"]),
            faq_item("如何在 eMule 中共享我的资料库?", "eMuleBB 保留 Shared Files 模型：添加经过整理的根目录，不共享 Temp，使用稳定路径，并等待 hashing 完成。", "共享指南", FAQ_LINKS["sharing"]),
            faq_item("如何限制 eMule 的上传槽?", "eMuleBB 增加有限的上传槽目标、弱槽回收和实用诊断，让高速线路更有用，同时避免队列失控。", "下载和搜索指南", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB 是 eMule 的协议分叉吗?", "不是。eMuleBB 默认保持 eD2K 和 Kad 的 stock 兼容行为，只在本地限制、自动化、诊断和发布纪律上改进。", "产品指南", FAQ_LINKS["product"]),
            faq_item("测试时应该使用哪个 eMule 版本?", FAQ_TESTING_ANSWERS["zh_cn"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("如何保证 eMule WebServer 或 REST 安全?", "eMuleBB 把 WebServer 和 REST 视为可信控制器接口。只在需要时启用，明确 bind，使用 API key，并避免大范围暴露。", "控制器和 REST 指南", FAQ_LINKS["controllers"]),
            faq_item("如何在 eMule 中使用 Kad 和服务器?", "eMuleBB 保留服务器、global search 和 Kad 工作流。先使用可信服务器列表，谨慎 bootstrap Kad，并在大量改设置前诊断 Low ID 或 Kad firewalled。", "网络指南", FAQ_LINKS["network"]),
            faq_item("如何处理 eMule 的大型共享库?", "eMuleBB 面向大型资料库：逐步添加根目录，使用支持 long paths 的 Windows，检查 share-ignore，并让 startup cache 稳定下来。", "共享指南", FAQ_LINKS["sharing"]),
            faq_item("可以用外部工具自动化 eMule 吗?", "可以。eMuleBB 提供经过认证的 JSON REST API 给可信本地控制器，同时把原生传输和共享语义保留在桌面应用中。", "控制器和 REST 指南", FAQ_LINKS["controllers"]),
        ],
    },
    "ja": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "eMule ユーザー向けの短いFAQ。eMuleBB の binding、共有ライブラリ、upload slots、Kad、REST、0.7.3 テストを扱います。",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "eMule ユーザー向け eMuleBB クイックFAQ。",
        "nav_label": "FAQ ナビゲーション",
        "eyebrow": "FAQ",
        "h1": "よくある eMule の質問を eMuleBB 向けに回答",
        "lead": "クラシックな eMule の操作感を保ちながら、よりよい broadband 制御、明確なネットワーク設定、検証されたリリースを使いたい人向けです。",
        "home_label": "ホーム",
        "docs_label": "ドキュメント",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "言語",
        "read_more": "詳しく読む",
        "items": [
            faq_item("eMule をインターフェイスや VPN に bind するには?", "eMuleBB は P2P トラフィックを指定インターフェイスまたはローカルアドレスに bind でき、対象がない場合は起動を止められます。VPN kill switch、firewall、WebServer/REST bind は別管理です。", "ネットワークガイド", FAQ_LINKS["network"]),
            faq_item("eMule でライブラリを共有するには?", "eMuleBB は Shared Files モデルを保ちます。整理した root を追加し、Temp は共有せず、安定したパスを使い、hashing 完了を待ちます。", "共有ガイド", FAQ_LINKS["sharing"]),
            faq_item("eMule の upload slots を制限するには?", "eMuleBB は有限の upload slot 目標、弱い slot の再利用、実用的な診断を追加し、高速回線をキュー崩壊なしに活かします。", "ダウンロードと検索ガイド", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB は eMule のプロトコル fork ですか?", "いいえ。eMuleBB は eD2K と Kad の stock 互換動作を保ち、その周囲でローカル制限、自動化、診断、リリース規律を改善します。", "製品ガイド", FAQ_LINKS["product"]),
            faq_item("テストにはどの eMule release を使えばよいですか?", FAQ_TESTING_ANSWERS["ja"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("eMule WebServer や REST を安全に保つには?", "eMuleBB は WebServer と REST を信頼済み controller 向けの surface として扱います。必要な時だけ有効化し、明示的に bind し、API key を使い、広い公開は避けます。", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("eMule で Kad とサーバーを使うには?", "eMuleBB は server、global search、Kad の流れを保ちます。信頼できる server list から始め、Kad を慎重に bootstrap し、Low ID や Kad firewalled を先に診断します。", "ネットワークガイド", FAQ_LINKS["network"]),
            faq_item("eMule の大きな共有ライブラリを扱うには?", "eMuleBB は大きなライブラリ向けです。root を段階的に追加し、long paths 対応 Windows を使い、share-ignore を確認し、startup cache が落ち着くのを待ちます。", "共有ガイド", FAQ_LINKS["sharing"]),
            faq_item("外部ツールで eMule を自動化できますか?", "はい。eMuleBB は信頼済みローカル controller 向けに認証付き JSON REST API を提供し、転送と共有の native semantics は desktop app に残します。", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
    "pt_pt": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Respostas curtas para utilizadores eMule que querem experimentar o eMuleBB para binding, partilha, slots de upload, Kad, REST e testes de 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "Respostas rápidas do eMuleBB para utilizadores eMule.",
        "nav_label": "Navegação das FAQ",
        "eyebrow": "FAQ",
        "h1": "Perguntas comuns sobre eMule, respondidas para o eMuleBB",
        "lead": "Respostas curtas para quem quer o fluxo clássico do eMule com melhor controlo de banda larga, rede mais segura e provas de release mais claras.",
        "home_label": "Início",
        "docs_label": "Documentação",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "Idiomas",
        "read_more": "Saber mais",
        "items": [
            faq_item("Como ligo o eMule a uma interface ou VPN?", "O eMuleBB pode vincular o tráfego P2P a uma interface ou endereço local e bloquear o arranque se o destino faltar. Mantenha o kill switch da VPN, a firewall e o bind do WebServer/REST separados.", "Guia de rede", FAQ_LINKS["network"]),
            faq_item("Como partilho a minha biblioteca no eMule?", "O eMuleBB mantém o modelo Shared Files: adicione raízes selecionadas, mantenha a Temp fora das partilhas, use caminhos estáveis e deixe o hashing terminar antes de crescer.", "Guia de partilha", FAQ_LINKS["sharing"]),
            faq_item("Como limito os slots de upload no eMule?", "O eMuleBB acrescenta um alvo finito de slots de upload em banda larga, reciclagem de slots fracos e diagnósticos práticos para que ligações rápidas continuem úteis sem inundar a fila.", "Guia de transferências e pesquisa", FAQ_LINKS["downloads"]),
            faq_item("O eMuleBB é um fork de protocolo do eMule?", "Não. O eMuleBB mantém o comportamento eD2K e Kad compatível com o stock por omissão e melhora os limites locais, a automação, os diagnósticos e a disciplina de release à sua volta.", "Guia do produto", FAQ_LINKS["product"]),
            faq_item("Que release do eMule devo usar para testar?", FAQ_TESTING_ANSWERS["pt_pt"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("Como mantenho o WebServer ou o REST do eMule seguros?", "O eMuleBB trata o WebServer e o REST como superfícies para controladores de confiança. Ative-os apenas quando necessário, faça bind deliberadamente, use uma API key e evite exposição ampla.", "Guia de controladores e REST", FAQ_LINKS["controllers"]),
            faq_item("Como uso o eMule com Kad e servidores?", "O eMuleBB mantém os fluxos clássicos de servidor, pesquisa global e Kad. Comece com listas de servidores de confiança, faça bootstrap do Kad deliberadamente e diagnostique Low ID ou Kad com firewall antes de mudar muitas opções.", "Guia de rede", FAQ_LINKS["network"]),
            faq_item("Como lido com grandes bibliotecas partilhadas no eMule?", "O eMuleBB foi feito para grandes bibliotecas: adicione raízes gradualmente, use Windows com long paths, reveja as regras de share-ignore e deixe a cache de arranque assentar.", "Guia de partilha", FAQ_LINKS["sharing"]),
            faq_item("Posso automatizar o eMule com ferramentas externas?", "Sim. O eMuleBB expõe uma REST API JSON autenticada para controladores locais de confiança, mantendo a semântica nativa de transferências e partilha na aplicação de ambiente de trabalho.", "Guia de controladores e REST", FAQ_LINKS["controllers"]),
        ],
    },
    "tr": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "binding, paylaşım, yükleme yuvaları, Kad, REST ve 0.7.3 testleri için eMuleBB'yi denemek isteyen eMule kullanıcılarına kısa yanıtlar.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "eMule kullanıcıları için hızlı eMuleBB yanıtları.",
        "nav_label": "SSS gezinmesi",
        "eyebrow": "SSS",
        "h1": "eMuleBB için yanıtlanan yaygın eMule soruları",
        "lead": "Klasik eMule iş akışını daha iyi geniş bant denetimi, daha güvenli ağ ve daha net sürüm kanıtıyla isteyen kullanıcılara kısa yanıtlar.",
        "home_label": "Ana sayfa",
        "docs_label": "Dokümanlar",
        "faq_label": "SSS",
        "github_label": "GitHub",
        "languages_label": "Diller",
        "read_more": "Daha fazla oku",
        "items": [
            faq_item("eMule'yi bir arabirime veya VPN'e nasıl bind ederim?", "eMuleBB, P2P trafiğini adlandırılmış bir arabirime veya yerel adrese bind edebilir ve hedef yoksa başlatmayı engelleyebilir. VPN kill switch'inizi, güvenlik duvarınızı ve WebServer/REST bind politikanızı ayrı tutun.", "Ağ kılavuzu", FAQ_LINKS["network"]),
            faq_item("eMule'de kütüphanemi nasıl paylaşırım?", "eMuleBB tanıdık Shared Files modelini korur: özenle seçilmiş kökler ekleyin, Temp'i paylaşımların dışında tutun, kararlı yollar kullanın ve büyütmeden önce hashing'in bitmesini bekleyin.", "Paylaşım kılavuzu", FAQ_LINKS["sharing"]),
            faq_item("eMule'de yükleme yuvalarını nasıl sınırlandırırım?", "eMuleBB, sınırlı bir geniş bant yükleme yuvası hedefi, zayıf yuva geri dönüşümü ve pratik tanılama ekler; böylece hızlı hatlar kuyruğu boğmadan yararlı kalır.", "İndirme ve arama kılavuzu", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB, eMule'nin bir protokol fork'u mu?", "Hayır. eMuleBB stok uyumlu eD2K ve Kad davranışını varsayılan olarak korur, ardından çevresindeki yerel sınırları, otomasyonu, tanılamayı ve sürüm disiplinini geliştirir.", "Ürün kılavuzu", FAQ_LINKS["product"]),
            faq_item("Test için hangi eMule sürümünü kullanmalıyım?", FAQ_TESTING_ANSWERS["tr"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("eMule WebServer veya REST'i nasıl güvende tutarım?", "eMuleBB, WebServer ve REST'i güvenilir denetleyici yüzeyleri olarak ele alır. Yalnızca gerektiğinde etkinleştirin, bilinçli bind yapın, bir API key kullanın ve geniş erişimden kaçının.", "Denetleyiciler ve REST kılavuzu", FAQ_LINKS["controllers"]),
            faq_item("eMule'yi Kad ve sunucularla nasıl kullanırım?", "eMuleBB klasik sunucu, küresel ve Kad arama iş akışlarını korur. Güvenilir sunucu listeleriyle başlayın, Kad'ı bilinçli olarak bootstrap edin ve çok ayar değiştirmeden önce Low ID veya güvenlik duvarı arkasındaki Kad'ı teşhis edin.", "Ağ kılavuzu", FAQ_LINKS["network"]),
            faq_item("eMule'de büyük paylaşılan kütüphaneleri nasıl yönetirim?", "eMuleBB büyük kütüphaneler için yapılmıştır: kökleri kademeli ekleyin, uzun yol destekli Windows kurulumları kullanın, share-ignore kurallarını gözden geçirin ve başlangıç önbelleğinin yerleşmesini bekleyin.", "Paylaşım kılavuzu", FAQ_LINKS["sharing"]),
            faq_item("eMule'yi harici araçlarla otomatikleştirebilir miyim?", "Evet. eMuleBB, güvenilir yerel denetleyiciler için kimliği doğrulanmış bir JSON REST API sunarken aktarım ve paylaşımın yerel semantiğini masaüstü uygulamasında tutar.", "Denetleyiciler ve REST kılavuzu", FAQ_LINKS["controllers"]),
        ],
    },
    "ko": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "binding, 공유, 업로드 슬롯, Kad, REST, 0.7.3 테스트를 위해 eMuleBB를 사용해 보려는 eMule 사용자를 위한 짧은 답변.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "eMule 사용자를 위한 빠른 eMuleBB 답변.",
        "nav_label": "FAQ 내비게이션",
        "eyebrow": "FAQ",
        "h1": "eMuleBB를 위해 답한 일반적인 eMule 질문",
        "lead": "더 나은 광대역 제어, 더 안전한 네트워킹, 더 명확한 릴리스 증거와 함께 클래식한 eMule 워크플로를 원하는 사용자를 위한 짧은 답변.",
        "home_label": "홈",
        "docs_label": "문서",
        "faq_label": "FAQ",
        "github_label": "GitHub",
        "languages_label": "언어",
        "read_more": "더 읽기",
        "items": [
            faq_item("eMule을 인터페이스나 VPN에 어떻게 bind하나요?", "eMuleBB는 P2P 트래픽을 지정된 인터페이스나 로컬 주소에 bind할 수 있고, 대상이 없으면 시작을 막을 수 있습니다. VPN 킬 스위치, 방화벽, WebServer/REST bind 정책은 따로 유지하세요.", "네트워크 가이드", FAQ_LINKS["network"]),
            faq_item("eMule에서 라이브러리를 어떻게 공유하나요?", "eMuleBB는 익숙한 Shared Files 모델을 유지합니다. 정리된 루트를 추가하고, Temp는 공유에서 빼고, 안정적인 경로를 사용하며, 규모를 키우기 전에 hashing이 끝나게 두세요.", "공유 가이드", FAQ_LINKS["sharing"]),
            faq_item("eMule에서 업로드 슬롯을 어떻게 제한하나요?", "eMuleBB는 한정된 광대역 업로드 슬롯 목표, 약한 슬롯 재활용, 실용적인 진단을 추가하여 빠른 회선이 큐를 넘치게 하지 않으면서 유용하게 유지되도록 합니다.", "다운로드 및 검색 가이드", FAQ_LINKS["downloads"]),
            faq_item("eMuleBB는 eMule의 프로토콜 포크인가요?", "아니요. eMuleBB는 스톡 호환 eD2K 및 Kad 동작을 기본으로 유지하고, 그 주위에서 로컬 한계, 자동화, 진단, 릴리스 규율을 개선합니다.", "제품 가이드", FAQ_LINKS["product"]),
            faq_item("테스트에는 어떤 eMule 릴리스를 사용해야 하나요?", FAQ_TESTING_ANSWERS["ko"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("eMule WebServer나 REST를 어떻게 안전하게 유지하나요?", "eMuleBB는 WebServer와 REST를 신뢰된 컨트롤러 표면으로 다룹니다. 필요할 때만 활성화하고, 의도적으로 bind하고, API key를 사용하며, 광범위한 노출을 피하세요.", "컨트롤러 및 REST 가이드", FAQ_LINKS["controllers"]),
            faq_item("eMule을 Kad 및 서버와 함께 어떻게 사용하나요?", "eMuleBB는 클래식한 서버, 글로벌, Kad 검색 워크플로를 유지합니다. 신뢰할 수 있는 서버 목록으로 시작하고, Kad를 의도적으로 bootstrap하며, 많은 설정을 바꾸기 전에 Low ID나 방화벽 뒤의 Kad를 진단하세요.", "네트워크 가이드", FAQ_LINKS["network"]),
            faq_item("eMule에서 큰 공유 라이브러리를 어떻게 다루나요?", "eMuleBB는 큰 라이브러리를 위해 만들어졌습니다. 루트를 점진적으로 추가하고, 긴 경로를 지원하는 Windows 설정을 사용하고, share-ignore 규칙을 검토하며, 시작 캐시 작업이 안정되게 두세요.", "공유 가이드", FAQ_LINKS["sharing"]),
            faq_item("외부 도구로 eMule을 자동화할 수 있나요?", "네. eMuleBB는 신뢰된 로컬 컨트롤러를 위한 인증된 JSON REST API를 제공하면서 전송과 공유의 네이티브 시맨틱을 데스크톱 앱에 유지합니다.", "컨트롤러 및 REST 가이드", FAQ_LINKS["controllers"]),
        ],
    },
    "ar_ae": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "إجابات قصيرة لمستخدمي eMule الراغبين في تجربة eMuleBB من أجل binding والمشاركة وخانات الرفع وKad وREST واختبارات 0.7.3.",
        "og_title": "FAQ | eMule broadband edition",
        "og_description": "إجابات eMuleBB سريعة لمستخدمي eMule.",
        "nav_label": "تنقل الأسئلة الشائعة",
        "eyebrow": "الأسئلة الشائعة",
        "h1": "أسئلة eMule الشائعة، مُجابة لأجل eMuleBB",
        "lead": "إجابات قصيرة لمن يريد سير عمل eMule الكلاسيكي مع تحكم أفضل في النطاق العريض وشبكة أكثر أمانًا وأدلة إصدار أوضح.",
        "home_label": "الرئيسية",
        "docs_label": "الوثائق",
        "faq_label": "الأسئلة الشائعة",
        "github_label": "GitHub",
        "languages_label": "اللغات",
        "read_more": "اقرأ المزيد",
        "items": [
            faq_item("كيف أربط eMule بواجهة أو VPN؟", "يستطيع eMuleBB ربط حركة P2P بواجهة مُسمّاة أو عنوان محلي، ويمكنه منع بدء التشغيل عند غياب الهدف. أبقِ مفتاح إيقاف VPN وجدار الحماية وسياسة ربط WebServer/REST منفصلة.", "دليل الشبكة", FAQ_LINKS["network"]),
            faq_item("كيف أشارك مكتبتي في eMule؟", "يحافظ eMuleBB على نموذج Shared Files المألوف: أضف جذورًا منسّقة، وأبقِ Temp خارج المشاركات، واستخدم مسارات ثابتة، ودع الـ hashing ينتهي قبل التوسّع.", "دليل المشاركة", FAQ_LINKS["sharing"]),
            faq_item("كيف أحدّ من خانات الرفع في eMule؟", "يضيف eMuleBB هدفًا محدودًا لخانات الرفع عريض النطاق، وإعادة تدوير الخانات الضعيفة، وتشخيصًا عمليًا حتى تبقى الخطوط السريعة مفيدة دون إغراق الطابور.", "دليل التنزيل والبحث", FAQ_LINKS["downloads"]),
            faq_item("هل eMuleBB تفرّع بروتوكول من eMule؟", "لا. يحافظ eMuleBB على سلوك eD2K وKad المتوافق مع الأصل افتراضيًا، ثم يحسّن الحدود المحلية والأتمتة والتشخيص وانضباط الإصدار حوله.", "دليل المنتج", FAQ_LINKS["product"]),
            faq_item("أي إصدار eMule يجب أن أستخدم للاختبار؟", FAQ_TESTING_ANSWERS["ar_ae"], "eMuleBB Rust releases", RUST_RELEASES_URL),
            faq_item("كيف أبقي WebServer أو REST في eMule آمنًا؟", "يتعامل eMuleBB مع WebServer وREST كأسطح لمتحكمات موثوقة. فعّلها عند الحاجة فقط، واربط عن قصد، واستخدم مفتاح API، وتجنّب الكشف الواسع.", "دليل المتحكمات وREST", FAQ_LINKS["controllers"]),
            faq_item("كيف أستخدم eMule مع Kad والخوادم؟", "يحافظ eMuleBB على سير عمل البحث عبر الخادم والبحث العام وKad. ابدأ بقوائم خوادم موثوقة، وقم بـ bootstrap لـ Kad عن قصد، وشخّص Low ID أو Kad خلف جدار الحماية قبل تغيير إعدادات كثيرة.", "دليل الشبكة", FAQ_LINKS["network"]),
            faq_item("كيف أتعامل مع المكتبات المشتركة الكبيرة في eMule؟", "صُمِّم eMuleBB للمكتبات الكبيرة: أضف الجذور تدريجيًا، واستخدم إعدادات Windows داعمة للمسارات الطويلة، وراجع قواعد share-ignore، ودع عمل ذاكرة بدء التشغيل يستقر.", "دليل المشاركة", FAQ_LINKS["sharing"]),
            faq_item("هل يمكنني أتمتة eMule بأدوات خارجية؟", "نعم. يعرض eMuleBB واجهة JSON REST API مصادَقًا عليها للمتحكمات المحلية الموثوقة مع إبقاء دلالات النقل والمشاركة الأصلية في تطبيق سطح المكتب.", "دليل المتحكمات وREST", FAQ_LINKS["controllers"]),
        ],
    },
}


def load_localized_copy(root: Path) -> dict[str, dict[str, Any]]:
    """Load fully curated localized page copy from structured JSON."""

    path = root / LOCALIZED_COPY_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def load_public_presence_contract(path: Path) -> dict[str, Any]:
    """Load the validated public-presence contract needed by the site renderer."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"unsupported public-presence contract: {path}")
    for key in ("release_channels", "repositories", "compatibility_references"):
        records = payload.get(key)
        if not isinstance(records, list) or not records or not all(isinstance(record, dict) for record in records):
            raise ValueError(f"public-presence contract field {key!r} must be a non-empty object array")
    if not isinstance(payload.get("installer"), dict) or not isinstance(payload.get("historical_bundle_note"), str):
        raise ValueError("public-presence contract must define installer and historical_bundle_note")
    return payload


def rust_product(contract: dict[str, Any]) -> dict[str, str]:
    """Return the Rust product record, with a schema-v1 transition fallback."""

    required = (
        "key",
        "repository_key",
        "display_name",
        "lifecycle_label",
        "published_version",
        "development_target",
        "development_eta",
        "testing_summary",
        "nightly_url",
        "release_url",
        "docs_url",
        "issues_url",
    )
    products = contract.get("products")
    if products is not None:
        if not isinstance(products, list) or not products or not all(
            isinstance(record, dict) for record in products
        ):
            raise ValueError("public-presence contract field 'products' must be a non-empty object array")
        product = next(
            (record for record in products if record.get("key") == "emulebb-rust"),
            None,
        )
        if product is None:
            raise ValueError("public-presence contract must define the emulebb-rust product")
        missing = [key for key in required if not isinstance(product.get(key), str) or not product[key].strip()]
        if missing:
            raise ValueError(f"emulebb-rust product is missing required fields: {', '.join(missing)}")
        return product

    channel = next(
        channel for channel in contract["release_channels"] if channel["key"] == "rust-nightly"
    )
    return {
        "key": "emulebb-rust",
        "repository_key": "emulebb-rust",
        "display_name": "eMuleBB Rust",
        "lifecycle_label": "Active beta",
        "published_version": "0.1.0-beta.2",
        "development_target": "Beta 3",
        "development_eta": "Beta 3 is expected after a few more weeks of implementation and stabilization.",
        "testing_summary": "Repeatedly tested on live eD2K/Kad networks.",
        "nightly_url": channel["download_url"],
        "release_url": f"{RUST_REPOSITORY_URL}/releases/tag/rust-v0.1.0-beta.2",
        "docs_url": f"{DOCS_SITE_URL}/products/emulebb-rust/",
        "issues_url": f"{RUST_REPOSITORY_URL}/issues",
    }


def public_repository_links(contract: dict[str, Any]) -> list[dict[str, str]]:
    """Return current repository and compatibility cards from the shared contract."""

    records = [*contract["repositories"], *contract["compatibility_references"]]
    return [
        {"href": record["url"], "title": record["name"], "text": record["role"]}
        for record in records
    ]


def make_evergreen_locale_content(record: dict[str, Any]) -> dict[str, Any]:
    """Build one focused translated homepage without release-cycle copy."""

    summary = record["summary"]
    return {
        "title": record["title"],
        "meta_description": summary,
        "og_title": record["title"],
        "og_description": summary,
        "structured_description": summary,
        "nav_label": record["nav_label"],
        "project_links_label": record["product_summary_label"],
        "product_summary_label": record["product_summary_label"],
        "footer_links_label": record["footer_links_label"],
        "nav": [{"label": label} for label in record["nav"]],
        "intro": summary,
        "why": {
            **s(record["nav"][0], "eMuleBB", summary),
            "cards": [c("eD2K · Kad", "eMuleBB", summary)],
        },
    }


def apply_localized_copy(root: Path) -> None:
    """Merge frozen evergreen locale records into the render tables."""

    for key, record in load_localized_copy(root).items():
        CONTENT[key] = make_evergreen_locale_content(record)
        DOC_SECTION_COPY[key] = tuple(record["doc_section"])
        MENU_COPY[key] = record["menu"]
        LANGUAGE_LINK_COPY[key] = record["language_link"]


def load_stock_locale_text(root: Path) -> dict[str, dict[str, Any]]:
    """Load stock-language page copy from structured JSON."""

    path = root / STOCK_LOCALE_TEXT_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def make_stock_locale_content(t: dict[str, Any]) -> dict[str, Any]:
    """Build minimal evergreen homepage copy from one stock-language record."""

    record = {
        "title": t["title"],
        "summary": t["intro"],
        "nav_label": t["open"],
        "product_summary_label": "eMuleBB",
        "footer_links_label": t["lang"],
        "nav": [t["nav"][0], t["nav"][1], t["nav"][2], t["nav"][3], t["nav"][5], t["nav"][6]],
        "doc_section": [t["nav"][3], t["docs"]],
    }
    return make_evergreen_locale_content(record)


def ensure_stock_locale_content(root: Path) -> None:
    """Merge JSON-backed stock-language content into the render tables."""

    apply_localized_copy(root)
    stock_text = load_stock_locale_text(root)
    page_keys = {page.key for page in PAGES}
    missing = (page_keys - set(CONTENT)) - set(stock_text)
    extra = set(stock_text) - page_keys
    if missing or extra:
        raise SystemExit(f"stock locale JSON mismatch; missing={sorted(missing)}, extra={sorted(extra)}")

    for key, text in stock_text.items():
        CONTENT[key] = make_stock_locale_content(text)
        DOC_SECTION_COPY[key] = (text["nav"][3], text["docs"])
        MENU_COPY[key] = {"label": text["menu"], "open_label": text["open"], "close_label": text["close"]}
        LANGUAGE_LINK_COPY[key] = text["lang"]


def apply_faq_product_copy() -> None:
    """Normalize current product-lane metadata across localized FAQ copy."""

    for key, faq in FAQ_CONTENT.items():
        faq["meta_description"] = FAQ_TESTING_ANSWERS[key]


def prepare_focused_content(root: Path, contract: dict[str, Any]) -> None:
    """Build the four-block homepage content for every supported locale."""

    ensure_stock_locale_content(root)
    apply_faq_product_copy()
    product = rust_product(contract)
    channels = {channel["key"]: channel for channel in contract["release_channels"]}
    rust_channel = channels["rust-nightly"]
    mfc_channel = channels["mfc-stable"]
    repositories = {repository["key"]: repository for repository in contract["repositories"]}

    for page in PAGES:
        content = CONTENT[page.key]
        content["menu"] = MENU_COPY[page.key]
        content["languages_link_label"] = LANGUAGE_LINK_COPY[page.key]
        content["product_docs_url"] = product["docs_url"]
        faq_href = FAQ_PAGE_BY_KEY.get(page.key, ENGLISH_FAQ_PAGE).url

        if page.key == "en":
            content.update(
                {
                    "title": "eMuleBB Rust | eD2K/Kad client for search, transfers, and sharing",
                    "meta_description": (
                        "eMuleBB Rust is a cross-platform eD2K/Kad client for search, "
                        "downloads, uploads, sharing, seeding, and API-driven operation."
                    ),
                    "og_title": "eMuleBB Rust | Cross-platform eD2K/Kad client",
                    "og_description": (
                        "Search, transfer, share, and seed on eD2K/Kad through a headless "
                        "Rust client with an embedded browser console and REST API."
                    ),
                    "structured_description": (
                        f"{product['display_name']} is a cross-platform eD2K/Kad client for "
                        "search, downloads, uploads, sharing, seeding, and API-driven operation. "
                        f"{product['testing_summary']}"
                    ),
                    "nav": [
                        {"href": product["nightly_url"], "label": "Nightlies", "class": "nav-download"},
                        {"id": "proof", "label": "Capabilities"},
                        {"id": "docs", "label": "Docs"},
                        {"id": "repos", "label": "Repositories"},
                        {"href": faq_href, "label": "FAQ"},
                    ],
                    "hero": {
                        "eyebrow": product["lifecycle_label"],
                        "h1": "eMuleBB Rust is an eD2K/Kad client for search, downloads, uploads, sharing, and seeding.",
                        "lead": (
                            "Run the cross-platform headless daemon through its embedded browser "
                            "operations console or authenticated REST API. Stock-compatible wire "
                            "behavior and a Rust async core support broadband links and large libraries."
                        ),
                        "install": "Get Rust nightlies",
                        "primary_href": product["nightly_url"],
                        "source": "MFC stable release",
                        "secondary_href": mfc_channel["download_url"],
                        "panel_kicker": "Current posture",
                        "panel_h2": "Active beta, moving toward Beta 3",
                        "panel_p": (
                            f"Rust is the active product lane. {product['development_eta']} "
                            "The MFC client remains available as the maintained Windows line."
                        ),
                        "signals": [
                            "Tested for months on live eD2K/Kad networks",
                            "CI-gated Windows, Linux, and macOS packages",
                            "SHA-256 checksums and provenance",
                        ],
                    },
                    "proof": {
                        **s("What eMuleBB Rust does", "The focused eD2K/Kad client surface"),
                        "cards": [
                            c(
                                "Search and download",
                                "Find sources and manage durable transfers",
                                "Search eD2K servers and Kad, discover sources, and manage long-running downloads.",
                            ),
                            c(
                                "Share and seed",
                                "Upload from user-owned libraries",
                                "Share files, serve upload queues, and keep completed content available to the network.",
                            ),
                            c(
                                "Operate and automate",
                                "Use the browser console or REST API",
                                "Monitor and control the headless client through the embedded WebUI and authenticated API.",
                            ),
                        ],
                    },
                    "docs": {
                        **s("Essentials", "Downloads, documentation, issues, and contribution"),
                        "links": [
                            {
                                "href": product["nightly_url"],
                                "title": "GitHub Releases",
                                "text": "Choose the newest dated Rust nightly for current testing.",
                            },
                            {
                                "href": product["docs_url"],
                                "title": "Rust product docs",
                                "text": "Architecture, operation, validation, and product direction.",
                            },
                            {
                                "href": product["issues_url"],
                                "title": "Issues",
                                "text": "Report reproducible client, package, or network problems.",
                            },
                            {
                                "href": rust_channel["contributing_url"],
                                "title": "Contributing",
                                "text": "Code, tests, documentation, and validation contributions are welcome.",
                            },
                        ],
                    },
                    "repos": {
                        **s("Repositories", "The focused public project surface"),
                        "links": [
                            {
                                "href": repositories[key]["url"],
                                "title": repositories[key]["name"],
                                "text": repositories[key]["role"],
                            }
                            for key in ("emulebb-rust", "emulebb", "emulebb-tooling")
                        ],
                    },
                }
            )
            continue

        summary = content["intro"]
        nav_labels = [item["label"] for item in content["nav"]]
        content["meta_description"] = summary
        content["og_description"] = summary
        content["structured_description"] = summary
        content["nav"] = [
            {"href": product["nightly_url"], "label": nav_labels[2], "class": "nav-download"},
            {"id": "proof", "label": nav_labels[0]},
            {"id": "docs", "label": nav_labels[3]},
            {"id": "repos", "label": nav_labels[-1]},
            {"href": faq_href, "label": "FAQ"},
        ]
        content["hero"] = {
            "eyebrow": "eMuleBB",
            "h1": "eMuleBB Rust",
            "lead": summary,
            "install": "GitHub Releases",
            "primary_href": product["nightly_url"],
            "source": "eMuleBB Rust docs",
            "secondary_href": product["docs_url"],
            "panel_kicker": content["product_summary_label"],
            "panel_h2": "eD2K · Kad",
            "panel_p": summary,
            "signals": ["eD2K", "Kad", "GitHub"],
        }
        content["proof"] = content["why"]
        content["docs"] = {
            **s(*DOC_SECTION_COPY[page.key]),
            "links": [
                {"href": product["nightly_url"], "title": "GitHub Releases", "text": summary},
                {"href": product["docs_url"], "title": "eMuleBB Rust docs", "text": summary},
            ],
        }
        content["repos"] = {
            **s(nav_labels[-1], "eMuleBB"),
            "links": [
                {"href": RUST_REPOSITORY_URL, "title": "emulebb-rust", "text": "eD2K · Kad"},
                {"href": "https://github.com/emulebb", "title": "eMuleBB", "text": "GitHub"},
            ],
        }
        serialized = json.dumps(content, ensure_ascii=False)
        if LOCALIZED_DYNAMIC_RELEASE_PATTERN.search(serialized):
            raise SystemExit(f"localized homepage {page.key!r} contains release-cycle copy")


def to_namespace(value: Any) -> Any:
    """Recursively convert dictionaries so templates can use attribute access."""

    if isinstance(value, dict):
        return SimpleNamespace(**{key: to_namespace(item) for key, item in value.items()})
    if isinstance(value, list):
        return [to_namespace(item) for item in value]
    return value


def alternates() -> list[dict[str, str]]:
    """Return reciprocal hreflang alternates for generated pages."""

    result = [{"hreflang": page.hreflang, "url": page.url} for page in PAGES]
    result.append({"hreflang": "x-default", "url": f"{SITE_BASE_URL}/"})
    return result


def faq_alternates() -> list[dict[str, str]]:
    """Return reciprocal hreflang alternates for FAQ pages."""

    result = [{"hreflang": page.hreflang, "url": page.url} for page in FAQ_PAGES]
    result.append({"hreflang": "x-default", "url": ENGLISH_FAQ_PAGE.url})
    return result


def relative_prefix(page: PageSpec) -> str:
    """Return the relative prefix from a generated page to the site root."""

    if not page.directory:
        return ""
    return "../" * len(page.directory.split("/"))


def relative_page_href(source: PageSpec, target: PageSpec) -> str:
    """Return a relative URL from one generated page to another page."""

    source_directory = source.directory or "."
    target_directory = target.directory or "."
    relative = posixpath.relpath(target_directory, source_directory)
    return "./" if relative == "." else f"{relative}/"


def language_groups() -> list[dict[str, Any]]:
    """Return grouped language links for the selector page."""

    by_key = {page.key: page for page in PAGES}
    groups = []
    for label, keys in LANGUAGE_GROUPS:
        groups.append(
            {
                "label": label,
                "links": [
                    {
                        "href": relative_page_href(LANGUAGE_PAGE, by_key[key]),
                        "label": by_key[key].language_label,
                        "hreflang": by_key[key].hreflang,
                    }
                    for key in keys
                ],
            }
        )
    return groups


def environment(root: Path) -> Environment:
    """Create the Jinja2 environment for site rendering."""

    return Environment(
        loader=FileSystemLoader(root / "templates"),
        autoescape=select_autoescape(("html", "j2")),
        trim_blocks=False,
        lstrip_blocks=False,
    )


def render_rust_redirect() -> str:
    """Render the no-index compatibility redirect for the retired Rust URL."""

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1" name="viewport"/>
<meta content="noindex,follow" name="robots"/>
<meta content="0; url=../" http-equiv="refresh"/>
<link href="https://emulebb.github.io/" rel="canonical"/>
<title>eMuleBB Rust moved</title>
</head>
<body>
<p>eMuleBB Rust is now presented on the <a href="../">eMuleBB homepage</a>.</p>
</body>
</html>
"""


def render_sitemap(lastmod: str) -> str:
    """Render sitemap.xml from the canonical page table."""

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for page in (*PAGES, LANGUAGE_PAGE, *FAQ_PAGES):
        lines.extend(
            [
                "  <url>",
                f"    <loc>{page.url}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "    <changefreq>weekly</changefreq>",
                f"    <priority>{page.priority}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def render_outputs(root: Path, lastmod: str, contract: dict[str, Any]) -> dict[Path, str]:
    """Render every generated file into an in-memory path map."""

    prepare_focused_content(root, contract)
    env = environment(root)
    home = env.get_template("home.html.j2")
    languages = env.get_template("languages.html.j2")
    faq = env.get_template("faq.html.j2")
    alt = alternates()
    faq_alt = faq_alternates()
    home_pages = {page.key: page for page in PAGES}
    outputs: dict[Path, str] = {}
    for page in PAGES:
        outputs[page.output_path] = home.render(
            site_base_url=SITE_BASE_URL,
            pico_cdn=PICO_CDN,
            ga_measurement_id=GA_MEASUREMENT_ID,
            page=page,
            content=to_namespace(CONTENT[page.key]),
            alternates=alt,
            language_href=relative_page_href(page, LANGUAGE_PAGE),
        )
    for page in FAQ_PAGES:
        content = dict(FAQ_CONTENT[page.key])
        content["menu"] = MENU_COPY.get(page.key, MENU_COPY["en"])
        home_page = home_pages[page.key]
        nav = [
            {"href": home_page.url, "label": content["home_label"]},
            {"href": RUST_RELEASES_URL, "label": "Rust releases"},
            {"href": page.url, "label": content["faq_label"]},
            {"href": DOCS_SITE_URL + "/", "label": content["docs_label"]},
            {"href": f"{SITE_BASE_URL}/languages/", "label": content["languages_label"]},
            {"href": "https://github.com/emulebb", "label": content["github_label"]},
        ]
        outputs[page.output_path] = faq.render(
            site_base_url=SITE_BASE_URL,
            pico_cdn=PICO_CDN,
            ga_measurement_id=GA_MEASUREMENT_ID,
            page=page,
            content=to_namespace(content),
            alternates=faq_alt,
            nav=to_namespace(nav),
        )
    outputs[RUST_REDIRECT_PATH] = render_rust_redirect()
    outputs[LANGUAGE_PAGE.output_path] = languages.render(
        site_base_url=SITE_BASE_URL,
        pico_cdn=PICO_CDN,
        ga_measurement_id=GA_MEASUREMENT_ID,
        page=LANGUAGE_PAGE,
        alternates=alt,
        groups=language_groups(),
    )
    outputs[Path("sitemap.xml")] = render_sitemap(lastmod)
    return outputs


def write_outputs(root: Path, outputs: dict[Path, str], check: bool) -> int:
    """Write rendered files or fail when generated output differs."""

    failures = 0
    for relative, rendered in outputs.items():
        path = root / relative
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == rendered:
            continue
        if check:
            failures += 1
            print(f"{relative} is out of date", file=sys.stderr)
            diff = difflib.unified_diff(
                current.splitlines(),
                rendered.splitlines(),
                fromfile=f"{relative} (current)",
                tofile=f"{relative} (rendered)",
                lineterm="",
            )
            for line in list(diff)[:120]:
                print(line, file=sys.stderr)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"rendered {relative}")
    return 1 if failures else 0


def prepare_staging_root(source_root: Path, output_root: Path) -> None:
    """Create a clean staging directory below the repository-local .local tree."""

    allowed_root = (source_root / ".local").resolve()
    resolved_output = output_root.resolve()
    if resolved_output == allowed_root or not resolved_output.is_relative_to(allowed_root):
        raise ValueError(f"--output-root must be a child of {allowed_root}")
    if resolved_output.exists():
        shutil.rmtree(resolved_output)
    resolved_output.mkdir(parents=True)


def copy_static_site_files(source_root: Path, output_root: Path) -> None:
    """Copy the bounded non-generated public files into a staged site artifact."""

    for relative_path in STATIC_SITE_PATHS:
        source = source_root / relative_path
        destination = output_root / relative_path
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def parse_args() -> argparse.Namespace:
    """Parse render command arguments."""

    parser = argparse.ArgumentParser(description="Render the eMuleBB static pages.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, default=DEFAULT_PUBLIC_PRESENCE_CONTRACT)
    parser.add_argument("--output-root", type=Path, help="Stage a clean deployable site below ROOT/.local.")
    parser.add_argument("--lastmod", default=dt.date.today().isoformat())
    parser.add_argument("--check", action="store_true", help="Fail if generated files differ.")
    return parser.parse_args()


def main() -> int:
    """Render or check the generated static pages."""

    args = parse_args()
    try:
        dt.date.fromisoformat(args.lastmod)
    except ValueError as exc:
        raise SystemExit(f"--lastmod must be an ISO date, got {args.lastmod!r}") from exc
    root = args.root.resolve()
    try:
        contract = load_public_presence_contract(args.contract.resolve())
        if args.output_root and args.check:
            raise ValueError("--check and --output-root cannot be combined")
        output_root = root
        if args.output_root:
            output_root = args.output_root if args.output_root.is_absolute() else root / args.output_root
            output_root = output_root.resolve()
            prepare_staging_root(root, output_root)
            copy_static_site_files(root, output_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"render error: {exc}", file=sys.stderr)
        return 1
    outputs = render_outputs(root, args.lastmod, contract)
    return write_outputs(output_root, outputs, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
