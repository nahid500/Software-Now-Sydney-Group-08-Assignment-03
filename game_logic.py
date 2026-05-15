"""
game_logic.py
Manages all game state: found differences, mistakes, scoring, and game-over conditions.
Demonstrates: encapsulation, constructor, methods, class interaction.
"""


class DifferenceGame:
    """
    Tracks the state of a single image round:
    - Which of the 5 differences have been found
    - How many mistakes the player has made
    - Cumulative score across multiple images
    """

    MAX_MISTAKES = 3
    TOTAL_DIFFERENCES = 5

    def __init__(self):
        # Cumulative across images
        self._total_found: int = 0
        self._total_images: int = 0

        # Per-image state
        self._differences: list[dict] = []
        self._mistakes: int = 0
        self._game_active: bool = False
        self._revealed: bool = False

    # ── Setup ────────────────────────────────
    def start_round(self, difference_regions: list[dict]) -> None:
        """Begin a new round with the given list of difference region dicts."""
        # Reset each region's found/revealed flags
        self._differences = []
        for region in difference_regions:
            self._differences.append({
                'x': region['x'],
                'y': region['y'],
                'w': region['w'],
                'h': region['h'],
                'type': region['type'],
                'found': False,
                'revealed': False,
            })
        self._mistakes = 0
        self._game_active = True
        self._revealed = False
        self._total_images += 1

    # ── Player actions ────────────────────────
    def check_click(self, click_x: int, click_y: int, tolerance: int = 35) -> dict:
        """
        Evaluate a player's click on the modified image.
        Returns a result dict:
          {
            'hit': bool,           # True if a difference was found
            'already_found': bool, # True if this region was already marked
            'mistake': bool,       # True if it counts as a mistake
            'region': dict | None, # The matched region (if hit)
            'all_found': bool,     # True if all 5 are now found
            'game_over': bool,     # True if max mistakes reached
          }
        """
        result = {
            'hit': False,
            'already_found': False,
            'mistake': False,
            'region': None,
            'all_found': False,
            'game_over': False,
        }

        if not self._game_active or self._revealed:
            return result

        # Check each difference region
        for diff in self._differences:
            cx = diff['x'] + diff['w'] // 2
            cy = diff['y'] + diff['h'] // 2
            distance = ((click_x - cx) ** 2 + (click_y - cy) ** 2) ** 0.5

            if distance <= tolerance + max(diff['w'], diff['h']) // 2:
                if diff['found']:
                    result['already_found'] = True
                    result['region'] = diff
                    return result
                # Mark as found
                diff['found'] = True
                self._total_found += 1
                result['hit'] = True
                result['region'] = diff
                result['all_found'] = self.all_found
                if result['all_found']:
                    self._game_active = False
                return result

        # Miss — counts as mistake
        self._mistakes += 1
        result['mistake'] = True
        if self._mistakes >= self.MAX_MISTAKES:
            self._game_active = False
            result['game_over'] = True
        return result

    def reveal_all(self) -> list[dict]:
        """Mark all unfound differences as revealed. Returns list of newly revealed regions."""
        newly_revealed = []
        for diff in self._differences:
            if not diff['found']:
                diff['revealed'] = True
                newly_revealed.append(diff)
        self._revealed = True
        self._game_active = False
        return newly_revealed

    # ── Read-only properties ──────────────────
    @property
    def differences(self) -> list[dict]:
        return self._differences

    @property
    def mistakes(self) -> int:
        return self._mistakes

    @property
    def remaining(self) -> int:
        return sum(1 for d in self._differences if not d['found'])

    @property
    def found_count(self) -> int:
        return sum(1 for d in self._differences if d['found'])

    @property
    def all_found(self) -> bool:
        return all(d['found'] for d in self._differences)

    @property
    def game_active(self) -> bool:
        return self._game_active

    @property
    def is_revealed(self) -> bool:
        return self._revealed

    @property
    def total_found(self) -> int:
        return self._total_found

    @property
    def total_images(self) -> int:
        return self._total_images

    @property
    def max_mistakes(self) -> int:
        return self.MAX_MISTAKES
