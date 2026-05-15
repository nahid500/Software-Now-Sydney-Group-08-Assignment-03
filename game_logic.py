class GameLogic:
    def __init__(self):
        self.differences = []
        self.mistakes = 0
        self.max_mistakes = 3
        self.total_found = 0
        self.active = False

    def new_round(self, regions):
        self.differences = []
        for r in regions:
            self.differences.append({
                'x': r['x'],
                'y': r['y'],
                'w': r['w'],
                'h': r['h'],
                'found': False
            })
        self.mistakes = 0
        self.active = True

    def check_click(self, cx, cy):
        # go through each difference and see if click is close enough
        for diff in self.differences:
            if diff['found']:
                continue

            # centre of the difference region
            mid_x = diff['x'] + diff['w'] // 2
            mid_y = diff['y'] + diff['h'] // 2

            # use a tolerance based on region size
            tol = max(diff['w'], diff['h']) // 2 + 10

            if abs(cx - mid_x) < tol and abs(cy - mid_y) < tol:
                diff['found'] = True
                self.total_found += 1
                return 'found'

        # wrong click
        self.mistakes += 1
        if self.mistakes >= self.max_mistakes:
            self.active = False
            return 'gameover'

        return 'wrong'

    def remaining(self):
        count = 0
        for d in self.differences:
            if not d['found']:
                count += 1
        return count

    def all_found(self):
        for d in self.differences:
            if not d['found']:
                return False
        self.active = False
        return True

    def reveal(self):
        # mark everything as found so we can draw circles
        for d in self.differences:
            if not d['found']:
                d['found'] = True
                d['revealed'] = True
        self.active = False