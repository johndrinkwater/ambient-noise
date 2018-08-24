#!/usr/bin/env python3
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

import gi, os, threading
from six.moves import urllib
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('Keybinder', '3.0')
from gi.repository import Gtk, GLib, GObject, Gst, Keybinder
from dbus.mainloop.glib import DBusGMainLoop
from utils import *
from sound_menu import SoundMenuControls
from preferences import Preferences
try:
    from view import GUI
except ImportError:
    pass

# i18n
import gettext
gettext.textdomain('anoise')
_ = gettext.gettext

# playbin breaks in Kubuntu 14.04 > Needs Gst 0.10
try:
    gi.require_version('Gst', '1.0')
except:
    gi.require_version('Gst', '0.10')
    PLAYBIN = "playbin2"
else:
    PLAYBIN = "playbin"


class ANoise:
    """Control the sound indicator"""
    def __init__(self):
        # These 3 are need
        GObject.threads_init()
        DBusGMainLoop(set_as_default=True)
        Gst.init(None)
        GLib.set_application_name(_('Ambient Noise'))
        self.sound_menu = SoundMenuControls('Ambient Noise', 'anoise')
        self.noise = Noise()
        self.win_preferences = Preferences(self)

        try:
            self.keybinder = Keybinder
            self.keybinder.init()
            if self.keybinder.bind('AudioPlay', self._sound_menu_play_toggle, None):
                self.keybinder.bind('AudioStop', self._sound_menu_stop, None)
                self.keybinder.bind('AudioPause', self._sound_menu_pause, None)
                self.keybinder.bind('AudioNext', self._sound_menu_next, None)
                self.keybinder.bind('AudioPrev', self._sound_menu_previous, None)
            else:
                self.keybinder = None

        except (ValueError, ImportError):
            self.keybinder = None

        # Need in a few DE
        try:
            self.window = GUI(self)
        except:
            pass

        self.player = Gst.ElementFactory.make(PLAYBIN, "player")
        self.player.connect("about-to-finish", self._loop)

        dummy_i18n = (_("Coffee Shop"), _("Fire"), _("Forest"), _("Night"), _("Rain"), _("River"), _("Sea"), _("Storm"), _("Wind")) # Need i18n

        # Overwrite libraty methods
        self.sound_menu._sound_menu_is_playing = self._sound_menu_is_playing
        self.sound_menu._sound_menu_play       = self._sound_menu_play
        self.sound_menu._sound_menu_pause      = self._sound_menu_pause
        self.sound_menu._sound_menu_next       = self._sound_menu_next
        self.sound_menu._sound_menu_previous   = self._sound_menu_previous
        self.sound_menu._sound_menu_raise      = self._sound_menu_raise
        self.sound_menu._sound_menu_play_toggle= self._sound_menu_play_toggle

        # Autostart when click on sound indicator icon
        threading.Timer(1, self._sound_menu_play).start()

    def _loop(self, message):
        """Start again the same sound in the EOS"""
        self.player.set_property('uri', self.noise.get_current_filename_uri())

    def _sound_menu_is_playing(self):
        """Called in the first click"""
        return self.is_playing

    def _sound_menu_play_toggle(self, keypress = None, data = None):
        """Play toggle, media keys have an expectation that play is a toggle"""
        if self.is_playing:
            self._sound_menu_pause('AudioPause')
        else:
            self._sound_menu_play('AudioPlay')

    def _sound_menu_play(self, keypress = None, data = None):
        """Play"""
        self.is_playing = True # Need to overwrite this for an issue with autstart
        self.sound_menu.song_changed(self.noise.get_current_index(), '', '', self.noise.get_name(),
            urllib.parse.quote(self.noise.get_icon_uri(), ':/'),
            urllib.parse.quote(self.noise.get_current_filename_uri(), ':/'))
        self.player.set_property('uri', self.noise.get_current_filename_uri())
        self.player.set_state(Gst.State.PLAYING)
        self.sound_menu.signal_playing()

    def _sound_menu_stop(self, keypress = None, data = None):
        """Stop, different from pause in that it sets the pointer of the track to the start again"""
        self.is_playing = False
        self.player.set_state(Gst.State.READY) # assuming this is akin to stop?
        self.sound_menu.signal_stopped()

    def _sound_menu_pause(self, keypress = None, data = None):
        """Pause"""
        self.is_playing = False # Need to overwrite this for an issue with autstart
        self.player.set_state(Gst.State.PAUSED)
        self.sound_menu.signal_paused()

    def _set_new_play(self, what):
        """Next or Previous"""
        # Get Next/Previous
        if what == 'next':
            self.noise.set_next()
        if what == 'previous':
            self.noise.set_previous()
        # From pause?
        self.player.set_state(Gst.State.READY)
        # Play
        if self.is_playing:
            self._sound_menu_play()
        else:
            self.sound_menu.song_changed(self.noise.get_current_index(), '', '', self.noise.get_name(),
                urllib.parse.quote(self.noise.get_icon_uri(), ':/'),
                urllib.parse.quote(self.noise.get_current_filename_uri(), ':/'))

    def _sound_menu_previous(self, keypress = None, data = None):
        """Previous"""
        self._set_new_play('previous')

    def _sound_menu_next(self, keypress = None, data = None):
        """Next"""
        self._set_new_play('next')

    def _sound_menu_raise(self):
        """Click on player"""
        self.win_preferences.show()

    def set_timer(self, enable, seconds):
        if enable:
            self.timer = threading.Timer(seconds, self._set_future_pause)
            self.timer.start()
        else:
            self.timer.cancel()

    def _set_future_pause(self):
        self.win_preferences.set_show_timer()
        self._sound_menu_pause()

if __name__ == "__main__":
    Lock()
    # libcanberra named properties
    os.environ[ 'PULSE_PROP_application.icon_name' ] = "anoise"
    os.environ[ 'PULSE_PROP_media.role' ] = "music"
    anoise = ANoise()
    Gtk.main()
