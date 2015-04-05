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

import webbrowser, subprocess, sys, gettext, threading
from gi.repository import Gtk, GObject, Gst
from dbus.mainloop.glib import DBusGMainLoop
from utils import *
from sound_menu import SoundMenuControls

# i18n
gettext.textdomain('anoise')
_ = gettext.gettext


class ANoise(Gtk.Window):
    """Control the sound indicator"""
    def __init__(self):
        # These 3 are need
        GObject.threads_init()
        DBusGMainLoop(set_as_default=True)
        Gst.init(None)
        
        win = Gtk.Window()
        win.connect("delete-event", Gtk.main_quit)
        win.show_all() # For debug

        self.sound_menu = SoundMenuControls('anoise')
        self.noise = Noise()
        
        self.player = Gst.ElementFactory.make("playbin", "player")
        self.player.set_property('uri', self.noise.get_current_filename())
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
    
    def _play(self):
        
    def _sound_menu_play(self):
        """Play"""
        self.player.set_state(Gst.State.PLAYING)
        self.sound_menu.signal_playing()
        self.sound_menu.song_changed('', '', self.noise.get_name(), self.noise.get_icon())
    
    def _sound_menu_pause(self):
        """Pause"""
        self.player.set_state(Gst.State.PAUSED)
        self.sound_menu.signal_paused()
    
    def _set_new_play(self, what):
        """Next or Previous"""
        self.noise.refresh_all_ogg()
        # Get Next/Previous
        if what == 'next':
            self.noise.set_next()
        if what == 'previous':
            self.noise.set_previous()
        # From pause?
        if self.is_playing:
            self.player.set_state(Gst.State.READY)
        else:
            self.is_playing = True
        # Set new sound
        self.player.set_property('uri', self.noise.get_current_filename())
        # Play
        self.player.set_state(Gst.State.PLAYING)
        self.sound_menu.signal_playing()
        self.sound_menu.song_changed('', '', self.noise.get_name(), self.noise.get_icon())
    
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
    Lock()
    anoise = ANoise()
    Gtk.main()
