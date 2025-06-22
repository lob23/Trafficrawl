import json
from datetime import datetime
import os
import sys

import re2

from adblockparser import AdblockRules
from glob import glob
from urllib.parse import urlparse
import tldextract
import base64
import gzip
from iso3166 import countries    
ISO_CC = {c.alpha2.lower() for c in countries}

from urllib.parse import urlparse
from publicsuffix2 import PublicSuffixList        
import ipaddress

from mitmproxy import http,ctx
from mitmproxy.script import concurrent

IMAGE_MATCHER = re2.compile(r"\.(png|jpe?g|gif|webp|svg|ico|tiff?|avif|bmp|heic)$", re2.IGNORECASE)
SCRIPT_MATCHER = re2.compile(r"\.(js|mjs|jsx|ts|tsx|vue|coffee|dart|svelte|wasm)$", re2.IGNORECASE)
MEDIA_MATCHER = re2.compile(r"\.(mp4|mp3|webm|ogg|avi|mov|flac|mkv|m3u8|mpd|wav|aac|m4a|opus|3gp|flv|rmvb|mpg)$", re2.IGNORECASE)
STYLESHEET_MATCHER = re2.compile(r"\.(css)$", re2.IGNORECASE)
XHR_MATCHER = re2.compile(r"\.(json|xml|php|aspx|jsp|cgi|yaml|yml|graphql|proto)$", re2.IGNORECASE)
WEBSOCKET_MATCHER = re2.compile(r"^wss?:\/\/", re2.IGNORECASE)
# Stems from both :
# [1] Exodus tracker list
# [2] "A Comprehensive Study on Third-Party User Tracking in Mobile Applications" by Federica Paci et al.
# [3] “Mobile health and privacy: cross sectional study,” by G. Tangari et al.
# [4] "A fait accompli? an empirical study into the absence of consent to {Third-Party} tracking in android apps" by Kollnig et al.
# [5] "A Study of Third-Party Tracking by Mobile Apps in the Wild" by Seungyeop Han et al.
THIRD_PARTY_DOMAINS = [
    "googletagmanager.com",
    "mixpanel.com",
    "twitter.com",
    "liftoff.io"
    "startappservice.com",
    "apps-ticket.com",
    "ya-tracker.com",
    "googleadservices.com",
    "yahoo.com",
    "nexage.com",
    "gstatic.com",
    "googleusercontent.com",
    "facebook.net",
    "google.com",
    "googleapis.com",      
    "facebook.com",      
    "cloudfront.net",     
    "apple.com",           
    "gvt2.com",           
    "crashlytics.com",     
    "app-measurement.com",
    "appsflyer.com",      
    "doubleclick.net",     
    "adjust.com",         
    "demdex.net",         
    "branch.io",         
    "google-analytics.com",
    "googlesyndication.com",
    "admob.com",
    "2mdn.net",
    "inmobi.com",
    "admarvel.com",
    "mojiva.com",
    "flurry.com",
    "scorecardresearch.com",
    "quantserve.com",
    "medialytics.com",
    "imrworldwide.com",
    "statcounter.com",
    "localytics.com",
    "chartbeat.net",
    "bluekai.com",
    "mydas.mobi",
    "jumptap.com",
    "atdmt.com",
    "chartboost.com",
    "unity3d.com",
    "vungle.com",
    "applovin.com",
    "airpush.com"
]
BORING_PKG_TOKENS = {
    "com", "org", "net", "io", "gov", "edu", "mil", "info", "biz",
    "free", "paid", "beta", "lite", "demo", "trial",
    "test", "alpha", "rc", "debug",
    "android", "lib", "libs", "core", "util", "utils",
    "common", "internal", "impl", "framework", "component",
    "tools", "base", "prefs", "settings",
}
_psl = PublicSuffixList()

def load_tracker_domains(filepath):
    domains = set()
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.replace(".*.", "")  
            line = line.lstrip(".")      
            if "." in line:
                domains.add(line)
    return list(domains)

exodus_domains = load_tracker_domains("exodus_tracker_patterns_processed.txt")
THIRD_PARTY_DOMAINS.extend(exodus_domains)

def load(loader):
    loader.add_option(
        "app_package", str, "", "App package name"
    )
APP_PACKAGE = ""

def running():
    global APP_PACKAGE
    APP_PACKAGE = ctx.options.app_package
    print(f"APP PACKAGE: {APP_PACKAGE}")
    os.makedirs("results", exist_ok=True)

def log(message):
    print(f"[Traffic Analysis] {message}")

blocklist_files = glob("easylist/*")
if not blocklist_files:
    print("No easylist and easyprivacy files. Please download these files before continue.")
    raise SystemExit

rules = AdblockRules((line for file in blocklist_files for line in open(file, "r", encoding="utf-8")),
                     supported_options=["third-party", "script", "image", "stylesheet", "xmlhttprequest", "subdocument", "document", "ping", "media", "font", "other"])

def normalise_domain(host: str | bytes | None) -> str:
    if not host:
        return ""

    if isinstance(host, bytes):
        host = host.decode("ascii", "ignore")
    host = host.lower().strip("[]")  

    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    suffix = _psl.get_public_suffix(host)
    if not suffix:
        print(f"NO SUFFIX FOR {suffix}")
        return host 

    lbl = host.rsplit("." + suffix, 1)[0].split(".")[-1]
    return f"{lbl}.{suffix}" if lbl else host


def _header(req, key: str) -> str:
    return (req.headers.get(key, "") or "").strip()

