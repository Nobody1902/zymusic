import random


class Queue:
    def __init__(self):
        self._items: list = []
        self._current_index: int = -1
        self._on_change = []

    def on_change(self, callback):
        self._on_change.append(callback)

    def _emit_change(self):
        for cb in self._on_change:
            cb()

    @property
    def current(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return None

    @property
    def items(self):
        return list(self._items)

    @property
    def current_index(self):
        return self._current_index

    @property
    def is_empty(self):
        return len(self._items) == 0

    def append(self, song):
        self._items.append(song)
        if self._current_index == -1:
            self._current_index = 0
        self._emit_change()

    def extend(self, songs):
        if not songs:
            return
        self._items.extend(songs)
        if self._current_index == -1:
            self._current_index = 0
        self._emit_change()

    def insert_next(self, song):
        insert_at = self._current_index + 1 if self._current_index >= 0 else 0
        self._items.insert(insert_at, song)
        self._emit_change()

    def insert_at(self, index, song):
        self._items.insert(index, song)
        if index <= self._current_index:
            self._current_index += 1
        self._emit_change()

    def remove(self, index):
        if 0 <= index < len(self._items):
            removed = self._items.pop(index)
            if index <= self._current_index:
                self._current_index = max(-1, self._current_index - 1)
            self._emit_change()
            return removed
        return None

    def move(self, from_index, to_index):
        if not (0 <= from_index < len(self._items) and 0 <= to_index < len(self._items)):
            return False
        song = self._items.pop(from_index)
        self._items.insert(to_index, song)
        if self._current_index == from_index:
            self._current_index = to_index
        elif from_index < self._current_index <= to_index:
            self._current_index -= 1
        elif to_index <= self._current_index < from_index:
            self._current_index += 1
        self._emit_change()
        return True

    def clear(self):
        self._items.clear()
        self._current_index = -1
        self._emit_change()

    def next(self):
        if self._current_index + 1 < len(self._items):
            self._current_index += 1
            return self._items[self._current_index]
        return None

    def prev(self):
        if self._current_index > 0:
            self._current_index -= 1
            return self._items[self._current_index]
        return None

    def go_to(self, index):
        if 0 <= index < len(self._items):
            self._current_index = index
            return self._items[index]
        return None

    def shuffle(self):
        if not self._items:
            return
        current = self._items[self._current_index] if self._current_index >= 0 else None
        rest = [s for s in self._items if s is not current]
        random.shuffle(rest)
        if current:
            self._items = [current] + rest
            self._current_index = 0
        else:
            self._items = rest
        self._emit_change()

    def reorder(self, new_order):
        if len(new_order) != len(self._items):
            return
        current_id = id(self._items[self._current_index]) if self._current_index >= 0 else None
        self._items = [self._items[i] for i in new_order]
        if current_id is not None:
            for i, item in enumerate(self._items):
                if id(item) == current_id:
                    self._current_index = i
                    break
        self._emit_change()

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]
