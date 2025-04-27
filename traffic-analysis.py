import json
from datetime import datetime
import os
import sys

import re2
from mitmproxy import http
from mitmproxy.script import concurrent
from adblockparser import AdblockRules
from glob import glob
from urllib.parse import urlparse
import tldextract
import base64
import gzip


IMAGE_MATCHER = re2.compile(r"\.(png|jpe?g|gif|webp|svg|ico|tiff?|avif|bmp|heic)$", re2.IGNORECASE)
SCRIPT_MATCHER = re2.compile(r"\.(js|mjs|jsx|ts|tsx|vue|coffee|dart|svelte|wasm)$", re2.IGNORECASE)
MEDIA_MATCHER = re2.compile(r"\.(mp4|mp3|webm|ogg|avi|mov|flac|mkv|m3u8|wav|aac|m4a|opus|3gp|flv|rmvb|mpg|hls)$", re2.IGNORECASE)
STYLESHEET_MATCHER = re2.compile(r"\.(css|scss|less|sass|styl)$", re2.IGNORECASE)
OBJECT_MATCHER = re2.compile(r"\.(swf|flv|jar|exe|apk|dmg|deb|ipa|aab)$", re2.IGNORECASE)
XHR_MATCHER = re2.compile(r"\.(json|xml|php|aspx|jsp|cgi|yaml|yml|graphql|proto)$", re2.IGNORECASE)
WEBSOCKET_MATCHER = re2.compile(r"^wss?:\/\/", re2.IGNORECASE)


# Stems from both :A Comprehensive Study on Third-Party User Tracking in Mobile Applications by Federica Paci 
# and A Study of Third-Party Tracking by Mobile Apps in the Wild by Seungyeop Han
THIRD_PARTY_DOMAINS = [
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
    "atdmt.com"
]

def log(message):
    print(f"[Traffic Analysis] {message}")

blocklist_files = glob("easylist/*")
if not blocklist_files:
    print("No easylist and easyprivacy files. Please download these files before continue.")
    raise SystemExit

rules = AdblockRules((line for file in blocklist_files for line in open(file, "r", encoding="utf-8")),
                     supported_options=["third-party", "script", "image", "stylesheet", "object", "xmlhttprequest", "subdocument", "document", "ping", "media", "font", "other"])

def normalize_domain(host):
    if not host:
        return ""
    extracted = tldextract.extract(host.lower())
    if extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"
    return host.lower()



def is_third_party(req):
    req_host = normalize_domain(req.host)
    
    if any(req_host == domain or req_host.endswith(f".{domain}") for domain in THIRD_PARTY_DOMAINS):
        return True

    app_domain = None
    app_package = req.headers.get("X-Requested-With", "").strip() or \
                  req.headers.get("X-Google-Maps-Mobile-API", "").split(",")[0].strip()
    if app_package:
        parts = app_package.split('.')
        if len(parts) >= 2:
            if parts[0] in ("com", "io") and len(parts) >= 3:
                app_domain = f"{parts[1]}.{parts[0]}"
            else:
                app_domain = f"{parts[-2]}.{parts[-1]}"
    
    if app_domain:
        app_domain_normalized = normalize_domain(app_domain)
        if req_host == app_domain_normalized or req_host.endswith(f".{app_domain_normalized}"):
            return False
        
    referer = req.headers.get("Referer", "").strip()
    origin = req.headers.get("Origin", "").strip()

    referer_host = normalize_domain(urlparse(referer).netloc) if referer.startswith("http") else ""
    origin_host = normalize_domain(urlparse(origin).netloc) if origin.startswith("http") else ""

    if referer_host and origin_host:
        return req_host != referer_host and req_host != origin_host
    elif referer_host:
        return req_host != referer_host
    elif origin_host:
        return req_host != origin_host
    
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
    elif OBJECT_MATCHER.search(url_path) or content_type.startswith(("application/x-shockwave-flash", "application/java-archive", "application/octet-stream")): # More object content types
        options["object"] = True
    elif XHR_MATCHER.search(url_path) or req.headers.get("X-Requested-With") == "XMLHttpRequest" or content_type == "application/json" or any(pattern in req.url for pattern in ["/api/", "/graphql", "/rest/"]):
        options["xmlhttprequest"] = True
    elif MEDIA_MATCHER.search(url_path) or content_type.startswith(("audio/", "video/", "application/vnd.apple.mpegurl")): # Add m3u8 content type
        options["media"] = True
    elif content_type.startswith(("text/html", "application/xhtml+xml", "application/vnd.wap.xhtml+xml")): # More document content types
        options["document"] = True
    elif (upgrade_header == "websocket" and connection_header == "upgrade") or (upgrade_header == "websocket" and WEBSOCKET_MATCHER.search(req.url)):
        options["websocket"] = True
    return options


# Analyze each HTTP request and log whether it is blocked or allowed
LOG_FILE = "blocked_requests.jsonl"

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
                # Final fallback: base64 encode binary
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

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        json.dump(log_entry, f, ensure_ascii=False)
        f.write("\n")