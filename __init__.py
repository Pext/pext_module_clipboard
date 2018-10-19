#!/usr/bin/env python3

# Copyright (C) 2018 Sylvia van Os <sylvia@hackerchick.me>
#
# Pext clipboard module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from threading import Thread
from time import sleep

import pyperclip

from pext_base import ModuleBase
from pext_helpers import Action


class Module(ModuleBase):
    def init(self, settings, q):
        self.q = q

        self.entries = []

        self.clipboard_watcher = Thread(target=self._watch_clipboard)
        self.clipboard_watcher.start()

    def _watch_clipboard(self):
        while True:
            sleep(0.1)

            try:
                content = pyperclip.paste()
            except Exception as e:
                continue

            if self.entries and content == self.entries[0]:
                continue

            try:
                self.entries.remove(content)
            except ValueError:
                pass

            self.entries.insert(0, content)
            self.q.put([Action.replace_entry_list, self.entries])

    def stop(self):
        pass

    def selection_made(self, selection):
        if len(selection) == 0:
            self.q.put([Action.replace_entry_list, self.entries])
        elif len(selection) == 1:
            self.q.put([Action.copy_to_clipboard, selection[0]["value"]])
            self.q.put([Action.close])

    def process_response(self, response):
        pass
