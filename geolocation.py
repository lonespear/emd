"""
geolocation.py
--------------

Geographic distance calculation and travel cost estimation for realistic
exercise planning.

Features:
- Hardcoded database of ~100 major military bases/locations
- Haversine distance calculation (great-circle distance)
- Travel cost estimation based on distance and duration
- Fallback geocoding API for unknown locations
- Lead time estimation for CONUS vs OCONUS travel

Classes:
- GeoLocation: Represents a geographic location with lat/lon
- LocationDatabase: Hardcoded database of military installations
- DistanceCalculator: Calculate distances between locations
- TravelCostEstimator: Estimate travel costs and lead times
- GeocodingService: Fallback for unknown locations (optional)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import math


@dataclass
class GeoLocation:
    """
    Represents a geographic location.

    Attributes:
        name: Location name (e.g., "Joint Base Lewis-McChord")
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        country: Country code (US, KR, JP, DE, etc.)
        aor: Area of Responsibility (NORTHCOM, INDOPACOM, EUCOM, etc.)
        installation_type: Type (Army Base, Air Force Base, Naval Station, etc.)
    """
    name: str
    lat: float
    lon: float
    country: str = "US"
    aor: str = "NORTHCOM"
    installation_type: str = "Army Base"

    def __str__(self):
        return f"{self.name} ({self.lat:.4f}, {self.lon:.4f})"


class LocationDatabase:
    """
    Hardcoded database of ~100 major military installations worldwide.

    Organized by:
    - CONUS bases
    - OCONUS bases by AOR
    - Training centers
    - Common exercise locations
    """

    def __init__(self):
        self.locations: Dict[str, GeoLocation] = {}
        self._initialize_database()

    def _initialize_database(self):
        """Initialize hardcoded location database."""

        # ====================
        # CONUS - Major Army Bases
        # ====================
        self._add("JBLM", GeoLocation("Joint Base Lewis-McChord", 47.0979, -122.5811, "US", "NORTHCOM", "Joint Base"))
        self._add("Fort Bragg", GeoLocation("Fort Bragg", 35.1391, -79.0066, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Campbell", GeoLocation("Fort Campbell", 36.6584, -87.4592, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Hood", GeoLocation("Fort Hood", 31.1350, -97.7760, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Carson", GeoLocation("Fort Carson", 38.7355, -104.7891, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Riley", GeoLocation("Fort Riley", 39.0555, -96.7967, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Stewart", GeoLocation("Fort Stewart", 31.8796, -81.6103, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Bliss", GeoLocation("Fort Bliss", 31.8046, -106.4068, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Drum", GeoLocation("Fort Drum", 44.0447, -75.7537, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Benning", GeoLocation("Fort Benning", 32.3543, -84.9486, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Sill", GeoLocation("Fort Sill", 34.6508, -98.4024, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Gordon", GeoLocation("Fort Gordon", 33.4357, -82.1357, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Jackson", GeoLocation("Fort Jackson", 34.0481, -80.8969, "US", "NORTHCOM", "Army Base"))

        # CONUS - Training Centers
        self._add("NTC", GeoLocation("National Training Center (Fort Irwin)", 35.2609, -116.6890, "US", "NORTHCOM", "Training Center"))
        self._add("Fort Irwin", GeoLocation("Fort Irwin / NTC", 35.2609, -116.6890, "US", "NORTHCOM", "Training Center"))
        self._add("JRTC", GeoLocation("Joint Readiness Training Center (Fort Polk)", 31.0545, -93.2091, "US", "NORTHCOM", "Training Center"))
        self._add("Fort Polk", GeoLocation("Fort Polk / JRTC", 31.0545, -93.2091, "US", "NORTHCOM", "Training Center"))
        self._add("JMRC", GeoLocation("Joint Multinational Readiness Center (Hohenfels)", 49.2133, 11.8353, "DE", "EUCOM", "Training Center"))

        # ====================
        # INDOPACOM
        # ====================
        # Korea
        self._add("Camp Humphreys", GeoLocation("Camp Humphreys", 36.9676, 127.0356, "KR", "INDOPACOM", "Army Base"))
        self._add("Camp Casey", GeoLocation("Camp Casey", 37.7453, 127.0693, "KR", "INDOPACOM", "Army Base"))
        self._add("Osan AB", GeoLocation("Osan Air Base", 37.0902, 127.0297, "KR", "INDOPACOM", "Air Force Base"))

        # Japan
        self._add("Kadena AB", GeoLocation("Kadena Air Base", 26.3560, 127.7684, "JP", "INDOPACOM", "Air Force Base"))
        self._add("Camp Zama", GeoLocation("Camp Zama", 35.5160, 139.3996, "JP", "INDOPACOM", "Army Base"))
        self._add("Yokota AB", GeoLocation("Yokota Air Base", 35.7485, 139.3486, "JP", "INDOPACOM", "Air Force Base"))
        self._add("Misawa AB", GeoLocation("Misawa Air Base", 40.7033, 141.3683, "JP", "INDOPACOM", "Air Force Base"))

        # Guam / Pacific Islands
        self._add("Guam", GeoLocation("Anderson Air Force Base (Guam)", 13.5840, 144.9301, "GU", "INDOPACOM", "Air Force Base"))
        self._add("Anderson AFB", GeoLocation("Anderson Air Force Base", 13.5840, 144.9301, "GU", "INDOPACOM", "Air Force Base"))

        # Hawaii
        self._add("Schofield Barracks", GeoLocation("Schofield Barracks", 21.4966, -158.0640, "US", "INDOPACOM", "Army Base"))
        self._add("Hawaii", GeoLocation("Schofield Barracks (Hawaii)", 21.4966, -158.0640, "US", "INDOPACOM", "Army Base"))

        # Australia
        self._add("Darwin", GeoLocation("Robertson Barracks (Darwin)", -12.4262, 130.8845, "AU", "INDOPACOM", "Training Area"))

        # Philippines
        self._add("Philippines", GeoLocation("Clark Air Base (Philippines)", 15.1856, 120.5603, "PH", "INDOPACOM", "Air Force Base"))

        # ====================
        # EUCOM
        # ====================
        # Germany
        self._add("Grafenwoehr", GeoLocation("Grafenwoehr Training Area", 49.7167, 11.9167, "DE", "EUCOM", "Training Area"))
        self._add("Ramstein AB", GeoLocation("Ramstein Air Base", 49.4369, 7.6003, "DE", "EUCOM", "Air Force Base"))
        self._add("Wiesbaden", GeoLocation("Wiesbaden Army Airfield", 50.0499, 8.3254, "DE", "EUCOM", "Army Airfield"))
        self._add("Hohenfels", GeoLocation("Hohenfels Training Area", 49.2133, 11.8353, "DE", "EUCOM", "Training Area"))

        # Poland
        self._add("Drawsko Pomorskie", GeoLocation("Drawsko Pomorskie Training Area", 53.5333, 15.8167, "PL", "EUCOM", "Training Area"))
        self._add("Poland", GeoLocation("Drawsko Pomorskie (Poland)", 53.5333, 15.8167, "PL", "EUCOM", "Training Area"))

        # Romania
        self._add("Romania", GeoLocation("Mihail Kogalniceanu Air Base", 44.3625, 28.4883, "RO", "EUCOM", "Air Base"))

        # Baltic States
        self._add("Estonia", GeoLocation("Tapa Training Area (Estonia)", 59.2597, 25.9567, "EE", "EUCOM", "Training Area"))
        self._add("Latvia", GeoLocation("Adazi Training Area (Latvia)", 57.0750, 24.3211, "LV", "EUCOM", "Training Area"))
        self._add("Lithuania", GeoLocation("Pabrade Training Area (Lithuania)", 54.9806, 25.2000, "LT", "EUCOM", "Training Area"))

        # ====================
        # SOUTHCOM
        # ====================
        self._add("Soto Cano", GeoLocation("Soto Cano Air Base (Honduras)", 14.3828, -87.6217, "HN", "SOUTHCOM", "Air Base"))
        self._add("Honduras", GeoLocation("Soto Cano Air Base", 14.3828, -87.6217, "HN", "SOUTHCOM", "Air Base"))
        self._add("Colombia", GeoLocation("Tolemaida Air Base (Colombia)", 4.2833, -74.8667, "CO", "SOUTHCOM", "Air Base"))
        self._add("Peru", GeoLocation("Lima (Peru)", -12.0464, -77.0428, "PE", "SOUTHCOM", "Exercise Location"))
        self._add("Panama", GeoLocation("Howard Air Force Base (Panama)", 8.9167, -79.6000, "PA", "SOUTHCOM", "Air Force Base"))

        # ====================
        # AFRICOM
        # ====================
        self._add("Djibouti", GeoLocation("Camp Lemonnier (Djibouti)", 11.5450, 43.1597, "DJ", "AFRICOM", "Naval Base"))
        self._add("Camp Lemonnier", GeoLocation("Camp Lemonnier", 11.5450, 43.1597, "DJ", "AFRICOM", "Naval Base"))
        self._add("Niger", GeoLocation("Niamey Air Base (Niger)", 13.4817, 2.1764, "NE", "AFRICOM", "Air Base"))
        self._add("Kenya", GeoLocation("Camp Simba (Kenya)", -2.4500, 40.9000, "KE", "AFRICOM", "Training Area"))
        self._add("Ghana", GeoLocation("Accra (Ghana)", 5.6037, -0.1870, "GH", "AFRICOM", "Exercise Location"))

        # ====================
        # CENTCOM
        # ====================
        self._add("Kuwait", GeoLocation("Camp Arifjan (Kuwait)", 29.0983, 48.0708, "KW", "CENTCOM", "Army Base"))
        self._add("Qatar", GeoLocation("Al Udeid Air Base (Qatar)", 25.1173, 51.3150, "QA", "CENTCOM", "Air Base"))
        self._add("Bahrain", GeoLocation("NSA Bahrain", 26.1939, 50.6097, "BH", "CENTCOM", "Naval Base"))

        # ====================
        # Additional Common Locations
        # ====================
        self._add("Alaska", GeoLocation("Fort Wainwright (Alaska)", 64.8378, -147.7164, "US", "NORTHCOM", "Army Base"))
        self._add("Fort Wainwright", GeoLocation("Fort Wainwright", 64.8378, -147.7164, "US", "NORTHCOM", "Army Base"))

    def _add(self, key: str, location: GeoLocation):
        """Add location to database with case-insensitive key."""
        self.locations[key.lower()] = location

    def get(self, location_name: str) -> Optional[GeoLocation]:
        """Get location by name (case-insensitive)."""
        return self.locations.get(location_name.lower())

    def search(self, query: str) -> list[GeoLocation]:
        """Search for locations matching query."""
        query_lower = query.lower()
        matches = []
        for key, loc in self.locations.items():
            if query_lower in key or query_lower in loc.name.lower():
                matches.append(loc)
        return matches

    def list_by_aor(self, aor: str) -> list[GeoLocation]:
        """List all locations in a specific AOR."""
        return [loc for loc in self.locations.values() if loc.aor == aor]


class DistanceCalculator:
    """
    Calculate great-circle distances between locations using Haversine formula.
    """

    EARTH_RADIUS_MILES = 3958.8
    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "miles") -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point (decimal degrees)
            lat2, lon2: Second point (decimal degrees)
            unit: "miles" or "km"

        Returns:
            Distance in specified unit
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Calculate distance
        if unit == "km":
            return c * DistanceCalculator.EARTH_RADIUS_KM
        else:
            return c * DistanceCalculator.EARTH_RADIUS_MILES

    @staticmethod
    def calculate(loc1: str | GeoLocation, loc2: str | GeoLocation, db: Optional[LocationDatabase] = None) -> float:
        """
        Calculate distance between two locations.

        Args:
            loc1: Location name or GeoLocation object
            loc2: Location name or GeoLocation object
            db: LocationDatabase (created if None)

        Returns:
            Distance in miles
        """
        if db is None:
            db = LocationDatabase()

        # Resolve location names to GeoLocation objects
        if isinstance(loc1, str):
            geo1 = db.get(loc1)
            if geo1 is None:
                raise ValueError(f"Location not found: {loc1}")
        else:
            geo1 = loc1

        if isinstance(loc2, str):
            geo2 = db.get(loc2)
            if geo2 is None:
                raise ValueError(f"Location not found: {loc2}")
        else:
            geo2 = loc2

        return DistanceCalculator.haversine(geo1.lat, geo1.lon, geo2.lat, geo2.lon)


class TravelCostEstimator:
    """
    Estimate travel costs and lead times based on distance and duration.

    Factors:
    - Transportation (ground, domestic air, international air)
    - Per diem
    - Lead time for coordination
    """

    # Cost parameters (realistic FY2025 estimates)
    IRS_MILEAGE_RATE = 0.67  # $/mile for POV
    DOMESTIC_FLIGHT_BASE = 400  # Base cost for domestic flight
    DOMESTIC_FLIGHT_PER_MILE = 0.15  # $/mile
    INTERNATIONAL_FLIGHT_BASE = 1200  # Base cost for international
    INTERNATIONAL_FLIGHT_PER_MILE = 0.20  # $/mile
    PER_DIEM_CONUS = 150  # $/day for CONUS
    PER_DIEM_OCONUS = 200  # $/day for OCONUS (higher average)

    @staticmethod
    def estimate_travel_cost(distance_miles: float, duration_days: int, is_oconus: bool = False) -> float:
        """
        Estimate total travel cost (transportation + per diem).

        Args:
            distance_miles: Distance to travel
            duration_days: Duration of TDY/deployment
            is_oconus: Whether destination is OCONUS

        Returns:
            Estimated cost in USD
        """
        # Transportation cost
        if distance_miles < 500:
            # Ground transport (POV or bus)
            transport_cost = 150 + (distance_miles * TravelCostEstimator.IRS_MILEAGE_RATE)
        elif distance_miles < 3000:
            # Domestic flight
            transport_cost = (TravelCostEstimator.DOMESTIC_FLIGHT_BASE +
                            distance_miles * TravelCostEstimator.DOMESTIC_FLIGHT_PER_MILE)
        else:
            # International flight
            transport_cost = (TravelCostEstimator.INTERNATIONAL_FLIGHT_BASE +
                            distance_miles * TravelCostEstimator.INTERNATIONAL_FLIGHT_PER_MILE)

        # Per diem
        per_diem_rate = TravelCostEstimator.PER_DIEM_OCONUS if is_oconus else TravelCostEstimator.PER_DIEM_CONUS
        per_diem_cost = duration_days * per_diem_rate

        total_cost = transport_cost + per_diem_cost
        return total_cost

    @staticmethod
    def estimate_lead_time(distance_miles: float, is_oconus: bool = False) -> int:
        """
        Estimate lead time required for coordination (in days).

        Args:
            distance_miles: Distance to travel
            is_oconus: Whether destination is OCONUS

        Returns:
            Lead time in days
        """
        if is_oconus:
            # OCONUS requires passport, country clearance, etc.
            if distance_miles > 7000:  # Far OCONUS (Asia, Africa)
                return 28  # 4 weeks
            else:  # Near OCONUS (Europe, Korea)
                return 21  # 3 weeks
        else:
            # CONUS
            if distance_miles > 2000:
                return 14  # 2 weeks
            elif distance_miles > 500:
                return 7  # 1 week
            else:
                return 3  # 3 days for local

    @staticmethod
    def categorize_distance(distance_miles: float) -> str:
        """Categorize distance for reporting."""
        if distance_miles < 100:
            return "Local"
        elif distance_miles < 500:
            return "Regional"
        elif distance_miles < 1500:
            return "Domestic - Near"
        elif distance_miles < 3000:
            return "Domestic - Far"
        elif distance_miles < 7000:
            return "OCONUS - Near"
        else:
            return "OCONUS - Far"


class GeocodingService:
    """
    Fallback geocoding service for locations not in database.

    Uses OpenStreetMap Nominatim API (free, no key required).
    """

    @staticmethod
    def geocode(location_name: str) -> Optional[GeoLocation]:
        """
        Geocode a location using Nominatim API.

        Args:
            location_name: Location to geocode

        Returns:
            GeoLocation object or None if not found
        """
        try:
            import requests

            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location_name,
                "format": "json",
                "limit": 1
            }
            headers = {
                "User-Agent": "EMD-ManningSupportTool/1.0"
            }

            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()

            results = response.json()
            if results:
                result = results[0]
                return GeoLocation(
                    name=location_name,
                    lat=float(result["lat"]),
                    lon=float(result["lon"]),
                    country="Unknown",
                    aor="Unknown",
                    installation_type="Unknown"
                )
        except Exception as e:
            print(f"Geocoding failed for {location_name}: {e}")
            return None


# ===========================
# Helper Functions
# ===========================

def get_location(location_name: str, db: Optional[LocationDatabase] = None) -> Optional[GeoLocation]:
    """
    Get location from database, with fallback to geocoding.

    Args:
        location_name: Location to look up
        db: LocationDatabase (created if None)

    Returns:
        GeoLocation or None
    """
    if db is None:
        db = LocationDatabase()

    # Try database first
    loc = db.get(location_name)
    if loc:
        return loc

    # Fallback to geocoding
    print(f"Location '{location_name}' not in database, attempting geocoding...")
    return GeocodingService.geocode(location_name)


def calculate_distance_and_cost(home_station: str, exercise_location: str,
                                 duration_days: int = 14) -> Tuple[float, float, int, str]:
    """
    Calculate distance, cost, lead time, and category for a TDY.

    Args:
        home_station: Home station name
        exercise_location: Exercise location name
        duration_days: Duration in days

    Returns:
        (distance_miles, cost_usd, lead_time_days, distance_category)
    """
    db = LocationDatabase()

    # Get locations
    home = get_location(home_station, db)
    exercise = get_location(exercise_location, db)

    if not home or not exercise:
        # Return defaults if locations not found
        return 0.0, 0.0, 0, "Unknown"

    # Calculate distance
    distance = DistanceCalculator.calculate(home, exercise, db)

    # Determine if OCONUS
    is_oconus = (home.country != exercise.country) or (exercise.country != "US")

    # Calculate cost
    cost = TravelCostEstimator.estimate_travel_cost(distance, duration_days, is_oconus)

    # Estimate lead time
    lead_time = TravelCostEstimator.estimate_lead_time(distance, is_oconus)

    # Categorize
    category = TravelCostEstimator.categorize_distance(distance)

    return distance, cost, lead_time, category
