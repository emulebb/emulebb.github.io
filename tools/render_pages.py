#!/usr/bin/env python3
"""Render the static eMuleBB pages from Jinja2 templates and structured copy."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import posixpath
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
FAQ_LOCALE_KEYS = ("en", "it", "es", "pt_br", "fr", "de", "pl", "nl", "ru", "uk", "zh_cn", "ja")
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

DOCS = [
    (f"{DOCS_SITE_URL}/reference/GUIDE-SETUP/", "setup"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-EMULEBB/", "emulebb"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-STACK-INTEGRATIONS/", "stack_integrations"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-CONTROLLERS-REST/", "controllers"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-DOWNLOADS-SEARCH/", "downloads"),
    (f"{DOCS_SITE_URL}/reference/GUIDE-P2P-OVERLORD-EMULE-AGENT/", "p2p_overlord_agent"),
    (f"{DOCS_SITE_URL}/active/RELEASE-0.7.3/", "release"),
]

REPOS = [
    ("https://github.com/emulebb/emulebb", "emule"),
    ("https://github.com/emulebb/amutorrent", "amutorrent"),
    ("https://github.com/emulebb/emulebb-build", "build"),
    ("https://github.com/emulebb/emulebb-build-tests", "tests"),
    ("https://github.com/emulebb/emulebb-tooling", "tooling"),
    ("https://github.com/emulebb/p2p-overlord-agents", "p2p_overlord_agents"),
    ("https://github.com/emulebb/p2p-overlord-be", "p2p_overlord_be"),
    ("https://github.com/emulebb/p2p-overlord-tooling", "p2p_overlord_tooling"),
    ("https://github.com/emulebb/amule", "amule"),
]

RELEASE_DOWNLOADS = [
    ("https://github.com/emulebb/emulebb/releases/tag/emulebb-v0.7.3-rc.1", "eMuleBB RC1"),
    ("https://github.com/emulebb/emulebb/releases/download/emulebb-v0.7.3-rc.1/emulebb-0.7.3-rc.1-x64.zip", "x64 ZIP"),
    ("https://github.com/emulebb/amutorrent/releases/tag/amutorrent-v3.8.5-emulebb-v0.7.3-rc.1", "aMuTorrent RC1"),
]

INSTALL_CALLOUT = {
    "id": "install",
    "eyebrow": "Download",
    "h2": "Install RC1 with one PowerShell line, or download the ZIP manually.",
    "p": "Use the full-suite bootstrapper for eMuleBB plus controller integration, or use the standalone ZIP when you only want the desktop app.",
    "command_label": "Full x64 suite",
    "command": "irm https://github.com/emulebb/emulebb/releases/download/emulebb-v0.7.3-rc.1/Bootstrap-eMuleBBSuite.ps1 | iex",
    "copy": "Copy",
    "copied": "Copied",
    "copy_error": "Select and copy",
    "standalone": "Standalone app: download the RC1 ZIP, extract it, and run <code>emulebb.exe</code>.",
    "primary": "Open RC1 release",
    "primary_href": "https://github.com/emulebb/emulebb/releases/tag/emulebb-v0.7.3-rc.1",
    "secondary": "Setup details",
    "secondary_href": f"{DOCS_SITE_URL}/reference/GUIDE-SETUP/",
}

TESTING_CALLOUT = {
    "eyebrow": "RC1 published",
    "h2": "0.7.3-rc.1 is open for testers",
    "p": "Try the published RC1 packages, keep a disposable or backed-up profile, and report crashes, freezes, package issues, controller/API problems, and real-network regressions.",
    "primary": "eMuleBB RC1",
    "primary_href": "https://github.com/emulebb/emulebb/releases/tag/emulebb-v0.7.3-rc.1",
    "secondary": "Report issues",
    "secondary_href": "https://github.com/emulebb/emulebb/issues",
}

TEAM_IMAGES = [
    {
        "file": "upload-mule.png",
        "alt": "Cartoon mule carrying an upload arrow and a clipboard.",
    },
    {
        "file": "kad-trail-mule.png",
        "alt": "Cartoon mule carrying connected Kad nodes across a trail.",
    },
    {
        "file": "release-pack-mule.png",
        "alt": "Cartoon mule hauling release packages and checks.",
    },
]
BRAND_LOGO_FILE = "emulebb-broadband-edition-logo.png"

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
        "meta_description": "eMuleBB RC1 is published: install eMule broadband edition with a PowerShell suite bootstrapper or standalone ZIP, with GitHub-built package provenance.",
        "og_title": "eMuleBB home | eMule broadband edition",
        "og_description": "eMuleBB is its own broadband-focused eMule product and the home for Windows P2P builds, controller tooling, release proof, and exploratory eD2K/Kad engineering.",
        "structured_description": "eMuleBB is the home of eMule broadband edition, an independent broadband-focused eMule product with upload control, automated testing, SBOM-backed packages, REST automation, eD2K/Kad compatibility, and out-of-the-box aMuTorrent, Prowlarr, Radarr, and Sonarr integration paths. The first public release candidate 0.7.3-rc.1 is published on GitHub Releases.",
        "nav_label": "Primary navigation",
        "project_links_label": "Project links",
        "release_downloads_label": "Download releases",
        "product_summary_label": "eMuleBB product summary",
        "footer_links_label": "Footer links",
        "nav": [
            {"id": "why", "label": "Why"},
            {"id": "features", "label": "Features"},
            {"id": "install", "label": "Download", "class": "nav-download"},
            {"id": "docs", "label": "Guide"},
            {"id": "release", "label": "Provenance"},
            {"id": "repos", "label": "Repos"},
        ],
        "hero": {
            "eyebrow": "The eMuleBB home for broadband P2P",
            "h1": "eMuleBB is the broadband eMule product built by P2P people.",
            "lead": "RC1 is published: a serious Windows eMule line for fast upload links, large shared libraries, always-on sessions, REST controller workflows, Arr integration, and GitHub-built package evidence.",
            "install": "Download RC1",
            "source": "Source",
            "guide": "Product guide",
            "panel_kicker": "Product posture",
            "panel_h2": "eMuleBB is the product. The ecosystem is the proof lab.",
            "panel_p": "The desktop app stays stock-compatible where the network matters. The RC1 suite adds local controller workflows around it without turning eMuleBB into a generic torrent shell.",
            "signals": ["0.7.3-rc.1 published", "One-line suite bootstrap", "Manual standalone ZIP", "GitHub Actions builds", "Manifest hash verification", "SPDX SBOMs", "aMuTorrent controller", "Prowlarr Torznab", "Radarr/Sonarr qBit adapter", "Stock eD2K/Kad compatibility"],
        },
        "intro": "This is the home of <strong>eMuleBB</strong>: <strong>eMule broadband edition</strong>, an independent product for people who still value eMule's distributed sharing model and want it operated like modern software. RC1 packages are published on GitHub Releases with a full-suite bootstrapper, standalone ZIPs, manifests, hashes, SBOMs, and matching aMuTorrent controller assets.",
        "why": {
            **s("Why", "P2P software earns trust by surviving real sessions", "eMuleBB is a product effort and an engineering practice: preserve a complex native Windows client with real network behavior, then surround it with modern builds, tests, documentation, automation, and release proof."),
            "cards": [
                c("Product reason", "eMuleBB is its own product", "The goal is not a cosmetic mod, a protocol fork, or a generic downloader shell. It is a broadband-focused eMule line for long sessions, rare files, deliberate seeding, and power users who still want the native desktop workflow."),
                c("Engineering reason", "Make P2P behavior inspectable", "Upload slots, timeouts, buffers, large libraries, WebServer exposure, REST control, and package evidence are made explicit so each change can be reviewed, tested, documented, and adjusted."),
                c("Ecosystem reason", "Build the tools around the client", "The same workspace discipline covers the app, controller tooling, Windows builds, deterministic eD2K services, and exploratory headless eD2K/Kad work without pretending every lab project is a stable end-user product."),
            ],
        },
        "features": {
            **s("Features", "What eMuleBB adds around the classic client", "The RC1 work is focused on operator-visible behavior: predictable upload policy, safer binding, fixed performance limits, large-library operation, local automation, and package evidence."),
            "cards": [
                c("Sharing and upload", "Broadband upload control", "Bounded slot targets, weak-slot recycling, ratio readouts, and seeding controls keep fast upload links useful without changing the eD2K upload protocol."),
                c("Network control", "Binding, NAT, and exposure policy", "Interface-aware binding, UPnP/NAT mapping validation, HTTPS, allowed-IP rules, and separate WebServer bind settings keep remote surfaces explicit and testable. Binding is not a VPN kill switch."),
                c("Performance and scale", "Modern defaults for large sessions", "Higher socket buffers, queue/source limits, file buffering, timeout defaults, recursive share sync, startup cache work, and long-path guidance target current Windows systems and large libraries."),
                c("Classic network", "eD2K and Kad stay first", "Server, global, and Kad search remain the native foundation, with Kad identity tracking, bad-node handling, cleanup, and timing work kept inside compatibility boundaries."),
                c("Automation", "REST and controller workflows", "Authenticated JSON endpoints cover transfers, searches, shared files, servers, Kad, logs, categories, uploads, statistics, preferences, and controlled shutdown from trusted local tools."),
                c("Testing and release discipline", "Evidence before labels", "<code>0.7.3-rc.1</code> is published with GitHub Actions packaging, manifests, SHA-256 evidence, SPDX SBOMs, diagnostics assets, and bootstrapper hash evidence."),
            ],
        },
        "guide": {
            **s("Guide", "Product guide, automation, and docs"),
            "cards": [
                c("", "Start with the product guide", "Run eMuleBB as eMule first: trusted servers, deliberate Kad bootstrap, predictable incoming/temp paths, and visible shared folders."),
                c("", "Use local automation", "Enable REST only for trusted controllers, then use aMuTorrent, Prowlarr, Radarr, and Sonarr through the documented adapter paths."),
                c("", "Read the evidence", "Setup, API, release, SBOM, and package details live in the rendered docs so public claims stay tied to source-controlled evidence."),
            ],
        },
        "docs": {
            **s("Guide", "Product guide, automation, and documentation", "Start with setup, then use the product and integration guides for the operating model, controller workflows, and release evidence."),
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
            **s("Security and provenance", "RC1 is built and packaged on GitHub"),
            "cards": [
                c("", "Published RC1", "<code>emulebb-v0.7.3-rc.1</code> is a GitHub prerelease with x64 and ARM64 ZIPs, diagnostics packages, manifests, SBOMs, and the suite bootstrapper."),
                c("", "Hash-checked setup", "The bootstrapper downloads release assets and verifies package hashes from the published manifests before installing."),
                c("", "Suite assets", "The matching aMuTorrent RC1 package is published separately, and the full x64 bootstrap flow resolves it automatically for controller setup."),
                c("", "Controller proof", "aMuTorrent, Prowlarr, Radarr, Sonarr, Torznab, and qBittorrent-compatible lanes are documented as local integration paths around the native <code>/api/v1</code> contract."),
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
        "install_callout": INSTALL_CALLOUT,
        "testing_callout": TESTING_CALLOUT,
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
        'tools_menu': ('Tools menu guide',
                       'Power-user actions for logs, dumps, folders, reloads, and controller setup helpers.'),
        'controllers': ('Controllers and REST guide',
                        'Trusted local controller usage and automation boundaries.'),
        'stack_integrations': ('Use aMuTorrent with eMuleBB',
                               'Task-first setup for eMuleBB, aMuTorrent, Prowlarr, Radarr, and Sonarr.'),
        'rest_contract': ('REST API contract',
                          'Human-readable contract for the authenticated JSON control surface.'),
        'rest_adapters': ('REST adapter contracts',
                          'qBittorrent-compatible and Torznab adapter surface for controller authors.'),
        'diagnostics': ('Collect diagnostics for reports',
                        'Redacted snapshots, dumps, startup traces, unsafe diagnostic REST, and metadata diagnostics.'),
        'troubleshooting': ('Troubleshooting guide',
                            'Symptom-led checks for Low ID, network issues, sharing, and automation.'),
        'p2p_overlord_agent': ('p2p-overlord eMule agent',
                               'Headless Rust Kad/eD2K agent boundary, source docs, and eMuleBB contract notes.'),
        'release': ('0.7.3 release dashboard',
                    'Current RC gates, automated test evidence, SBOM/package proof, and readiness rules.')}}


REPO_COPY = {'en': {'emule': 'flagship desktop app and product source',
        'setup': 'reproducible workspace setup',
        'build': 'build, validation, and release orchestration',
        'tests': 'native, Python, UI, REST, and live E2E tests',
        'tooling': 'roadmap, backlog, policy, audits, and reference docs',
        'amutorrent': 'fork used for eMuleBB management and controller workflows',
        'goed2k_server': 'eD2K server work for deterministic testing and ecosystem services',
        'p2p_overlord_agents': 'exploratory agents for the p2p-overlord P2P suite',
        'p2p_overlord_be': 'exploratory headless Rust eD2K/Kad client backend work',
        'p2p_overlord_tooling': 'scenario manifests, parity runners, reports, and quality guards',
        'amule': 'Windows build and validation track for aMule users',
        'miniupnpc': 'Windows build and validation track for MiniUPnP/miniupnpc'}}


DOC_SECTION_COPY = {'en': ('Documentation', 'Guides, API, and release notes')}


REPO_SECTION_COPY = {'en': ('eMuleBB ecosystem', 'Primary repositories')}


MENU_COPY = {'en': {'label': 'Menu', 'open_label': 'Open primary navigation', 'close_label': 'Close primary navigation'}}


LANGUAGE_LINK_COPY = {'en': 'Languages'}


FAQ_LINKS = {
    "network": f"{DOCS_SITE_URL}/reference/GUIDE-NETWORK/",
    "sharing": f"{DOCS_SITE_URL}/reference/GUIDE-SHARING/",
    "downloads": f"{DOCS_SITE_URL}/reference/GUIDE-DOWNLOADS-SEARCH/",
    "controllers": f"{DOCS_SITE_URL}/reference/GUIDE-CONTROLLERS-REST/",
    "release": f"{DOCS_SITE_URL}/active/RELEASE-0.7.3/",
    "product": f"{DOCS_SITE_URL}/reference/GUIDE-EMULEBB/",
}


def faq_item(question: str, answer: str, doc_title: str, doc_href: str) -> dict[str, str]:
    """Make a FAQ entry."""

    return {"question": question, "answer": answer, "doc_title": doc_title, "doc_href": doc_href}


FAQ_CONTENT: dict[str, dict[str, Any]] = {
    "en": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Short answers for eMule users who want to try eMuleBB for binding, sharing, upload slots, Kad, REST, and 0.7.3-rc.1 testing.",
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
            faq_item("Which eMule release should I use for testing?", "Use the published eMuleBB 0.7.3-rc.1 GitHub Release for RC testing. The stable target remains 0.7.3 after the release gates pass.", "0.7.3 release dashboard", FAQ_LINKS["release"]),
            faq_item("How do I keep eMule WebServer or REST safe?", "eMuleBB treats WebServer and REST as trusted-controller surfaces. Enable them only when needed, bind deliberately, use an API key, and avoid broad exposure.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("How do I use eMule with Kad and servers?", "eMuleBB keeps classic server, global, and Kad search workflows. Start with trusted server lists, bootstrap Kad deliberately, and diagnose Low ID or firewalled Kad before changing many settings.", "Network guide", FAQ_LINKS["network"]),
            faq_item("How do I handle large shared libraries in eMule?", "eMuleBB is built for large libraries: add roots gradually, use long-path capable Windows setups, review share-ignore rules, and let startup cache work settle.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Can I automate eMule with external tools?", "Yes. eMuleBB exposes an authenticated JSON REST API for trusted local controllers while keeping native transfer and sharing semantics in the desktop app.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
    "it": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Risposte brevi per utenti eMule che vogliono provare eMuleBB per binding, condivisione, slot di upload, Kad, REST e test 0.7.3-rc.1.",
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
            faq_item("Quale release di eMule dovrei usare per i test?", "Usa la release GitHub eMuleBB 0.7.3-rc.1 pubblicata per i test RC. Il target stabile resta 0.7.3 dopo il passaggio dei gate.", "Dashboard release 0.7.3", FAQ_LINKS["release"]),
            faq_item("Come tengo sicuri WebServer o REST di eMule?", "eMuleBB tratta WebServer e REST come superfici per controller fidati. Abilitali solo quando servono, configura il bind, usa una API key ed evita esposizione ampia.", "Guida controller e REST", FAQ_LINKS["controllers"]),
            faq_item("Come uso eMule con Kad e server?", "eMuleBB conserva server, ricerca globale e Kad. Parti da liste server fidate, avvia Kad con cura e diagnostica Low ID o Kad firewalled prima di cambiare troppe opzioni.", "Guida rete", FAQ_LINKS["network"]),
            faq_item("Come gestisco grandi librerie condivise in eMule?", "eMuleBB e pensato per grandi librerie: aggiungi radici gradualmente, usa Windows con long paths, rivedi share-ignore e lascia stabilizzare la cache di avvio.", "Guida condivisione", FAQ_LINKS["sharing"]),
            faq_item("Posso automatizzare eMule con strumenti esterni?", "Si. eMuleBB espone una REST API JSON autenticata per controller locali fidati, mantenendo semantica nativa di trasferimenti e condivisioni nell'app desktop.", "Guida controller e REST", FAQ_LINKS["controllers"]),
        ],
    },
    "es": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Respuestas breves para usuarios de eMule que quieren probar eMuleBB con binding, biblioteca compartida, slots de subida, Kad, REST y 0.7.3-rc.1.",
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
            faq_item("Que release de eMule debo usar para pruebas?", "Usa la release GitHub eMuleBB 0.7.3-rc.1 publicada para pruebas RC. El objetivo estable sigue siendo 0.7.3 despues de pasar los gates.", "Panel de release 0.7.3", FAQ_LINKS["release"]),
            faq_item("Como mantengo seguro WebServer o REST de eMule?", "eMuleBB trata WebServer y REST como superficies para controladores confiables. Activalos solo cuando haga falta, configura el bind, usa API key y evita exponerlos ampliamente.", "Guia de controladores y REST", FAQ_LINKS["controllers"]),
            faq_item("Como uso eMule con Kad y servidores?", "eMuleBB conserva servidores, busqueda global y Kad. Empieza con listas confiables, arranca Kad con cuidado y diagnostica Low ID o Kad firewalled antes de tocar muchas opciones.", "Guia de red", FAQ_LINKS["network"]),
            faq_item("Como manejo bibliotecas compartidas grandes en eMule?", "eMuleBB esta preparado para bibliotecas grandes: agrega raices gradualmente, usa Windows con long paths, revisa share-ignore y deja asentarse la cache de inicio.", "Guia de comparticion", FAQ_LINKS["sharing"]),
            faq_item("Puedo automatizar eMule con herramientas externas?", "Si. eMuleBB ofrece una REST API JSON autenticada para controladores locales confiables, manteniendo la semantica nativa de transferencias y comparticion en la app desktop.", "Guia de controladores y REST", FAQ_LINKS["controllers"]),
        ],
    },
    "pt_br": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Respostas curtas para usuarios do eMule que querem testar o eMuleBB com binding, compartilhamento, slots de upload, Kad, REST e 0.7.3-rc.1.",
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
            faq_item("Qual release do eMule devo usar para testes?", "Use a release GitHub eMuleBB 0.7.3-rc.1 publicada para testes RC. O alvo estavel continua sendo 0.7.3 depois que os gates passarem.", "Painel da release 0.7.3", FAQ_LINKS["release"]),
            faq_item("Como mantenho seguros WebServer ou REST do eMule?", "O eMuleBB trata WebServer e REST como superficies para controladores confiaveis. Ative apenas quando precisar, configure bind, use API key e evite exposicao ampla.", "Guia de controladores e REST", FAQ_LINKS["controllers"]),
            faq_item("Como uso eMule com Kad e servidores?", "O eMuleBB mantem servidores, busca global e Kad. Comece com listas confiaveis, inicialize Kad com cuidado e diagnostique Low ID ou Kad firewalled antes de mudar muita coisa.", "Guia de rede", FAQ_LINKS["network"]),
            faq_item("Como lidar com grandes bibliotecas compartilhadas no eMule?", "O eMuleBB foi feito para bibliotecas grandes: adicione raizes aos poucos, use Windows com long paths, revise share-ignore e deixe a cache de inicio estabilizar.", "Guia de compartilhamento", FAQ_LINKS["sharing"]),
            faq_item("Posso automatizar o eMule com ferramentas externas?", "Sim. O eMuleBB expoe uma REST API JSON autenticada para controladores locais confiaveis, mantendo a semantica nativa de transferencias e compartilhamento no app desktop.", "Guia de controladores e REST", FAQ_LINKS["controllers"]),
        ],
    },
    "fr": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Reponses courtes pour les utilisateurs eMule qui veulent essayer eMuleBB: binding, partage, slots d'upload, Kad, REST et 0.7.3-rc.1.",
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
            faq_item("Quelle release eMule utiliser pour tester?", "Utilisez la release GitHub eMuleBB 0.7.3-rc.1 publiee pour les tests RC. La cible stable reste 0.7.3 apres le passage des gates.", "Tableau release 0.7.3", FAQ_LINKS["release"]),
            faq_item("Comment securiser WebServer ou REST d'eMule?", "eMuleBB traite WebServer et REST comme des surfaces pour controleurs de confiance. Activez-les seulement si besoin, liez-les explicitement, utilisez une API key et evitez l'exposition large.", "Guide controleurs et REST", FAQ_LINKS["controllers"]),
            faq_item("Comment utiliser eMule avec Kad et les serveurs?", "eMuleBB conserve serveurs, recherche globale et Kad. Commencez avec des listes fiables, amorcez Kad proprement et diagnostiquez Low ID ou Kad firewalled avant de trop changer.", "Guide reseau", FAQ_LINKS["network"]),
            faq_item("Comment gerer de grandes bibliotheques partagees dans eMule?", "eMuleBB vise les grandes bibliotheques: ajoutez les racines graduellement, utilisez Windows avec long paths, revoyez share-ignore et laissez la cache de demarrage se stabiliser.", "Guide partage", FAQ_LINKS["sharing"]),
            faq_item("Puis-je automatiser eMule avec des outils externes?", "Oui. eMuleBB expose une REST API JSON authentifiee pour des controleurs locaux de confiance, tout en gardant la semantique native dans l'app desktop.", "Guide controleurs et REST", FAQ_LINKS["controllers"]),
        ],
    },
    "de": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Kurze Antworten fuer eMule-Nutzer, die eMuleBB fuer Binding, Shares, Upload-Slots, Kad, REST und 0.7.3-rc.1 testen wollen.",
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
            faq_item("Welche eMule-Release soll ich testen?", "Nutze die veroeffentlichte eMuleBB 0.7.3-rc.1 GitHub Release fuer RC-Tests. Das stabile Ziel bleibt 0.7.3 nach bestandenen Gates.", "0.7.3 release dashboard", FAQ_LINKS["release"]),
            faq_item("Wie halte ich eMule WebServer oder REST sicher?", "eMuleBB behandelt WebServer und REST als Oberflaechen fuer vertrauenswuerdige Controller. Nur bei Bedarf aktivieren, bewusst binden, API key nutzen und breite Exposition vermeiden.", "Controllers and REST Guide", FAQ_LINKS["controllers"]),
            faq_item("Wie nutze ich eMule mit Kad und Servern?", "eMuleBB behaelt Server, globale Suche und Kad. Starte mit vertrauenswuerdigen Serverlisten, bootstrappe Kad bewusst und diagnostiziere Low ID oder Kad firewalled vor grossen Aenderungen.", "Network Guide", FAQ_LINKS["network"]),
            faq_item("Wie betreibe ich grosse Freigabe-Bibliotheken in eMule?", "eMuleBB ist fuer grosse Bibliotheken gedacht: Wurzeln schrittweise hinzufuegen, Windows mit long paths nutzen, share-ignore pruefen und Startup-Cache stabilisieren lassen.", "Sharing Guide", FAQ_LINKS["sharing"]),
            faq_item("Kann ich eMule mit externen Tools automatisieren?", "Ja. eMuleBB bietet eine authentifizierte JSON REST API fuer vertrauenswuerdige lokale Controller und behaelt native Transfer- und Share-Semantik in der Desktop-App.", "Controllers and REST Guide", FAQ_LINKS["controllers"]),
        ],
    },
    "pl": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Krotkie odpowiedzi dla uzytkownikow eMule, ktorzy chca wyprobowac eMuleBB: binding, udostepnianie, sloty uploadu, Kad, REST i 0.7.3-rc.1.",
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
            faq_item("Ktore wydanie eMule wybrac do testow?", "Do testow RC uzywaj opublikowanej GitHub release eMuleBB 0.7.3-rc.1. Stabilnym celem pozostaje 0.7.3 po przejsciu gate'ow.", "Panel wydania 0.7.3", FAQ_LINKS["release"]),
            faq_item("Jak zabezpieczyc WebServer albo REST w eMule?", "eMuleBB traktuje WebServer i REST jako powierzchnie dla zaufanych kontrolerow. Wlaczaj je tylko w razie potrzeby, ustaw bind, uzyj API key i unikaj szerokiej ekspozycji.", "Przewodnik kontrolerow i REST", FAQ_LINKS["controllers"]),
            faq_item("Jak uzywac eMule z Kad i serwerami?", "eMuleBB zachowuje serwery, wyszukiwanie globalne i Kad. Zacznij od zaufanych list, ostroznie bootstrapuj Kad i diagnozuj Low ID lub Kad firewalled przed duzymi zmianami.", "Przewodnik sieciowy", FAQ_LINKS["network"]),
            faq_item("Jak obslugiwac duze biblioteki udostepniane w eMule?", "eMuleBB jest przygotowany na duze biblioteki: dodawaj katalogi stopniowo, uzywaj Windows z long paths, sprawdz share-ignore i pozwol ustabilizowac cache startowy.", "Przewodnik udostepniania", FAQ_LINKS["sharing"]),
            faq_item("Czy moge automatyzowac eMule zewnetrznymi narzedziami?", "Tak. eMuleBB udostepnia uwierzytelniona JSON REST API dla zaufanych lokalnych kontrolerow, zachowujac natywna semantyke transferow i udostepniania w aplikacji desktop.", "Przewodnik kontrolerow i REST", FAQ_LINKS["controllers"]),
        ],
    },
    "nl": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Korte antwoorden voor eMule-gebruikers die eMuleBB willen proberen voor binding, delen, uploadslots, Kad, REST en 0.7.3-rc.1.",
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
            faq_item("Welke eMule-release moet ik testen?", "Gebruik de gepubliceerde eMuleBB 0.7.3-rc.1 GitHub Release voor RC-tests. Het stabiele doel blijft 0.7.3 nadat de gates slagen.", "0.7.3 release dashboard", FAQ_LINKS["release"]),
            faq_item("Hoe houd ik eMule WebServer of REST veilig?", "eMuleBB behandelt WebServer en REST als oppervlakken voor vertrouwde controllers. Zet ze alleen aan wanneer nodig, bind bewust, gebruik een API key en voorkom brede blootstelling.", "Controllers en REST-gids", FAQ_LINKS["controllers"]),
            faq_item("Hoe gebruik ik eMule met Kad en servers?", "eMuleBB houdt servers, globale zoekactie en Kad. Begin met vertrouwde serverlijsten, bootstrap Kad bewust en diagnoseer Low ID of Kad firewalled voordat je veel wijzigt.", "Netwerkgids", FAQ_LINKS["network"]),
            faq_item("Hoe beheer ik grote gedeelde bibliotheken in eMule?", "eMuleBB is gemaakt voor grote bibliotheken: voeg roots geleidelijk toe, gebruik Windows met long paths, controleer share-ignore en laat de startcache stabiliseren.", "Deelgids", FAQ_LINKS["sharing"]),
            faq_item("Kan ik eMule automatiseren met externe tools?", "Ja. eMuleBB biedt een geauthenticeerde JSON REST API voor vertrouwde lokale controllers en houdt native transfer- en deelgedrag in de desktop-app.", "Controllers en REST-gids", FAQ_LINKS["controllers"]),
        ],
    },
    "ru": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Короткие ответы для пользователей eMule, которые хотят попробовать eMuleBB: binding, общие папки, upload slots, Kad, REST и 0.7.3-rc.1.",
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
            faq_item("Какой релиз eMule использовать для тестов?", "Для RC-тестирования используйте опубликованный GitHub Release eMuleBB 0.7.3-rc.1. Стабильная цель остается 0.7.3 после прохождения gate.", "0.7.3 release dashboard", FAQ_LINKS["release"]),
            faq_item("Как безопасно включить eMule WebServer или REST?", "eMuleBB считает WebServer и REST поверхностями для доверенных контроллеров. Включайте их только при необходимости, задавайте bind, используйте API key и не открывайте широко.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("Как использовать eMule с Kad и серверами?", "eMuleBB сохраняет серверы, global search и Kad. Начните с доверенных списков серверов, аккуратно bootstrap Kad и диагностируйте Low ID или Kad firewalled до массовых изменений.", "Network guide", FAQ_LINKS["network"]),
            faq_item("Как работать с большой общей библиотекой в eMule?", "eMuleBB рассчитан на большие библиотеки: добавляйте корни постепенно, используйте Windows с long paths, проверяйте share-ignore и дайте startup cache стабилизироваться.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Можно ли автоматизировать eMule внешними инструментами?", "Да. eMuleBB предоставляет authenticated JSON REST API для доверенных локальных контроллеров, сохраняя native transfer и sharing semantics в desktop app.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
    "uk": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "Короткі відповіді для користувачів eMule, які хочуть спробувати eMuleBB: binding, спільні бібліотеки, upload slots, Kad, REST і 0.7.3-rc.1.",
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
            faq_item("Який реліз eMule використовувати для тестів?", "Для RC-тестування використовуйте опублікований GitHub Release eMuleBB 0.7.3-rc.1. Стабільна ціль лишається 0.7.3 після проходження gate.", "0.7.3 release dashboard", FAQ_LINKS["release"]),
            faq_item("Як безпечно використовувати eMule WebServer або REST?", "eMuleBB розглядає WebServer і REST як поверхні для довірених контролерів. Увімкніть лише за потреби, задайте bind, використовуйте API key і не відкривайте широко.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("Як використовувати eMule з Kad і серверами?", "eMuleBB зберігає сервери, global search і Kad. Почніть із довірених списків серверів, обережно bootstrap Kad і діагностуйте Low ID або Kad firewalled перед масовими змінами.", "Network guide", FAQ_LINKS["network"]),
            faq_item("Як працювати з великою спільною бібліотекою в eMule?", "eMuleBB розрахований на великі бібліотеки: додавайте корені поступово, використовуйте Windows з long paths, перевіряйте share-ignore і дайте startup cache стабілізуватися.", "Sharing guide", FAQ_LINKS["sharing"]),
            faq_item("Чи можна автоматизувати eMule зовнішніми інструментами?", "Так. eMuleBB надає authenticated JSON REST API для довірених локальних контролерів, зберігаючи native transfer і sharing semantics у desktop app.", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
    "zh_cn": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "面向 eMule 用户的简短问答：用 eMuleBB 处理绑定、共享库、上传槽、Kad、REST 和 0.7.3-rc.1 测试。",
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
            faq_item("测试时应该使用哪个 eMule 版本?", "RC 测试请使用已发布的 eMuleBB 0.7.3-rc.1 GitHub Release。通过 release gates 后，稳定目标仍是 0.7.3。", "0.7.3 发布面板", FAQ_LINKS["release"]),
            faq_item("如何保证 eMule WebServer 或 REST 安全?", "eMuleBB 把 WebServer 和 REST 视为可信控制器接口。只在需要时启用，明确 bind，使用 API key，并避免大范围暴露。", "控制器和 REST 指南", FAQ_LINKS["controllers"]),
            faq_item("如何在 eMule 中使用 Kad 和服务器?", "eMuleBB 保留服务器、global search 和 Kad 工作流。先使用可信服务器列表，谨慎 bootstrap Kad，并在大量改设置前诊断 Low ID 或 Kad firewalled。", "网络指南", FAQ_LINKS["network"]),
            faq_item("如何处理 eMule 的大型共享库?", "eMuleBB 面向大型资料库：逐步添加根目录，使用支持 long paths 的 Windows，检查 share-ignore，并让 startup cache 稳定下来。", "共享指南", FAQ_LINKS["sharing"]),
            faq_item("可以用外部工具自动化 eMule 吗?", "可以。eMuleBB 提供经过认证的 JSON REST API 给可信本地控制器，同时把原生传输和共享语义保留在桌面应用中。", "控制器和 REST 指南", FAQ_LINKS["controllers"]),
        ],
    },
    "ja": {
        "title": "FAQ | eMule broadband edition",
        "meta_description": "eMule ユーザー向けの短いFAQ。eMuleBB の binding、共有ライブラリ、upload slots、Kad、REST、0.7.3-rc.1 テストを扱います。",
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
            faq_item("テストにはどの eMule release を使えばよいですか?", "RC テストには公開済みの eMuleBB 0.7.3-rc.1 GitHub Release を使ってください。安定版の目標は gates 通過後の 0.7.3 です。", "0.7.3 リリースダッシュボード", FAQ_LINKS["release"]),
            faq_item("eMule WebServer や REST を安全に保つには?", "eMuleBB は WebServer と REST を信頼済み controller 向けの surface として扱います。必要な時だけ有効化し、明示的に bind し、API key を使い、広い公開は避けます。", "Controllers and REST guide", FAQ_LINKS["controllers"]),
            faq_item("eMule で Kad とサーバーを使うには?", "eMuleBB は server、global search、Kad の流れを保ちます。信頼できる server list から始め、Kad を慎重に bootstrap し、Low ID や Kad firewalled を先に診断します。", "ネットワークガイド", FAQ_LINKS["network"]),
            faq_item("eMule の大きな共有ライブラリを扱うには?", "eMuleBB は大きなライブラリ向けです。root を段階的に追加し、long paths 対応 Windows を使い、share-ignore を確認し、startup cache が落ち着くのを待ちます。", "共有ガイド", FAQ_LINKS["sharing"]),
            faq_item("外部ツールで eMule を自動化できますか?", "はい。eMuleBB は信頼済みローカル controller 向けに認証付き JSON REST API を提供し、転送と共有の native semantics は desktop app に残します。", "Controllers and REST guide", FAQ_LINKS["controllers"]),
        ],
    },
}


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
        "tools_menu": (t["docs"], t["docs"]),
        "controllers": (t["automation"], t["automation"]),
        "stack_integrations": ("aMuTorrent + eMuleBB", t["automation"]),
        "rest_contract": ("REST API", t["automation"]),
        "rest_adapters": ("REST adapters", t["automation"]),
        "diagnostics": (t["docs"], t["docs"]),
        "troubleshooting": (t["docs"], t["docs"]),
        "release": ("0.7.3-rc.1", t["release"]),
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
        "p2p_overlord_tooling": "Scenario manifests, parity runners, reports, and quality guards for p2p-overlord.",
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
            "install": "Install",
            "source": t["source"],
            "guide": t["product_guide"],
            "panel_kicker": "eMuleBB",
            "panel_h2": t["method"],
            "panel_p": t["intro"],
            "signals": ["eD2K/Kad", "Upload", "Testing", "RC1", "Performance", "REST API", "0.7.3-rc.1"],
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
        "guide": {**s(t["nav"][2], t["guide"]), "cards": [c("", t["keep"], t["intro"]), c("", t["control"], t["lead"]), c("", "Testing", t["proof"]), c("", "RC1 published", t["release"]), c("", "0.7.3-rc.1", t["release"]), c("", t["product_guide"], t["docs"])]},
        "docs": {**s(t["nav"][3], t["docs"]), "links": []},
        "automation": {"eyebrow": t["nav"][4], "h2": t["automation"], "p": f"{t['automation']} <code>/api/v1</code>, JSON, <code>X-API-Key</code>.", "pills_label": "REST API", "pills": ["Transfers", "Searches", "Servers", "Kad", "Shared files", "Uploads", "Logs", "Preferences"]},
        "release": {**s(t["nav"][5], t["release"]), "cards": [c("", "0.7.3-rc.1", t["release"]), c("", "Fast CI", t["proof"]), c("", t["proof"], t["proof"]), c("", "Performance", t["lead"]), c("", "eD2K/Kad", t["keep"]), c("", "Status", t["release"])]},
        "method": {**s(t["method"], t["method"], t["intro"]), "cards": [c("eD2K/Kad", t["keep"], t["keep"]), c("Upload", t["control"], t["control"]), c("REST", "REST API", t["automation"]), c("Testing", t["proof"], t["release"])]},
        "repos": {**s(t["nav"][6], t["repos"]), "links": []},
        "install_callout": INSTALL_CALLOUT,
        "testing_callout": TESTING_CALLOUT,
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
    if not any("RC1" in signal for signal in signals):
        signals.append("RC1 on GitHub Releases")

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
    if not any("GitHub provenance" in card["h3"] for card in release_cards):
        release_cards.insert(
            4,
            c(
                "",
                "GitHub provenance",
                "RC1 assets are published from GitHub release automation with manifests, SHA-256 evidence, SBOMs, and a bootstrapper hash asset for verification.",
            ),
        )


def add_team_images(page: PageSpec, content: dict[str, Any]) -> None:
    """Attach section-local raster lore images to the team cards."""

    prefix = relative_prefix(page)
    for index, card in enumerate(content["team"]["cards"]):
        image = TEAM_IMAGES[index % len(TEAM_IMAGES)]
        card["image"] = {
            "src": f"{prefix}assets/team/{image['file']}",
            "alt": image["alt"],
        }


def add_brand_logo(page: PageSpec, content: dict[str, Any]) -> None:
    """Attach the header-only product logo path for the generated page."""

    prefix = relative_prefix(page)
    content["brand_logo"] = {
        "src": f"{prefix}assets/brand/{BRAND_LOGO_FILE}",
        "alt": "eMuleBB broadband edition",
    }


def with_generated_links(root: Path) -> None:
    """Populate repeated docs and repo link sections for every locale."""

    ensure_stock_locale_content(root)
    for page in PAGES:
        content = CONTENT[page.key]
        content.setdefault("install_callout", INSTALL_CALLOUT)
        content.setdefault("testing_callout", TESTING_CALLOUT)
        content["hero"]["install"] = "Download RC1" if page.key == "en" else content["hero"].get("install", "Install")
        add_release_evidence_copy(content)
        add_brand_logo(page, content)
        add_team_images(page, content)
        content.setdefault("release_downloads_label", CONTENT["en"]["release_downloads_label"])
        for nav_item in content["nav"]:
            if nav_item.get("id") in ("guide", "automation"):
                nav_item["id"] = "docs"
                nav_item.pop("href", None)
            if nav_item.get("id") == "release":
                nav_item["id"] = "install"
                nav_item["label"] = "Download"
                nav_item["class"] = "nav-download"
        for nav_item in content["nav"]:
            if nav_item.get("id") == "docs":
                nav_item.pop("href", None)
            if nav_item.get("id") == "faq":
                nav_item["href"] = FAQ_PAGE_BY_KEY.get(page.key, ENGLISH_FAQ_PAGE).url
        if not any(nav_item.get("id") == "install" for nav_item in content["nav"]):
            content["nav"].insert(
                3,
                {
                    "id": "install",
                    "label": "Download",
                    "class": "nav-download",
                },
            )
        deduped_nav = []
        seen_nav_ids = set()
        for nav_item in content["nav"]:
            nav_id = nav_item.get("id")
            if nav_id and nav_id in seen_nav_ids:
                continue
            if nav_id:
                seen_nav_ids.add(nav_id)
            deduped_nav.append(nav_item)
        content["nav"] = deduped_nav
        faq_href = FAQ_PAGE_BY_KEY.get(page.key, ENGLISH_FAQ_PAGE).url
        content["nav"] = [nav_item for nav_item in content["nav"] if nav_item.get("id") != "faq"]
        content["nav"].append({"id": "faq", "label": "FAQ", "href": faq_href})
        content["menu"] = MENU_COPY[page.key]
        content["languages_link_label"] = LANGUAGE_LINK_COPY[page.key]
        content["release_downloads"] = [
            {"href": href, "title": title}
            for href, title in RELEASE_DOWNLOADS
        ]
        content["docs"]["eyebrow"], content["docs"]["h2"] = DOC_SECTION_COPY[page.key]
        doc_copy = DOC_COPY[page.key]
        content["docs"]["links"] = [
            {
                "href": href,
                "title": doc_copy.get(key, DOC_COPY["en"][key])[0],
                "text": doc_copy.get(key, DOC_COPY["en"][key])[1],
            }
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
        "p2p_overlord_tooling": "p2p-overlord-tooling",
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


def render_outputs(root: Path, lastmod: str) -> dict[Path, str]:
    """Render every generated file into an in-memory path map."""

    with_generated_links(root)
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
        add_brand_logo(page, content)
        content["menu"] = MENU_COPY.get(page.key, MENU_COPY["en"])
        home_page = home_pages[page.key]
        nav = [
            {"href": home_page.url, "label": content["home_label"]},
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
