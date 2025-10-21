#!/usr/bin/env python3
"""
Simple XSS Callback Server - Detect Working Payloads
Tracks which XSS payloads successfully execute by monitoring ?id=N parameter
"""

import ssl
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════
CONFIG = {
    'DOMAIN': 'your-domain.com',
    'CERT_DIR': './ssl-certs',
    'HTTP_PORT': 80,
    'HTTPS_PORT': 443,
    'ENABLE_HTTP': True,
    'ENABLE_HTTPS': True,
    'REDIRECT_HTTP_TO_HTTPS': True,
    'RESULT_FILE': None,  # Will be set from command-line
    'WORDLIST_PATH': 'wordlists/www_input_payloads.txt',  # Default wordlist
    'CTF_MODE': False,  # CTF mode - limit hits per payload
    'MAX_HITS': 3,  # Max hits per payload in CTF mode
}

# CTF Mode - Track hits per payload ID
PAYLOAD_HIT_COUNT = {}  # {payload_id: count}

# ANSI Colors
class C:
    G = '\033[92m'  # Green
    Y = '\033[93m'  # Yellow
    R = '\033[91m'  # Red
    C = '\033[96m'  # Cyan
    B = '\033[1m'   # Bold
    E = '\033[0m'   # End

class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle all GET requests"""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        # Check if HTTPS redirect needed
        if CONFIG['REDIRECT_HTTP_TO_HTTPS'] and not isinstance(self.connection, ssl.SSLSocket):
            host = self.headers.get('Host', CONFIG['DOMAIN'])
            https_url = f"https://{host}{self.path}"
            self.send_response(301)
            self.send_header('Location', https_url)
            self.end_headers()
            return
        
        # Log the request
        self._log_request(parsed, query_params)
        
        # Send simple response
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'// XSS payload executed successfully')
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        self._log_request(parsed, query_params)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _get_payload_from_wordlist(self, payload_id):
        """Retrieve payload content from wordlist"""
        try:
            wordlist_path = CONFIG['WORDLIST_PATH']
            if not os.path.exists(wordlist_path):
                return None
            
            with open(wordlist_path, 'r', encoding='utf-8') as f:
                payload_count = 0  # Track actual payload number
                for line in f:
                    # Skip comments and empty lines
                    if line.strip() and not line.strip().startswith('#'):
                        payload_count += 1
                        # This is a payload line
                        if payload_count == int(payload_id):
                            return line.strip()
            return None
        except Exception as e:
            print(f"{C.R}✗ Error reading wordlist: {e}{C.E}")
            return None
    
    def _save_to_result_file(self, payload_id, payload_content, timestamp, ip, referer, hit_count=None):
        """Save working payload to result file"""
        if not CONFIG['RESULT_FILE']:
            return
        
        try:
            # Create result directory if needed
            result_dir = os.path.dirname(CONFIG['RESULT_FILE'])
            if result_dir and not os.path.exists(result_dir):
                os.makedirs(result_dir, exist_ok=True)
            
            # Check if file exists to determine if we need header
            file_exists = os.path.exists(CONFIG['RESULT_FILE'])
            
            with open(CONFIG['RESULT_FILE'], 'a', encoding='utf-8') as f:
                if not file_exists:
                    # Write header
                    f.write("="*80 + "\n")
                    f.write("WORKING XSS PAYLOADS - CALLBACK RESULTS\n")
                    if CONFIG['CTF_MODE']:
                        f.write(f"CTF Mode: Max {CONFIG['MAX_HITS']} hits per payload\n")
                    f.write("="*80 + "\n\n")
                
                # Write payload entry with CTF status if applicable
                if CONFIG['CTF_MODE'] and hit_count:
                    if hit_count == CONFIG['MAX_HITS']:
                        f.write(f"[{timestamp}] [CONFIRMED] Payload ID: {payload_id} (Hit {hit_count}/{CONFIG['MAX_HITS']})\n")
                    else:
                        f.write(f"[{timestamp}] Payload ID: {payload_id} (Hit {hit_count}/{CONFIG['MAX_HITS']})\n")
                else:
                    f.write(f"[{timestamp}] Payload ID: {payload_id}\n")
                
                f.write(f"From IP: {ip}\n")
                f.write(f"Referer: {referer}\n")
                f.write(f"Payload:\n{payload_content}\n")
                f.write("-"*80 + "\n\n")
            
            print(f"{C.G}✓ Saved to result file: {CONFIG['RESULT_FILE']}{C.E}")
        except Exception as e:
            print(f"{C.R}✗ Error saving to result file: {e}{C.E}")
    
    def _log_request(self, parsed, query_params):
        """Log request with payload ID detection"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip = self.client_address[0]
        protocol = 'HTTPS' if isinstance(self.connection, ssl.SSLSocket) else 'HTTP'
        
        # Extract payload ID
        payload_id = None
        if 'id' in query_params:
            payload_id = query_params['id'][0]
        
        # Get User-Agent
        user_agent = self.headers.get('User-Agent', 'Unknown')
        referer = self.headers.get('Referer', 'Direct')
        
        # CTF MODE: Check if should accept this payload ID
        if CONFIG['CTF_MODE'] and payload_id:
            current_hits = PAYLOAD_HIT_COUNT.get(payload_id, 0)
            
            if current_hits >= CONFIG['MAX_HITS']:
                # Already confirmed - silently reject
                # No log, no spam
                return
            
            # Record this hit
            PAYLOAD_HIT_COUNT[payload_id] = current_hits + 1
            hit_count = PAYLOAD_HIT_COUNT[payload_id]
        else:
            hit_count = None
        
        # Display hit
        if payload_id:
            # Get actual payload content from wordlist
            payload_content = self._get_payload_from_wordlist(payload_id)
            
            print(f"{C.G}{'='*70}{C.E}")
            
            # CTF Mode - Show hit count
            if CONFIG['CTF_MODE'] and hit_count:
                if hit_count < CONFIG['MAX_HITS']:
                    print(f"{C.B}{C.G}🎯 XSS PAYLOAD HIT! ({hit_count}/{CONFIG['MAX_HITS']}){C.E}")
                else:
                    print(f"{C.B}{C.G}✅ XSS PAYLOAD CONFIRMED! ({hit_count}/{CONFIG['MAX_HITS']}){C.E}")
            else:
                print(f"{C.B}{C.G}🎯 XSS PAYLOAD HIT!{C.E}")
            
            print(f"{C.G}{'='*70}{C.E}")
            print(f"{C.C}Time:{C.E}       {timestamp}")
            print(f"{C.C}Payload ID:{C.E}  {C.B}{C.Y}{payload_id}{C.E}")
            
            # CTF Mode - Show hit progress
            if CONFIG['CTF_MODE'] and hit_count:
                print(f"{C.C}Hit Count:{C.E}  {C.B}{C.Y}{hit_count}/{CONFIG['MAX_HITS']}{C.E}")
            
            print(f"{C.C}From IP:{C.E}    {ip}")
            print(f"{C.C}Protocol:{C.E}   {protocol}")
            print(f"{C.C}Path:{C.E}       {parsed.path}")
            print(f"{C.C}Referer:{C.E}    {referer[:60]}...")
            print(f"{C.C}User-Agent:{C.E} {user_agent[:60]}...")
            
            if payload_content:
                print(f"{C.C}Payload:{C.E}     {payload_content[:80]}...")
            
            print(f"{C.G}{'='*70}{C.E}")
            
            # CTF Mode - Show status
            if CONFIG['CTF_MODE'] and hit_count:
                if hit_count == CONFIG['MAX_HITS']:
                    print(f"{C.G}✅ CONFIRMED! Future requests for ID {payload_id} will be silently rejected{C.E}")
                else:
                    print(f"{C.Y}💡 {CONFIG['MAX_HITS'] - hit_count} more hit(s) needed to confirm{C.E}")
            
            print(f"{C.Y}💡 Find payload:{C.E} sed -n '{payload_id}p' {CONFIG['WORDLIST_PATH']}")
            print(f"{C.G}{'='*70}{C.E}\n")
            
            # Save to log file (in same folder as result file if specified)
            if CONFIG['RESULT_FILE']:
                log_dir = os.path.dirname(CONFIG['RESULT_FILE'])
                log_file = os.path.join(log_dir, 'xss_hits.log') if log_dir else 'xss_hits.log'
                # Create log directory if needed
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
            else:
                log_file = 'xss_hits.log'
            
            with open(log_file, 'a') as f:
                f.write(f"[{timestamp}] ID={payload_id} IP={ip} Protocol={protocol} Referer={referer}\n")
            
            # Save to result file (if enabled)
            if payload_content:
                self._save_to_result_file(payload_id, payload_content, timestamp, ip, referer, hit_count)
        else:
            # No ID parameter - just regular request
            print(f"{C.C}[{timestamp}]{C.E} {protocol} {C.Y}{parsed.path}{C.E} from {ip}")

