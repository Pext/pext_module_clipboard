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

import gettext
import os
from threading import Thread
from time import sleep

import pyperclip

from pext_base import ModuleBase
from pext_helpers import Action


class Module(ModuleBase):
    def init(self, settings, q):
        try:
            lang = gettext.translation('pext_module_clipboard', localedir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale'), languages=[settings['_locale']])
        except FileNotFoundError:
            lang = gettext.NullTranslations()
            print("No {} translation available for pext_module_clipboard".format(settings['_locale']))

        lang.install()

        self.q = q
        self.settings = settings

        self.tempignore = None
        self.entries = []

        self.clipboard_watcher = Thread(target=self._watch_clipboard)
        self.clipboard_watcher.daemon = True
        self.clipboard_watcher.start()

    def _watch_clipboard(self):
        while True:
            sleep(0.1)

            try:
                content = pyperclip.paste()
            except Exception:
                continue

            # Don't save only whitespace
            if content.isspace():
                continue

            if content == self.tempignore or (self.entries and content == self.entries[0]):
                continue

            try:
                self.entries.remove(content)
            except ValueError:
                pass

            self.entries.insert(0, content)
            self.q.put([Action.replace_entry_list, self.entries])
            if self.settings['_api_version'] >= [0, 4, 0]:
                self.q.put([Action.set_entry_context, content, [_("Edit"), _("Remove")]])

            self.tempignore = None

    def stop(self):
        pass

    def selection_made(self, selection):
        if len(selection) == 0:
            self.q.put([Action.replace_entry_list, self.entries])
        elif len(selection) == 1:
            if self.settings['_api_version'] >= [0, 4, 0]:
                if selection[0]["context_option"] == _("Edit"):
                    self.tempignore = selection[0]["value"]
                    self.q.put([Action.ask_input_multi_line, _("Change clipboard entry to"), selection[0]["value"], selection[0]["value"]])
                    self.q.put([Action.set_selection, []])
                    return
                elif selection[0]["context_option"] == _("Remove"):
                    self.tempignore = selection[0]["value"]
                    try:
                        self.entries.remove(selection[0]["value"])
                    except ValueError:
                        pass

                    self.q.put([Action.replace_entry_list, self.entries])
                    self.q.put([Action.set_selection, []])
                    return

            self.q.put([Action.copy_to_clipboard, selection[0]["value"]])
            self.q.put([Action.close])

    def process_response(self, response, identifier):
        if response is not None:
            for i, entry in enumerate(self.entries):
                if entry == identifier:
                    self.entries[i] = response
                    self.q.put([Action.replace_entry_list, self.entries])
                    if self.settings['_api_version'] >= [0, 4, 0]:
                        self.q.put([Action.set_entry_context, response, [_("Edit"), _("Remove")]])
                    self.q.put([Action.set_selection, []])
                    return
