# -*- coding: utf-8 -*-
# ANoise 0.0.17 (Ambient Noise)
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

from gi.repository import Gtk


class ExtraWindow:
    """This will be for DE as MATE 14.10+ which hasn't sound indicator with Gtk3"""
    def __init__(self, player):
        self.player = player
        builder = Gtk.Builder()
        
        builder.add_from_file('/usr/share/anoise/anoise.ui')
        self.win_icon  = builder.get_object('icon_noise')
        self.btn_play  = builder.get_object('btn_play')
        self.lbl_title = builder.get_object('lbl_title')
        builder.connect_signals(self)
        self.window = builder.get_object('main_win')
        self.window.show_all()
        self._set_window_icon()
    
    def _set_window_icon(self):
        self.window.set_icon_from_file(self.player.noise.get_icon().replace('file://', ''))
        self.win_icon.set_from_file(self.player.noise.get_icon().replace('file://', ''))
        self.lbl_title.set_text(self.player.noise.get_name())
    
    def on_btn_previous_clicked(self, widget, data=None):
        self.player._set_new_play('previous')
        image = Gtk.Image(stock=Gtk.STOCK_MEDIA_PAUSE)
        self.btn_play.set_image(image)
        self._set_window_icon()
    
    def on_btn_next_clicked(self, widget, data=None):
        self.player._set_new_play('next')
        image = Gtk.Image(stock=Gtk.STOCK_MEDIA_PAUSE)
        self.btn_play.set_image(image)
        self._set_window_icon()
    
    def on_btn_play_pause_clicked(self, widget, data=None):
        self.player.is_playing = not self.player.is_playing
        if not self.player.is_playing:
            self.player._sound_menu_pause()
            image = Gtk.Image(stock=Gtk.STOCK_MEDIA_PLAY)
            self.btn_play.set_image(image)
        else:
            self.player._sound_menu_play()
            image = Gtk.Image(stock=Gtk.STOCK_MEDIA_PAUSE)
            self.btn_play.set_image(image)
    
    def on_main_win_delete_event(self, widget, data=None):
        Gtk.main_quit()
    
    def on_menu_about_activate(self, widget, data=None):
        self.player._sound_menu_raise()