def _same_site(a: str, b: str) -> bool:
    if not a or not b:
        return False                   
    if a == b:
        return True
    return a.endswith("." + b) or b.endswith("." + a)
            
def normalize_domain(host):
    if not host:
        return ""
    extracted = tldextract.extract(host.lower())
    if extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"
    return host.lower()

def _extract_pkg_tokens(pkg: str) -> set[str]:
    toks = pkg.lower().split(".")
    while toks and toks[0] in ISO_CC:
        toks.pop(0)
        if toks and toks[0] == "co":
            toks.pop(0)
    return {
        t for t in toks
        if t not in BORING_PKG_TOKENS and len(t) > 2 and t.isalpha()
    }


def _first_party_by_pkg(req_host: str, package_name: str) -> bool:
    tokens  = _extract_pkg_tokens(package_name)
    labels  = normalise_domain(req_host).split(".")       
    return bool(tokens & set(labels))         

def is_third_party(req): 

    host = req.host or _header(req, ":authority") or getattr(req, "sni", "")
    req_host = normalise_domain(host)
    

    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    if req_host in THIRD_PARTY_DOMAINS or any(
        req_host.endswith("." + d) for d in THIRD_PARTY_DOMAINS
    ):
        return True

    pkg = _header(req, "X-Requested-With") or _header(req, "x-requested-with") or _header(req, "x-google-maps-mobile-api").split(",")[0]  or _header(req, "X-Google-Maps-Mobile-API").split(",")[0]
    if pkg and _first_party_by_pkg(req_host, pkg):
        return False
    

    referer = req.headers.get("Referer", "").strip() or req.headers.get("referer", "").strip()
    origin = req.headers.get("Origin", "").strip() or req.headers.get("origin", "").strip()

    referer_host = normalize_domain(urlparse(referer).netloc) if referer.startswith("http") else ""
    origin_host = normalize_domain(urlparse(origin).netloc) if origin.startswith("http") else ""
    if (origin_host or referer_host):
        if _same_site(req_host, origin_host) or _same_site(req_host, referer_host):
            return False    
        else:
            return True    
    
    return False


def get_request_options(req):
    options = {'domain': req.host}

    if is_third_party(req):
        options["third-party"] = True

    # Removing Query Parameters.
    url_path = req.url.split("?", 1)[0]
    content_type = req.headers.get("Content-Type", "")
    
    upgrade_header = req.headers.get("Upgrade", "").lower()
    connection_header = req.headers.get("Connection", "").lower()

    # Categorize Request Types
    if IMAGE_MATCHER.search(url_path) or content_type.startswith("image/"):
        options["image"] = True
    elif SCRIPT_MATCHER.search(url_path) or content_type.startswith(("application/javascript", "text/javascript")):
        options["script"] = True
    elif STYLESHEET_MATCHER.search(url_path) or content_type.startswith("text/css"):
        options["stylesheet"] = True

    elif XHR_MATCHER.search(url_path) or req.headers.get("X-Requested-With") == "XMLHttpRequest" or content_type == "application/json" or any(pattern in req.url for pattern in ["/api/", "/graphql", "/rest/"]):
        options["xmlhttprequest"] = True
    elif MEDIA_MATCHER.search(url_path) or content_type.startswith(("audio/", "video/", "application/vnd.apple.mpegurl")): 
        options["media"] = True
    elif content_type.startswith(("text/html", "application/xhtml+xml", "application/vnd.wap.xhtml+xml")): 
        options["document"] = True
    elif (upgrade_header == "websocket" and connection_header == "upgrade") or (upgrade_header == "websocket" and WEBSOCKET_MATCHER.search(req.url)):
        options["websocket"] = True
    return options


# Analyze each HTTP request and log whether it is blocked or allowed
LOG_FILE = "results/request_logs"
os.makedirs(LOG_FILE, exist_ok=True)

@concurrent
def request(flow: http.HTTPFlow):
    req = flow.request
    options = get_request_options(req)
    blocked = rules.should_block(req.url, options)

    request_body = ""
    decode_method = "none"
    raw_content = req.content

    if req.headers.get("Content-Encoding", "").lower() == "gzip":
        try:
            raw_content = gzip.decompress(req.content)
            decode_method = "gzip"
        except Exception as e:
            decode_method = f"gzip-decompress-failed: {str(e)}"

    if not decode_method.startswith("gzip-decompress-failed") and raw_content:
        try:
            request_body = raw_content.decode("utf-8")
            decode_method = decode_method + "+utf-8" if decode_method != "none" else "utf-8"
        except UnicodeDecodeError:
            try:
                request_body = raw_content.decode("latin1")
                decode_method = decode_method + "+latin1" if decode_method != "none" else "latin1"
            except Exception:
                encoded = base64.b64encode(raw_content).decode("ascii")
                request_body = encoded
                decode_method = decode_method + "+base64" if decode_method != "none" else "base64"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "url": req.url,
        "host": req.host,
        "method": req.method,
        "content_type": req.headers.get("Content-Type", "unknown"),
        "content_encoding": req.headers.get("Content-Encoding", "none"),
        "decode_method": decode_method,
        "headers": dict(req.headers),
        "options": options,
        "request_body": request_body,
        "action": "BLOCKED" if blocked else "ALLOWED"
    }

    with open(f'{LOG_FILE}/{APP_PACKAGE}.jsonl', "a", encoding="utf-8") as f:
        json.dump(log_entry, f, ensure_ascii=False)
        f.write("\n")