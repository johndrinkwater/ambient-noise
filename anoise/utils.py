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

class Noise:
    """Manage access to noises"""
    def __init__(self):
        self.CFG_DIR   = os.path.join(BaseDirectory.xdg_config_home, 'anoise')
        self.DATA_DIR  = os.path.join(BaseDirectory.xdg_data_home, 'anoise')
        self.CFG_FILE  = os.path.join(self.CFG_DIR, 'config')
        if not os.path.exists(self.CFG_DIR):
            try:
                os.makedirs(self.CFG_DIR)
            except OSError as exception:
                pass
            except:
                pass

        try:
            self.BASE_ICON = Gtk.IconTheme.get_default().lookup_icon('anoise', 48, 0).get_filename()
        except:
            self.BASE_ICON = ''
        self.refresh_all_ogg()

    def refresh_all_ogg(self):
        """Get all current files in sounds paths"""
        all_files = []
        sound_types = ['.ogg','.mp3','.wav','.webm']
        # Global
        sound_files = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'sounds', '*.*')
        available_sounds = glob.glob(sound_files)
        for sound in available_sounds:
            if os.path.splitext(sound)[1].lower() in sound_types:
                all_files.append(sound)
        # Local
        sound_files = os.path.join(self.DATA_DIR, '*.*')
        available_sounds = glob.glob(sound_files)
        for sound in available_sounds:
            if os.path.splitext(sound)[1].lower() in sound_types:
                all_files.append(sound)
        sound_files = os.path.join(os.getenv('HOME'), 'ANoise', '*.*')
        available_sounds = glob.glob(sound_files)
        for sound in available_sounds:
            if os.path.splitext(sound)[1].lower() in sound_types:
                all_files.append(sound)
        sound_files = os.path.join(os.getenv('HOME'), '.ANoise', '*.*')
        available_sounds = glob.glob(sound_files)
        for sound in available_sounds:
            if os.path.splitext(sound)[1].lower() in sound_types:
                all_files.append(sound)
        
        if not len(all_files):
            sys.exit('Not noise files found')
        
        self.noises = {}
        for noise in all_files:
            self.noises[self.get_name(noise)] = noise
        
        self.noises = sorted(self.noises.items(), key=operator.itemgetter(0))
        
        self.max = len(self.noises) - 1
        self.current = self._get_cfg_last(self.max)
        if self.current > self.max:
            self.current = 0
    
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


    def _get_cfg_last(self, max):
        current = 0
        try:
            with open (self.CFG_FILE, "r") as myfile:
                current=int(myfile.readlines()[0])
                if current > max:
                    current = 0
        except:
            pass
        return current
    
    def _set_cfg_current(self):
        cfg_file = open(self.CFG_FILE, "w")
        cfg_file.write(str(self.current))
        cfg_file.close()
