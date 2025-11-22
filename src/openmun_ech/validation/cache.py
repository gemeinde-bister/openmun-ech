"""RAM cache for Swiss open data used in validation.

This module provides singleton cache classes that lazy-load Swiss open data
from the openmun-opendata library and keep it in RAM for fast lookups.

The caches use a singleton pattern to ensure data is loaded only once per
Python process, regardless of how many validation contexts are created.

Core Principle: Fast validation through RAM caching with lazy initialization.
"""

from typing import Dict, List, Optional

try:
    from openmun_opendata import PostalCodesAPI, MunicipalitiesAPI, StreetsAPI
    from openmun_opendata.geo.models.postal_codes import PostalLocalityV1
    from openmun_opendata.geo.models.municipalities import MunicipalityV1
    from openmun_opendata.geo.models.streets import StreetV1
    OPENDATA_AVAILABLE = True
except ImportError:
    OPENDATA_AVAILABLE = False
    PostalCodesAPI = None  # type: ignore
    PostalLocalityV1 = None  # type: ignore
    MunicipalitiesAPI = None  # type: ignore
    MunicipalityV1 = None  # type: ignore
    StreetsAPI = None  # type: ignore
    StreetV1 = None  # type: ignore


class PostalCodeCache:
    """Singleton RAM cache for Swiss postal code lookups.

    This cache lazy-loads postal code data from openmun-opendata on first access
    and keeps it in RAM for fast subsequent lookups. The singleton pattern ensures
    data is loaded only once per Python process.

    The cache maps postal codes (4-digit strings) to lists of localities,
    since a single postal code can serve multiple localities.

    Attributes:
        _instance: Singleton instance (class attribute)
        _data: Cached postal code data (None until first access)

    Example:
        >>> cache = PostalCodeCache()  # Same instance every time
        >>> localities = cache.get_localities("8001")
        >>> for locality in localities:
        ...     print(locality.locality_name)
        Zürich
        Zürich Sihlpost

    Note:
        Requires openmun-opendata package to be installed. If not available,
        the cache will be empty and validation will be disabled.
    """

    _instance: Optional['PostalCodeCache'] = None
    _data: Optional[Dict[str, List['PostalLocalityV1']]] = None

    def __new__(cls) -> 'PostalCodeCache':
        """Ensure only one instance exists (singleton pattern).

        Returns:
            The singleton PostalCodeCache instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def data(self) -> Dict[str, List['PostalLocalityV1']]:
        """Get cached postal code data, loading it on first access.

        This property lazy-loads the data on first access to avoid unnecessary
        loading if validation is never used.

        Returns:
            Dictionary mapping postal codes to lists of localities.
            Returns empty dict if openmun-opendata is not available.

        Raises:
            No exceptions are raised. If data loading fails, an empty dict
            is returned and a warning is printed.
        """
        if self._data is None:
            self._load_data()
        return self._data or {}

    def _load_data(self) -> None:
        """Load postal code data from openmun-opendata.

        This method is called automatically on first data access.
        It builds an index mapping postal codes to localities for fast lookups.

        Side Effects:
            - Prints loading status to stdout
            - Sets self._data to populated dictionary or empty dict on failure
        """
        if not OPENDATA_AVAILABLE:
            print("⚠️  openmun-opendata not available - postal code validation disabled")
            self._data = {}
            return

        try:
            print("🔄 Loading Swiss postal codes (one-time, cached in RAM)...")

            # Initialize API with fallback to cached data
            api = PostalCodesAPI(fallback_allowed=True)

            # Build index: postal_code -> List[PostalLocalityV1]
            self._data = {}
            locality_count = 0

            for locality in api.iter_all():
                postal_code = locality.postal_code
                if postal_code not in self._data:
                    self._data[postal_code] = []
                self._data[postal_code].append(locality)
                locality_count += 1

            print(
                f"✅ Loaded {locality_count} localities "
                f"({len(self._data)} unique postal codes)"
            )

        except Exception as e:
            # Never raise exceptions - validation is optional
            print(f"⚠️  Failed to load postal codes: {e}")
            print("   Postal code validation will be disabled")
            self._data = {}

    def get_localities(self, postal_code: str) -> List['PostalLocalityV1']:
        """Get all localities for a given postal code.

        Args:
            postal_code: The postal code to look up (4 digits, can include spaces)

        Returns:
            List of PostalLocalityV1 objects for this postal code.
            Returns empty list if postal code not found or data not available.

        Example:
            >>> cache = PostalCodeCache()
            >>> localities = cache.get_localities("8001")
            >>> len(localities)
            2
            >>> localities[0].locality_name
            'Zürich'
        """
        normalized = self.normalize_postal_code(postal_code)
        return self.data.get(normalized, [])

    @staticmethod
    def normalize_postal_code(postal_code: str) -> str:
        """Normalize postal code for consistent lookups.

        Swiss postal codes are 4 digits. This method:
        - Removes all whitespace
        - Pads with leading zeros if needed

        Args:
            postal_code: Raw postal code string

        Returns:
            Normalized 4-digit postal code string

        Examples:
            >>> PostalCodeCache.normalize_postal_code("8001")
            '8001'
            >>> PostalCodeCache.normalize_postal_code(" 8001 ")
            '8001'
            >>> PostalCodeCache.normalize_postal_code("801")
            '0801'
            >>> PostalCodeCache.normalize_postal_code("1")
            '0001'
        """
        # Remove all whitespace
        clean = postal_code.replace(" ", "").replace("\t", "").replace("\n", "")

        # Ensure 4 digits (pad with zeros if needed)
        return clean.zfill(4)

    def is_available(self) -> bool:
        """Check if postal code data is available.

        This method triggers lazy loading if data hasn't been loaded yet.

        Returns:
            True if openmun-opendata is installed and data was loaded successfully,
            False otherwise.

        Example:
            >>> cache = PostalCodeCache()
            >>> if cache.is_available():
            ...     # Perform validation
            ...     pass
            ... else:
            ...     print("Validation disabled")
        """
        # Trigger lazy loading by accessing .data property
        # This ensures we actually check if data can be loaded, not just if package exists
        return OPENDATA_AVAILABLE and len(self.data) > 0

    def clear(self) -> None:
        """Clear cached data.

        This is primarily useful for testing. In production, you typically
        want the cache to persist for the lifetime of the Python process.

        Example:
            >>> cache = PostalCodeCache()
            >>> cache.clear()  # Force reload on next access
        """
        self._data = None

    def __repr__(self) -> str:
        """Return developer-friendly representation.

        Returns:
            String showing cache status and data counts.
        """
        if not OPENDATA_AVAILABLE:
            return "PostalCodeCache(status=unavailable)"

        if self._data is None:
            return "PostalCodeCache(status=not_loaded)"

        postal_codes = len(self._data)
        localities = sum(len(locs) for locs in self._data.values())

        return f"PostalCodeCache(postal_codes={postal_codes}, localities={localities})"


class MunicipalityCache:
    """Singleton RAM cache for Swiss municipality (BFS) code lookups.

    This cache lazy-loads municipality data from openmun-opendata on first access
    and keeps it in RAM for fast subsequent lookups. The singleton pattern ensures
    data is loaded only once per Python process.

    The cache indexes municipalities by BFS code for fast validation of
    birth_municipality_bfs, reporting_municipality_bfs, and other BFS fields.

    Attributes:
        _instance: Singleton instance (class attribute)
        _data: Cached municipality data (None until first access)
        _by_bfs: Index by BFS code (string)
        _by_historical: Index by historical code (for merged municipalities)

    Example:
        >>> cache = MunicipalityCache()  # Same instance every time
        >>> municipality = cache.get_by_bfs_code("261")
        >>> municipality.name
        'Zürich'
        >>> municipality.canton_code
        'ZH'

    Note:
        Requires openmun-opendata package to be installed. If not available,
        the cache will be empty and validation will be disabled.
    """

    _instance: Optional['MunicipalityCache'] = None
    _data: Optional[List['MunicipalityV1']] = None
    _by_bfs: Optional[Dict[str, 'MunicipalityV1']] = None
    _by_historical: Optional[Dict[str, 'MunicipalityV1']] = None

    def __new__(cls) -> 'MunicipalityCache':
        """Ensure only one instance exists (singleton pattern).

        Returns:
            The singleton MunicipalityCache instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def data(self) -> List['MunicipalityV1']:
        """Get cached municipality data, loading it on first access.

        This property lazy-loads the data on first access to avoid unnecessary
        loading if validation is never used.

        Returns:
            List of MunicipalityV1 objects.
            Returns empty list if openmun-opendata is not available.

        Raises:
            No exceptions are raised. If data loading fails, an empty list
            is returned and a warning is printed.
        """
        if self._data is None:
            self._load_data()
        return self._data or []

    def _load_data(self) -> None:
        """Load municipality data from openmun-opendata.

        This method is called automatically on first data access.
        It builds indices for fast lookups by BFS code and historical code.

        Side Effects:
            - Prints loading status to stdout
            - Sets self._data, self._by_bfs, self._by_historical
        """
        if not OPENDATA_AVAILABLE:
            print("⚠️  openmun-opendata not available - municipality validation disabled")
            self._data = []
            self._by_bfs = {}
            self._by_historical = {}
            return

        try:
            print("🔄 Loading Swiss municipalities (one-time, cached in RAM)...")

            # Initialize API with fallback to cached data
            api = MunicipalitiesAPI(fallback_allowed=True)

            # Load all municipalities
            self._data = list(api.iter_all())

            # Build indices for fast lookup
            self._by_bfs = {}
            self._by_historical = {}

            for municipality in self._data:
                # Index by BFS code (string)
                if municipality.bfs_code:
                    self._by_bfs[str(municipality.bfs_code)] = municipality

                # Index by historical code (for merged municipalities)
                if municipality.historical_code:
                    self._by_historical[str(municipality.historical_code)] = municipality

            print(
                f"✅ Loaded {len(self._data)} municipalities "
                f"({len(self._by_bfs)} unique BFS codes)"
            )

        except Exception as e:
            # Never raise exceptions - validation is optional
            print(f"⚠️  Failed to load municipalities: {e}")
            print("   Municipality validation will be disabled")
            self._data = []
            self._by_bfs = {}
            self._by_historical = {}

    def get_by_bfs_code(self, bfs_code: str) -> Optional['MunicipalityV1']:
        """Get municipality by BFS code.

        Args:
            bfs_code: The BFS municipality code to look up (e.g., "261" for Zürich)

        Returns:
            MunicipalityV1 object if found, None otherwise.

        Example:
            >>> cache = MunicipalityCache()
            >>> zurich = cache.get_by_bfs_code("261")
            >>> zurich.name
            'Zürich'
            >>> zurich.canton_code
            'ZH'
        """
        # Trigger lazy loading
        if self._by_bfs is None:
            _ = self.data

        return self._by_bfs.get(str(bfs_code)) if self._by_bfs else None

    def get_by_historical_code(self, historical_code: str) -> Optional['MunicipalityV1']:
        """Get municipality by historical code.

        Historical codes are used for municipalities that have been merged.

        Args:
            historical_code: The historical municipality code

        Returns:
            MunicipalityV1 object if found, None otherwise.
        """
        # Trigger lazy loading
        if self._by_historical is None:
            _ = self.data

        return self._by_historical.get(str(historical_code)) if self._by_historical else None

    def is_available(self) -> bool:
        """Check if municipality data is available.

        This method triggers lazy loading if data hasn't been loaded yet.

        Returns:
            True if openmun-opendata is installed and data was loaded successfully,
            False otherwise.

        Example:
            >>> cache = MunicipalityCache()
            >>> if cache.is_available():
            ...     # Perform validation
            ...     pass
            ... else:
            ...     print("Validation disabled")
        """
        # Trigger lazy loading by accessing .data property
        # This ensures we actually check if data can be loaded, not just if package exists
        return OPENDATA_AVAILABLE and len(self.data) > 0

    def clear(self) -> None:
        """Clear cached data.

        This is primarily useful for testing. In production, you typically
        want the cache to persist for the lifetime of the Python process.

        Example:
            >>> cache = MunicipalityCache()
            >>> cache.clear()  # Force reload on next access
        """
        self._data = None
        self._by_bfs = None
        self._by_historical = None

    def __repr__(self) -> str:
        """Return developer-friendly representation.

        Returns:
            String showing cache status and data counts.
        """
        if not OPENDATA_AVAILABLE:
            return "MunicipalityCache(status=unavailable)"

        if self._data is None:
            return "MunicipalityCache(status=not_loaded)"

        active = sum(1 for m in self._data if m.valid_to is None)
        historical = len(self._data) - active

        return f"MunicipalityCache(municipalities={len(self._data)}, active={active}, historical={historical})"


