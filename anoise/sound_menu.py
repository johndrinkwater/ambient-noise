# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2011 Rick Spencer <rick.spencer@canonical.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

"""Contains SoundMenuControls, A class to make it easy to integrate with the Ubuntu Sound Menu.

In order for a media player to appear in the Sound Menu, it must have
a desktop file in /usr/share/applications. For example, for a media player
named "simple" player, there must be desktop file /usr/share/applications/simple-player.desktop

The desktop file must specify that it is indeed a media player. For example, simple-player.desktop
might look like the following:
[Desktop Entry]
Name=Simple Player
Comment=SimplePlayer application
Categories=GNOME;Audio;Music;Player;AudioVideo;
Exec=simple-player
Icon=simple-player
Terminal=false
Type=Application
MimeType=application/x-ogg;application/ogg;audio/x-vorbis+ogg;audio/x-scpls;audio/x-mp3;audio/x-mpeg;audio/mpeg;audio/x-mpegurl;audio/x-flac;

In order for the Sound Menu to run, a D-Bus loop must be running before
the player is created and before the gtk mainloop is run. you can add
DBusGMainLoop(set_as_default=True) to your application's __main__ function.

The Ubuntu Sound Menu integrates with applications via the MPRIS2 D-Bus api,
which is specified here: http://www.mpris.org/2.1/spec/

This module does strive to provide an MPRIS2 implementation, but rather
focuses on the subset of functionality required by the Sound Menu.

The SoundMenuControls class can be instantiated, but does not provide any
default functionality. In order to provide the required functionality,
implementations must be provided for the functions starting with
"_sound_menu", such as "_sound_menu_play", etc...

Functions and properties starting with capitalized letters, such as
"Next" and "Previous" are called by the Ubuntu Sound Menu. These
functions and properties are not designed to be called directly
or overridden by application code, only the Sound Menu.

Other functions are designed to be called as needed by the
implementation to inform the Sound Menu of changes. These functions
include signal_playing, signal_stopped, signal_paused, and song_changed.

Using
#create the Sound Menu object and reassign functions
sound_menu = SoundMenuControls(desktop_name)
sound_menu._sound_menu_next = _sound_menu_next
sound_menu._sound_menu_previous = _sound_menu_previous
sound_menu._sound_menu_is_playing = _sound_menu_is_playing
sound_menu._sound_menu_play = _sound_menu_play
sound_menu._sound_menu_pause = _sound_menu_play
sound_menu._sound_menu_raise = _sound_menu_raise

#when the player changes track, it should inform the Sound Menu
sound_menu.song_changed(artist,album,title)

#when the player changes playback state, it should inform the Sound Menu
sound_menu.signal_playing()
sound_menu.signal_stopped()
sound_menu.signal_paused()

Configuring
SoundMenuControls does not come with any stock behaviours, so it
cannot be configured

Extending
SoundMenuControls can be used as a base class with single or multiple inheritance.

_sound_menu_next
_sound_menu_previous
_sound_menu_is_playing
_sound_menu_play
_sound_menu_pause

"""

import dbus
import dbus.service

