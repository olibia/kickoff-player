import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gtk, Gdk, GLib
from handlers.stream import StreamHandler
from widgets.gstbox import GstBox
from helpers.gtk import toggle_cursor


class PlayerHandler(object):

  def __init__(self, app):
    self.stream = StreamHandler(self)
    self.app    = app
    self.stack  = app.player_stack

    self.url = None
    self.xid = None

    self.loading = False
    self.cstream = None

    self.is_fullscreen = False
    self.toolbar_stick = True

    self.player = Gtk.Builder()
    self.player.add_from_file('ui/player.ui')
    self.player.connect_signals(self)

    self.overlay = self.player.get_object('overlay_player')
    self.stack.add_named(self.overlay, 'player_video')

    self.playbin = GstBox(callback=self.update_status)
    self.overlay.add(self.playbin)
    self.playbin.connect('button-press-event', self.on_gstbox_player_button_press_event)
    self.playbin.connect('motion-notify-event', self.on_gstbox_player_motion_notify_event)

    self.status = self.player.get_object('label_player_status')
    self.status.set_text('Not playing')

    self.toolbar        = self.player.get_object('toolbar_player')
    self.volume_button  = self.player.get_object('button_volume')
    self.full_button    = self.player.get_object('button_fullscreen')
    self.restore_button = self.player.get_object('button_unfullscreen')
    self.play_button    = self.player.get_object('button_play')
    self.pause_button   = self.player.get_object('button_pause')
    self.stop_button    = self.player.get_object('button_stop')
    self.toolbar_event  = GLib.timeout_add(3000, self.toggle_toolbar, True)

  @property

  def visible(self):
    return self.stack.get_visible_child() == self.overlay

  @property

  def state(self):
    return self.playbin.get_state()

  @property

  def actionable(self):
    return self.url is not None

  def open_stream(self, stream):
    self.cstream = stream
    self.stream.open(stream.url)

    self.toggle_controls()
    self.app.set_stack_visible_child(self.stack)

  def reload_stream(self):
    GLib.idle_add(self.app.toggle_reload, False)

    self.close_stream()
    self.open_stream(self.cstream)

    GLib.idle_add(self.app.toggle_reload, True)

  def close_stream(self):
    self.stop()
    self.stream.close()

  def open(self, url):
    self.url = url
    self.playbin.open(self.url)
    self.play()

  def close(self):
    self.url = None
    self.close_stream()

  def play(self):
    self.playbin.play()
    self.toggle_buttons(True)

  def pause(self):
    self.playbin.pause()

  def stop(self):
    self.toggle_buttons(False)
    self.playbin.stop()

  def set_volume(self, volume):
    self.playbin.set_volume(volume)

  def update_status(self, status):
    labels = {
      'PLAYING': 'Playing',
      'PAUSED':  'Paused',
      'NULL':    'Stopped',
      'ERROR':   'Error',
      'BUFFER':  'Buffering'
    }

    status = labels.get(status, status)
    self.status.set_text(status)

  def toggle_buttons(self, active=True):
    self.pause_button.set_sensitive(active)
    self.stop_button.set_sensitive(active)

  def toggle_fullscreen(self):
    if not self.visible:
      return

    if self.is_fullscreen:
      self.restore_button.hide()
      self.full_button.show()
      self.app.window.unfullscreen()

      self.is_fullscreen = False
    else:
      self.full_button.hide()
      self.restore_button.show()
      self.app.window.fullscreen()

      self.is_fullscreen = True

  def toggle_toolbar(self, timer=True):
    visible = self.toolbar.is_visible()

    if not self.toolbar_stick and self.actionable:
      if timer and visible:
        self.toggle_controls(True)

      if not timer and not visible:
        self.toggle_controls(False)

    return timer

  def toggle_controls(self, hide=False):
    if hide:
      self.toolbar.hide()
      toggle_cursor(self.overlay, True)
    else:
      self.toolbar.show()
      toggle_cursor(self.overlay, False)

  def on_stream_activated(self, _widget, stream):
    self.open_stream(stream)

  def on_button_play_clicked(self, _event):
    if not self.loading:
      self.play()
      self.set_volume(self.volume_button.get_value())

  def on_button_pause_clicked(self, _event):
    if not self.loading:
      self.pause()

  def on_button_stop_clicked(self, _event):
    if not self.loading:
      self.stop()

  def on_button_volume_value_changed(self, _event, value):
    if not self.loading and self.actionable:
      self.set_volume(value)

  def on_window_main_key_release_event(self, _widget, event):
    stack = self.app.get_stack_visible_child()
    kname = Gdk.keyval_name(event.keyval)

    if stack == self.stack and kname == 'F11':
      self.toggle_fullscreen()

  def on_header_button_reload_clicked(self, _event):
    stack = self.app.get_stack_visible_child()

    if stack == self.stack and self.cstream is not None:
      self.reload_stream()

  def on_button_fullscreen_clicked(self, _event):
    self.toggle_fullscreen()

  def on_button_unfullscreen_clicked(self, _event):
    self.toggle_fullscreen()

  def on_gstbox_player_button_press_event(self, _widget, event):
    if event.type == Gdk.EventType._2BUTTON_PRESS:
      self.toggle_fullscreen()

  def on_gstbox_player_motion_notify_event(self, _widget, _event):
    self.toolbar_stick = False

    GLib.source_remove(self.toolbar_event)
    GLib.idle_add(self.toggle_toolbar, False)

    self.toolbar_event = GLib.timeout_add(3000, self.toggle_toolbar, True)

  def on_toolbar_player_enter_notify_event(self, _widget, _event):
    self.toolbar_stick = True
    GLib.idle_add(self.toggle_toolbar, False)
