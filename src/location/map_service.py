"""
Module for generating map URLs for locations.
"""

from typing import Optional

from src.config import MapService, settings


def get_map_url(
    latitude: float, 
    longitude: float, 
    service: Optional[MapService] = None
) -> str:
    """Generate a map URL for the given coordinates.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        service: Map service to use (default: from settings)
    
    Returns:
        URL for the location on the specified map service
    """
    if service is None:
        service = settings.MAP_SERVICE
    
    if service == MapService.GOOGLE:
        return _get_google_maps_url(latitude, longitude)
    elif service == MapService.OSM:
        return _get_osm_url(latitude, longitude)
    elif service == MapService.APPLE:
        return _get_apple_maps_url(latitude, longitude)
    else:
        # Default to Google Maps
        return _get_google_maps_url(latitude, longitude)


def _get_google_maps_url(latitude: float, longitude: float) -> str:
    """Generate a Google Maps URL.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
    
    Returns:
        Google Maps URL
    """
    # Include API key if provided
    if settings.GOOGLE_MAPS_API_KEY:
        return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}&key={settings.GOOGLE_MAPS_API_KEY}"
    else:
        return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"


def _get_osm_url(latitude: float, longitude: float) -> str:
    """Generate an OpenStreetMap URL.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
    
    Returns:
        OpenStreetMap URL
    """
    return f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=15/{latitude}/{longitude}"


def _get_apple_maps_url(latitude: float, longitude: float) -> str:
    """Generate an Apple Maps URL.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
    
    Returns:
        Apple Maps URL
    """
    return f"https://maps.apple.com/?ll={latitude},{longitude}&q={latitude},{longitude}"