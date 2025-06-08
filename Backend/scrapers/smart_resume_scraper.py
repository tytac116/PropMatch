#!/usr/bin/env python3
"""
Smart Auto-Resume Property24 Scraper
====================================

An intelligent scraper that can resume from ANY interruption point by:
- Auto-detecting current state from existing files
- Automatically determining which API key to use
- Calculating the correct starting page
- Robust error handling and automatic retries
- Smart API key rotation when credits are exhausted

Author: AI Assistant
Date: 2025-06-06
"""

import os
import re
import json
import csv
import math
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

from models.models import PropertyData, POI
from .enhanced_property24_scraper import EnhancedProperty24Scraper

# Load environment variables
load_dotenv('config/.env')

class SmartResumeScraper:
    """Intelligent auto-resume scraper that can restart from any point"""
    
    def __init__(self, data_file: str = "data/property24_production_20250605_165810.json"):
        self.data_file = data_file
        self.setup_logging()
        self.load_config()
        self.setup_api_keys()
        self.setup_directories()
        self.auto_detect_current_state()
        self.initialize_tracking()
        
        # Initialize the enhanced scraper
        self.base_scraper = EnhancedProperty24Scraper()
        
        # Rate limiting
        self.last_request_time = 0
        self.request_interval = 60 / int(os.getenv('MAX_SCRAPES_PER_MINUTE', 10))
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 5
        
        self.logger.info("🧠 Smart Resume Scraper initialized successfully")
        self.display_current_state()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/smart_resume_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.log_filename = log_filename
    
    def load_config(self):
        """Load configuration from environment variables"""
        self.max_credits_per_key = int(os.getenv('MAX_CREDITS_PER_KEY', 490))
        self.total_credits = int(os.getenv('TOTAL_AVAILABLE_CREDITS', 2940))
        self.max_scrapes_per_minute = int(os.getenv('MAX_SCRAPES_PER_MINUTE', 10))
    
    def setup_api_keys(self):
        """Setup API key rotation system"""
        self.api_keys = []
        key_index = 1
        
        while True:
            key = os.getenv(f'FIRECRAWL_API_KEY_{key_index}')
            if not key:
                break
            self.api_keys.append(key)
            key_index += 1
        
        if not self.api_keys:
            raise ValueError("No API keys found in environment variables")
        
        self.logger.info(f"Loaded {len(self.api_keys)} API keys")
    
    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs('production_data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    def auto_detect_current_state(self):
        """Intelligently detect current state from existing files"""
        self.logger.info("🔍 Auto-detecting current state...")
        
        # Load existing properties
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.existing_properties = json.load(f)
            self.logger.info(f"Found {len(self.existing_properties)} existing properties")
        else:
            self.existing_properties = []
            self.logger.warning(f"No existing data file found: {self.data_file}")
        
        # Find the most recent tracking file
        tracking_files = []
        for file in os.listdir('production_data'):
            if 'tracking.json' in file:
                tracking_files.append(f"production_data/{file}")
        
        if tracking_files:
            # Get the most recent tracking file
            latest_tracking = max(tracking_files, key=os.path.getmtime)
            self.logger.info(f"Found tracking file: {latest_tracking}")
            
            with open(latest_tracking, 'r') as f:
                tracking_data = json.load(f)
            
            # Extract state from tracking data
            credits_per_key = tracking_data.get('credits_used_per_key', {})
            self.credits_used_per_key = [
                int(credits_per_key.get(str(i+1), 0)) for i in range(len(self.api_keys))
            ]
            self.current_key_index = tracking_data.get('current_api_key', 1) - 1
            
            self.logger.info(f"Detected API key state: {self.credits_used_per_key}")
            self.logger.info(f"Current API key: {self.current_key_index + 1}")
            
        else:
            # No tracking file found, start fresh
            self.logger.warning("No tracking file found, starting with fresh API key state")
            self.credits_used_per_key = [0] * len(self.api_keys)
            self.current_key_index = 0
        
        # Ensure we're using a valid API key with available credits
        self.find_next_available_key()
        
        # Calculate starting page
        properties_count = len(self.existing_properties)
        self.start_page = max(1, math.ceil(properties_count / 23) + 1)
        
        self.logger.info(f"Calculated starting page: {self.start_page}")
        
        # Initialize current app
        self.current_app = FirecrawlApp(api_key=self.api_keys[self.current_key_index])
    
    def find_next_available_key(self):
        """Find the next API key with available credits"""
        original_index = self.current_key_index
        
        while self.credits_used_per_key[self.current_key_index] >= self.max_credits_per_key:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            # If we've cycled through all keys
            if self.current_key_index == original_index:
                total_used = sum(self.credits_used_per_key)
                if total_used >= self.total_credits - 50:
                    raise Exception("All API keys exhausted!")
                break
        
        self.logger.info(f"Using API key {self.current_key_index + 1}")
        self.logger.info(f"Credits used on this key: {self.credits_used_per_key[self.current_key_index]}/{self.max_credits_per_key}")
    
    def display_current_state(self):
        """Display current state for user confirmation"""
        total_used = sum(self.credits_used_per_key)
        remaining_total = self.total_credits - total_used
        remaining_current = self.max_credits_per_key - self.credits_used_per_key[self.current_key_index]
        
        print(f"\n🧠 SMART RESUME SCRAPER - CURRENT STATE 🧠")
        print(f"├─ Existing properties: {len(self.existing_properties)}")
        print(f"├─ Calculated starting page: {self.start_page}")
        print(f"├─ Current API key: {self.current_key_index + 1}/{len(self.api_keys)}")
        print(f"├─ Current key credits: {self.credits_used_per_key[self.current_key_index]}/{self.max_credits_per_key} (remaining: {remaining_current})")
        print(f"├─ Total credits used: {total_used}/{self.total_credits}")
        print(f"├─ Total credits remaining: {remaining_total}")
        print(f"├─ API key status:")
        for i, used in enumerate(self.credits_used_per_key):
            status = "ACTIVE" if i == self.current_key_index else ("EXHAUSTED" if used >= self.max_credits_per_key else "AVAILABLE")
            print(f"│  ├─ Key {i+1}: {used}/490 ({status})")
        print(f"└─ Ready to continue scraping!")
        print("=" * 60)
    
    def initialize_tracking(self):
        """Initialize tracking for this session"""
        self.new_properties = []
        self.total_scraped_this_session = 0
        self.successful_scrapes_this_session = 0
        self.failed_scrapes_this_session = 0
        self.skipped_properties = []
        self.start_time = datetime.now()
        
        # Create tracking file for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.tracking_file = f"production_data/smart_resume_{timestamp}_tracking.json"
        self.save_tracking_data()
    
    def rotate_api_key(self) -> bool:
        """Rotate to next available API key"""
        if self.credits_used_per_key[self.current_key_index] >= self.max_credits_per_key:
            self.logger.info(f"API key {self.current_key_index + 1} exhausted")
            
            original_index = self.current_key_index
            while True:
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                
                if self.credits_used_per_key[self.current_key_index] < self.max_credits_per_key:
                    self.current_app = FirecrawlApp(api_key=self.api_keys[self.current_key_index])
                    self.logger.info(f"🔄 Switched to API key {self.current_key_index + 1}")
                    return True
                
                if self.current_key_index == original_index:
                    self.logger.error("🚨 All API keys exhausted!")
                    return False
        
        return True
    
    def rate_limit_wait(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            wait_time = self.request_interval - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def save_incremental_data(self):
        """Save all properties (existing + new) to the main data file"""
        if not self.new_properties:
            return
        
        # Combine existing + new properties
        all_properties = self.existing_properties + [prop.to_dict() for prop in self.new_properties]
        
        # Save to main file
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(all_properties, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Updated main file: {len(all_properties)} total properties")
    
    def display_progress(self):
        """Display real-time progress"""
        total_used = sum(self.credits_used_per_key)
        remaining_total = self.total_credits - total_used
        remaining_current = self.max_credits_per_key - self.credits_used_per_key[self.current_key_index]
        
        print(f"\n🚀 SCRAPING PROGRESS 🚀")
        print(f"├─ Existing properties: {len(self.existing_properties)}")
        print(f"├─ New properties this session: {len(self.new_properties)}")
        print(f"├─ Total properties: {len(self.existing_properties) + len(self.new_properties)}")
        print(f"├─ Session success rate: {(self.successful_scrapes_this_session / max(self.total_scraped_this_session, 1)) * 100:.1f}%")
        print(f"├─ Current API Key: {self.current_key_index + 1}/{len(self.api_keys)}")
        print(f"├─ Current key: {self.credits_used_per_key[self.current_key_index]}/{self.max_credits_per_key} (remaining: {remaining_current})")
        print(f"├─ Total credits used: {total_used}")
        print(f"└─ Total credits remaining: {remaining_total}")
        print("=" * 60)
    
    def scrape_with_retry(self, url: str) -> Optional[PropertyData]:
        """Scrape a property with intelligent retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                # Check API key availability
                if not self.rotate_api_key():
                    self.logger.error("No more API credits available")
                    return None
                
                # Rate limiting
                self.rate_limit_wait()
                
                # Track credit usage
                self.credits_used_per_key[self.current_key_index] += 1
                self.total_scraped_this_session += 1
                
                print(f"Scraping property: {url}")
                self.logger.info(f"API Key {self.current_key_index + 1} - Credit {self.credits_used_per_key[self.current_key_index]}/{self.max_credits_per_key}")
                
                # Use enhanced scraper with our API app
                original_app = self.base_scraper.app
                self.base_scraper.app = self.current_app
                
                property_data = self.base_scraper.scrape_individual_property(url)
                
                # Restore original app
                self.base_scraper.app = original_app
                
                # Validate scraping success
                if property_data and property_data.title and property_data.price:
                    self.successful_scrapes_this_session += 1
                    self.new_properties.append(property_data)
                    
                    # Save incrementally
                    self.save_incremental_data()
                    
                    print(f"✅ Successfully scraped: {property_data.title}")
                    
                    # Show progress
                    self.display_progress()
                    
                    return property_data
                else:
                    self.logger.warning(f"Incomplete data for {url} - attempt {attempt + 1}")
                    if attempt == self.max_retries:
                        self.failed_scrapes_this_session += 1
                        self.skipped_properties.append(url)
                        return None
            
            except Exception as e:
                self.logger.error(f"Error scraping {url} - attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    self.failed_scrapes_this_session += 1
                    self.skipped_properties.append(url)
                    return None
        
        return None
    
    def save_tracking_data(self):
        """Save current progress to tracking file"""
        tracking_data = {
            "timestamp": datetime.now().isoformat(),
            "existing_properties": len(self.existing_properties),
            "new_properties_this_session": len(self.new_properties),
            "total_properties": len(self.existing_properties) + len(self.new_properties),
            "session_scraped": self.total_scraped_this_session,
            "session_successful": self.successful_scrapes_this_session,
            "session_failed": self.failed_scrapes_this_session,
            "credits_used_per_key": {str(i+1): credits for i, credits in enumerate(self.credits_used_per_key)},
            "current_api_key": self.current_key_index + 1,
            "total_credits_used": sum(self.credits_used_per_key),
            "remaining_credits": self.total_credits - sum(self.credits_used_per_key),
            "skipped_properties_count": len(self.skipped_properties),
            "runtime_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "current_page": self.start_page
        }
        
        with open(self.tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
    
    def run_smart_scrape(self):
        """Run the intelligent scraping operation"""
        self.logger.info("🧠 Starting Smart Resume Scraping")
        self.logger.info("=" * 80)
        
        try:
            page_num = self.start_page
            
            while sum(self.credits_used_per_key) < self.total_credits - 50:
                print(f"\n📄 Scraping page {page_num}")
                self.logger.info(f"Scraping listing page {page_num}")
                
                # Get listing page (uses 1 credit)
                if not self.rotate_api_key():
                    break
                
                self.rate_limit_wait()
                self.credits_used_per_key[self.current_key_index] += 1
                
                # Scrape listing page
                original_app = self.base_scraper.app
                self.base_scraper.app = self.current_app
                page_result = self.base_scraper.scrape_listing_page(page_num)
                self.base_scraper.app = original_app
                
                if not page_result['success']:
                    self.logger.error(f"Failed to scrape listing page {page_num}")
                    break
                
                property_urls = page_result['property_urls']
                
                if not property_urls:
                    self.logger.warning(f"No properties found on page {page_num}")
                    break
                
                print(f"Found {len(property_urls)} properties on page {page_num}")
                
                # Scrape each property
                for i, url in enumerate(property_urls, 1):
                    if sum(self.credits_used_per_key) >= self.total_credits - 10:
                        self.logger.warning("🚨 Approaching credit limit!")
                        break
                    
                    property_data = self.scrape_with_retry(url)
                    
                    # Save tracking every 10 properties
                    if len(self.new_properties) % 10 == 0:
                        self.save_tracking_data()
                
                page_num += 1
                
                # Check stopping conditions
                if sum(self.credits_used_per_key) >= self.total_credits - 50:
                    self.logger.info("💳 Credit limit approaching, stopping...")
                    break
        
        except KeyboardInterrupt:
            self.logger.info("⏹️ Scraping interrupted by user")
        except Exception as e:
            self.logger.error(f"💥 Unexpected error: {str(e)}")
        
        finally:
            self.finalize_scraping()
    
    def finalize_scraping(self):
        """Finalize and generate reports"""
        self.logger.info("🏁 Finalizing scraping session...")
        
        # Final save
        self.save_tracking_data()
        
        # Generate report
        self.generate_final_report()
        
        self.logger.info("✅ Smart scraping session completed!")
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        runtime = end_time - self.start_time
        
        total_props = len(self.existing_properties) + len(self.new_properties)
        
        print(f"\n🎯 FINAL SMART RESUME REPORT 🎯")
        print(f"├─ Session runtime: {runtime}")
        print(f"├─ Properties at start: {len(self.existing_properties)}")
        print(f"├─ New properties scraped: {len(self.new_properties)}")
        print(f"├─ Total properties now: {total_props}")
        print(f"├─ Session success rate: {(self.successful_scrapes_this_session / max(self.total_scraped_this_session, 1)) * 100:.1f}%")
        print(f"├─ Total credits used: {sum(self.credits_used_per_key)}")
        print(f"├─ Credits remaining: {self.total_credits - sum(self.credits_used_per_key)}")
        print(f"├─ Data file: {self.data_file}")
        print(f"└─ Tracking file: {self.tracking_file}")
        print("=" * 60)

def main():
    """Main entry point"""
    print("🧠 Smart Auto-Resume Property24 Scraper")
    print("=" * 60)
    
    try:
        scraper = SmartResumeScraper()
        scraper.run_smart_scrape()
    except Exception as e:
        print(f"💥 Critical error: {e}")
        logging.error(f"Critical error: {e}")

if __name__ == "__main__":
    main() 