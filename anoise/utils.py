# -*- coding: utf-8 -*-
# ANoise 0.0.29 (Ambient Noise)
# Copyright (C) 2015 Marcos Alvarez Costales https://launchpad.net/~costales
#
# ANoise is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# ANoise is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ANoise; if not, see http://www.gnu.org/licenses
# for more information.

import os, glob, sys, socket, operator, gi
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from xdg import BaseDirectory
# i18n
import gettext
gettext.textdomain('anoise')
_ = gettext.gettext


class Lock:
    """1 Instance"""
    def __init__(self):
        global lock_socket

        lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        try:
            lock_socket.bind('\0' + 'anoise_running') # Lock
        except socket.error:
            sys.exit() # Was locked before

        try:
            os.remove('/tmp/anoise_preferences')
        except:
            pass

class NoisePathWatcher(PatternMatchingEventHandler):

    def __init__(self, noiseref):
        super(NoisePathWatcher, self).__init__()
        self._callback = noiseref
        self._patterns = noiseref.SOUND_TYPES

    def on_deleted(self, event):
        # file was removed from DATA_DIR that we support, so update listing
        self._callback.refresh_sound_files()

    def on_created(self, event):
        # file was copied into DATA_DIR that we support, so update listing
        self._callback.refresh_sound_files()

    def on_moved(self, event):
        # file was renamed inside DATA_DIR that we support, so update listing
        self._callback.refresh_sound_files()

class Noise:
    """Manage access to noises"""
    def __init__(self):
        self.CFG_DIR   = os.path.join(BaseDirectory.xdg_config_home, 'anoise')
        self.DATA_DIR  = os.path.join(BaseDirectory.xdg_data_home, 'anoise')
        self.CFG_FILE  = os.path.join(self.CFG_DIR, 'config')
        self.SOUND_TYPES = ['*.ogg','*.mp3','*.wav','*.webm']
        self.SOUND_PATHS = []
        self.DEFAULT_PATHS = [
            os.path.join(os.path.split(os.path.abspath(__file__))[0], 'sounds'),
            os.path.join(os.getenv('HOME'), '.ANoise'),
            os.path.join(os.getenv('HOME'), 'ANoise'),
            os.path.join(self.DATA_DIR)
        ]
        self.PATH_WATCHER = NoisePathWatcher( self )
        self.PATH_OBSERVER = None
        self.noises = {}
        self.current = self._get_cfg_last()

        if not os.path.exists(self.CFG_DIR):
            try:
                os.makedirs(self.CFG_DIR)
            except OSError as exception:
                pass
            except:
                pass

        self.refresh_sound_file_observers()

        try:
            self.BASE_ICON = Gtk.IconTheme.get_default().lookup_icon('anoise', 48, 0).get_filename()
        except:
            self.BASE_ICON = ''

        self.refresh_sound_files()

    def refresh_sound_file_observers(self):
        self.SOUND_PATHS = []
        for sound_path in self.DEFAULT_PATHS:
            if os.path.exists( sound_path ):
                  self.SOUND_PATHS.append( sound_path )

        if self.PATH_OBSERVER is not None:
            self.PATH_OBSERVER.unschedule_all()
        else:
            self.PATH_OBSERVER = Observer()
            self.PATH_OBSERVER.start()

        for sound_path in self.SOUND_PATHS:
            self.PATH_OBSERVER.schedule(self.PATH_WATCHER, path=sound_path, recursive=False)

    def refresh_sound_files(self):
        """Get all current files in sounds paths"""
        all_files = []
        save_current_filename = None

        if self.noises:
            try:
                save_current_filename = self.noises[self.current][1]
            except:
                pass

        for sound_files in self.SOUND_PATHS:
            available_sounds = glob.glob(os.path.join(sound_files, '*.*'))
            for sound in available_sounds:
                if ('*' + os.path.splitext(sound)[1].lower()) in self.SOUND_TYPES:
                    all_files.append(sound)

        if not len(all_files):
            sys.exit(_('No noise files found'))

        self.noises = {}
        for noise in all_files:
            self.noises[self.get_name(noise)] = noise

        self.noises = sorted(self.noises.items(), key=operator.itemgetter(0))
        self.max = len(self.noises) - 1

        # we can still arrive as this point if user deleted noises since last start
        if self.current > self.max:
            self.current = 0

        if save_current_filename:
            new_index = [self.noises.index(x) for x in self.noises if x[1] == save_current_filename]
            if new_index:
                self.current = new_index[0]
                self._set_cfg_current()

    def get_current_index(self):
        """Get current sound index in tracklist"""
        return self.current

    def get_current_filename(self):
        """Get current sound filename"""
        return self.noises[self.current][1]

    def get_current_filename_uri(self):
        """Get current sound filename as a file:// uri"""
        return ''.join(['file://', self.get_current_filename()])

    def set_next(self):
        """Next sound filename"""
        self.current = self.current + 1
        if self.current > self.max:
            self.current = 0
        self._set_cfg_current()

    def set_previous(self):
        """Previous sound filename"""
        self.current = self.current - 1
        if self.current < 0:
            self.current = self.max
        self._set_cfg_current()

    def get_name(self, noise=None):
        """Title for sound indicator"""
        if noise == None:
            filename = self.noises[self.current][0]
        else:
            filename = os.path.basename(os.path.splitext(noise)[0])
            filename = filename.replace('_', ' ')
            filename = filename.replace('-', ' ')
            filename = filename.replace('.', '\n')
            filename = filename.title()
        return _(filename)

    def get_icon_uri(self):
        """Get current sound thumbnail icon as a file:// uri"""
        filename = os.path.splitext(self.get_current_filename())[0]
        filename = '.'.join([filename, 'png'])
        if not os.path.exists(filename):
            filename = self.BASE_ICON

        return ''.join(['file://', filename])

    def _get_cfg_last(self):
        current = 0
        try:
            with open (self.CFG_FILE, "r") as myfile:
                current=int(myfile.readlines()[0])
        except:
            pass
        return current

    def _set_cfg_current(self):
        cfg_file = open(self.CFG_FILE, "w")
        cfg_file.write(str(self.current))
        cfg_file.close()
