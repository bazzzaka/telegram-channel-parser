"""
Module for extracting location information from text.
Specializes in handling Ukrainian text.
"""

import re
from typing import List, Tuple, Optional

from geopy.geocoders import Nominatim
import transliterate

# Keywords for location detection in Ukrainian
UA_LOCATION_KEYWORDS = [
    "місто", "село", "вулиця", "проспект", "бульвар", "площа", "район",
    "область", "регіон", "перехрестя", "шосе", "траса", "автомагістраль",
    "міст", "станція", "зупинка", "метро", "аеропорт", "вокзал", "порт",
]

# Keywords for danger information detection
DANGER_KEYWORDS = [
    "небезпека", "загроза", "тривога", "обстріл", "вибух", "пожежа", "аварія",
    "евакуація", "сирена", "радіація", "хімічна", "біологічна", "ядерна",
    "повітряна", "ракетна", "артилерійська", "мінометна", "снайперська",
    "заміновано", "підозрілий", "постраждалі", "жертви", "руйнування",
]


class LocationExtractor:
    """Class for extracting location information from text."""
    
    def __init__(self):
        """Initialize the location extractor."""
        self.geolocator = Nominatim(user_agent="tg-channel-parser")
        
        # Compile regex patterns
        self.coordinate_pattern = re.compile(
            r'(?P<lat>\d+\.\d+)[,\s]+(?P<lng>\d+\.\d+)'
        )
        
        # Compile location keyword patterns
        self.location_keywords_pattern = re.compile(
            r'(?:^|\s)(' + '|'.join(UA_LOCATION_KEYWORDS) + r')[\s:]([^.!?,;]+)',
            re.IGNORECASE | re.UNICODE
        )
        
        # Compile danger keyword patterns
        self.danger_keywords_pattern = re.compile(
            r'(?:^|\s)(' + '|'.join(DANGER_KEYWORDS) + r')[\s:]?([^.!?,;]+)',
            re.IGNORECASE | re.UNICODE
        )
    
    def extract_locations(self, text: str) -> List[Tuple[str, float, float]]:
        """Extract location information from text.
        
        Args:
            text: Text to extract locations from
        
        Returns:
            List of tuples containing (original_text, latitude, longitude)
        """
        locations = []
        
        # Extract coordinates
        for match in self.coordinate_pattern.finditer(text):
            lat = float(match.group("lat"))
            lng = float(match.group("lng"))
            original_text = match.group(0)
            locations.append((original_text, lat, lng))
        
        # Extract locations based on keywords
        for match in self.location_keywords_pattern.finditer(text):
            location_type = match.group(1)
            location_name = match.group(2).strip()
            
            # Combine for full location text
            full_location = f"{location_type} {location_name}"
            
            # Try to geocode the location
            coordinates = self._geocode_location(full_location)
            if coordinates:
                lat, lng = coordinates
                locations.append((full_location, lat, lng))
            else:
                # Try with transliteration
                transliterated = self._transliterate_text(full_location)
                coordinates = self._geocode_location(transliterated)
                if coordinates:
                    lat, lng = coordinates
                    locations.append((full_location, lat, lng))
        
        return locations
    
    def extract_danger_info(self, text: str) -> List[Tuple[str, int]]:
        """Extract danger information from text.
        
        Args:
            text: Text to extract danger information from
        
        Returns:
            List of tuples containing (text, severity)
        """
        danger_info = []
        
        # Extract danger information based on keywords
        for match in self.danger_keywords_pattern.finditer(text):
            danger_type = match.group(1)
            danger_desc = match.group(2).strip()
            
            # Combine for full danger text
            full_danger = f"{danger_type} {danger_desc}"
            
            # Determine severity based on keywords
            severity = self._calculate_severity(full_danger)
            
            danger_info.append((full_danger, severity))
        
        return danger_info
    
    def _geocode_location(self, location_text: str) -> Optional[Tuple[float, float]]:
        """Geocode a location text to coordinates.
        
        Args:
            location_text: Location text to geocode
        
        Returns:
            Tuple of (latitude, longitude) or None if geocoding failed
        """
        try:
            # Try to geocode with country context
            location = self.geolocator.geocode(
                f"{location_text}, Україна",
                language="uk",
                timeout=10
            )
            
            if location:
                return (location.latitude, location.longitude)
            
            # Try without country context
            location = self.geolocator.geocode(
                location_text,
                language="uk",
                timeout=10
            )
            
            if location:
                return (location.latitude, location.longitude)
            
            return None
        except Exception:
            return None
    
    def _transliterate_text(self, text: str) -> str:
        """Transliterate Ukrainian text to Latin script.
        
        Args:
            text: Ukrainian text to transliterate
        
        Returns:
            Transliterated text
        """
        try:
            return transliterate.translit(text, "uk", reversed=True)
        except Exception:
            return text
    
    def _calculate_severity(self, text: str) -> int:
        """Calculate severity of danger information.
        
        Args:
            text: Danger information text
        
        Returns:
            Severity on a scale of 1-10
        """
        # High severity keywords
        high_severity = [
            "ядерн", "радіац", "хіміч", "біолог", "ракет", "вибух",
            "артилер", "обстріл", "жертв", "загинул", "постраждал",
        ]
        
        # Medium severity keywords
        medium_severity = [
            "евакуац", "тривог", "сирен", "замінов", "підозріл",
            "небезпе", "загроз", "пожеж", "руйнув",
        ]
        
        # Count occurrences of keywords
        high_count = sum(1 for keyword in high_severity if keyword in text.lower())
        medium_count = sum(1 for keyword in medium_severity if keyword in text.lower())
        
        # Calculate severity
        severity = min(high_count * 2 + medium_count, 10)
        return max(severity, 1)  # Ensure at least 1