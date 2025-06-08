import os
import re
import json
import math
import time
from typing import List, Dict, Any, Optional
from firecrawl import FirecrawlApp
from models.models import PropertyData, POI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

class EnhancedProperty24Scraper:
    def __init__(self):
        self.api_key = "fc-14ac47b3a1da455c9a1aad36ef4bebc0"
        self.app = FirecrawlApp(api_key=self.api_key)
        
        # Improved URL structure based on the successful old scraper
        self.base_url = "https://www.property24.com/for-sale/cape-town/western-cape/432"
        self.query_params = "?PropertyCategory=House%2cApartmentOrFlat%2cTownhouse&sp=so%3dNewest"
        self.listings_per_page = 20  # Expected properties per page
        
    def build_page_url(self, page_number: int) -> str:
        """Construct the URL for a given overview page using the successful pattern."""
        if page_number == 1:
            return f"{self.base_url}{self.query_params}"
        else:
            return f"{self.base_url}/p{page_number}{self.query_params}"
    
    def extract_total_properties(self, markdown: str) -> Optional[int]:
        """Extract the total number of properties from text like 'Showing : 1 - 20 of 1326'"""
        patterns = [
            r"Showing\s*:\s*\d+\s*-\s*\d+\s*of\s*([\d,]+)",
            r"(\d+)\s+properties\s+found",
            r"(\d+)\s+results\s+found"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1).replace(",", ""))
                except ValueError:
                    continue
        return None
    
    def extract_property_urls_improved(self, markdown: str) -> List[str]:
        """Extract property URLs using multiple patterns to maximize extraction."""
        property_urls = []
        
        # Pattern 1: URLs in markdown image links - this is where most properties are
        # Look for: [![...](image_url)](property_url)
        image_link_pattern = r'\]\(https://images\.prop24\.com/[^\)]+\)\]\((https://www\.property24\.com/for-sale/[^\)]+)\)'
        matches = re.findall(image_link_pattern, markdown)
        for match in matches:
            url = match.strip()
            if url not in property_urls:
                property_urls.append(url)
        
        # Pattern 2: URLs in price/description sections  
        # Look for property URLs following price information
        price_pattern = r'\[R [0-9\s,]+.*?\]\((https://www\.property24\.com/for-sale/[^\)]+)\)'
        matches = re.findall(price_pattern, markdown)
        for match in matches:
            url = match.strip()
            if url not in property_urls:
                property_urls.append(url)
        
        # Pattern 3: Direct URL extraction
        direct_patterns = [
            r'https://www\.property24\.com/for-sale/[^/]+/[^/]+/western-cape/\d+/\d+\?[^\s\)]+',
            r'https://www\.property24\.com/for-sale/[^\s\)\]]+\?plId=\d+[^\s\)]*'
        ]
        
        for pattern in direct_patterns:
            matches = re.findall(pattern, markdown)
            for match in matches:
                # Clean URL
                url = match.split(')')[0].split(']')[0].split(' ')[0]
                if url not in property_urls:
                    property_urls.append(url)
        
        # Pattern 4: Look in the listings section specifically
        # Split by common property listing markers
        listing_sections = re.split(r'(?=\[!\[.*?\]\(https://images\.prop24\.com)', markdown)
        
        for section in listing_sections:
            # Look for property URLs in each section
            url_matches = re.findall(r'https://www\.property24\.com/for-sale/[^\s\)\]]+', section)
            for url in url_matches:
                clean_url = url.split(')')[0].split(']')[0].split(' ')[0]
                if clean_url not in property_urls:
                    property_urls.append(clean_url)
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in property_urls:
            # Filter out navigation and non-property URLs
            if (url not in seen and len(url) > 50 and 
                '/western-cape/' in url and
                not any(nav_pattern in url for nav_pattern in [
                    'sp=so%3dNewest', 'sp=r%3dTrue', 'sp=oa%3dTrue', 'sp=os%3dTrue', 
                    'sp=rp%3dTrue', '#', '/432?', '/432/', '/9?', '/new-developments'
                ]) and
                # Must have a listing number pattern
                re.search(r'/\d{9,}(?:\?|$)', url)):
                unique_urls.append(url)
                seen.add(url)
        
        return unique_urls
    
    def scrape_listing_page(self, page_num: int) -> Dict[str, Any]:
        """Scrape a listing page and return both total count and property URLs"""
        url = self.build_page_url(page_num)
        print(f"Scraping listing page {page_num}: {url}")
        
        try:
            result = self.app.scrape_url(url)
            markdown_content = result.get('markdown', '')
            
            # Extract total properties count
            total_properties = self.extract_total_properties(markdown_content)
            
            # Extract property URLs
            property_urls = self.extract_property_urls_improved(markdown_content)
            print(f"Found {len(property_urls)} properties on page {page_num}")
            
            # Debug: Print first few URLs
            if property_urls:
                print("Sample URLs found:")
                for i, url in enumerate(property_urls[:3]):
                    print(f"  {i+1}. {url}")
            
            return {
                'total_properties': total_properties,
                'property_urls': property_urls,
                'success': True
            }
            
        except Exception as e:
            print(f"Error scraping listing page {page_num}: {e}")
            return {
                'total_properties': None,
                'property_urls': [],
                'success': False
            }

    def extract_dynamic_features(self, markdown_content: str) -> Dict[str, Dict[str, Any]]:
        """Extract all features dynamically using the new improved methods"""
        
        # Use the new dynamic extraction methods
        rooms_data = self.extract_rooms_dynamic(markdown_content)
        external_data = self.extract_external_features_dynamic(markdown_content)
        
        # Filter additional rooms (non-standard room types)
        standard_rooms = ['Bedroom', 'Bedrooms', 'Bathroom', 'Bathrooms', 'Kitchen', 'Kitchens']
        additional_rooms = {k: v for k, v in rooms_data.items() if k not in standard_rooms}
        
        # For building features, we'll keep the existing building section extraction
        # but also add any boolean external features that might be building-related
        building_features = {}
        
        # Add building features from external data that are boolean
        building_related = ['Security', 'Alarm', 'Electric Fence', 'Access Control']
        for feature, value in external_data.items():
            if any(building_word in feature for building_word in building_related):
                building_features[feature] = value
        
        # Also extract from Building section as before
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == "Building":
                j = i + 1
                while j < len(lines) and j < i + 15:
                    current_line = lines[j].strip()
                    
                    if current_line in ['Other Features', 'External Features', 'Property Overview', 'Rooms']:
                        break
                    
                    if self.is_clean_content(current_line):
                        if j + 1 < len(lines):
                            value_line = lines[j + 1].strip()
                            if self.is_clean_content(value_line) and len(value_line) < 50:
                                building_features[current_line] = value_line
                                j += 1
                            else:
                                building_features[current_line] = True
                        else:
                            building_features[current_line] = True
                    
                    j += 1
                break
        
        result = {
            'additional_rooms': additional_rooms,
            'external_features': external_data,
            'building_features': building_features
        }
        
        print(f"Final dynamic features: {result}")
        return result
    
    def is_clean_content(self, text: str) -> bool:
        """Check if content is clean (not HTML, UI elements, etc.)"""
        if not text or len(text.strip()) < 2:
            return False
        
        text_lower = text.lower().strip()
        
        # Filter out HTML/markdown/UI elements
        unwanted_patterns = [
            'https://', 'http://', '.svg', '.gif', '.png', '.jpg',
            'view more', 'view less', 'read more', 'show more',
            'loading', 'icon_', 'content/images', 'optimized',
            'calculator', 'bond', 'deposit', 'monthly repayment',
            'qualify', 'breakdown', 'affordability', 'purchase price',
            'loan term', 'interest rate', 'gross monthly income',
            'base64-image-removed'
        ]
        
        # Filter out distance patterns
        if re.match(r'\d+\.?\d*km$', text):
            return False
        
        return not any(pattern in text_lower for pattern in unwanted_patterns)

    def extract_points_of_interest(self, markdown_content: str) -> Dict[str, List[POI]]:
        """Extract Points of Interest with categories and distances - WORKING VERSION"""
        poi_data = {}
        
        # Multiple patterns to find POI section
        poi_patterns = [
            r'Points of Interest\n\n(.*?)(?=\n\n#### |$)',
            r'Points of Interest\s*\n(.*?)(?=\n\n[A-Z][^:]*:|$)',
            r'Points of Interest(.*?)(?=\n(?:Listing|Agent|#### |$))',
            r'#### Points of Interest\n\n(.*?)(?=\n\n#### |$)',
        ]
        
        poi_text = None
        for pattern in poi_patterns:
            match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
            if match:
                poi_text = match.group(1)
                break
        
        if not poi_text:
            return poi_data
        
        # Process POI lines based on actual structure
        lines = poi_text.split('\n')
        current_category = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Skip "View more" entries
            if line == "View more":
                i += 1
                continue
            
            # Check if this is a category header
            poi_category_names = [
                'Food and Entertainment', 'Education', 'Transport and Public Services',
                'Health', 'Shopping', 'Sports and Leisure', 'Health and Medical'
            ]
            
            is_category = False
            if line in poi_category_names:
                is_category = True
            elif len(line) > 15 and any(cat_word in line for cat_word in ['and', 'Services', 'Entertainment']):
                is_category = True
            
            if is_category:
                current_category = line
                poi_data[current_category] = []
                i += 1
                continue
            
            # This should be a POI entry if we have a current category
            if current_category and line:
                poi_name = line
                
                # Look for distance on the next non-empty line
                distance = None
                j = i + 1
                while j < len(lines) and j < i + 3:
                    next_line = lines[j].strip()
                    if next_line and re.match(r'\d+\.?\d*km$', next_line):
                        distance = next_line
                        break
                    j += 1
                
                if distance:
                    poi = POI(name=poi_name, distance=distance)
                    poi_data[current_category].append(poi)
                    i = j + 1  # Skip the distance line
                else:
                    i += 1
            else:
                i += 1
        
        return poi_data

    def extract_price(self, markdown_content: str) -> Optional[float]:
        """Extract price from property markdown"""
        patterns = [
            r'R\s*([\d\s,]+)\s*\n',  # Price followed by newline
            r'R\s*([\d\s,]+)\s*Bond',  # Price before "Bond"
            r'R\s*([\d\s,]+)\s*\|',  # Price before pipe
            r'\nR\s*([\d\s,]+)',  # Price at start of line
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, markdown_content)
            if matches:
                price_str = matches[0].replace(' ', '').replace(',', '')
                try:
                    price = float(price_str)
                    if price > 100000:  # Reasonable property price
                        return price
                except:
                    continue
        return None
    
    def extract_title(self, markdown_content: str) -> str:
        """Extract property title"""
        patterns = [
            r'##### ([^#\n]+)',  # h5 heading
            r'# ([^#\n]+(?:for sale|for Sale)[^#\n]*)',  # Main heading with "for sale"
            r'(\d+\s+Bedroom\s+[^#\n]+for sale[^#\n]*)',  # Bedroom ... for sale
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, markdown_content, re.IGNORECASE)
            if matches:
                title = matches[0].strip()
                if len(title) > 10 and 'property24' not in title.lower():
                    return re.sub(r'\s+', ' ', title)
        return ""
    
    def extract_street_address(self, markdown_content: str) -> str:
        """Extract street address from Property Overview section"""
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "Street Address":
                for j in range(i+1, min(i+5, len(lines))):
                    address_line = lines[j].strip()
                    if address_line and len(address_line) > 5:
                        if not any(skip in address_line.lower() for skip in ['contact agent', 'description', 'new development']):
                            address = re.sub(r'\s+', ' ', address_line)
                            address = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', address)
                            return address.strip()
        return ""
    
    def extract_property_overview_dynamic(self, markdown_content: str) -> Dict[str, Any]:
        """Extract all Property Overview fields dynamically based on the actual structure"""
        overview_data = {}
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "Property Overview":
                print(f"Found Property Overview section at line {i}")
                
                # Process next lines looking for key-value pairs
                j = i + 1
                while j < len(lines) and j < i + 40:  # Look ahead 40 lines max
                    current_line = lines[j].strip()
                    
                    # Stop if we hit another major section
                    if current_line in ['Rooms', 'External Features', 'Building', 'Points of Interest']:
                        break
                    
                    # Skip empty lines
                    if not current_line:
                        j += 1
                        continue
                    
                    # Look for property overview keys
                    overview_keys = [
                        'Listing Number', 'Type of Property', 'Street Address', 'Listing Date',
                        'Floor Size', 'Erf Size', 'Price per m²', 'Pets Allowed', 'Rates and Taxes',
                        'Levies', 'Transfer Duty', 'Development Name'
                    ]
                    
                    if current_line in overview_keys:
                        # Look for the value in next non-empty lines
                        for k in range(j+1, min(j+5, len(lines))):
                            value_line = lines[k].strip()
                            if value_line and value_line not in overview_keys:
                                # Clean up the value
                                if current_line == 'Pets Allowed':
                                    overview_data[current_line] = value_line.lower() == 'yes'
                                elif 'Size' in current_line and 'm²' in value_line:
                                    # Extract numeric value from "64 m²"
                                    size_match = re.search(r'(\d+(?:,\d+)*)\s*m²', value_line)
                                    if size_match:
                                        overview_data[current_line] = float(size_match.group(1).replace(',', ''))
                                elif 'Price per m²' in current_line:
                                    # Extract numeric value from "R 28 906"
                                    price_match = re.search(r'R\s*([\d\s,]+)', value_line)
                                    if price_match:
                                        overview_data[current_line] = float(price_match.group(1).replace(' ', '').replace(',', ''))
                                else:
                                    overview_data[current_line] = value_line
                                break
                    
                    j += 1
                break
        
        print(f"Extracted Property Overview: {overview_data}")
        return overview_data

    def extract_rooms_dynamic(self, markdown_content: str) -> Dict[str, float]:
        """Extract all room types dynamically from the Rooms section"""
        rooms_data = {}
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "Rooms":
                print(f"Found Rooms section at line {i}")
                
                # Process next lines looking for room types and counts
                j = i + 1
                while j < len(lines) and j < i + 50:  # Increased search range
                    current_line = lines[j].strip()
                    
                    # Stop if we hit another section
                    if current_line in ['External Features', 'Building', 'Other Features', 'Property Overview']:
                        break
                    
                    # Skip empty lines and unwanted content
                    if not current_line or 'icon_read_more' in current_line or 'svg' in current_line:
                        j += 1
                        continue
                    
                    # Common room types (singular and plural forms)
                    room_types = [
                        'Bedroom', 'Bedrooms', 'Bathroom', 'Bathrooms', 'Kitchen', 'Kitchens',
                        'Reception Room', 'Reception Rooms', 'Lounge', 'Lounges', 'Dining Room', 'Dining Rooms',
                        'Study', 'Studies', 'Office', 'Offices', 'Family Room', 'Family Rooms',
                        'TV Room', 'TV Rooms', 'Entertainment Room', 'Entertainment Rooms',
                        'Scullery', 'Laundry', 'Pantry', 'Entrance Hall', 'Entrance Halls',
                        'Domestic Rooms', 'Domestic Room'
                    ]
                    
                    if current_line in room_types:
                        # Look for the count in next lines
                        found_count = False
                        for k in range(j+1, min(j+5, len(lines))):
                            value_line = lines[k].strip()
                            
                            # Check for numeric values (including decimals)
                            if value_line and re.match(r'^\d+(?:\.\d+)?$', value_line):
                                rooms_data[current_line] = float(value_line)
                                print(f"Found {current_line}: {value_line}")
                                found_count = True
                                break
                            # Check for patterns like "1 Lounge"
                            elif value_line and re.match(r'^\d+\s+\w+', value_line):
                                count_match = re.search(r'^(\d+)', value_line)
                                if count_match:
                                    rooms_data[current_line] = float(count_match.group(1))
                                    print(f"Found {current_line}: {count_match.group(1)} (from pattern)")
                                    found_count = True
                                    break
                            # If we hit another room type, stop looking
                            elif value_line in room_types:
                                break
                        
                        # If no count found but room type exists, assume 1
                        if not found_count:
                            # Only assume 1 for Kitchen, Bathroom (singular) - typical uncounted rooms
                            if current_line in ['Kitchen', 'Bathroom', 'Laundry', 'Scullery', 'Pantry']:
                                rooms_data[current_line] = 1.0
                                print(f"Found {current_line}: 1 (assumed, no count given)")
                    
                    j += 1
                break
        
        print(f"Extracted Rooms: {rooms_data}")
        return rooms_data

    def extract_external_features_dynamic(self, markdown_content: str) -> Dict[str, Any]:
        """Extract all external features dynamically with proper value types"""
        external_data = {}
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "External Features":
                print(f"Found External Features section at line {i}")
                
                # Process next lines looking for features
                j = i + 1
                while j < len(lines) and j < i + 25:
                    current_line = lines[j].strip()
                    
                    # Stop if we hit another section
                    if current_line in ['Building', 'Other Features', 'Property Overview', 'Points of Interest']:
                        break
                    
                    # Skip empty lines and unwanted content
                    if not current_line or 'icon_read_more' in current_line or 'svg' in current_line:
                        j += 1
                        continue
                    
                    # External feature types with enhanced parking/garage detection
                    external_types = [
                        'Parking', 'Garage', 'Garages', 'Pool', 'Pools', 'Garden', 'Gardens',
                        'Balcony', 'Balconies', 'Patio', 'Patios', 'Terrace', 'Terraces',
                        'Courtyard', 'Courtyards', 'Tennis Court', 'Tennis Courts',
                        'Entertainment Area', 'Braai Area', 'Boma', 'Jacuzzi', 'Spa',
                        'Driveway', 'Carport', 'Shed', 'Store Room', 'Workshop',
                        'Parking Spaces', 'Covered Parking', 'Open Parking', 'Secure Parking'
                    ]
                    
                    # Don't capture POI categories or other unrelated content
                    poi_categories = [
                        'Education', 'Transport and Public Services', 'Food and Entertainment',
                        'Health', 'Shopping', 'Sports and Leisure'
                    ]
                    
                    if current_line in external_types and current_line not in poi_categories:
                        # Look for the value in next lines
                        found_value = False
                        for k in range(j+1, min(j+4, len(lines))):
                            value_line = lines[k].strip()
                            
                            if value_line and value_line.isdigit():
                                # Numeric value
                                external_data[current_line] = float(value_line)
                                print(f"Found {current_line}: {value_line} (numeric)")
                                found_value = True
                                break
                            elif value_line and value_line.lower() in ['yes', 'no']:
                                # Boolean value
                                external_data[current_line] = value_line.lower() == 'yes'
                                print(f"Found {current_line}: {value_line} (boolean)")
                                found_value = True
                                break
                            elif value_line and re.match(r'^(\d+)\s*(spaces?|bays?|cars?)', value_line.lower()):
                                # Pattern like "2 spaces" or "3 bays" or "1 car"
                                count_match = re.search(r'^(\d+)', value_line)
                                if count_match:
                                    external_data[current_line] = float(count_match.group(1))
                                    print(f"Found {current_line}: {count_match.group(1)} (from pattern '{value_line}')")
                                    found_value = True
                                    break
                            elif not value_line or value_line in external_types:
                                # No value found, assume presence = True
                                external_data[current_line] = True
                                print(f"Found {current_line}: True (default)")
                                found_value = True
                                break
                        
                        # If we didn't find a value in the next lines, check the current line for patterns
                        if not found_value:
                            # Check if current line has a number in it (like "Parking 2" or "2 Garages")
                            if re.search(r'\d+', current_line):
                                number_match = re.search(r'(\d+)', current_line)
                                if number_match:
                                    external_data[current_line] = float(number_match.group(1))
                                    print(f"Found {current_line}: {number_match.group(1)} (from current line)")
                                else:
                                    external_data[current_line] = True
                                    print(f"Found {current_line}: True (default)")
                            else:
                                external_data[current_line] = True
                                print(f"Found {current_line}: True (default)")
                    
                    j += 1
                break
        
        print(f"Extracted External Features: {external_data}")
        return external_data

    def extract_property_details(self, markdown_content: str) -> Dict[str, Optional[float]]:
        """Extract property details using the new dynamic methods"""
        # Use the new dynamic rooms extraction
        rooms_data = self.extract_rooms_dynamic(markdown_content)
        
        # Map room types to our standard fields
        details = {
            'bedrooms': None, 'bathrooms': None, 'kitchens': None, 'garages': None,
            'parking': None, 'parking_spaces': None, 'floor_size': None, 'erf_size': None
        }
        
        # Map from rooms data
        for room_type, count in rooms_data.items():
            if room_type in ['Bedroom', 'Bedrooms']:
                details['bedrooms'] = count
            elif room_type in ['Bathroom', 'Bathrooms']:
                details['bathrooms'] = count
            elif room_type in ['Kitchen', 'Kitchens']:
                details['kitchens'] = count
        
        # Get external features for garage/parking with enhanced extraction
        external_data = self.extract_external_features_dynamic(markdown_content)
        total_parking_spaces = 0
        
        for feature_type, value in external_data.items():
            if feature_type in ['Garage', 'Garages'] and isinstance(value, (int, float)):
                details['garages'] = value
                total_parking_spaces += value
            elif feature_type == 'Parking' and isinstance(value, (int, float)):
                details['parking'] = value
                total_parking_spaces += value
            elif feature_type in ['Parking Spaces', 'Covered Parking', 'Open Parking', 'Secure Parking'] and isinstance(value, (int, float)):
                # These are additional parking spaces beyond standard parking/garage
                total_parking_spaces += value
            elif feature_type == 'Carport' and isinstance(value, (int, float)):
                # Carports count as parking spaces
                total_parking_spaces += value
        
        # Enhanced: Look for parking numbers in the description
        description = self.extract_description(markdown_content)
        if description:
            # Look for patterns like "parking for 4 vehicles", "4 parking spaces", etc.
            parking_patterns = [
                r'(\d+) secure undercover parking bays?',
                r'(\d+) secure parking bays?', 
                r'(\d+) undercover parking bays?',
                r'(\d+) parking bays?',
                r'parking for (\d+) vehicles?',
                r'(\d+) parking spaces?',
                r'(\d+) car parking',
                r'(\d+) vehicle parking',
                r'(\d+) cars? parking',
                r'parking (\d+) cars?',
                r'(\d+) garage spaces?',
                r'(\d+) covered parking',
            ]
            
            for pattern in parking_patterns:
                match = re.search(pattern, description.lower())
                if match:
                    desc_parking = int(match.group(1))
                    # Use the description number if it's higher than what we found
                    if desc_parking > total_parking_spaces:
                        total_parking_spaces = desc_parking
                        print(f"Found parking from description: {desc_parking} spaces (pattern: '{pattern}')")
                    break
        
        # If we found boolean features but no numbers, count them
        if total_parking_spaces == 0:
            for feature_type, value in external_data.items():
                if feature_type in ['Garage', 'Garages', 'Parking', 'Carport', 'Secure Parking', 'Covered Parking'] and value is True:
                    total_parking_spaces += 1
        
        # Set total parking spaces if we found any
        if total_parking_spaces > 0:
            details['parking_spaces'] = total_parking_spaces
        
        # Set individual parking/garage fields
        if 'Parking' in external_data:
            details['parking'] = 1 if external_data['Parking'] is True else external_data['Parking']
        if any(feature in external_data for feature in ['Garage', 'Garages']):
            garage_count = 0
            for feature_type, value in external_data.items():
                if feature_type in ['Garage', 'Garages']:
                    garage_count += 1 if value is True else (value if isinstance(value, (int, float)) else 0)
            if garage_count > 0:
                details['garages'] = garage_count
        
        # Get property overview for sizes
        overview_data = self.extract_property_overview_dynamic(markdown_content)
        for field, value in overview_data.items():
            if field == 'Floor Size' and isinstance(value, (int, float)):
                details['floor_size'] = value
            elif field == 'Erf Size' and isinstance(value, (int, float)):
                details['erf_size'] = value
        
        return details
    
    def extract_location_info(self, url: str) -> Dict[str, str]:
        """Extract location information from URL"""
        url_parts = url.split('/')
        info = {'suburb': '', 'city': '', 'province': '', 'location': ''}
        
        if len(url_parts) > 6:
            suburb = url_parts[4].replace('-', ' ').title()
            city = url_parts[5].replace('-', ' ').title()
            province = url_parts[6].replace('-', ' ').title()
            
            info.update({
                'suburb': suburb, 'city': city, 'province': province, 'location': suburb
            })
        
        return info
    
    def extract_listing_number(self, url: str) -> str:
        """Extract listing number from URL - improved patterns based on analysis"""
        patterns = [
            r'/(\d{9,})(?:\?|$)',  # Standard pattern: /116038600 or /116038600?
            r'/(\d+)\?plId=',      # Old pattern: /123?plId=456
            r'/(\d{8,})/',         # At least 8 digits followed by slash
            r'(\d{9,})'            # Any sequence of 9+ digits
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return ""
    
    def extract_property_type(self, markdown_content: str) -> str:
        """Extract property type"""
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "Type of Property":
                for j in range(i+1, min(i+5, len(lines))):
                    prop_type_line = lines[j].strip()
                    if prop_type_line and len(prop_type_line) > 2:
                        prop_type = prop_type_line.lower()
                        if 'commercial' in prop_type:
                            return 'commercial'
                        elif 'house' in prop_type:
                            return 'house'
                        elif 'apartment' in prop_type or 'flat' in prop_type:
                            return 'apartment'
                        elif 'townhouse' in prop_type:
                            return 'townhouse'
                        else:
                            return prop_type_line
        return ""
    
    def scrape_individual_property(self, url: str) -> PropertyData:
        """Scrape an individual property page with full dynamic features"""
        print(f"Scraping property: {url}")
        
        try:
            result = self.app.scrape_url(url)
            markdown_content = result.get('markdown', '')
            
            # Initialize property data
            property_data = PropertyData()
            property_data.url = url
            property_data.listing_number = self.extract_listing_number(url)
            property_data.transaction_type = "for-sale"
            property_data.scraped_at = datetime.now().isoformat()
            
            # Extract basic info
            property_data.title = self.extract_title(markdown_content)
            property_data.street_address = self.extract_street_address(markdown_content)
            property_data.price = self.extract_price(markdown_content)
            property_data.property_type = self.extract_property_type(markdown_content)
            
            # Extract location info
            location_info = self.extract_location_info(url)
            property_data.suburb = location_info['suburb']
            property_data.city = location_info['city']
            property_data.province = location_info['province']
            property_data.location = location_info['location']
            
            # Extract property details using new dynamic methods
            details = self.extract_property_details(markdown_content)
            property_data.bedrooms = details['bedrooms']
            property_data.bathrooms = details['bathrooms']
            property_data.kitchens = details['kitchens']
            property_data.garages = details['garages']
            property_data.parking = details['parking']
            property_data.parking_spaces = details['parking_spaces']
            property_data.floor_size = details['floor_size']
            property_data.erf_size = details['erf_size']
            
            # Extract DYNAMIC FEATURES using new methods
            dynamic_features = self.extract_dynamic_features(markdown_content)
            property_data.additional_rooms = dynamic_features['additional_rooms']
            property_data.external_features = dynamic_features['external_features']
            property_data.building_features = dynamic_features['building_features']
            
            # Extract PROPERTY OVERVIEW DATA dynamically - NEW
            overview_data = self.extract_property_overview_dynamic(markdown_content)
            
            # Map overview data to existing fields and add new ones
            for field, value in overview_data.items():
                if field == 'Pets Allowed':
                    property_data.pets_allowed = value
                elif field == 'Listing Date':
                    property_data.listing_date = value
                elif field == 'Rates and Taxes':
                    property_data.rates_and_taxes = value
                elif field == 'Street Address' and not property_data.street_address:
                    property_data.street_address = value
            
            # Extract content
            property_data.description = self.extract_description(markdown_content)
            property_data.features = self.extract_features(markdown_content)
            property_data.images = self.extract_images(markdown_content)
            
            # Extract POINTS OF INTEREST
            property_data.points_of_interest = self.extract_points_of_interest(markdown_content)
            
            print(f"Successfully scraped property {property_data.listing_number} with {len(property_data.points_of_interest)} POI categories")
            print(f"Additional rooms found: {property_data.additional_rooms}")
            return property_data
            
        except Exception as e:
            print(f"Error scraping property {url}: {e}")
            property_data = PropertyData()
            property_data.url = url
            return property_data
    
    def extract_description(self, markdown_content: str) -> str:
        """Extract property description"""
        lines = markdown_content.split('\n')
        
        title_found = False
        description_lines = []
        
        for line in lines:
            line = line.strip()
            
            if not title_found and line.startswith('#####') and len(line) > 20:
                title_found = True
                continue
            
            if title_found:
                if any(marker in line for marker in ['Property Overview', 'Facilities', 'External Features', 'Building', 'Listing number:']):
                    break
                
                if len(line) > 20 and not line.startswith('#') and not line.startswith('[') and 'property24.com' not in line:
                    if not any(skip in line.lower() for skip in ['whatsapp', 'brokers', 'read more', 'view more', 'log in']):
                        description_lines.append(line)
        
        if description_lines:
            description = ' '.join(description_lines)
            description = re.sub(r'\s+', ' ', description)
            sentences = description.split('. ')
            unique_sentences = []
            seen = set()
            for sentence in sentences:
                if sentence not in seen and len(sentence) > 10:
                    unique_sentences.append(sentence)
                    seen.add(sentence)
            return '. '.join(unique_sentences).strip()
        
        return ""
    
    def extract_features(self, markdown_content: str) -> List[str]:
        """Extract basic property features"""
        features = []
        content_lower = markdown_content.lower()
        
        feature_keywords = [
            'pet friendly', 'garden', 'pool', 'garage', 'parking', 'security',
            'fireplace', 'balcony', 'patio', 'air conditioning'
        ]
        
        for keyword in feature_keywords:
            if keyword in content_lower:
                features.append(keyword.title())
        
        return list(set(features))
    
    def extract_images(self, markdown_content: str) -> List[str]:
        """Extract image URLs"""
        image_pattern = r'https://images\.prop24\.com/\d+/'
        image_urls = re.findall(image_pattern, markdown_content)
        
        unique_images = []
        seen = set()
        for url in image_urls:
            if url not in seen:
                unique_images.append(url)
                seen.add(url)
        
        return unique_images
    
    def run_full_scrape(self, target_properties: int = 40) -> List[PropertyData]:
        """Run a complete scrape to get target number of properties"""
        print(f"Starting Enhanced Property24 scraper to collect {target_properties} properties...")
        
        all_properties = []
        page_num = 1
        total_pages_estimated = None
        
        while len(all_properties) < target_properties:
            print(f"\n{'='*50}")
            print(f"SCRAPING PAGE {page_num}")
            print(f"{'='*50}")
            
            # Get property URLs from listing page
            page_result = self.scrape_listing_page(page_num)
            
            if not page_result['success']:
                print(f"Failed to scrape page {page_num}, stopping...")
                break
            
            # Calculate total pages on first page
            if page_num == 1 and page_result['total_properties']:
                total_pages_estimated = math.ceil(page_result['total_properties'] / self.listings_per_page)
                print(f"Total properties available: {page_result['total_properties']}")
                print(f"Estimated total pages: {total_pages_estimated}")
            
            property_urls = page_result['property_urls']
            
            if not property_urls:
                print(f"No properties found on page {page_num}, stopping...")
                break
            
            print(f"\nScraping {len(property_urls)} individual properties...")
            
            # Scrape each property
            for i, url in enumerate(property_urls, 1):
                if len(all_properties) >= target_properties:
                    print(f"Reached target of {target_properties} properties, stopping...")
                    break
                
                print(f"\nProperty {i}/{len(property_urls)} (Total: {len(all_properties)+1})")
                property_data = self.scrape_individual_property(url)
                all_properties.append(property_data)
                
                # Small delay between requests
                time.sleep(2)
            
            page_num += 1
            
            # Stop if we've tried too many pages
            if total_pages_estimated and page_num > total_pages_estimated:
                print("Reached estimated total pages, stopping...")
                break
            
            # Delay between pages
            if len(all_properties) < target_properties:
                print(f"\nRate limiting: waiting 10 seconds before next page...")
                time.sleep(10)
        
        return all_properties
    
    def save_results(self, properties: List[PropertyData], filename: str = None):
        """Save scraped properties to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_scrape_{timestamp}.json"
        
        # Convert to dictionaries for JSON serialization
        properties_data = [prop.to_dict() for prop in properties]
        
        with open(filename, 'w') as f:
            json.dump(properties_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to {filename}")
        print(f"Total properties scraped: {len(properties)}")
        
        # Print summary
        successful_scrapes = [p for p in properties if p.title and p.price]
        print(f"Successfully scraped: {len(successful_scrapes)}")
        print(f"Failed scrapes: {len(properties) - len(successful_scrapes)}")

    def extract_rates_and_taxes(self, markdown_content: str) -> Optional[str]:
        """Extract rates and taxes information from Property Overview"""
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "Rates and Taxes":
                # Look in next few lines for the value
                for j in range(i+1, min(i+4, len(lines))):
                    value_line = lines[j].strip()
                    if value_line and re.match(r'R\s*[\d\s,]+', value_line):
                        return value_line
        
        return None

    def extract_pets_allowed(self, markdown_content: str) -> Optional[bool]:
        """Extract pets allowed information from Property Overview"""
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "Pets Allowed":
                # Look in next few lines for the value
                for j in range(i+1, min(i+4, len(lines))):
                    value_line = lines[j].strip().lower()
                    if value_line in ['yes', 'no']:
                        return value_line == 'yes'
        
        return None

    def extract_listing_date(self, markdown_content: str) -> Optional[str]:
        """Extract listing date from Property Overview"""
        lines = markdown_content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == "Listing Date":
                # Look in next few lines for the value
                for j in range(i+1, min(i+4, len(lines))):
                    value_line = lines[j].strip()
                    if value_line and re.match(r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December|\w{3})\s+\d{4}', value_line):
                        return value_line
        
        return None

def main():
    """Test the enhanced scraper with 40 properties"""
    scraper = EnhancedProperty24Scraper()
    
    print("Starting Enhanced Property24 scraper with FULL DYNAMIC FEATURES and POI extraction...")
    print("Target: 40 properties from Cape Town sale listings")
    
    properties = scraper.run_full_scrape(target_properties=40)
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enhanced_40_properties_{timestamp}.json"
    scraper.save_results(properties, filename)
    
    # Print detailed summary
    print(f"\n{'='*50}")
    print("ENHANCED SCRAPING SUMMARY")
    print(f"{'='*50}")
    
    successful_scrapes = [p for p in properties if p.title and p.price]
    if successful_scrapes:
        print(f"\nSample properties with dynamic features:")
        for i, sample in enumerate(successful_scrapes[:3], 1):
            print(f"\n{i}. {sample.title}")
            print(f"   Price: R {sample.price:,.0f}" if sample.price else "   Price: Not found")
            print(f"   Location: {sample.location}")
            print(f"   Bedrooms: {sample.bedrooms}, Bathrooms: {sample.bathrooms}")
            print(f"   Type: {sample.property_type}")
            print(f"   Additional Rooms: {len(sample.additional_rooms)} found")
            print(f"   External Features: {len(sample.external_features)} found")
            print(f"   Building Features: {len(sample.building_features)} found")
            print(f"   POI Categories: {len(sample.points_of_interest)} found")
            if sample.points_of_interest:
                for category, pois in list(sample.points_of_interest.items())[:2]:
                    print(f"     - {category}: {len(pois)} locations")

if __name__ == "__main__":
    main() 