def sort_result_file(result_file):
    """Sort result file by payload ID for easy review"""
    try:
        import re
        
        if not os.path.exists(result_file):
            return
        
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by separator lines
        entries = re.split(r'-{80}\n', content)
        
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
                    # Header
                    header.append(entry)
        
        # Sort payload entries by ID
        payload_entries.sort(key=lambda x: x[0])
        
        # Reconstruct file
        with open(result_file, 'w', encoding='utf-8') as f:
            # Write header
            for h in header:
                f.write(h)
                if not h.endswith('\n'):
                    f.write('\n')
            
            # Write sorted entries
            for payload_id, entry in payload_entries:
                f.write(entry)
                if not entry.endswith('\n'):
                    f.write('\n')
                f.write('-'*80 + '\n\n')
        
        print(f"{C.G}✓ Sorted result file by ID: {result_file}{C.E}")
    except Exception as e:
        print(f"{C.Y}⚠ Could not sort result file: {e}{C.E}")

def sort_xss_hits_log(log_file='xss_hits.log'):
    """Sort xss_hits.log by payload ID for easy review"""
    try:
        import re
        
        if not os.path.exists(log_file):
            return
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract ID from each line and sort
        entries = []
        for line in lines:
            if line.strip():
                # Extract ID from line like: [timestamp] ID=123 ...
                id_match = re.search(r'ID=(\d+)', line)
                if id_match:
                    payload_id = int(id_match.group(1))
                    entries.append((payload_id, line))
        
        # Sort by ID
        entries.sort(key=lambda x: x[0])
        
        # Write back sorted
        with open(log_file, 'w', encoding='utf-8') as f:
            for payload_id, line in entries:
                f.write(line)
        
        print(f"{C.G}✓ Sorted log file by ID: {log_file}{C.E}")
    except Exception as e:
        print(f"{C.Y}⚠ Could not sort log file: {e}{C.E}")

