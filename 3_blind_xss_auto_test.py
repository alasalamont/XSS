#!/usr/bin/env python3
"""
Automated XSS Testing with Headless Browser
Injects payloads and waits for callbacks to trigger
Supports both --target URL and --request file (Burp Suite format)
"""

import sys
import time
import re
import html
import json
import threading
from urllib.parse import quote_plus, unquote, unquote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# ANSI Colors
class C:
    G = '\033[92m'  # Green
    Y = '\033[93m'  # Yellow
    R = '\033[91m'  # Red
    C = '\033[96m'  # Cyan
    B = '\033[1m'   # Bold
    E = '\033[0m'   # End

class HTTPRequest:
    """Parse and store HTTP request from file"""
    def __init__(self):
        self.method = 'GET'
        self.path = '/'
        self.protocol = 'HTTP/1.1'
        self.host = ''
        self.headers = {}
        self.body = ''
        self.cookies = {}
    
    @classmethod
    def from_file(cls, filepath):
        """Parse HTTP request from file (Burp format)"""
        req = cls()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
            
            # Parse request line
            if lines:
                parts = lines[0].split(' ')
                if len(parts) >= 2:
                    req.method = parts[0]
                    req.path = parts[1]
                    if len(parts) >= 3:
                        req.protocol = parts[2]
            
            # Parse headers
            i = 1
            while i < len(lines) and lines[i].strip():
                if ':' in lines[i]:
                    key, value = lines[i].split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    req.headers[key] = value
                    
                    if key.lower() == 'host':
                        req.host = value
                    elif key.lower() == 'cookie':
                        # Parse cookies
                        for cookie in value.split(';'):
                            if '=' in cookie:
                                k, v = cookie.strip().split('=', 1)
                                req.cookies[k] = v
                i += 1
            
            # Parse body (if exists)
            if i < len(lines):
                req.body = '\n'.join(lines[i+1:]).strip()
            
            return req
        except Exception as e:
            print(f"✗ Error parsing request file: {e}")
            sys.exit(1)
    
    def has_fuzz(self):
        """Check if request contains FUZZ marker"""
        return 'FUZZ' in self.path or 'FUZZ' in self.body
    
    def get_base_url(self):
        """Get base URL (protocol + host)"""
        # Detect protocol from request
        protocol = 'https' if self.protocol.startswith('HTTP/2') else 'http'
        if ':443' in self.host or 'https' in self.path:
            protocol = 'https'
        return f"{protocol}://{self.host.split(':')[0]}"

