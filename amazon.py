#!/usr/bin/env python3
import requests
import re
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

class AmazonEmailChecker:
    def __init__(self):
        self.version = "2.0"
        self.tmp_dir = "./tmp"
        self.log_file = "./checker.log"
        self.valid_file = "./valid_emails.txt"
        self.invalid_file = "./invalid_emails.txt"
        self.retry_file = "./retry_emails.txt"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.timeout = 10
        self.max_retries = 2
        self.email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Initialize files and directories
        self.init_files()
    
    def init_files(self):
        os.makedirs(self.tmp_dir, exist_ok=True)
        open(self.log_file, 'w').close()
        open(self.valid_file, 'w').close()
        open(self.invalid_file, 'w').close()
        open(self.retry_file, 'w').close()
    
    def show_banner(self):
        print(f"""
  _______ _           _       _      _______    
 |__   __(_)Sel3a    | |9wiya| |    |__   __|   
    | |   _ _ __   __| | __ _| |_The   | |_ __  
    | |  | | '_ \ / _` |/ _` | | | | | | | '_ \ 
    | |  | | | | | (_| | (_| | | |_| |_| | | | |
    |_|  |_|_| |_|\__,_|\__,_|_|\__, (_)_|_| |_|
     Just For Fun!               __/ |          
                                |___/  
              #############################
              #     Amazon checker V1     #
              #############################                                            
                    

""")
    
    def validate_email_format(self, email):
        return bool(self.email_regex.match(email))
    
    def check_email(self, email):
        url = "https://www.amazon.com/ap/register"
        params = {
            '_encoding': 'UTF8',
            'openid.assoc_handle': 'usflex',
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.mode': 'checkid_setup',
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.ns.pape': 'http://specs.openid.net/extensions/pape/1.0',
            'openid.pape.max_auth_age': '0',
            'openid.return_to': 'https://www.amazon.com/gp/yourstore/home?ie=UTF8&ref_=gno_newcust',
            'email': email
        }
        
        headers = {'User-Agent': self.user_agent}
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                if "Create account" in response.text:
                    return "invalid"
                else:
                    return "valid"
            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                if attempt == self.max_retries - 1:
                    return "failed"
                continue
    
    def process_email(self, email, count, total):
        if not self.validate_email_format(email):
            status = f"[!] Skipping invalid email format: {email}"
            self.log(status)
            return "skipped"
        
        result = self.check_email(email)
        
        if result == "valid":
            with open(self.valid_file, 'a') as f:
                f.write(f"{email}\n")
            status = f"[+] {email} - Valid"
            self.log(status)
            return "valid"
        elif result == "invalid":
            with open(self.invalid_file, 'a') as f:
                f.write(f"{email}\n")
            status = f"[-] {email} - Invalid"
            self.log(status)
            return "invalid"
        else:
            with open(self.retry_file, 'a') as f:
                f.write(f"{email}\n")
            status = f"[?] {email} - Check failed"
            self.log(status)
            return "failed"
    
    def log(self, message):
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(f"{message}\n")
    
    def process_file(self, email_file):
        with open(email_file, 'r') as f:
            emails = [line.strip() for line in f if line.strip()]
        
        total = len(emails)
        results = {
            'valid': 0,
            'invalid': 0,
            'failed': 0,
            'skipped': 0
        }
        
        print(f"\n[*] Processing {total} emails...\n")
        
        # Using ThreadPoolExecutor for concurrent checking
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i, email in enumerate(emails, 1):
                future = executor.submit(
                    self.process_email, email, i, total
                )
                futures.append(future)
            
            for future in futures:
                result = future.result()
                results[result] += 1
                progress = sum(results.values())
                percentage = (progress * 100) // total
                print(f"\r[*] Progress: {progress}/{total} ({percentage}%)", end='', flush=True)
        
        print("\n\n=== Results ===")
        print(f"[+] Valid: {results['valid']}")
        print(f"[-] Invalid: {results['invalid']}")
        print(f"[!] Failed: {results['failed']}")
        print(f"[!] Skipped: {results['skipped']}")
        print(f"\nValid emails saved to: {self.valid_file}")
        print(f"Invalid emails saved to: {self.invalid_file}")
        print(f"Failed checks saved to: {self.retry_file}")
        print(f"Full log saved to: {self.log_file}")

if __name__ == "__main__":
    checker = AmazonEmailChecker()
    checker.show_banner()
    
    import sys
    if len(sys.argv) > 1:
        email_file = sys.argv[1]
    else:
        email_file = input("Enter email list file: ")
    
    if not os.path.isfile(email_file):
        print(f"[ERROR] File not found: {email_file}")
        sys.exit(1)
    
    checker.process_file(email_file)