﻿import asyncio
import random


class Queue:

    def __init__(self):
        self.entries = list()

    async def get(self):
        while True:
            try:
                item = self.entries.pop(0)
            except IndexError:
                pass
            else:
                return item

            await asyncio.sleep(0.2)

    def shuffle(self):
        random.shuffle(self.entries)

    def put(self, item):
        self.entries.append(item)

    def put_left(self, item):
        self.entries.insert(0, item)

    def pop(self):
        return self.entries.pop(0)

    def pop_index(self, index: int):
        return self.entries.pop(index)
    
    def clear(self):
        del self.entries[:]
    
    def clear_index(self, index: int):
        del self.entries[index]
    
    def clear_range(self, start: int, end: int):
        del self.entries[start:end]

    async def find_next(self):
        while True:
            try:
                item = self.entries.pop(0)
            except IndexError:
                await asyncio.sleep(0.2)
                continue
            else:
                if item.is_dead:
                    await asyncio.sleep(0.2)
                    continue