class XSSAutoTester:
    def __init__(self, target_url=None, request_file=None, wordlist_path=None, delay=3, headless=True, output_file='result/findings.txt', second_order_file=None, attacker_server='https://attacker.com', num_threads=1):
        """
        Args:
            target_url: URL with FUZZ placeholder (e.g., https://target.com/search?q=FUZZ)
            request_file: Path to HTTP request file (Burp format)
            wordlist_path: Path to payload wordlist
            delay: Seconds to wait after loading page (for JS to execute)
            headless: Run browser in headless mode
            output_file: File to save potential XSS findings
            second_order_file: Path to second-order request file (for second-order XSS detection)
            attacker_server: Attacker callback server URL (for DOM detection)
            num_threads: Number of concurrent threads (default: 1, max: 10)
        """
        self.target_url = target_url
        self.request_file = request_file
        self.request_obj = None
        self.second_order_file = second_order_file
        self.second_order_obj = None
        self.wordlist_path = wordlist_path
        self.delay = delay
        self.headless = headless
        self.driver = None
        
        # Validate and set num_threads (max 10)
        if num_threads > 10:
            print(f"{C.Y}⚠ Warning: Maximum 10 threads allowed. Setting to 10.{C.E}")
            self.num_threads = 10
        else:
            self.num_threads = num_threads
        
        # Create output folder if needed
        self.output_file = output_file
        import os
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        self.potential_xss = []
        self.current_payload = None  # Track current payload for second-order checks
        self.attacker_server = attacker_server  # For DOM detection
        
        # Thread-safe locks
        self.file_lock = threading.Lock()
        self.print_lock = threading.Lock()
        self.results_lock = threading.Lock()
        
        # Parse request file if provided
        if request_file:
            self.request_obj = HTTPRequest.from_file(request_file)
            if not self.request_obj.has_fuzz():
                print("✗ Error: Request file must contain 'FUZZ' marker")
                sys.exit(1)
        
        # Parse second-order request file if provided
        if second_order_file:
            self.second_order_obj = HTTPRequest.from_file(second_order_file)
            print(f"✓ Second-order detection enabled: {second_order_file}")
        
    def _create_browser_instance(self):
        """Create a new browser instance (for threading)"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        # Disable various security features for testing
        options.set_preference('security.fileuri.strict_origin_policy', False)
        options.set_preference('security.mixed_content.block_active_content', False)
        
        # Handle alerts automatically (dismiss them)
        options.set_preference('dom.disable_beforeunload', True)
        
        try:
            from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
            
            caps = DesiredCapabilities.FIREFOX.copy()
            # Auto-dismiss unexpected alerts
            caps['unhandledPromptBehavior'] = 'dismiss'
            
            driver = webdriver.Firefox(options=options, desired_capabilities=caps)
            driver.set_page_load_timeout(10)
            return driver
        except Exception as e:
            with self.print_lock:
                print(f"{C.R}✗ Failed to create browser instance: {e}{C.E}")
            raise
    
    def setup_browser(self):
        """Initialize Firefox browser (for single-threaded mode)"""
        try:
            self.driver = self._create_browser_instance()
            print(f"✓ Browser initialized (headless={self.headless})")
        except Exception as e:
            print(f"✗ Failed to initialize browser: {e}")
            print("\nInstall requirements:")
            print("  sudo apt-get install firefox-geckodriver")
            print("  pip3 install selenium")
            sys.exit(1)
    
    def load_payloads(self):
        """Load payloads from wordlist and extract callback server"""
        payloads = []
        try:
            with open(self.wordlist_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        payloads.append(line)
                        
                        # Extract attacker server from first payload
                        if not hasattr(self, 'attacker_server') or self.attacker_server == 'https://attacker.com':
                            # Decode if URL encoded
                            line_decoded = unquote(line) if '%' in line else line
                            # Extract https://domain from payload
                            import re
                            match = re.search(r'https?://([^/\s"\'\)]+)', line_decoded)
                            if match:
                                self.attacker_server = f"{match.group(0).split('/')[0]}//{match.group(1)}"
            
            print(f"✓ Loaded {len(payloads)} payloads from {self.wordlist_path}")
            if hasattr(self, 'attacker_server'):
                print(f"✓ Detected callback server: {self.attacker_server}")
            return payloads
        except Exception as e:
            print(f"✗ Error loading wordlist: {e}")
            sys.exit(1)
    
    def detect_xss_execution(self, payload, callback_server):
        """
        Comprehensive XSS detection using multiple methods
        Returns: (detection_type, found, escaped, details)
        
        Detection types:
        - 'html-reflected': Payload in HTML response
        - 'dom-executed': Payload executed via DOM (detected in browser)
        - 'url-injection': Payload in URL only
        - 'not-detected': Not found
        """
        from selenium.common.exceptions import UnexpectedAlertPresentException
        
        try:
            # Try to get page source, handle alerts
            try:
                page_source = self.driver.page_source
                current_url = self.driver.current_url
            except UnexpectedAlertPresentException:
                # Alert present, dismiss and retry
                self._dismiss_alerts()
                page_source = self.driver.page_source
                current_url = self.driver.current_url
            
            # Decode payload if URL encoded
            payload_decoded = payload
            if '%' in payload and any(c in payload for c in ['%2', '%3', '%0']):
                try:
                    payload_decoded = unquote(payload)
                except:
                    pass
            
            # Also handle JSON escaping
            payload_json_unescaped = payload_decoded.replace('\\"', '"').replace('\\\\', '\\')
            
            # Extract callback domain from payload
            callback_domain = callback_server.replace('https://', '').replace('http://', '').split('/')[0]
            
            # ========== METHOD 1: HTML Source Check ==========
            html_found = False
            matched_payload = None
            reflection_count = 0
            
            for variant in [payload_decoded, payload_json_unescaped, payload]:
                if variant in page_source:
                    html_found = True
                    matched_payload = variant
                    reflection_count = page_source.count(variant)
                    break
            
            # Check if escaped
            escaped = False
            if html_found:
                escape_patterns = ['&lt;', '&gt;', '&quot;', '&#39;', '\\u003c', '\\u003e', '\\u0022']
                for pattern in escape_patterns:
                    if pattern in page_source:
                        escaped = True
                        break
            
            # ========== METHOD 2: DOM Execution Check (Performance API) ==========
            dom_executed = False
            try:
                perf_check = self.driver.execute_script(f"""
                    var resources = performance.getEntriesByType('resource');
                    for(var i=0; i<resources.length; i++) {{
                        if(resources[i].name.includes('{callback_domain}')) {{
                            return true;
                        }}
                    }}
                    return false;
                """)
                dom_executed = perf_check
            except UnexpectedAlertPresentException:
                self._dismiss_alerts()
            except:
                pass
            
            # ========== METHOD 3: DOM Script Tag Check ==========
            script_injected = False
            try:
                script_check = self.driver.execute_script(f"""
                    var scripts = document.getElementsByTagName('script');
                    for(var i=0; i<scripts.length; i++) {{
                        if(scripts[i].src && scripts[i].src.includes('{callback_domain}')) {{
                            return true;
                        }}
                    }}
                    return false;
                """)
                script_injected = script_check
            except UnexpectedAlertPresentException:
                self._dismiss_alerts()
            except:
                pass
            
            # ========== METHOD 4: URL Injection Check ==========
            url_injection = False
            try:
                decoded_url = unquote(current_url)
                if payload_decoded in decoded_url:
                    url_injection = True
            except:
                pass
            
            # ========== Determine Detection Type ==========
            if html_found and not escaped:
                return 'html-reflected', True, False, {
                    'matched_payload': matched_payload,
                    'reflections': reflection_count,
                    'dom_executed': dom_executed,
                    'script_injected': script_injected
                }
            elif dom_executed or script_injected:
                return 'dom-executed', True, False, {
                    'matched_payload': payload_decoded,
                    'reflections': 0,
                    'dom_executed': dom_executed,
                    'script_injected': script_injected,
                    'url_injection': url_injection
                }
            elif html_found and escaped:
                return 'html-escaped', True, True, {
                    'matched_payload': matched_payload,
                    'reflections': reflection_count
                }
            elif url_injection:
                return 'url-injection', True, False, {
                    'matched_payload': payload_decoded,
                    'url_injection': True
                }
            else:
                return 'not-detected', False, False, {}
            
        except Exception as e:
            print(f"    ⚠ Error in XSS detection: {e}")
            return 'error', False, False, {}
    
    def _dismiss_alerts(self):
        """Dismiss any alert dialogs that appear"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException, NoAlertPresentException
            
            # Check for alert with very short timeout
            try:
                alert = WebDriverWait(self.driver, 0.5).until(EC.alert_is_present())
                alert_text = alert.text
                alert.accept()  # Dismiss alert
                return alert_text
            except (TimeoutException, NoAlertPresentException):
                return None
        except:
            return None
    
    def try_trigger_events(self):
        """Try to trigger common events (hover, click) to activate payloads"""
        try:
            # Dismiss any existing alerts first
            self._dismiss_alerts()
            
            # Find all visible elements
            elements = self.driver.find_elements(By.XPATH, "//*[not(ancestor::script) and not(ancestor::style)]")
            
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.common.exceptions import UnexpectedAlertPresentException
            actions = ActionChains(self.driver)
            
            # Try hover on first few elements
            for elem in elements[:5]:
                try:
                    actions.move_to_element(elem).perform()
                    time.sleep(0.1)
                    # Dismiss alerts after each action
                    self._dismiss_alerts()
                except UnexpectedAlertPresentException:
                    # Alert appeared, dismiss and continue
                    self._dismiss_alerts()
                except:
                    pass
            
            # Try clicking on clickable elements
            clickable = self.driver.find_elements(By.XPATH, "//a | //button | //input[@type='submit'] | //div[@onclick] | //span[@onclick]")
            for elem in clickable[:3]:
                try:
                    elem.click()
                    time.sleep(0.1)
                    # Dismiss alerts after each action
                    self._dismiss_alerts()
                except UnexpectedAlertPresentException:
                    # Alert appeared, dismiss and continue
                    self._dismiss_alerts()
                except:
                    pass
                    
        except Exception as e:
            # Dismiss alerts if any
            try:
                self._dismiss_alerts()
            except:
                pass
    
    def test_payload(self, payload, index):
        """Test a single payload (single-threaded version)"""
        # Just call internal method (no lock needed in single-threaded)
        self._test_payload_internal(payload, index)
    
    def _check_second_order(self, payload, index):
        """Check for payload reflection in second-order page"""
        try:
            print(f"    🔍 Checking second-order page...")
            
            # Build second-order URL
            second_url = self.second_order_obj.get_base_url() + self.second_order_obj.path
            
            # Set cookies if present in second-order request
            if self.second_order_obj.cookies:
                self._set_cookies(second_url, self.second_order_obj.cookies)
            
            # Navigate to second-order page
            if self.second_order_obj.method == 'POST':
                # If second-order is POST, use form submission
                self._do_post_request(second_url, "")  # No FUZZ, just load the page
            else:
                self.driver.get(second_url)
            
            time.sleep(0.5)
            
            # Dismiss any alerts on second-order page
            alert_text = self._dismiss_alerts()
            if alert_text:
                print(f"    ℹ [ID {index}] Alert on second-order page: {alert_text[:50]}...")
            
            # Check if payload is reflected in second-order page
            second_url_actual = self.driver.current_url
            detection_type, found, escaped, details = self.detect_xss_execution(payload, self.attacker_server)
            
            if detection_type == 'html-reflected':
                # Stored XSS - Found in HTML
                print(f"    {C.G}🎯 [ID {index}] SECOND-ORDER XSS [CONFIRMED - HTML]{C.E}")
                print(f"    {C.G}✓{C.E} Payload in HTML response: {details['matched_payload'][:60]}...")
                print(f"    {C.C}Reflections:{C.E} {details['reflections']} time(s)")
                if details.get('dom_executed'):
                    print(f"    {C.G}✓{C.E} Execution CONFIRMED via Performance API")
                
                self.potential_xss.append({
                    'id': index,
                    'payload': payload,
                    'matched_payload': details['matched_payload'],
                    'reflections': details['reflections'],
                    'url': f"{self.second_order_obj.method} {self.second_order_obj.path}",
                    'location': 'second-order',
                    'type': 'html-reflected',
                    'page_url': second_url_actual
                })
                self._save_finding(index, payload, details['reflections'],
                                 f"{self.second_order_obj.method} {self.second_order_obj.path}",
                                 'second-order', second_url_actual, details['matched_payload'], 'stored-xss')
                                 
            elif detection_type == 'dom-executed':
                # Stored XSS - Executed via DOM
                print(f"    {C.G}🎯 [ID {index}] SECOND-ORDER XSS [CONFIRMED - DOM]{C.E}")
                print(f"    {C.G}✓{C.E} Execution DETECTED in second-order page")
                if details.get('dom_executed'):
                    print(f"    {C.G}✓{C.E} Callback request detected (Performance API)")
                if details.get('script_injected'):
                    print(f"    {C.G}✓{C.E} Script tag found in DOM")
                
                self.potential_xss.append({
                    'id': index,
                    'payload': payload,
                    'matched_payload': details['matched_payload'],
                    'reflections': 0,
                    'url': f"{self.second_order_obj.method} {self.second_order_obj.path}",
                    'location': 'second-order',
                    'type': 'dom-based',
                    'page_url': second_url_actual
                })
                self._save_finding(index, payload, 0,
                                 f"{self.second_order_obj.method} {self.second_order_obj.path}",
                                 'second-order', second_url_actual, details['matched_payload'], 'stored-dom-xss')
                                 
            elif detection_type == 'html-escaped':
                print(f"    ℹ [ID {index}] Reflected but ESCAPED ({details['reflections']}x) in second-order page")
            else:
                print(f"    ℹ [ID {index}] Payload NOT detected in second-order page")
            
            # Trigger events in second-order page
            print(f"    Triggering events (hover/click) in second-order page...")
            self.try_trigger_events()
            
            # Wait for callback
            print(f"    Waiting {self.delay}s for callback...")
            time.sleep(self.delay)
            
            print(f"    ✓ Done (check callback server for confirmed hits)")
            
        except Exception as e:
            print(f"    ⚠ Error checking second-order page: {e}")
    
    def _save_finding(self, payload_id, payload, reflections, url, location='first-order', page_url='', matched_payload=None, detection_type='unknown'):
        """Save XSS finding to file"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                
                # Header based on detection type
                if detection_type == 'html-reflected':
                    status = "[CONFIRMED - HTML-REFLECTED]" if location == 'first-order' else "[CONFIRMED - STORED XSS]"
                elif detection_type == 'dom-based':
                    status = "[CONFIRMED - DOM-BASED]" if location == 'first-order' else "[CONFIRMED - STORED DOM]"
                elif detection_type == 'stored-xss':
                    status = "[CONFIRMED - STORED XSS]"
                elif detection_type == 'stored-dom-xss':
                    status = "[CONFIRMED - STORED DOM XSS]"
                elif location == 'second-order':
                    status = "[NEED_TO_VERIFY - SECOND-ORDER]"
                else:
                    status = "[NEED_TO_VERIFY]"
                
                f.write(f"{status} Payload ID: {payload_id}\n")
                f.write(f"URL/Request: {url}\n")
                f.write(f"Location: {location}\n")
                f.write(f"Detection Type: {detection_type}\n")
                if page_url:
                    f.write(f"Page URL: {page_url}\n")
                f.write(f"Reflections: {reflections}\n")
                f.write(f"Payload (original):\n{payload}\n")
                if matched_payload and matched_payload != payload:
                    f.write(f"Payload (decoded/matched):\n{matched_payload}\n")
                f.write("="*70 + "\n\n")
        except Exception as e:
            print(f"    ⚠ Could not save to file: {e}")
    
    def _build_url_from_request(self, payload):
        """Build full URL from request object with payload"""
        base_url = self.request_obj.get_base_url()
        path_with_payload = self.request_obj.path.replace('FUZZ', payload)
        return base_url + path_with_payload
    
    def _set_cookies(self, url, cookies):
        """Set cookies in browser"""
        try:
            # Navigate to domain first to set cookies
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain_url = f"{parsed.scheme}://{parsed.netloc}"
            
            self.driver.get(domain_url)
            
            for name, value in cookies.items():
                self.driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': parsed.netloc.split(':')[0]
                })
        except Exception as e:
            print(f"    ⚠ Could not set cookies: {e}")
    
    def _do_post_request(self, url, payload):
        """Handle POST request by injecting appropriate method"""
        body_with_payload = self.request_obj.body.replace('FUZZ', payload)
        content_type = self.request_obj.headers.get('Content-Type', '').lower()
        
        # Determine body type and send accordingly
        if 'application/json' in content_type or body_with_payload.strip().startswith('{'):
            # JSON - Send via fetch API with proper escaping
            self._do_json_request(url, body_with_payload, content_type)
        elif 'application/x-www-form-urlencoded' in content_type or '=' in body_with_payload:
            # Form-urlencoded - Send via form with URL encoding
            self._do_form_request(url, body_with_payload)
        else:
            # Raw body - Send via fetch
            self._do_raw_request(url, body_with_payload, content_type)
    
    def _do_json_request(self, url, json_body, content_type):
        """Send JSON request via JavaScript fetch"""
        # Method 1: Try to parse JSON, validate, and re-stringify (preserves structure)
        try:
            # Parse JSON to validate structure
            json_obj = json.loads(json_body)
            # Re-stringify to ensure proper escaping
            json_stringified = json.dumps(json_obj, ensure_ascii=False)
            # Escape for JavaScript string literal
            json_escaped = json_stringified.replace('\\', '\\\\').replace("'", "\\'")
        except json.JSONDecodeError:
            # If invalid JSON (payload broke structure), send as-is with escaping
            # This handles cases where payload contains unescaped quotes
            json_escaped = json_body.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
        
        html_template = f"""
        <html>
        <body>
        <script>
            // Send JSON via fetch
            fetch('{url}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': '{content_type or "application/json"}'
                }},
                body: '{json_escaped}'
            }}).then(r => {{
                // Render response
                return r.text();
            }}).then(html => {{
                document.open();
                document.write(html);
                document.close();
            }}).catch(e => console.error(e));
        </script>
        <p>Sending JSON request...</p>
        </body>
        </html>
        """
        self._load_temp_html(html_template)
    
    def _do_form_request(self, url, form_body):
        """Send form-urlencoded request via HTML form"""
        # Parse parameters and URL encode each value
        params = []
        for param in form_body.split('&'):
            if '=' in param:
                name, value = param.split('=', 1)
                # HTML escape for attribute safety (browser will handle URL encoding on submit)
                name_escaped = html.escape(name, quote=True)
                value_escaped = html.escape(value, quote=True)
                params.append(f'<input type="hidden" name="{name_escaped}" value="{value_escaped}">')
        
        form_inputs = '\n            '.join(params)
        
        html_template = f"""
        <html>
        <body>
        <form id="xss_form" method="POST" action="{url}">
            {form_inputs}
        </form>
        <script>
            document.getElementById('xss_form').submit();
        </script>
        </body>
        </html>
        """
        self._load_temp_html(html_template)
    
    def _do_raw_request(self, url, raw_body, content_type):
        """Send raw body via fetch"""
        body_escaped = raw_body.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
        
        html_template = f"""
        <html>
        <body>
        <script>
            fetch('{url}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': '{content_type or "text/plain"}'
                }},
                body: '{body_escaped}'
            }}).then(r => r.text()).then(html => {{
                document.open();
                document.write(html);
                document.close();
            }});
        </script>
        </body>
        </html>
        """
        self._load_temp_html(html_template)
    
    def _load_temp_html(self, html_content):
        """Load HTML content in temp file"""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name
        
        self.driver.get(f'file://{temp_file}')
        time.sleep(0.5)
        
        try:
            os.unlink(temp_file)
        except:
            pass
    
    def _check_callback_server(self):
        """Check if callback server is accessible"""
        try:
            import urllib.request
            # Try to connect to callback server
            url = self.attacker_server if self.attacker_server != 'https://attacker.com' else None
            if url:
                req = urllib.request.Request(url, method='HEAD')
                urllib.request.urlopen(req, timeout=2)
                return True
        except:
            return False
        return None  # Cannot check (default URL)
    
    def run(self):
        """Run the test"""
        print("\n" + "="*70)
        print("🤖 Automated XSS Testing with Headless Browser")
        print("="*70)
        
        if self.request_obj:
            print(f"Mode:       Request file")
            print(f"Request:    {self.request_file}")
            print(f"Method:     {self.request_obj.method}")
            print(f"Host:       {self.request_obj.host}")
            print(f"Path:       {self.request_obj.path[:60]}...")
        else:
            print(f"Mode:       Direct URL")
            print(f"Target URL: {self.target_url}")
        
        if self.second_order_obj:
            print(f"\n🔍 Second-order detection:")
            print(f"File:       {self.second_order_file}")
            print(f"Method:     {self.second_order_obj.method}")
            print(f"Host:       {self.second_order_obj.host}")
            print(f"Path:       {self.second_order_obj.path[:60]}...")
        
        print(f"\nWordlist:   {self.wordlist_path}")
        print(f"Output:     {self.output_file}")
        print(f"Delay:      {self.delay}s per payload")
        if self.num_threads > 1:
            print(f"{C.G}Threads:    {self.num_threads} (multi-threaded mode){C.E}")
        print("="*70 + "\n")
        
        # Check callback server
        print(f"{C.C}Checking callback server...{C.E}")
        server_status = self._check_callback_server()
        if server_status is True:
            print(f"{C.G}✓ Callback server is accessible: {self.attacker_server}{C.E}\n")
        elif server_status is False:
            print(f"{C.Y}⚠ WARNING: Cannot reach callback server: {self.attacker_server}{C.E}")
            print(f"{C.Y}  Make sure callback_server.py is running!{C.E}")
            print(f"{C.Y}  Continuing anyway... (some detections may not work){C.E}\n")
        else:
            print(f"{C.Y}ℹ Using default URL - callback server check skipped{C.E}\n")
        
        # Clear output file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write("# XSS Auto-Tester - Findings\n")
                f.write("# " + "="*68 + "\n")
                if self.num_threads > 1:
                    f.write(f"# Multi-threaded mode: {self.num_threads} threads\n")
                f.write(f"# These payloads were detected via multiple methods\n")
                f.write("# " + "="*68 + "\n\n")
            print(f"✓ Output file initialized: {self.output_file}")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize output file: {e}")
        
        # Load payloads
        payloads = self.load_payloads()
        
        # Choose execution mode
        if self.num_threads > 1:
            self._run_multithreaded(payloads)
        else:
            self._run_singlethreaded(payloads)
    
    def _run_singlethreaded(self, payloads):
        """Run tests in single thread (original behavior)"""
        # Setup
        self.setup_browser()
        
        print(f"\n🚀 Starting tests (single-threaded)...")
        print(f"⏱️  Estimated time: {len(payloads) * self.delay / 60:.1f} minutes\n")
        
        # Test each payload
        start_time = time.time()
        for i, payload in enumerate(payloads, 1):
            self.test_payload(payload, i)
            
            # Progress indicator
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (len(payloads) - i) / rate if rate > 0 else 0
                print(f"\n📊 Progress: {i}/{len(payloads)} ({i*100//len(payloads)}%) - ETA: {remaining/60:.1f} min\n")
        
        # Cleanup
        print("\n" + "="*70)
        print(f"✓ Completed {len(payloads)} tests in {(time.time()-start_time)/60:.1f} minutes")
        print("="*70)
        
        self.driver.quit()
        
        # Sort findings by ID
        print(f"\n{C.C}Sorting results by ID...{C.E}")
        self._sort_findings_by_id()
        
        self._print_summary()
    
    def _run_multithreaded(self, payloads):
        """Run tests with multiple threads"""
        print(f"\n{C.G}🚀 Starting tests (multi-threaded with {self.num_threads} threads)...{C.E}")
        print(f"⏱️  Estimated time: {len(payloads) * self.delay / self.num_threads / 60:.1f} minutes\n")
        
        start_time = time.time()
        completed = 0
        errors = 0
        
        # Use ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            # Submit all tasks
            future_to_payload = {}
            for index, payload in enumerate(payloads, 1):
                future = executor.submit(self._test_payload_worker, payload, index)
                future_to_payload[future] = (index, payload)
            
            # Process completed tasks
            for future in as_completed(future_to_payload):
                index, payload = future_to_payload[future]
                completed += 1
                
                try:
                    result = future.result()  # Get result or raise exception
                except Exception as e:
                    errors += 1
                    with self.print_lock:
                        print(f"{C.R}✗ Error in thread for payload {index}: {e}{C.E}")
                
                # Progress indicator (every 10 payloads or every thread completion)
                if completed % max(1, len(payloads) // 20) == 0 or completed == len(payloads):
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (len(payloads) - completed) / rate if rate > 0 else 0
                    percent = completed * 100 // len(payloads)
                    
                    with self.print_lock:
                        print(f"\n{C.C}📊 Progress: {completed}/{len(payloads)} ({percent}%) | Errors: {errors} | ETA: {remaining/60:.1f} min{C.E}\n")
        
        # Cleanup
        print(f"\n{'='*70}")
        print(f"{C.G}✓ Completed {len(payloads)} tests in {(time.time()-start_time)/60:.1f} minutes{C.E}")
        print(f"{C.C}Threads used: {self.num_threads} | Errors: {errors}{C.E}")
        print("="*70)
        
        # Sort findings by ID
        print(f"\n{C.C}Sorting results by ID...{C.E}")
        self._sort_findings_by_id()
        
        self._print_summary()
    
    def _is_browser_alive(self, driver):
        """Check if browser instance is still alive"""
        try:
            # Try to execute simple command
            driver.current_url
            return True
        except:
            return False
    
    def _test_payload_worker(self, payload, index):
        """Worker method for testing payload in separate thread"""
        driver = None
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Create browser instance for this thread
                if driver is None or not self._is_browser_alive(driver):
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    driver = self._create_browser_instance()
                
                # Test payload with this driver
                self._test_payload_with_driver(driver, payload, index)
                
                return True
                
            except Exception as e:
                retry_count += 1
                error_str = str(e)
                
                # Check if it's a connection error (browser crashed)
                if 'Connection refused' in error_str or 'Connection aborted' in error_str or 'RemoteDisconnected' in error_str or 'Alert Text:' in error_str:
                    # Browser crashed or alert issue, retry silently
                    if retry_count == 1:
                        # Only log on first retry
                        with self.print_lock:
                            print(f"{C.Y}    [ID {index}] Browser issue detected, retrying...{C.E}")
                    
                    # Force close dead browser
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = None
                    
                    time.sleep(1)  # Wait before retry
                    
                    if retry_count >= max_retries:
                        with self.print_lock:
                            print(f"{C.Y}    [ID {index}] Payload skipped after retries{C.E}")
                        break
                else:
                    # Other error, log and exit
                    with self.print_lock:
                        print(f"{C.R}[{index}] Thread error: {error_str[:100]}{C.E}")
                    break
        
        # Cleanup
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        return False
    
    def _test_payload_with_driver(self, driver, payload, index):
        """Test single payload with given driver (thread-safe version)"""
        # Temporarily assign driver to self for reusing existing methods
        original_driver = self.driver
        self.driver = driver
        
        try:
            with self.print_lock:
                print(f"\n{C.B}[{index}]{C.E} Testing payload ID {index}...")
                print(f"    Payload: {payload[:80]}...")
            
            # Reuse existing test_payload logic
            self._test_payload_internal(payload, index)
                
        except Exception as e:
            with self.print_lock:
                print(f"    {C.R}✗ Thread error: {str(e)[:100]}{C.E}")
        finally:
            # Restore original driver
            self.driver = original_driver
    
    def _test_payload_internal(self, payload, index):
        """Internal payload testing logic (reused by both single and multi-threaded)"""
        from selenium.common.exceptions import UnexpectedAlertPresentException
        
        try:
            # Store current payload
            self.current_payload = payload
            
            # Build URL based on mode
            if self.request_obj:
                test_url = self._build_url_from_request(payload)
                
                if self.request_obj.cookies:
                    self._set_cookies(test_url, self.request_obj.cookies)
                
                try:
                    if self.request_obj.method == 'POST':
                        self._do_post_request(test_url, payload)
                    else:
                        self.driver.get(test_url)
                except UnexpectedAlertPresentException:
                    # Alert during navigation, dismiss it
                    self._dismiss_alerts()
            else:
                test_url = self.target_url.replace('FUZZ', payload)
                try:
                    self.driver.get(test_url)
                except UnexpectedAlertPresentException:
                    # Alert during navigation, dismiss it
                    self._dismiss_alerts()
            
            time.sleep(0.5)
            
            # Dismiss any alerts that appeared during page load
            alert_text = self._dismiss_alerts()
            if alert_text:
                # Alert detected - this is actually a good sign (XSS triggered)
                if self.num_threads <= 1:
                    print(f"    ℹ Alert detected: {alert_text[:50]}...")
                else:
                    with self.print_lock:
                        print(f"    ℹ [ID {index}] Alert detected: {alert_text[:50]}...")
            
            # FIRST-ORDER CHECK
            try:
                current_url = self.driver.current_url
                detection_type, found, escaped, details = self.detect_xss_execution(payload, self.attacker_server)
                
                # Process results (with print lock for threading)
                self._process_and_save_results(detection_type, details, index, payload, test_url, current_url, 'first-order')
            except UnexpectedAlertPresentException:
                # Alert during detection, dismiss and continue
                self._dismiss_alerts()
                if self.num_threads <= 1:
                    print(f"    ℹ Alert interrupted detection, dismissed")
                else:
                    with self.print_lock:
                        print(f"    ℹ [ID {index}] Alert interrupted detection, dismissed")
            
            # Trigger events
            try:
                if self.num_threads <= 1:
                    print(f"    Triggering events (hover/click)...")
                else:
                    with self.print_lock:
                        print(f"    Triggering events (hover/click)...")
                
                self.try_trigger_events()
            except UnexpectedAlertPresentException:
                # Alert during event triggering
                self._dismiss_alerts()
            
            # Wait for callback
            if self.num_threads <= 1:
                print(f"    Waiting {self.delay}s for callback...")
            else:
                with self.print_lock:
                    print(f"    Waiting {self.delay}s for callback...")
            
            time.sleep(self.delay)
            
            if self.num_threads <= 1:
                print(f"    {C.G}✓{C.E} Done (check callback server for confirmed hits)\n")
            else:
                with self.print_lock:
                    print(f"    {C.G}✓{C.E} Done (check callback server for confirmed hits)\n")
            
            # SECOND-ORDER CHECK
            if self.second_order_obj:
                self._check_second_order(payload, index)
                
        except TimeoutException:
            # Dismiss alerts before logging timeout
            self._dismiss_alerts()
            
            msg = f"    {C.Y}⚠{C.E} Page load timeout (might still work)"
            if self.num_threads > 1:
                with self.print_lock:
                    print(msg)
            else:
                print(msg)
            time.sleep(self.delay)
        except Exception as e:
            # Dismiss alerts before logging error
            try:
                self._dismiss_alerts()
            except:
                pass
            
            # Filter out noisy errors
            error_str = str(e)
            if 'Alert Text:' in error_str or 'UnexpectedAlertOpenError' in error_str:
                # Alert error already handled, skip logging
                pass
            else:
                msg = f"    {C.R}✗ Error: {str(e)[:200]}{C.E}"
                if self.num_threads > 1:
                    with self.print_lock:
                        print(msg)
                else:
                    print(msg)
    
    def _process_and_save_results(self, detection_type, details, index, payload, test_url, current_url, location):
        """Process detection results and save (thread-safe)"""
        # Print results (with lock if multithreaded)
        def safe_print(msg):
            if self.num_threads > 1:
                with self.print_lock:
                    print(msg)
            else:
                print(msg)
        
        # Process based on detection type
        if detection_type == 'html-reflected':
            safe_print(f"    {C.G}🎯 [ID {index}] HTML-REFLECTED XSS [CONFIRMED]{C.E}")
            safe_print(f"    {C.G}✓{C.E} Payload in HTML response: {details['matched_payload'][:60]}...")
            safe_print(f"    {C.C}Reflections:{C.E} {details['reflections']} time(s)")
            if details.get('dom_executed'):
                safe_print(f"    {C.G}✓{C.E} Execution CONFIRMED via Performance API")
            if details.get('script_injected'):
                safe_print(f"    {C.G}✓{C.E} Script tag FOUND in DOM")
            
            # Save (thread-safe)
            with self.results_lock:
                self.potential_xss.append({
                    'id': index,
                    'payload': payload,
                    'matched_payload': details['matched_payload'],
                    'reflections': details['reflections'],
                    'url': test_url if not self.request_obj else f"{self.request_obj.method} {self.request_obj.path}",
                    'location': location,
                    'type': 'html-reflected',
                    'page_url': current_url
                })
            
            self._save_finding_threadsafe(index, payload, details['reflections'],
                                         test_url if not self.request_obj else f"{self.request_obj.method} {self.request_obj.path}",
                                         location, current_url, details['matched_payload'], 'html-reflected')
        
        elif detection_type == 'dom-executed':
            safe_print(f"    {C.G}🎯 [ID {index}] DOM-BASED XSS [CONFIRMED]{C.E}")
            safe_print(f"    {C.G}✓{C.E} Execution DETECTED via browser (not in HTML response)")
            if details.get('dom_executed'):
                safe_print(f"    {C.G}✓{C.E} Resource load to callback server detected (Performance API)")
            if details.get('script_injected'):
                safe_print(f"    {C.G}✓{C.E} Script tag with callback URL found in DOM")
            if details.get('url_injection'):
                safe_print(f"    {C.C}ℹ{C.E} Payload present in URL, not present in HTML response")
            
            with self.results_lock:
                self.potential_xss.append({
                    'id': index,
                    'payload': payload,
                    'matched_payload': details['matched_payload'],
                    'reflections': 0,
                    'url': test_url if not self.request_obj else f"{self.request_obj.method} {self.request_obj.path}",
                    'location': location,
                    'type': 'dom-based',
                    'page_url': current_url
                })
            
            self._save_finding_threadsafe(index, payload, 0,
                                         test_url if not self.request_obj else f"{self.request_obj.method} {self.request_obj.path}",
                                         location, current_url, details['matched_payload'], 'dom-based')
        
        elif detection_type == 'html-escaped':
            safe_print(f"    ℹ [ID {index}] Reflected but ESCAPED ({details.get('reflections', 0)}x) - likely blocked")
        
        elif detection_type == 'url-injection':
            safe_print(f"    ℹ [ID {index}] Payload in URL but NOT executed (no callback detected yet)")
            safe_print(f"    💡 May execute later or need user interaction")
        
        else:
            safe_print(f"    ℹ [ID {index}] Payload NOT detected in any form")
    
    def _save_finding_threadsafe(self, payload_id, payload, reflections, url, location='first-order', page_url='', matched_payload=None, detection_type='unknown'):
        """Thread-safe version of _save_finding"""
        with self.file_lock:
            self._save_finding(payload_id, payload, reflections, url, location, page_url, matched_payload, detection_type)
    
    def _sort_findings_by_id(self):
        """Sort findings file by payload ID for easy review"""
        try:
            import re
            
            if not os.path.exists(self.output_file):
                return
            
            with open(self.output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by separator lines
            entries = re.split(r'={70}\n', content)
            
            # Separate header and payload entries
            header = []
            payload_entries = []
            
            for entry in entries:
                if entry.strip():
                    # Check if it's a payload entry (contains "Payload ID:")
                    if 'Payload ID:' in entry:
                        # Extract ID from entry
                        id_match = re.search(r'Payload ID:\s*(\d+)', entry)
                        if id_match:
                            payload_id = int(id_match.group(1))
                            payload_entries.append((payload_id, entry))
                    else:
                        # Header or comment
                        header.append(entry)
            
            # Sort payload entries by ID
            payload_entries.sort(key=lambda x: x[0])
            
            # Reconstruct file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Write header
                for h in header:
                    f.write(h)
                    if not h.endswith('\n'):
                        f.write('\n')
                
                # Write sorted entries
                for payload_id, entry in payload_entries:
                    f.write('='*70 + '\n')
                    f.write(entry)
                    if not entry.endswith('\n'):
                        f.write('\n')
            
            print(f"{C.G}✓ Sorted findings by ID: {self.output_file}{C.E}")
        except Exception as e:
            print(f"{C.Y}⚠ Could not sort findings: {e}{C.E}")
    
    def _print_summary(self):
        """Print summary of findings"""
        # Summary
        if self.potential_xss:
            # Count by type and location
            html_reflected = [f for f in self.potential_xss if f.get('type') == 'html-reflected']
            dom_based = [f for f in self.potential_xss if f.get('type') == 'dom-based']
            first_order = [f for f in self.potential_xss if f.get('location') == 'first-order']
            second_order = [f for f in self.potential_xss if f.get('location') == 'second-order']
            
            print(f"\n{C.B}{C.C}{'='*70}{C.E}")
            print(f"{C.B}{C.G}🎯 XSS FINDINGS SUMMARY: {len(self.potential_xss)} total{C.E}")
            print(f"{C.B}{C.C}{'='*70}{C.E}")
            print(f"{C.C}Saved to:{C.E} {C.Y}{self.output_file}{C.E}\n")
            
            # By detection method
            if html_reflected:
                print(f"{C.G}📊 HTML-Reflected XSS: {len(html_reflected)} [CONFIRMED]{C.E}")
                for finding in html_reflected[:5]:  # Show first 5
                    loc = "2nd-order" if finding.get('location') == 'second-order' else "1st-order"
                    print(f"   {C.C}-{C.E} ID {C.Y}{finding['id']}{C.E} ({loc}): {finding.get('reflections', 0)} reflection(s)")
            
            if dom_based:
                print(f"\n{C.G}📊 DOM-Based XSS: {len(dom_based)} [CONFIRMED]{C.E}")
                for finding in dom_based[:5]:
                    loc = "2nd-order" if finding.get('location') == 'second-order' else "1st-order"
                    print(f"   {C.C}-{C.E} ID {C.Y}{finding['id']}{C.E} ({loc}): Executed via Performance API")
            
            print(f"\n{C.B}{C.C}{'='*70}{C.E}")
            
            # By location
            if first_order:
                print(f"\n{C.C}📍 First-order:{C.E} {len(first_order)} findings")
            
            if second_order:
                print(f"{C.C}📍 Second-order (Stored):{C.E} {len(second_order)} findings")
        else:
            print(f"\n   {C.Y}No XSS detected{C.E}")
        
        print(f"\n{C.G}💡 Check callback_server.py for additional confirmation{C.E}")
        print(f"{C.G}💡 All findings saved in {self.output_file}{C.E}\n")
        
        self.driver.quit()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Automated XSS Testing with Headless Browser - Browser-Based Fuzzing + Source Code Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # GET request (use URL encoded wordlist)
  python3 auto_xss_test.py --request burp_get.txt --wordlist wordlists/url_payloads.txt
  
  # POST form-urlencoded
  python3 auto_xss_test.py --request burp_post_form.txt --wordlist wordlists/www_input_payloads.txt
  
  # POST JSON
  python3 auto_xss_test.py --request burp_post_json.txt --wordlist wordlists/json_input_payloads.txt
  
  # Multi-threaded (5 threads - default)
  python3 auto_xss_test.py --request burp.txt --wordlist wordlists/www_input_payloads.txt --threads 5
  
  # Fast mode (10 threads, 1s delay)
  python3 auto_xss_test.py --request burp.txt --wordlist wordlists/www_input_payloads.txt --threads 10 --delay 1
  
  # With second-order XSS detection (stored XSS)
  python3 auto_xss_test.py --request burp_post.txt --second-order burp_display.txt --wordlist wordlists/www_input_payloads.txt
  
  # Single-threaded mode (careful testing)
  python3 auto_xss_test.py --request burp.txt --wordlist wordlists/www_input_payloads.txt --threads 1
  
  # With visible browser (for debugging, single-threaded only)
  python3 auto_xss_test.py --request burp_request.txt --wordlist wordlists/www_input_payloads.txt --threads 1 --no-headless

Request file format (copy from Burp Suite):
  GET /test-xss?search=FUZZ HTTP/2
  Host: target.com
  Cookie: session=abc123
  User-Agent: Mozilla/5.0...
  
  (body for POST requests)

Second-order file format:
  GET /user/profile HTTP/1.1
  Host: target.com
  Cookie: session=abc123
  
  (No FUZZ marker needed - just the page where payload might appear)

Features:
  • First-order XSS detection (immediate reflection)
  • Second-order XSS detection (stored XSS display on different page)
  • Automatic callback detection (for auto-trigger payloads)
  • Source code analysis (detects non-escaped reflections)
  • Event triggering (hover/click to activate interaction-based payloads)
  • [NEED_TO_VERIFY] tagging for manual verification

Output files:
  • result.txt - Confirmed XSS (from callback server)
  • potential_xss.txt - Potential XSS [NEED_TO_VERIFY] (from source analysis)
    - Includes both first-order and second-order findings
        """
    )
    
    # Target options (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument('--target', help='Target URL with FUZZ placeholder')
    target_group.add_argument('--request', help='HTTP request file (Burp format) with FUZZ marker')
    
    # Other options
    parser.add_argument('--wordlist', default='wordlists/www_input_payloads.txt', help='Payload wordlist (default: www_input_payloads.txt)')
    parser.add_argument('--server', default='', help='Callback server URL (auto-detected from wordlist if not specified)')
    parser.add_argument('--threads', type=int, default=1, help='Number of concurrent threads (default: 1, max: 10)')
    parser.add_argument('--delay', type=int, default=3, help='Delay (seconds) after loading each page (default: 3)')
    parser.add_argument('--output', default='result/findings.txt', help='Output file for XSS findings (default: result/findings.txt)')
    parser.add_argument('--second-order', dest='second_order', help='Second-order request file (Burp format) to check for stored XSS')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window (for debugging)')
    
    args = parser.parse_args()
    
    # Validate
    if args.target and 'FUZZ' not in args.target:
        print("✗ Error: Target URL must contain 'FUZZ' placeholder")
        print("  Example: https://target.com/search?q=FUZZ")
        sys.exit(1)
    
    tester = XSSAutoTester(
        target_url=args.target,
        request_file=args.request,
        wordlist_path=args.wordlist,
        delay=args.delay,
        headless=not args.no_headless,
        output_file=args.output,
        second_order_file=args.second_order,
        attacker_server=args.server if args.server else 'https://attacker.com',
        num_threads=args.threads
    )
    
    tester.run()

if __name__ == '__main__':
    main()

