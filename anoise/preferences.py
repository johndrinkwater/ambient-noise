# -*- coding: utf-8 -*-
# ANoise 0.0.21 (Ambient Noise)
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

import os, shutil
from datetime import datetime, timedelta
from gi.repository import Gtk
# i18n
import gettext
gettext.textdomain('anoise')
_ = gettext.gettext


class Preferences:
    """This will be for DE as MATE 14.10+ which hasn't sound indicator with Gtk3"""
    def __init__(self, player):
        self.AUTOSTART = os.path.join(os.getenv('HOME'), '.config', 'autostart', 'anoise.desktop')
        self.DESKTOP = '/usr/share/applications/anoise.desktop'
        
        self.player = player
        builder = Gtk.Builder()
        
        builder.add_from_file('/usr/share/anoise/preferences.ui')
        self.win_preferences = builder.get_object('preferences_win')
        self.adjustment   = builder.get_object('adjustment_timer')
        self.sp_timer     = builder.get_object('spin_timer')
        self.cb_sleep     = builder.get_object('cb_timesleep')
        self.cb_autostart = builder.get_object('cb_autostart')
        self.img_info     = builder.get_object('img_info')
        
        self._set_initial_values()
        
        builder.connect_signals(self)
        self.win_preferences.show_all()
    
    def _set_initial_values(self):
        if os.path.isfile(self.AUTOSTART):
            self.cb_autostart.set_active(True)
        else:
            self.cb_autostart.set_active(False)
    
    def on_cb_autostart_toggled(self, widget, data=None):
        if self.cb_autostart.get_active():
            try:
                shutil.copy2(self.DESKTOP, self.AUTOSTART)
            except:
                pass
        else:
            try:
                os.remove(self.AUTOSTART)
            except:
                pass
    
    def on_cb_timesleep_toggled(self, widget, data=None):
        seconds = self.sp_timer.get_value_as_int() * 60
        self.sp_timer.set_sensitive(not self.cb_sleep.get_active())
        self.player.set_timer(self.cb_sleep.get_active(), seconds)
        if self.cb_sleep.get_active():
            x = datetime.now() + timedelta(seconds=seconds)
            msg = ' '.join([_("Noise will stop at"), x.strftime('%H:%M')])
            self.img_info.set_tooltip_text(msg)
        else:
            self.img_info.set_tooltip_text(_("ANoise will not autostop the current sound"))
    
    def on_preferences_delete_event(self, widget, data=None):
        try:
            os.remove('/tmp/anoise_preferences')
        except:
            pass
        self.win_preferences.destroy()