class SoundMenuControls(dbus.service.Object):
    """
    SoundMenuControls - A class to make it easy to integrate with the Ubuntu Sound Menu.

    """

    def __init__(self, identity, desktop_name):
        """
        Creates a SoundMenuControls object.

        Requires a D-Bus loop to be created before the gtk mainloop,
        typically by calling DBusGMainLoop(set_as_default=True).

        arguments:
        identity: The name of the application,
        desktop_name: The XDG name and .desktop filename,
        such as, "simple-player" to refer to the file: simple-player.desktop.

        """
        self.desktop_name = desktop_name
        self.identity = identity
        bus_str = """org.mpris.MediaPlayer2.%s""" % desktop_name
        bus_name = dbus.service.BusName(bus_str, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, "/org/mpris/MediaPlayer2")
        self.__playback_status = "Stopped"
        self.__loop_status = "Track"

        self.song_changed( 0 )

    def song_changed(self, trackid, artists = None, album = None, title = None, album_art = None, filename = None):
        """song_changed - sets the info for the current song.

        This method is not typically overridden. It should be called
        by implementations of this class when the player has changed
        songs.

        named arguments:
            trackid - an integer of the sound index in the tracklist
            artists - a list of strings representing the artists"
            album - a string for the name of the album
            title - a string for the title of the song
            album_art - a string of the uri for the albumart filename
            filename - a string of the uri for the filename

        """
        trackid = dbus.ObjectPath("/".join(["/org", self.desktop_name, "playlist", str(trackid)]))
        if artists is None:
            artists = ["Artist Unknown"]
        if album is None:
            album = "Album Unknown"
        if title is None:
            title = "Title Unknown"
        if album_art is None:
            album_art = ""
        if filename is None:
            filename = ""

        self.__meta_data = dbus.Dictionary({
                            "mpris:trackid":trackid,
                            "xesam:url":filename,
                            "xesam:album":album,
                            "xesam:title":title,
                            "xesam:artist":artists,
                            "mpris:artUrl":album_art,
                            }, "sv", variant_level=1)

        d = dbus.Dictionary({"Metadata":self.__meta_data}, "sv",variant_level=1)
        self.PropertiesChanged("org.mpris.MediaPlayer2.Player",d,[])


    @dbus.service.method('org.mpris.MediaPlayer2')
    def Raise(self):
        """Raise

        D-Bus signal handler for the Raise signal. Do not override this
        function, instead override _sound_menu_raise.

        """

        self._sound_menu_raise()

    def _sound_menu_raise(self):
        """ _sound_menu_raise -

        Override this function to bring the media player to the front
        when selected by the Sound Menu. For example, by calling
        app_window.get_window().show()

        """

        raise NotImplementedError("""@dbus.service.method('org.mpris.MediaPlayer2') Raise
                                      is not implemented by this player.""")


    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        """Get

        A function necessary to implement D-Bus properties.

        This function is only called by the Sound Menu, and should not
        be overridden or called directly.

        """

        my_prop = self.__getattribute__(prop)
        return my_prop

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    def Set(self, interface, prop, value):
        """Set

        A function necessary to implement D-Bus properties.

        This function is only called by the Sound Menu, and should not
        be overridden or called directly.

        """
        my_prop = self.__getattribute__(prop)
        my_prop = value

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        """GetAll

        A function necessary to implement D-Bus properties.

        This function is only called by the Sound Menu, and should not
        be overridden or called directly.

        """
        return {
            'CanQuit':      False,
            'CanRaise':     True,
            'CanGoNext':    True,
            'CanGoPrevious':True,
            'HasTrackList': False,
            'DesktopEntry': self.desktop_name,
            'Identity':     self.identity,
        } # Fixed #1440061

    @property
    def CanControl(self):
        '''b Read only Interface MediaPlayer2.Player'''
        return True

    @property
    def CanPlay(self):
        '''b Read only Interface MediaPlayer2.Player'''
        return True

    @property
    def CanPause(self):
        '''b Read only Interface MediaPlayer2.Player'''
        return True

    @property
    def CanGoNext(self):
        '''b Read only Interface MediaPlayer2.Player'''
        return True

    @property
    def CanGoPrevious(self):
        '''b Read only Interface MediaPlayer2.Player'''
        return True

    @property
    def Identity(self):
        """Identity

        The name of the application

        This property is only used by the Sound Menu, and should not
        be overridden or called directly.

        """

        return self.identity

    @property
    def DesktopEntry(self):
        """DesktopEntry

        The name of the desktop file.

        This property is only used by the Sound Menu, and should not
        be overridden or called directly.

        """

        return self.desktop_name

    @property
    def PlaybackStatus(self):
        """PlaybackStatus

        Current status "Playing", "Paused", or "Stopped"

        This property is only used by the Sound Menu, and should not
        be overridden or called directly.

        """

        return self.__playback_status

    @property
    def LoopStatus(self):
        """LoopStatus

        Current status "None", "Track", or "Playlist"

        This property is only used by the Sound Menu, and should not
        be overridden or called directly.

        """

        return self.__loop_status

    @property
    def Metadata(self):
        """Metadata

        The info for the current song.

        This property is only used by the Sound Menu, and should not
        be overridden or called directly.

        """

        return self.__meta_data

    @dbus.service.method('org.mpris.MediaPlayer2.Player')
    def Next(self):
        """Next

        D-Bus signal handler for the Next signal. Do not override this
        function, instead override _sound_menu_next.

        """

        self._sound_menu_next()

    def _sound_menu_next(self):
        """_sound_menu_next

	Called when the user has clicked the next button in the Sound
	Indicator. Implementations should override this function in order to a
        function to advance to the next track. Implementations should call
	song_changed() and sound_menu.signal_playing() in order to keep the
        song information in the Sound Menu in sync.

        The default implementation of this function has no effect.

        """

        pass

    @dbus.service.method('org.mpris.MediaPlayer2.Player')
    def Previous(self):
        """Previous

        D-Bus signal handler for the Previous signal. Do not override this
        function, instead override _sound_menu_previous.

        """

        self._sound_menu_previous()

    def _sound_menu_previous(self):
        """_sound_menu_previous

        This function is called when the user has clicked
        the previous button in the Sound Indicator. Implementations
        should override this function in order to a function to
        advance to the next track. Implementations should call
        song_changed() and  sound_menu.signal_playing() in order to
        keep the song information in sync.

        The default implementation of this function has no effect.


        """
        pass

    @dbus.service.method('org.mpris.MediaPlayer2.Player')
    def PlayPause(self):
        """PlayPause

        D-Bus signal handler for the PlayPause signal. Do not override this
        function.

        """
        self._sound_menu_play_toggle()

    def _sound_menu_play_toggle(self):
        """_sound_menu_play_toggle

        This function is called when the user has clicked
        the play/pause button in the Sound Indicator. Implementations
        should override this function in order to a function to
        advance to the next track. Implementations should call
        song_changed() and  sound_menu.signal_playing() in order to
        keep the song information in sync.

        The default implementation of this function has no effect.

        """

        pass  

    def signal_playing(self):
        """signal_playing - Tell the Sound Menu that the player has
        started playing. Implementations many need to call this function in order
        to keep the Sound Menu in synch.

        arguments:
            none

        """

        self.__playback_status = "Playing"
        d = dbus.Dictionary({"PlaybackStatus":self.__playback_status, "LoopStatus":self.__loop_status},
                             "sv",variant_level=1)
        self.PropertiesChanged("org.mpris.MediaPlayer2.Player",d,[])

    def signal_paused(self):
        """signal_paused - Tell the Sound Menu that the player has
        been paused. Implementations many need to call this function in order
        to keep the Sound Menu in synch.

        arguments:
            none

        """

        self.__playback_status = "Paused"
        d = dbus.Dictionary({"PlaybackStatus":self.__playback_status, "LoopStatus":self.__loop_status},
                             "sv", variant_level=1)
        self.PropertiesChanged("org.mpris.MediaPlayer2.Player",d,[])

    def signal_stopped(self):
        """signal_stopped - Tell the Sound Menu that the player has
        been stopped. Implementations many need to call this function in order
        to keep the Sound Menu in synch.

        arguments:
            none

        """

        self.__playback_status = "Stopped"
        d = dbus.Dictionary({"PlaybackStatus":self.__playback_status, "LoopStatus":self.__loop_status},
                             "sv", variant_level=1)
        self.PropertiesChanged("org.mpris.MediaPlayer2.Player",d,[])

    def _sound_menu_is_playing(self):
        """_sound_menu_is_playing

        Check if the the player is playing,
        Implementations should override this function
        so that the Sound Menu can check whether to display
        Play or Pause functionality.

        The default implementation of this function always
        returns False.

        arguments:
            none

        returns:
            returns True if the player is playing, otherwise
            returns False if the player is stopped or paused.
        """

        return False

    def _sound_menu_pause(self):
        """_sound_menu_pause

        Responds to the Sound Menu when the user has clicked the
        Pause button.

        Implementations should override this function
        to pause playback when called.

        The default implementation of this function does nothing

        arguments:
            none

        returns:
            None
       """

        pass

    def _sound_menu_play(self):
        """_sound_menu_play

        Responds to the Sound Menu when the user has clicked the
        Play button.

        Implementations should override this function
        to play playback when called.

        The default implementation of this function does nothing

        arguments:
            none

        returns:
            None
       """

        pass

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface_name, changed_properties,
                          invalidated_properties):
        """PropertiesChanged

        A function necessary to implement D-Bus properties.

        Typically, this function is not overridden or called directly.

        """

        pass