def check_and_kill_port(port):
    """Kill process using the port"""
    import subprocess
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        if result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                subprocess.run(['kill', '-9', pid], capture_output=True)
            import time
            time.sleep(1)
    except:
        pass
    return True

def merge_ca_bundle(cert_path, cert_dir, domain):
    """Merge CA bundle with domain certificate if available"""
    ca_files = ['ca.cer', 'ca.crt', 'ca_bundle.crt', 'chain.pem']
    ca_path = None
    
    for ca_file in ca_files:
        ca_candidate = os.path.join(cert_dir, ca_file)
        if os.path.exists(ca_candidate):
            ca_path = ca_candidate
            break
    
    if not ca_path:
        return cert_path
    
    merged_path = os.path.join(cert_dir, f'{domain}_merged.crt')
    try:
        with open(merged_path, 'w') as merged:
            with open(cert_path, 'r') as cert:
                merged.write(cert.read())
            merged.write('\n')
            with open(ca_path, 'r') as ca:
                merged.write(ca.read())
        print(f"{C.G}✓ Merged CA bundle: {os.path.basename(ca_path)}{C.E}")
        return merged_path
    except Exception as e:
        print(f"{C.Y}⚠ Could not merge CA bundle: {e}{C.E}")
        return cert_path

def run_server(port, use_https, cert_dir=None, cert_file=None, key_file=None, silent=False):
    """Run HTTP or HTTPS server"""
    check_and_kill_port(port)
    
    httpd = HTTPServer(('0.0.0.0', port), CallbackHandler)
    protocol = 'HTTP'
    
    if use_https:
        # Determine cert paths
        if not cert_dir:
            cert_dir = CONFIG['CERT_DIR']
        
        cert_dir = os.path.abspath(cert_dir)
        
        if not os.path.exists(cert_dir):
            print(f"{C.R}✗ Certificate directory not found: {cert_dir}{C.E}")
            sys.exit(1)
        
        # Auto-detect cert files
        if cert_file and key_file:
            cert_path = os.path.join(cert_dir, cert_file)
            key_path = os.path.join(cert_dir, key_file)
        else:
            # Try common patterns
            cert_path = None
            key_path = None
            
            for ext in ['.cer', '.crt', '.pem']:
                test_cert = os.path.join(cert_dir, f'{CONFIG["DOMAIN"]}{ext}')
                test_key = os.path.join(cert_dir, f'{CONFIG["DOMAIN"]}.key')
                if os.path.exists(test_cert) and os.path.exists(test_key):
                    cert_path = test_cert
                    key_path = test_key
                    break
            
            if not cert_path:
                # Try any .cer/.crt file
                for f in os.listdir(cert_dir):
                    if f.endswith(('.cer', '.crt', '.pem')) and not f.endswith('_merged.crt'):
                        cert_path = os.path.join(cert_dir, f)
                        key_name = f.replace('.cer', '.key').replace('.crt', '.key').replace('.pem', '.key')
                        key_path = os.path.join(cert_dir, key_name)
                        if os.path.exists(key_path):
                            break
        
        if not cert_path or not key_path or not os.path.exists(cert_path) or not os.path.exists(key_path):
            print(f"{C.R}✗ SSL certificate files not found in {cert_dir}{C.E}")
            print(f"\n{C.Y}Place your certificate files in {cert_dir}:{C.E}")
            print(f"  - {CONFIG['DOMAIN']}.cer (or .crt)")
            print(f"  - {CONFIG['DOMAIN']}.key")
            print(f"  - ca.cer (optional - will auto-merge)\n")
            sys.exit(1)
        
        # Merge CA bundle if available
        cert_path = merge_ca_bundle(cert_path, cert_dir, CONFIG['DOMAIN'])
        
        # Load SSL
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        protocol = 'HTTPS'
    
    if not silent:
        print(f"\n{C.B}{C.C}{'='*70}{C.E}")
        if CONFIG['CTF_MODE']:
            print(f"{C.B}{C.G}🎯 XSS Callback Server - CTF Mode{C.E}")
        else:
            print(f"{C.B}{C.C}🎯 XSS Callback Server - Payload Tracker{C.E}")
        print(f"{C.B}{C.C}{'='*70}{C.E}")
        print(f"{C.C}Port:{C.E} {C.B}{port}{C.E} | {C.C}Protocol:{C.E} {C.B}{protocol}{C.E}")
        if use_https:
            print(f"{C.C}Certificate:{C.E} {os.path.basename(cert_path)}")
        
        # CTF Mode info
        if CONFIG['CTF_MODE']:
            print(f"\n{C.G}CTF Mode:{C.E} {C.B}ENABLED{C.E}")
            print(f"{C.C}Max hits per payload:{C.E} {C.Y}{CONFIG['MAX_HITS']}{C.E}")
            print(f"{C.C}Behavior:{C.E} After {CONFIG['MAX_HITS']} hits → Silent reject (prevent spam)")
        
        print(f"\n{C.C}Monitoring for:{C.E} ?id=N parameter")
        print(f"{C.C}Wordlist:{C.E} {CONFIG['WORDLIST_PATH']}")
        
        # Determine log file location
        if CONFIG['RESULT_FILE']:
            log_dir = os.path.dirname(CONFIG['RESULT_FILE'])
            log_file_display = os.path.join(log_dir, 'xss_hits.log') if log_dir else 'xss_hits.log'
            print(f"{C.C}Log file:{C.E} {log_file_display}")
            print(f"{C.C}Result file:{C.E} {C.G}{CONFIG['RESULT_FILE']}{C.E} (working payloads)")
        else:
            print(f"{C.C}Log file:{C.E} xss_hits.log")
        print(f"\n{C.Y}Waiting for XSS callbacks...{C.E}")
        print(f"{C.B}{C.C}{'='*70}{C.E}\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{C.Y}🛑 Stopping {protocol} server...{C.E}")
        httpd.shutdown()
        httpd.server_close()
        
        # Sort files on shutdown
        print(f"\n{C.C}Sorting files by ID...{C.E}")
        
        if CONFIG['RESULT_FILE']:
            log_dir = os.path.dirname(CONFIG['RESULT_FILE'])
            log_file = os.path.join(log_dir, 'xss_hits.log') if log_dir else 'xss_hits.log'
            
            # Sort result file
            sort_result_file(CONFIG['RESULT_FILE'])
            
            # Sort log file
            sort_xss_hits_log(log_file)
        else:
            # Sort log file only
            sort_xss_hits_log('xss_hits.log')

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Simple XSS Callback Server - Track Working Payloads',
        epilog="""
Examples:
  # Normal mode (unlimited hits)
  sudo python3 callback_server.py --domain your-domain.com --cert-dir ./ssl-certs --result working.txt
  
  # CTF mode (max 3 hits per payload, prevent spam)
  sudo python3 callback_server.py --domain your-domain.com --cert-dir ./ssl-certs --result working.txt --ctf-mode
  
  # CTF mode with custom max hits
  sudo python3 callback_server.py --domain your-domain.com --cert-dir ./ssl-certs --result working.txt --ctf-mode --max-hits 5
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--http-only', action='store_true', help='HTTP only')
    parser.add_argument('--https-only', action='store_true', help='HTTPS only')
    parser.add_argument('--http-port', type=int, default=80, help='HTTP port (default: 80)')
    parser.add_argument('--https-port', type=int, default=443, help='HTTPS port (default: 443)')
    parser.add_argument('--cert-dir', type=str, default='./ssl-certs', help='Certificate directory')
    parser.add_argument('--domain', type=str, help='Domain name')
    parser.add_argument('--result', type=str, default='result/working.txt', help='Save working payloads to file (default: result/working.txt)')
    parser.add_argument('--wordlist', type=str, default='wordlists/www_input_payloads.txt', help='Wordlist path (default: www_input_payloads.txt)')
    parser.add_argument('--ctf-mode', action='store_true', help='CTF mode - limit hits per payload to prevent spam')
    parser.add_argument('--max-hits', type=int, default=3, help='Max hits per payload in CTF mode (default: 3)')
    
    args = parser.parse_args()
    
    if args.domain:
        CONFIG['DOMAIN'] = args.domain
    if args.cert_dir:
        CONFIG['CERT_DIR'] = args.cert_dir
    
    # Always set result file (has default now)
    CONFIG['RESULT_FILE'] = args.result
    
    # Create result directory if needed
    if CONFIG['RESULT_FILE']:
        result_dir = os.path.dirname(CONFIG['RESULT_FILE'])
        if result_dir and not os.path.exists(result_dir):
            os.makedirs(result_dir, exist_ok=True)
        print(f"{C.G}✓ Working payloads will be saved to: {args.result}{C.E}")
    
    if args.wordlist:
        CONFIG['WORDLIST_PATH'] = args.wordlist
    if args.ctf_mode:
        CONFIG['CTF_MODE'] = True
        CONFIG['MAX_HITS'] = args.max_hits
        print(f"{C.G}✓ CTF Mode enabled: Max {args.max_hits} hits per payload{C.E}")
        print(f"{C.Y}  After {args.max_hits} hits → Silent reject (prevent spam){C.E}")
    
    try:
        if args.http_only:
            run_server(args.http_port, False)
        elif args.https_only:
            run_server(args.https_port, True, cert_dir=args.cert_dir)
        else:
            # Run both
            print(f"\n{C.B}{C.C}{'='*70}{C.E}")
            if CONFIG['CTF_MODE']:
                print(f"{C.B}{C.G}🎯 XSS Callback Server - Dual Mode (CTF){C.E}")
            else:
                print(f"{C.B}{C.C}🎯 XSS Callback Server - Dual Mode{C.E}")
            print(f"{C.B}{C.C}{'='*70}{C.E}")
            print(f"{C.C}HTTP Port:{C.E}  {C.B}{args.http_port}{C.E}")
            print(f"{C.C}HTTPS Port:{C.E} {C.B}{args.https_port}{C.E}")
            print(f"{C.C}Auto-redirect:{C.E} HTTP → HTTPS")
            
            # CTF Mode info
            if CONFIG['CTF_MODE']:
                print(f"\n{C.G}CTF Mode:{C.E} {C.B}ENABLED{C.E}")
                print(f"{C.C}Max hits per payload:{C.E} {C.Y}{CONFIG['MAX_HITS']}{C.E}")
                print(f"{C.C}Behavior:{C.E} After {CONFIG['MAX_HITS']} hits → Silent reject (prevent spam)")
            
            print(f"\n{C.C}Wordlist:{C.E} {CONFIG['WORDLIST_PATH']}")
            
            # Determine log file location
            if CONFIG['RESULT_FILE']:
                log_dir = os.path.dirname(CONFIG['RESULT_FILE'])
                log_file_display = os.path.join(log_dir, 'xss_hits.log') if log_dir else 'xss_hits.log'
                print(f"{C.C}Log file:{C.E} {log_file_display}")
                print(f"{C.C}Result file:{C.E} {C.G}{CONFIG['RESULT_FILE']}{C.E} (working payloads)")
            else:
                print(f"{C.C}Log file:{C.E} xss_hits.log")
            print(f"\n{C.Y}Waiting for XSS callbacks...{C.E}")
            print(f"{C.B}{C.C}{'='*70}{C.E}\n")
            
            # Start HTTP in background
            http_thread = threading.Thread(
                target=run_server,
                args=(args.http_port, False, None, None, None, True),
                daemon=True
            )
            http_thread.start()
            
            # Run HTTPS in main thread
            run_server(args.https_port, True, cert_dir=args.cert_dir, silent=True)
    
    except KeyboardInterrupt:
        print(f"\n{C.G}✓ Server stopped{C.E}\n")
        
        # Sort files on shutdown
        print(f"{C.C}Sorting files by ID...{C.E}")
        
        if CONFIG['RESULT_FILE']:
            log_dir = os.path.dirname(CONFIG['RESULT_FILE'])
            log_file = os.path.join(log_dir, 'xss_hits.log') if log_dir else 'xss_hits.log'
            
            # Sort result file
            sort_result_file(CONFIG['RESULT_FILE'])
            
            # Sort log file
            sort_xss_hits_log(log_file)
        else:
            # Sort log file only
            sort_xss_hits_log('xss_hits.log')
        
        print(f"{C.G}✓ Done{C.E}\n")

if __name__ == '__main__':
    main()
