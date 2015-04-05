# -*- coding: utf-8 -*-
# ANoise 0.0.15 (Ambient Noise)
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


from gi.repository import Gtk, GObject, Gst
from dbus.mainloop.glib import DBusGMainLoop
import os, glob, webbrowser, subprocess, socket, sys, gettext, shutil, threading
from sound_menu import SoundMenuControls

# i18n
gettext.textdomain('anoise')
_ = gettext.gettext


class Sounds:
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
        
    def set_previous(self):
        """Previous sound filename"""
        self.current = self.current - 1
        if self.current < 0:
            self.current = self.max
        
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
        
    def set_cfg_current(self):
        cfg_file = open(self.CFG_FILE, "w")
        cfg_file.write(str(self.current))
        cfg_file.close()


class ANoise(Gtk.Window):
    """Control the sound indicator"""
    def __init__(self):
        Gtk.Window.__init__(self, title="ANoise")
        self.sound_menu = SoundMenuControls('anoise')
        self.sounds = Sounds()
        
        self.player = Gst.ElementFactory.make("playbin", "player")
        self.player.set_property('uri', self.sounds.get_current_filename())
        self.is_playing = False
        
        dummy_i18n = (_("Coffee Shop"), _("Fire"), _("Forest"), _("Night"), _("Rain"), _("Sea"), _("Storm"), _("Wind")) # Need i18n
        
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message::eos", self._loop)
        
        # Overwrite libraty methods
        self.sound_menu._sound_menu_is_playing = self._sound_menu_is_playing
        self.sound_menu._sound_menu_play       = self._sound_menu_play
        self.sound_menu._sound_menu_pause      = self._sound_menu_pause
        self.sound_menu._sound_menu_next       = self._sound_menu_next
        self.sound_menu._sound_menu_previous   = self._sound_menu_previous
        self.sound_menu._sound_menu_raise      = self._sound_menu_raise
        
        # Autostart when click on sound indicator icon
        self._sound_menu_is_playing()
        self._sound_menu_play()
        threading.Timer(1, self._set_album_after_start).start()
    
    def _set_album_after_start(self):
        self.sound_menu.signal_playing()
    
    def _loop(self, bus, message):
        """Start again the same sound in the EOS"""
        self.player.set_state(Gst.State.READY)
        self.player.set_state(Gst.State.PLAYING)
    
    def _sound_menu_is_playing(self):
        """Called in the first click"""
        self.is_playing = not self.is_playing
        return not self.is_playing
    
    def _sound_menu_play(self):
        """Play"""
        self.player.set_state(Gst.State.PLAYING)
        self.sound_menu.signal_playing()
        self.sound_menu.song_changed('', '', self.sounds.get_name(), self.sounds.get_icon())
    
    def _sound_menu_pause(self):
        """Pause"""
        self.player.set_state(Gst.State.PAUSED)
        self.sound_menu.signal_paused()
    
    def _set_new_play(self, what):
        """Next or Previous"""
        self.sounds.refresh_all_ogg()
        # Get Next/Previous
        if what == 'next':
            self.sounds.set_next()
        if what == 'previous':
            self.sounds.set_previous()
        # Stop
        self.player.set_state(Gst.State.READY)
        # From pause?
        if not self.is_playing:
            self.is_playing = True
        # Set new sound
        self.player.set_property('uri', self.sounds.get_current_filename())
        self.sound_menu.song_changed('', '', self.sounds.get_name(), self.sounds.get_icon())
        # Play
        self.player.set_state(Gst.State.PLAYING)
        self.sound_menu.signal_playing()
        self.sounds.set_cfg_current()
    
    def _sound_menu_previous(self):
        """Previous"""
        self._set_new_play('previous')
    
    def _sound_menu_next(self):
        """Next"""
        self._set_new_play('next')
    
    def _sound_menu_raise(self):
        """Click on player"""
        webbrowser.open_new('http://gufw.org/donate_anoise')



if __name__ == "__main__":
    # 1 Instance
    global lock_socket
    lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        lock_socket.bind('\0' + 'anoise_running') # Lock
    except socket.error:
        sys.exit() # Was locked before
    
    GObject.threads_init()
    DBusGMainLoop(set_as_default=True)
    Gst.init(None)
    
    win = ANoise()
    win.connect("delete-event", Gtk.main_quit)
    win.hide()
    #win.show_all() # For debug
    Gtk.main()

