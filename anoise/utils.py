# -*- coding: utf-8 -*-
# ANoise 0.0.16 (Ambient Noise)
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

import os, glob, sys, shutil, socket
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


class Noise:
    """Manage access to noises"""
    def __init__(self):
        self.CFG_DIR   = os.path.join(os.getenv('HOME'), '.config', 'anoise')
        self.CFG_FILE  = os.path.join(self.CFG_DIR, 'anoise.cfg')
        if not os.path.exists(self.CFG_DIR):
            try:
                os.makedirs(self.CFG_DIR)
            except OSError as exception:
                pass
            except:
                pass
        
        self.refresh_all_ogg()
    
    def refresh_all_ogg(self):
        """Get all current files in sounds paths"""
        self.all_files = []
        # Global
        sound_files = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'sounds', '*.ogg')
        available_sounds = glob.glob(sound_files)
        for sound in available_sounds:
            self.all_files.append(sound)
        # Local
        sound_files = os.path.join(os.getenv('HOME'), 'ANoise', '*.ogg')
        available_sounds = glob.glob(sound_files)
        for sound in available_sounds:
            self.all_files.append(sound)
        
        if not len(self.all_files):
            sys.exit('Not noise files found')
        
        self.max = len(self.all_files) - 1
        self.current = self._get_cfg_last(self.max)
        if self.current > self.max:
            self.current = 0
    
    def get_current_filename(self):
        """Get current sound filename"""
        dirname = os.path.split(os.path.abspath(__file__))[0]
        filename = os.path.join(dirname, self.all_files[self.current])
        filename = ''.join(['file://', filename])
        return filename
        
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
        
    def get_name(self):
        """Get the name for set as Title in sound indicator"""
        filename = os.path.basename(self.get_current_filename())
        filename = filename.replace('.ogg', '').replace('_', ' ')
        filename = filename.title()
        return _(filename)
    
    def get_icon(self):
        """Get the name for set as Title in sound indicator"""
        filename = self.get_current_filename()
        filename = filename.replace('.ogg', '.png')
        return filename
    
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