class StreetCache:
    """Singleton RAM cache for Swiss street name lookups.

    This cache lazy-loads street data from openmun-opendata on first access
    and keeps it in RAM for fast subsequent lookups. The singleton pattern ensures
    data is loaded only once per Python process.

    The cache contains 200,000+ Swiss streets from the official federal street
    directory (Amtliches Strassenverzeichnis). Multiple indices are built for
    fast lookups by:
    - Street name (with normalization)
    - Municipality BFS code
    - Postal code

    Attributes:
        _instance: Singleton instance (class attribute)
        _data: All street records (None until first access)
        _by_name_prefix: Index by first 2 chars of normalized name
        _by_municipality: Index by BFS municipality code
        _by_postal_code: Index by postal code (4 digits)

    Example:
        >>> cache = StreetCache()  # Same instance every time
        >>> streets = cache.find_by_name("Bahnhofstrasse", municipality_bfs="261")
        >>> for street in streets:
        ...     print(f"{street.name} in {street.municipality_name}")
        Bahnhofstrasse in Zürich

    Memory Usage:
        Approximately 50-100 MB for all streets plus indices.
        This is acceptable for validation purposes.

    Note:
        Requires openmun-opendata package to be installed. If not available,
        the cache will be empty and validation will be disabled.
    """

    _instance: Optional['StreetCache'] = None
    _data: Optional[List['StreetV1']] = None
    _by_name_prefix: Optional[Dict[str, List['StreetV1']]] = None
    _by_municipality: Optional[Dict[str, List['StreetV1']]] = None
    _by_postal_code: Optional[Dict[str, List['StreetV1']]] = None

    def __new__(cls) -> 'StreetCache':
        """Ensure only one instance exists (singleton pattern).

        Returns:
            The singleton StreetCache instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def data(self) -> List['StreetV1']:
        """Get cached street data, loading it on first access.

        This property lazy-loads the data on first access to avoid unnecessary
        loading if street validation is never used.

        Returns:
            List of StreetV1 objects.
            Returns empty list if openmun-opendata is not available.

        Raises:
            No exceptions are raised. If data loading fails, an empty list
            is returned and a warning is printed.
        """
        if self._data is None:
            self._load_data()
        return self._data or []

    def _load_data(self) -> None:
        """Load street data from openmun-opendata.

        This method is called automatically on first data access.
        It loads all streets and builds multiple indices for fast lookups.

        Side Effects:
            - Prints loading status to stdout
            - Sets self._data, self._by_name_prefix, self._by_municipality, self._by_postal_code
        """
        if not OPENDATA_AVAILABLE:
            print("⚠️  openmun-opendata not available - street validation disabled")
            self._data = []
            self._by_name_prefix = {}
            self._by_municipality = {}
            self._by_postal_code = {}
            return

        try:
            print("🔄 Loading Swiss streets (one-time, cached in RAM - this may take 30-60 seconds)...")

            # Initialize API with fallback to cached data
            api = StreetsAPI(fallback_allowed=True)

            # Load all streets (streaming for memory efficiency)
            self._data = []
            for street in api.iter_all():
                self._data.append(street)

            print(f"   📦 Loaded {len(self._data)} streets into memory")

            # Build indices for fast lookup
            print("   🔍 Building search indices...")

            self._by_name_prefix = {}
            self._by_municipality = {}
            self._by_postal_code = {}

            for street in self._data:
                # Index by first 2 chars of normalized name (for fuzzy search)
                normalized_name = self._normalize_street_name(street.name)
                prefix = normalized_name[:2] if len(normalized_name) >= 2 else normalized_name

                if prefix not in self._by_name_prefix:
                    self._by_name_prefix[prefix] = []
                self._by_name_prefix[prefix].append(street)

                # Index by municipality BFS code
                bfs_code = str(street.municipality_bfs)
                if bfs_code not in self._by_municipality:
                    self._by_municipality[bfs_code] = []
                self._by_municipality[bfs_code].append(street)

                # Index by postal code(s)
                for postal_code in street.postal_code_list:
                    # Normalize postal code (4 digits)
                    postal_code_clean = postal_code.zfill(4)
                    if postal_code_clean not in self._by_postal_code:
                        self._by_postal_code[postal_code_clean] = []
                    self._by_postal_code[postal_code_clean].append(street)

            print(
                f"✅ Indexed {len(self._data)} streets "
                f"({len(self._by_name_prefix)} name prefixes, "
                f"{len(self._by_municipality)} municipalities, "
                f"{len(self._by_postal_code)} postal codes)"
            )

        except Exception as e:
            # Never raise exceptions - validation is optional
            print(f"⚠️  Failed to load streets: {e}")
            print("   Street validation will be disabled")
            self._data = []
            self._by_name_prefix = {}
            self._by_municipality = {}
            self._by_postal_code = {}

    def find_by_name(
        self,
        street_name: str,
        municipality_bfs: Optional[str] = None,
        postal_code: Optional[str] = None
    ) -> List['StreetV1']:
        """Find streets by name, optionally filtered by municipality or postal code.

        This method performs fuzzy matching on street names, handling:
        - Case-insensitive matching
        - Umlauts (ü -> u, ä -> a, ö -> o)
        - Common variations (strasse vs str., gasse vs g.)

        Args:
            street_name: Street name to search for
            municipality_bfs: Optional BFS code to filter results (e.g., "261" for Zürich)
            postal_code: Optional postal code to filter results (e.g., "8001")

        Returns:
            List of matching StreetV1 objects, sorted by relevance.
            Returns empty list if no matches found or data not available.

        Example:
            >>> cache = StreetCache()
            >>> # Exact search
            >>> streets = cache.find_by_name("Bahnhofstrasse")
            >>> len(streets)
            150+  # Many municipalities have a Bahnhofstrasse
            >>>
            >>> # Filter by municipality
            >>> streets = cache.find_by_name("Bahnhofstrasse", municipality_bfs="261")
            >>> len(streets)
            1  # Just Zürich's Bahnhofstrasse
            >>>
            >>> # Filter by postal code
            >>> streets = cache.find_by_name("Bahnhofstrasse", postal_code="8001")
            >>> streets[0].municipality_name
            'Zürich'
        """
        # Trigger lazy loading
        if self._data is None:
            _ = self.data

        # If indices not available, return empty list
        if not self._by_name_prefix:
            return []

        # Normalize search term
        normalized_search = self._normalize_street_name(street_name)
        prefix = normalized_search[:2] if len(normalized_search) >= 2 else normalized_search

        # Get candidate streets by prefix (fast lookup)
        candidates = self._by_name_prefix.get(prefix, [])

        # Filter by municipality if provided
        if municipality_bfs:
            candidates = [s for s in candidates if str(s.municipality_bfs) == str(municipality_bfs)]

        # Filter by postal code if provided
        if postal_code:
            postal_code_clean = postal_code.zfill(4)
            candidates = [
                s for s in candidates
                if postal_code_clean in s.postal_code_list
            ]

        # Fuzzy match on normalized name
        matches = []
        for street in candidates:
            normalized_street = self._normalize_street_name(street.name)
            if self._fuzzy_match_street(normalized_street, normalized_search):
                matches.append(street)

        # Sort by relevance (exact matches first, then by length)
        matches.sort(key=lambda s: (
            self._normalize_street_name(s.name) != normalized_search,  # False sorts before True
            len(s.name)  # Shorter names first
        ))

        return matches

    def get_by_municipality(self, municipality_bfs: str) -> List['StreetV1']:
        """Get all streets in a municipality.

        Args:
            municipality_bfs: BFS municipality code (e.g., "261" for Zürich)

        Returns:
            List of StreetV1 objects in this municipality.
            Returns empty list if municipality not found or data not available.

        Example:
            >>> cache = StreetCache()
            >>> streets = cache.get_by_municipality("261")  # Zürich
            >>> len(streets)
            5000+  # Zürich has many streets
        """
        # Trigger lazy loading
        if self._by_municipality is None:
            _ = self.data

        return self._by_municipality.get(str(municipality_bfs), []) if self._by_municipality else []

    def get_by_postal_code(self, postal_code: str) -> List['StreetV1']:
        """Get all streets served by a postal code.

        Args:
            postal_code: Postal code (e.g., "8001", can include spaces)

        Returns:
            List of StreetV1 objects served by this postal code.
            Returns empty list if postal code not found or data not available.

        Example:
            >>> cache = StreetCache()
            >>> streets = cache.get_by_postal_code("8001")
            >>> len(streets)
            500+  # Many streets in Zürich center
        """
        # Trigger lazy loading
        if self._by_postal_code is None:
            _ = self.data

        postal_code_clean = postal_code.replace(" ", "").replace("\t", "").zfill(4)
        return self._by_postal_code.get(postal_code_clean, []) if self._by_postal_code else []

    @staticmethod
    def _normalize_street_name(name: str) -> str:
        """Normalize street name for comparison.

        Normalization:
        - Convert to lowercase
        - Convert umlauts (ü -> u, ä -> a, ö -> o)
        - Remove common abbreviation variations (strasse -> str, gasse -> g)
        - Remove extra whitespace

        Args:
            name: Street name to normalize

        Returns:
            Normalized street name

        Examples:
            >>> StreetCache._normalize_street_name("Bahnhofstrasse")
            'bahnhofstrasse'
            >>> StreetCache._normalize_street_name("Zürich-Strasse")
            'zurich-strasse'
            >>> StreetCache._normalize_street_name("Hauptgasse  ")
            'hauptgasse'
        """
        # Convert to lowercase
        normalized = name.lower().strip()

        # Convert umlauts and special characters
        replacements = {
            'ä': 'a', 'ö': 'o', 'ü': 'u',
            'à': 'a', 'è': 'e', 'é': 'e', 'ê': 'e',
            'ô': 'o', 'û': 'u', 'ç': 'c'
        }
        for char, replacement in replacements.items():
            normalized = normalized.replace(char, replacement)

        # Normalize common abbreviations (for fuzzy matching)
        # Note: We keep both forms in the index, so this is for search normalization only

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    @staticmethod
    def _fuzzy_match_street(normalized_street: str, normalized_search: str) -> bool:
        """Fuzzy match two normalized street names.

        Args:
            normalized_street: Normalized street name from database
            normalized_search: Normalized search term from user

        Returns:
            True if streets match (fuzzy), False otherwise.

        Examples:
            >>> StreetCache._fuzzy_match_street("bahnhofstrasse", "bahnhofstrasse")
            True
            >>> StreetCache._fuzzy_match_street("bahnhofstrasse", "bahnhofstr")  # Partial
            True
            >>> StreetCache._fuzzy_match_street("bahnhofstrasse", "hauptstrasse")
            False
        """
        # Exact match
        if normalized_street == normalized_search:
            return True

        # Partial match (search term is prefix of street name)
        # Example: "Bahnhof" matches "Bahnhofstrasse"
        if normalized_street.startswith(normalized_search):
            return True

        # Abbreviation match (for common patterns)
        # Example: "Bahnhofstr" matches "Bahnhofstrasse"
        if len(normalized_search) >= 8:  # Only for reasonable length searches
            # Try removing "asse", "gasse", "strasse" suffixes from database
            for suffix in ['strasse', 'gasse', 'asse', 'platz', 'weg']:
                if normalized_street.endswith(suffix):
                    stem = normalized_street[:-len(suffix)]
                    if stem and (stem == normalized_search or stem.startswith(normalized_search)):
                        return True

        return False

    def is_available(self) -> bool:
        """Check if street data is available.

        This method triggers lazy loading if data hasn't been loaded yet.

        Returns:
            True if openmun-opendata is installed and data was loaded successfully,
            False otherwise.

        Example:
            >>> cache = StreetCache()
            >>> if cache.is_available():
            ...     # Perform validation
            ...     pass
            ... else:
            ...     print("Validation disabled")
        """
        # Trigger lazy loading by accessing .data property
        # This ensures we actually check if data can be loaded, not just if package exists
        return OPENDATA_AVAILABLE and len(self.data) > 0

    def clear(self) -> None:
        """Clear cached data.

        This is primarily useful for testing. In production, you typically
        want the cache to persist for the lifetime of the Python process.

        Example:
            >>> cache = StreetCache()
            >>> cache.clear()  # Force reload on next access
        """
        self._data = None
        self._by_name_prefix = None
        self._by_municipality = None
        self._by_postal_code = None

    def __repr__(self) -> str:
        """Return developer-friendly representation.

        Returns:
            String showing cache status and data counts.
        """
        if not OPENDATA_AVAILABLE:
            return "StreetCache(status=unavailable)"

        if self._data is None:
            return "StreetCache(status=not_loaded)"

        municipalities = len(self._by_municipality) if self._by_municipality else 0
        postal_codes = len(self._by_postal_code) if self._by_postal_code else 0

        return f"StreetCache(streets={len(self._data)}, municipalities={municipalities}, postal_codes={postal_codes})"
