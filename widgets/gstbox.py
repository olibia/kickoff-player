import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gst, GObject

Gst.init(None)
Gst.init_check(None)


class GstBox(Gtk.Box):

  __gtype_name__ = 'GstBox'

  callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.Box.__init__(self, *args, **kwargs)

    self.gtksink = Gst.ElementFactory.make('gtksink')
    self.pack_start(self.gtksink.props.widget, True, True, 0)
    self.gtksink.props.widget.show()

    self.playbin = Gst.ElementFactory.make('playbin')
    self.playbin.set_property('video-sink', self.gtksink)
    self.playbin.set_property('force-aspect-ratio', True)

    self.dbus = self.playbin.get_bus()
    self.dbus.add_signal_watch()
    self.dbus.connect('message', self.on_dbus_message)

  def get_state(self):
    state = self.playbin.get_state(1)
    state = list(state)[1]
    state = state.value_name.split('_')[-1]

    return state

  def open(self, url):
    self.playbin.set_state(Gst.State.NULL)
    self.playbin.set_property('uri', url)

  def play(self):
    if self.get_state() != 'PLAYING':
      self.playbin.set_state(Gst.State.PLAYING)
      self.callback('PLAYING')

  def pause(self):
    if self.get_state() != 'PAUSED':
      self.playbin.set_state(Gst.State.PAUSED)
      self.callback('PAUSED')

  def stop(self):
    if self.get_state() != 'NULL':
      self.playbin.set_state(Gst.State.NULL)
      self.callback('NULL')

  def set_volume(self, volume):
    self.playbin.set_property('volume', volume)

  def buffer(self, message):
    self.callback('BUFFER')

    if self.get_state() != 'PAUSED':
      self.playbin.set_state(Gst.State.PAUSED)

    if message.parse_buffering() == 100:
      self.play()

  def restart(self):
    self.callback('BUFFER')
    self.playbin.set_state(Gst.State.NULL)
    self.play()

  def on_dbus_message(self, _bus, message):
    if message.type == Gst.MessageType.ERROR:
      self.callback('ERROR')
    elif message.type == Gst.MessageType.EOS:
      self.restart()
    elif message.type == Gst.MessageType.BUFFERING:
      self.buffer(message)
