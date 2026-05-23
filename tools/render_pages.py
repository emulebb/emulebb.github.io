#!/usr/bin/env python3
"""Render the static eMuleBB pages from Jinja2 templates and structured copy."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
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
        if self.directory:
            return "../styles.css"
        return "styles.css"


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

DOCS = [
    (f"{DOCS_SITE_URL}/reference/GUIDE-EMULEBB/", "emulebb"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-SETUP/", "setup"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-NETWORK/", "network"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-SHARING/", "sharing"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-DOWNLOADS-SEARCH/", "downloads"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-CONTROLLERS-REST/", "controllers"),
    (f"{DOCS_SITE_URL}/rest/REST-API-CONTRACT/", "rest_contract"),
    (f"{DOCS_SITE_URL}/rest/REST-API-ADAPTERS/", "rest_adapters"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-TROUBLESHOOTING/", "troubleshooting"),
    (f"{DOCS_SITE_URL}/active/RELEASE-0.7.3/", "release"),
]

REPOS = [
    ("https://github.com/emulebb/emulebb", "emule"),
    ("https://github.com/emulebb/emulebb-setup", "setup"),
    ("https://github.com/emulebb/emulebb-build", "build"),
    ("https://github.com/emulebb/emulebb-build-tests", "tests"),
    ("https://github.com/emulebb/emulebb-tooling", "tooling"),
    ("https://github.com/emulebb/amutorrent", "amutorrent"),
    ("https://github.com/emulebb/goed2k-server", "goed2k_server"),
    ("https://github.com/emulebb/p2p-overlord-agents", "p2p_overlord_agents"),
    ("https://github.com/emulebb/p2p-overlord-be", "p2p_overlord_be"),
    ("https://github.com/emulebb/amule", "amule"),
    ("https://github.com/emulebb/emulebb-miniupnp", "miniupnpc"),
]

RELEASE_DOWNLOADS = [
    ("https://github.com/emulebb/emulebb/releases", "eMuleBB"),
    ("https://github.com/emulebb/amule/releases", "aMule"),
    ("https://github.com/emulebb/amutorrent/releases", "aMuTorrent"),
    ("https://github.com/emulebb/emulebb-miniupnp/releases", "MiniUPnP/miniupnpc"),
]

TEAM_ICONS = ["mule_upload", "kad_mule", "pack_mule"]

STOCK_LOCALE_TEXT_FILE = Path("content") / "stock-locales.json"
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
        "title": "eMuleBB home | eMule broadband edition",
        "meta_description": "eMuleBB is the home of eMule broadband edition: a modern eMule product, Windows P2P builds, controller tooling, and exploratory eD2K/Kad lab work.",
        "og_title": "eMuleBB home | eMule broadband edition",
        "og_description": "eMuleBB is its own broadband-focused eMule product and the home for Windows P2P builds, controller tooling, release proof, and exploratory eD2K/Kad engineering.",
        "structured_description": "eMuleBB is the home of eMule broadband edition, an independent broadband-focused eMule product with upload control, extensive automated testing, SBOM-backed packages, REST automation, eD2K/Kad compatibility, Windows builds for adjacent P2P tools, and exploratory P2P engineering. The first public release candidate is planned as 0.7.3-rc.1 and is not yet released.",
        "nav_label": "Primary navigation",
        "project_links_label": "Project links",
        "release_downloads_label": "Download releases",
        "product_summary_label": "eMuleBB product summary",
        "footer_links_label": "Footer links",
        "nav": [
            {"id": "why", "label": "Why"},
            {"id": "features", "label": "Features"},
            {"id": "guide", "label": "Guide"},
            {"id": "docs", "label": "Docs"},
            {"id": "automation", "label": "Automation"},
            {"id": "release", "label": "Release"},
            {"id": "repos", "label": "Repos"},
        ],
        "hero": {
            "eyebrow": "The eMuleBB home for broadband P2P",
            "h1": "eMuleBB is the broadband eMule product built by P2P people.",
            "lead": "A serious Windows eMule line for fast upload links, large shared libraries, always-on sessions, REST controller workflows, public product docs, SBOM-backed packages, and release proof deep enough for people who actually run P2P clients.",
            "source": "Source",
            "guide": "Product guide",
            "panel_kicker": "Product posture",
            "panel_h2": "eMuleBB is the product. The ecosystem is the proof lab.",
            "panel_p": "The desktop app stays stock-compatible where the network matters, while the wider eMuleBB organization builds Windows packages, controller workflows, deterministic test services, and exploratory eD2K/Kad tooling around it.",
            "signals": ["Stock eD2K/Kad compatibility", "Broadband upload slot control", "Extensive automated testing", "Rendered HTML docs", "Modern performance limits", "Authenticated JSON REST API", "0.7.3-rc.1 planned", "aMule Windows builds", "MiniUPnP Windows builds", "aMuTorrent manager fork", "goed2k lab work", "p2p-overlord Rust client"],
        },
        "intro": "This is the home of <strong>eMuleBB</strong>: <strong>eMule broadband edition</strong>, an independent product for people who still value eMule's distributed sharing model and want it operated like modern software. Around the flagship desktop app, the eMuleBB organization provides Windows builds for aMule and MiniUPnP, an aMuTorrent fork for managing eMuleBB, deterministic eD2K server work through goed2k, and exploratory headless eD2K/Kad work in the p2p-overlord suite. More is coming.",
        "why": {
            **s("Why", "P2P software earns trust by surviving real sessions", "eMuleBB is a product effort and an engineering practice: preserve a complex native Windows client with real network behavior, then surround it with modern builds, tests, documentation, automation, and release proof."),
            "cards": [
                c("Product reason", "eMuleBB is its own product", "The goal is not a cosmetic mod, a protocol fork, or a generic downloader shell. It is a broadband-focused eMule line for long sessions, rare files, deliberate seeding, and power users who still want the native desktop workflow."),
                c("Engineering reason", "Make P2P behavior inspectable", "Upload slots, timeouts, buffers, large libraries, WebServer exposure, REST control, and package evidence are made explicit so each change can be reviewed, tested, documented, and adjusted."),
                c("Ecosystem reason", "Build the tools around the client", "The same workspace discipline covers the app, controller tooling, Windows builds, deterministic eD2K services, and exploratory headless eD2K/Kad work without pretending every lab project is a stable end-user product."),
            ],
        },
        "features": {
            **s("Features", "What eMuleBB adds around the classic client", "The work is focused on operator-visible behavior: predictable upload policy, safer binding, fixed performance limits, large-library operation, local automation, and test evidence for the planned <code>0.7.3</code> release."),
            "cards": [
                c("Sharing and upload", "Broadband upload control", "Bounded slot targets, weak-slot recycling, ratio readouts, and seeding controls keep fast upload links useful without changing the eD2K upload protocol."),
                c("Network control", "Binding, NAT, and exposure policy", "Interface-aware binding, UPnP/NAT mapping validation, HTTPS, allowed-IP rules, and WebServer inheritance keep remote surfaces explicit and testable."),
                c("Performance and scale", "Modern defaults for large sessions", "Higher socket buffers, queue/source limits, file buffering, timeout defaults, recursive share sync, startup cache work, and long-path guidance target current Windows systems and large libraries."),
                c("Classic network", "eD2K and Kad stay first", "Server, global, and Kad search remain the native foundation, with Kad identity tracking, bad-node handling, cleanup, and timing work kept inside compatibility boundaries."),
                c("Automation", "REST and controller workflows", "Authenticated JSON endpoints cover transfers, searches, shared files, servers, Kad, logs, categories, uploads, statistics, preferences, and controlled shutdown from trusted local tools."),
                c("Testing and release discipline", "Evidence before public packages", "The planned <code>0.7.3-rc.1</code> candidate depends on hosted fast harness CI, native tests, REST contracts, UI/resource checks, live controller lanes, network adversity, packaging, SBOMs, and x64/ARM64 rehearsals."),
            ],
        },
        "guide": {
            **s("Product guide", "A short operating model"),
            "cards": [
                c("", "Start from known-good eMule habits", "Use trusted server lists, bootstrap Kad deliberately, keep incoming and shared directories predictable, and preserve the classic search/add/share workflow before layering automation on top."),
                c("", "Tune upload for your real link", "Set a finite upload limit, choose a realistic upload client target, and let the broadband policy favor fewer stronger slots instead of many low-rate sessions."),
                c("", "Curate large libraries", "Use long-path capable Windows setups, keep share roots clean, watch ratios, and treat rare files as deliberate publishing decisions."),
                c("", "Read claims through rendered docs", "The product guide is maintained as Markdown, rendered to public HTML, and tied to release strategy, test campaigns, CI, package, and SBOM evidence."),
                c("", "Automate only on trusted networks", "Enable WebServer/REST with an API key, bind and firewall it carefully, and use controllers that respect native eMule transfer and delete semantics."),
                c("", "Track release readiness", "Treat the public branch as active pre-release work until the planned <code>0.7.3-rc.1</code> gates, operator checks, and live E2E evidence say otherwise."),
            ],
        },
        "docs": {
            **s("Documentation", "Guides, API, and release notes", "The public documentation ties product use, REST automation, release gates, troubleshooting, and package evidence together in one place."),
            "links": [],
        },
        "automation": {
            "eyebrow": "Controller surface",
            "h2": "REST automation without replacing the desktop app",
            "p": "The broadband release track exposes a resource-oriented <code>/api/v1</code> JSON API from the existing WebServer listener. It authenticates with <code>X-API-Key</code>, serves JSON envelopes, and keeps native eMule state changes marshaled through the app.",
            "pills_label": "REST API areas",
            "pills": ["Transfers", "Searches", "Servers", "Kad", "Shared files", "Uploads", "Categories", "Logs", "Statistics", "Preferences"],
        },
        "release": {
            **s("Testing and performance proof", "Public release candidate 0.7.3-rc.1 is planned, extensively tested, SBOM-backed, and not yet released"),
            "cards": [
                c("", "Current status", "The first public release candidate target is <code>0.7.3-rc.1</code>. It is not yet released. Final proof is in progress, and public status stays tied to the active release docs."),
                c("", "Hosted fast CI", "The <a href=\"https://github.com/emulebb/emulebb-build-tests/actions/workflows/fast-harness-ci.yml\">Fast Harness CI</a> lane installs the shared Python harness and runs the default non-live, non-native pytest suite on pushes and pull requests."),
                c("", "Build and package proof", "Required proof covers workspace validation, Debug and Release x64 app builds, Release ARM64 app builds, test binaries, package generation, SBOM generation, clean-worktree checks, and recorded SHA-256 hashes."),
                c("", "Behavior proof", "Extensive test gates cover native suites, REST contract and OpenAPI drift, malformed requests, UI automation, live controller-surface E2E, full Release x64 live E2E, and network-adversity scenarios."),
                c("", "Performance proof", "Large-session performance work is described through concrete surfaces: upload-slot policy, queue/source limits, socket and file buffers, startup caches, long paths, and controller responsiveness."),
                c("", "Controller proof", "The aMuTorrent fork, Prowlarr, Radarr, Sonarr, and qBittorrent-compatible adapter lanes prove that automation works without weakening the native <code>/api/v1</code> contract."),
                c("", "Compatibility proof", "Stock eD2K/Kad behavior remains the default. Broadband, REST, and controller features are added around that compatibility goal and compared against the community baseline where useful."),
            ],
        },
        "method": {
            **s("Implementation method", "Modernize around the legacy core, then prove the result", "The implementation style is intentionally conservative. eMuleBB changes local policy, limits, diagnostics, API boundaries, and release discipline while keeping stock eD2K/Kad compatibility as the default. The wider organization uses the same discipline for Windows builds, managers, servers, and lab clients."),
            "cards": [
                c("Compatibility", "No casual protocol drift", "Kad and eD2K changes stay inside local routing, timing, validation, and control paths. Wire formats, opcodes, and native desktop workflows remain compatibility boundaries."),
                c("Limits", "Fixed, reviewable defaults", "Modern bandwidth, memory, socket, queue, startup, and timeout assumptions are expressed as explicit defaults or advanced preferences instead of hidden adaptive behavior."),
                c("REST", "Controller contracts, not screen scraping", "The authenticated JSON API follows an OpenAPI-backed contract, rejects malformed inputs, and marshals native state mutations through the app where the desktop client owns that state."),
                c("Release", "Evidence before labels", "The release process records commands, commits, logs, package paths, hashes, live evidence, performance-sensitive checks, and operator decisions so a release tag is a checked outcome."),
            ],
        },
        "repos": {**s("eMuleBB ecosystem", "Products, builds, managers, and P2P lab work"), "links": []},
        "team": {
            **s("Project lore", "The mule team behind the P2P workshop"),
            "cards": [
                c("", "Upload Mule Wrangler", "Keeps broadband upload slots from kicking the stable door down, then nudges the slow ones back into line with a very official clipboard."),
                c("", "Kad Trail Mule", "Carries bootstrap nodes, routing tables, and stubborn eD2K/Kad folklore across rough network terrain without dropping the protocol map."),
                c("", "Release Pack Mule", "Hauls packages, hashes, SBOMs, logs, live checks, and just enough attitude through the gate before anything gets called ready."),
            ],
        },
    },
}


LOCALIZED_COPY_FILE = Path("content") / "locales.json"

DOC_COPY = {'en': {'emulebb': ('eMuleBB product guide',
                    'Setup, tuning, automation, release-aware use, testing, and SBOM evidence.'),
        'setup': ('Setup guide', 'Install model, first-run profile behavior, and practical startup notes.'),
        'network': ('Network guide', 'eD2K, Kad, binding, UPnP, firewall, and connection diagnosis reference.'),
        'sharing': ('Sharing guide',
                    'Shared directories, monitored shares, large libraries, and share policy files.'),
        'downloads': ('Downloads and search guide',
                      'Search modes, result trust, categories, and power-user file workflows.'),
        'controllers': ('Controllers and REST guide',
                        'Trusted local controller usage and automation boundaries.'),
        'rest_contract': ('REST API contract',
                          'Human-readable contract for the authenticated JSON control surface.'),
        'rest_adapters': ('REST adapter contracts',
                          'qBittorrent-compatible and Torznab adapter surface for controller authors.'),
        'troubleshooting': ('Troubleshooting guide',
                            'Symptom-led checks for Low ID, network issues, sharing, and automation.'),
        'release': ('0.7.3 release dashboard',
                    'Current planned beta gates, automated test evidence, SBOM/package proof, and readiness rules.')}}


REPO_COPY = {'en': {'emule': 'flagship desktop app and product source',
        'setup': 'reproducible workspace setup',
        'build': 'build, validation, and release orchestration',
        'tests': 'native, Python, UI, REST, and live E2E tests',
        'tooling': 'roadmap, backlog, policy, audits, and reference docs',
        'amutorrent': 'fork used for eMuleBB management and controller workflows',
        'goed2k_server': 'eD2K server work for deterministic testing and ecosystem services',
        'p2p_overlord_agents': 'exploratory agents for the p2p-overlord P2P suite',
        'p2p_overlord_be': 'exploratory headless Rust eD2K/Kad client backend work',
        'amule': 'Windows build and validation track for aMule users',
        'miniupnpc': 'Windows build and validation track for MiniUPnP/miniupnpc'}}


DOC_SECTION_COPY = {'en': ('Documentation', 'Guides, API, and release notes')}


REPO_SECTION_COPY = {'en': ('eMuleBB ecosystem', 'Primary repositories')}


MENU_COPY = {'en': {'label': 'Menu', 'open_label': 'Open primary navigation', 'close_label': 'Close primary navigation'}}


LANGUAGE_LINK_COPY = {'en': 'Languages'}


def load_localized_copy(root: Path) -> dict[str, dict[str, Any]]:
    """Load fully curated localized page copy from structured JSON."""

    path = root / LOCALIZED_COPY_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def apply_localized_copy(root: Path) -> None:
    """Merge curated localized JSON records into the render tables."""

    for key, record in load_localized_copy(root).items():
        CONTENT[key] = record["content"]
        DOC_COPY[key] = record["docs"]
        REPO_COPY[key] = record["repos"]
        DOC_SECTION_COPY[key] = tuple(record["doc_section"])
        REPO_SECTION_COPY[key] = tuple(record["repo_section"])
        MENU_COPY[key] = record["menu"]
        LANGUAGE_LINK_COPY[key] = record["language_link"]


def load_stock_locale_text(root: Path) -> dict[str, dict[str, Any]]:
    """Load stock-language page copy from structured JSON."""

    path = root / STOCK_LOCALE_TEXT_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def stock_doc_copy(t: dict[str, Any]) -> dict[str, tuple[str, str]]:
    """Build localized document link labels for generated stock locales."""

    return {
        "emulebb": (t["product_guide"], t["intro"]),
        "setup": (t["guide"], t["lead"]),
        "network": (t["control"], t["lead"]),
        "sharing": (t["keep"], t["intro"]),
        "downloads": (t["features"], t["lead"]),
        "controllers": (t["automation"], t["automation"]),
        "rest_contract": ("REST API", t["automation"]),
        "rest_adapters": ("REST adapters", t["automation"]),
        "troubleshooting": (t["docs"], t["docs"]),
        "release": ("0.7.3", t["release"]),
    }


def stock_repo_copy(t: dict[str, Any]) -> dict[str, str]:
    """Build localized repository blurbs for generated stock locales."""

    return {
        "emule": t["intro"],
        "setup": t["guide"],
        "build": t["proof"],
        "tests": t["proof"],
        "tooling": t["docs"],
        "amutorrent": "aMuTorrent fork for managing eMuleBB.",
        "goed2k_server": "goed2k eD2K server work for deterministic tests and ecosystem services.",
        "p2p_overlord_agents": "Exploratory p2p-overlord agents for headless P2P workflows.",
        "p2p_overlord_be": "Exploratory Rust eD2K/Kad backend work in the p2p-overlord suite.",
        "amule": "Windows build and validation track for aMule users.",
        "miniupnpc": "Windows build and validation track for MiniUPnP/miniupnpc.",
    }


def make_stock_locale_content(t: dict[str, Any]) -> dict[str, Any]:
    """Build complete homepage copy from one stock-language JSON record."""

    nav_ids = ["why", "features", "guide", "docs", "automation", "release", "repos"]
    return {
        "title": t["title"],
        "meta_description": t["meta"],
        "og_title": t["title"],
        "og_description": t["meta"],
        "structured_description": t["meta"],
        "nav_label": t["open"],
        "project_links_label": t["repos"],
        "release_downloads_label": "Download releases",
        "product_summary_label": "eMuleBB",
        "footer_links_label": t["lang"],
        "languages_link_label": t["lang"],
        "nav": [{"id": item_id, "label": label} for item_id, label in zip(nav_ids, t["nav"])],
        "hero": {
            "eyebrow": t["features"],
            "h1": t["h1"],
            "lead": t["lead"],
            "source": t["source"],
            "guide": t["product_guide"],
            "panel_kicker": "eMuleBB",
            "panel_h2": t["method"],
            "panel_p": t["intro"],
            "signals": ["eD2K/Kad", "Upload", "Testing", "Performance", "REST API", "0.7.3"],
        },
        "intro": t["intro"],
        "why": {**s(t["nav"][0], t["why"], t["intro"]), "cards": [c("eD2K/Kad", t["keep"], t["intro"]), c("Upload", t["control"], t["lead"]), c("Release", t["proof"], t["release"])]},
        "features": {
            **s(t["nav"][1], t["features"], t["lead"]),
            "cards": [
                c("eD2K/Kad", t["keep"], t["intro"]),
                c("Upload", t["control"], t["lead"]),
                c("REST", t["automation"], f"{t['automation']} <code>/api/v1</code>, JSON, <code>X-API-Key</code>."),
                c("VPN", "VPN/interface binding", t["control"]),
                c("Kad", "Kad", t["keep"]),
                c("Testing", t["proof"], t["proof"]),
            ],
        },
        "guide": {**s(t["nav"][2], t["guide"]), "cards": [c("", t["keep"], t["intro"]), c("", t["control"], t["lead"]), c("", "Testing", t["proof"]), c("", "Performance", t["lead"]), c("", "0.7.3", t["release"]), c("", t["product_guide"], t["docs"])]},
        "docs": {**s(t["nav"][3], t["docs"]), "links": []},
        "automation": {"eyebrow": t["nav"][4], "h2": t["automation"], "p": f"{t['automation']} <code>/api/v1</code>, JSON, <code>X-API-Key</code>.", "pills_label": "REST API", "pills": ["Transfers", "Searches", "Servers", "Kad", "Shared files", "Uploads", "Logs", "Preferences"]},
        "release": {**s(t["nav"][5], t["release"]), "cards": [c("", "0.7.3", t["release"]), c("", "Fast CI", t["proof"]), c("", t["proof"], t["proof"]), c("", "Performance", t["lead"]), c("", "eD2K/Kad", t["keep"]), c("", "Status", t["release"])]},
        "method": {**s(t["method"], t["method"], t["intro"]), "cards": [c("eD2K/Kad", t["keep"], t["keep"]), c("Upload", t["control"], t["control"]), c("REST", "REST API", t["automation"]), c("Testing", t["proof"], t["release"])]},
        "repos": {**s(t["nav"][6], t["repos"]), "links": []},
        "team": {**s(t["team"], t["team"]), "cards": [c("", t["control"], t["control"]), c("", "Kad", t["keep"]), c("", t["proof"], t["proof"])]},
    }


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
        DOC_COPY[key] = stock_doc_copy(text)
        REPO_COPY[key] = stock_repo_copy(text)
        DOC_SECTION_COPY[key] = (text["nav"][3], text["docs"])
        REPO_SECTION_COPY[key] = (text["nav"][6], text["repos"])
        MENU_COPY[key] = {"label": text["menu"], "open_label": text["open"], "close_label": text["close"]}
        LANGUAGE_LINK_COPY[key] = text["lang"]


def add_release_evidence_copy(content: dict[str, Any]) -> None:
    """Add current release-evidence signals shared by all homepage locales."""

    signals = content["hero"]["signals"]
    if not any("HTML" in signal for signal in signals):
        signals.append("Rendered HTML product docs")
    if not any("SBOM" in signal for signal in signals):
        signals.append("SPDX SBOM package evidence")

    release_cards = content["release"]["cards"]
    if not any("SBOM" in card["h3"] for card in release_cards):
        release_cards.insert(
            3,
            c(
                "",
                "SPDX SBOM",
                "Release packages carry package-local <code>SBOM.spdx.json</code> plus sidecar <code>*.sbom.spdx.json</code> files, with manifest hashes that tie software contents to the exact package evidence.",
            ),
        )


def add_team_icons(content: dict[str, Any]) -> None:
    """Attach compact inline lore icons to the team cards."""

    for index, card in enumerate(content["team"]["cards"]):
        card.setdefault("icon", TEAM_ICONS[index % len(TEAM_ICONS)])


def with_generated_links(root: Path) -> None:
    """Populate repeated docs and repo link sections for every locale."""

    ensure_stock_locale_content(root)
    for page in PAGES:
        content = CONTENT[page.key]
        add_release_evidence_copy(content)
        add_team_icons(content)
        content.setdefault("release_downloads_label", CONTENT["en"]["release_downloads_label"])
        for nav_item in content["nav"]:
            if nav_item.get("id") == "docs":
                nav_item["href"] = DOCS_SITE_URL + "/"
        content["menu"] = MENU_COPY[page.key]
        content["languages_link_label"] = LANGUAGE_LINK_COPY[page.key]
        content["release_downloads"] = [
            {"href": href, "title": title}
            for href, title in RELEASE_DOWNLOADS
        ]
        content["docs"]["eyebrow"], content["docs"]["h2"] = DOC_SECTION_COPY[page.key]
        content["docs"]["links"] = [
            {"href": href, "title": DOC_COPY[page.key][key][0], "text": DOC_COPY[page.key][key][1]}
            for href, key in DOCS
        ]
        content["repos"]["eyebrow"], content["repos"]["h2"] = REPO_SECTION_COPY[page.key]
        content["repos"]["links"] = [
            {"href": href, "title": title_for_repo(key), "text": REPO_COPY[page.key].get(key, REPO_COPY["en"][key])}
            for href, key in REPOS
        ]


def title_for_repo(key: str) -> str:
    """Return the public repository display name for a repo key."""

    return {
        "emule": "emulebb",
        "setup": "emulebb-setup",
        "build": "emulebb-build",
        "tests": "emulebb-build-tests",
        "tooling": "emulebb-tooling",
        "amutorrent": "amutorrent",
        "goed2k_server": "goed2k-server",
        "p2p_overlord_agents": "p2p-overlord-agents",
        "p2p_overlord_be": "p2p-overlord-be",
        "amule": "aMule Windows builds",
        "miniupnpc": "emulebb-miniupnp",
    }[key]


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


def relative_page_href(source: PageSpec, target: PageSpec) -> str:
    """Return a relative URL from one generated page to another page."""

    prefix = "" if source.directory == "" else "../"
    if target.directory:
        return f"{prefix}{target.directory}/"
    return prefix or "./"


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


def render_sitemap(lastmod: str) -> str:
    """Render sitemap.xml from the canonical page table."""

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for page in (*PAGES, LANGUAGE_PAGE):
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


def render_outputs(root: Path, lastmod: str) -> dict[Path, str]:
    """Render every generated file into an in-memory path map."""

    with_generated_links(root)
    env = environment(root)
    home = env.get_template("home.html.j2")
    languages = env.get_template("languages.html.j2")
    alt = alternates()
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


def parse_args() -> argparse.Namespace:
    """Parse render command arguments."""

    parser = argparse.ArgumentParser(description="Render the eMuleBB static pages.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
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
    outputs = render_outputs(root, args.lastmod)
    return write_outputs(root, outputs, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
