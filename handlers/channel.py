import gi
import threading

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.gtk import filter_widget_items

from widgets.channelbox import ChannelBox
from widgets.filterbox import FilterBox


class ChannelHandler(object):

	def __init__(self, app):
		self.app = app
		self.data = app.data
		self.window = app.window
		self.stack = app.channels_stack
		self.player = app.player

		self.channels = Gtk.Builder()
		self.channels.add_from_file('ui/channels.ui')
		self.channels.connect_signals(self)

		self.channels_box = self.channels.get_object('box_channels')
		self.stack.add_named(self.channels_box, 'channels_container')

		GObject.idle_add(self.do_channels_filters)
		GObject.idle_add(self.do_channels_list)

	def update_channels_data(self):
		thread = threading.Thread(target=self.do_update_channels_data)
		thread.start()

	def do_update_channels_data(self):
		GObject.idle_add(self.app.toggle_reload, False)

		self.app.streams_api.save_channels()

		GObject.idle_add(self.update_channels_filters)
		GObject.idle_add(self.update_channels_list)
		GObject.idle_add(self.app.toggle_reload, True)

	def do_channels_filters(self):
		clistbox = self.channels.get_object('list_box_channels_filters')
		cfilters = ['All Languages'] + self.data.load_languages()

		for cfilter in cfilters:
			filterbox = FilterBox(filter_name=cfilter)
			clistbox.add(filterbox)

	def update_channels_filters(self):
		clistbox = self.channels.get_object('list_box_channels_filters')
		cfilters = ['All Languages'] + self.data.load_languages()

		for item in clistbox.get_children():
			if item.filter_name not in cfilters:
				clistbox.remove(item)

	def do_channels_list(self):
		channels = self.data.load_channels(True)
		cflowbox = self.channels.get_object('flow_box_channels_list')

		for channel in channels:
			channbox = ChannelBox(channel=channel, callback=self.player.open_stream)
			cflowbox.add(channbox)

	def update_channels_list(self):
		channels = self.data.load_channels(True, True)
		cflowbox = self.channels.get_object('flow_box_channels_list')

		for item in cflowbox.get_children():
			if item.channel.id in channels:
				channel = self.data.get_channel({ 'id': item.channel.id })
				item.set_property('channel', channel)
			else:
				cflowbox.remove(item)

	def on_header_button_reload_clicked(self, _event):
		if self.app.get_stack_visible_child() == self.stack:
			self.update_channels_data()

	def on_list_box_channels_filters_row_activated(self, _listbox, item):
		flowbox = self.channels.get_object('flow_box_channels_list')
		filter_widget_items(self.window, flowbox, item, 'All Languages', 'filter_name')
