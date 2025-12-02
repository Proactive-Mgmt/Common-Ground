#!/usr/bin/env python3
"""
Analyze HTML snapshots from the Practice Fusion scraping process.
This script checks for common issues in the captured HTML files.
"""

import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_html_file(filepath: Path):
    """Analyze a single HTML file for diagnostic information."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {filepath.name}")
    print(f"{'='*80}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check file size
    file_size = len(html_content)
    print(f"File size: {file_size:,} bytes")
    
    # Check for login page indicators
    login_indicators = [
        soup.find(id='inputUsername'),
        soup.find(id='inputPswd'),
        soup.find(id='loginButton'),
        soup.find(text=lambda t: t and 'login' in t.lower() and 'sign' in t.lower()),
    ]
    if any(login_indicators):
        print("⚠️  WARNING: Page appears to be a LOGIN page")
        print("   - Authentication may have failed")
    
    # Check for MFA page
    mfa_indicators = [
        soup.find(id='code'),
        soup.find(id='sendCodeButton'),
        soup.find(id='sendCallButton'),
        soup.find(text=lambda t: t and 'security' in t.lower() and 'code' in t.lower()),
    ]
    if any(mfa_indicators):
        print("⚠️  WARNING: Page appears to be an MFA page")
        print("   - MFA authentication may be required or failing")
    
    # Check for schedule page
    schedule_indicators = [
        soup.find('div', {'data-element': 'appointments-table'}),
        soup.find('button', {'class': lambda c: c and 'rotate-180' in c}),
        soup.find(text=lambda t: t and 'schedule' in t.lower()),
    ]
    if any(schedule_indicators):
        print("✓ Page appears to be a SCHEDULE page")
        
        # Check for appointment table
        appt_table = soup.find('div', {'data-element': 'appointments-table'})
        if appt_table:
            print("  ✓ Appointments table found")
        
        # Check for print view
        print_view_table = soup.find('table', {'data-element': 'table-agenda-print'})
        if print_view_table:
            print("  ✓ Print view table found")
            
            # Count appointments in print view
            rows = print_view_table.find_all('tr')
            if rows:
                # First row is header
                num_appointments = len(rows) - 1
                print(f"  📊 Found {num_appointments} appointments in print view")
                
                # Show first few appointments
                for i, row in enumerate(rows[1:6], 1):  # Show first 5
                    patient_td = row.find('td', {'data-element': 'td-patient-name'})
                    status_td = row.find('td', {'data-element': 'td-intake-status'})
                    type_td = row.find('td', {'data-element': 'td-appointment-type'})
                    provider_td = row.find('td', {'data-element': 'td-provider-name'})
                    
                    if patient_td and status_td and type_td:
                        patient_name = patient_td.text.strip().split('\n')[0]
                        status = status_td.text.strip()
                        appt_type = type_td.text.strip()
                        provider = provider_td.text.strip() if provider_td else 'N/A'
                        
                        emoji = "✓" if status == "Seen" and appt_type == "CLINICIAN" else "○"
                        print(f"  {emoji} {i}. {patient_name} | {status} | {appt_type} | {provider}")
        else:
            print("  ⚠️ Print view table NOT found")
    
    # Check for error pages
    error_indicators = [
        soup.find(text=lambda t: t and 'error' in t.lower()),
        soup.find(text=lambda t: t and '404' in str(t)),
        soup.find(text=lambda t: t and '500' in str(t)),
        soup.find(text=lambda t: t and 'not found' in t.lower()),
    ]
    if any(error_indicators):
        print("❌ ERROR: Page appears to contain error messages")
    
    # Check page title
    title = soup.find('title')
    if title:
        print(f"Page title: {title.text.strip()}")
    
    # Check for specific date in schedule
    h3_elements = soup.find_all('h3')
    for h3 in h3_elements:
        if 'Schedule Standard view' in h3.text:
            print(f"Schedule date: {h3.text}")
            break
    
    # Check URL from meta tags or scripts
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical:
        print(f"Canonical URL: {canonical.get('href')}")

def main():
    screenshots_dir = Path(__file__).parent.parent / 'screenshots'
    
    if not screenshots_dir.exists():
        print(f"Error: {screenshots_dir} does not exist")
        sys.exit(1)
    
    # Find all HTML files
    html_files = sorted(screenshots_dir.glob('*.html'))
    
    if not html_files:
        print(f"No HTML files found in {screenshots_dir}")
        sys.exit(1)
    
    print(f"Found {len(html_files)} HTML files to analyze\n")
    
    # Analyze each file in order
    for html_file in html_files:
        analyze_html_file(html_file)
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()

