#!/usr/bin/env python2
#
# Copyright 2012 Janis Jansons (janis.jansons@janhouse.lv)
#

import gi
# make sure you use gtk+ 3
gi.require_version('Gtk', '3.0')
import sys, os
import struct
from gi.repository import GObject, Polkit, GLib, Notify, GUdev, Gio, Gtk

class UsbGuard:

    def __init__(self):
        print "Starting USB Guard"

        ### Udev
        # empty array for all subsystems, char array for subsystem e.g. ["usb","video4linux"] etc
        self.client = GUdev.Client (subsystems=[])
        # or client = GUdev.Client.new ([])
        # Start listening to udev events
        self.client.connect("uevent", self.on_uevent)
        self.devices = self.client.query_by_subsystem("usb")

        ### Random stuff
        # USB device relation store
        self.devtree={}
        
        self.notifications={}
        
        ### Main loop
        self.mainloop = GLib.MainLoop ()
        
        ### Systray stuff
        self.statusicon = Gtk.StatusIcon()
        self.statusicon.set_from_icon_name("security-medium")
        self.statusicon.set_tooltip_text("USB Guard")
        #self.statusicon.connect("popup-menu", self.OnShowPopupMenu)
        
        ### Polkit
        """
        #mainloop = GObject.MainLoop()
        authority = Polkit.Authority.get()
        subject = Polkit.UnixProcess.new(os.getppid())

        cancellable = Gio.Cancellable()
        GObject.timeout_add(10 * 1000, do_cancel, cancellable)

        authority.check_authorization(subject,
            "org.freedesktop.policykit.exec", #"org.freedesktop.policykit.exec",
            None,
            Polkit.CheckAuthorizationFlags.ALLOW_USER_INTERACTION,
            cancellable,
            check_authorization_cb,
            mainloop)
        """

        ### Main GTK window
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main.ui")

        self.window = self.builder.get_object("window1")
        
        
        self.style = self.window.get_style_context()

        # pack the table into the scrolled window
        self.container = self.builder.get_object("dev_container")#.add_with_viewport(table)

        self.container_box = Gtk.Box(spacing=10, orientation=Gtk.Orientation.VERTICAL)

        self.container.add_with_viewport(self.container_box)
        self.container_box.show()

        ###############


        self.sort_devices()

        #for device in self.devices:
        #    self.print_device(device)


        ###############
        
        # Make the main window visible      
        self.window.show()
        # Start the main loop
        self.mainloop.run ()
        
        return

    def print_device(self, device):
        print "subsystem", device.get_subsystem()
        print "devtype", device.get_devtype()
        print "name", device.get_name()
        print "number", device.get_number()
        print "sysfs_path:", device.get_sysfs_path()
        print "driver:", device.get_driver()
        print "action:", device.get_action()
        print "seqnum:", device.get_seqnum()
        print "device type:", device.get_device_type()
        print "device number:", device.get_device_number()
        print "device file:", device.get_device_file()
        print "device file symlinks:", ", ".join(device.get_device_file_symlinks())
        print "device keys:", ", ".join(device.get_property_keys())
        #for device_key in device.get_property_keys():
        #    print "   device property %s: %s"  % (device_key, device.get_property(device_key))

    def on_tensec_timeout(self, loop):
      print("Ten seconds have passed. Now exiting.")
      loop.quit()
      return False

    def device_enabled(self, path):
        f = open(path+'authorized', 'r')
        enabled=f.read().rstrip()
        f.close
        #print enabled
        if enabled == '1':
            return True
        elif enabled == '0':
            return False

    def check_authorization_cb(self, authority, res, loop):
        try:
            result = authority.check_authorization_finish(res)
            if result.get_is_authorized():
                print("Authorized")
            elif result.get_is_challenge():
                print("Challenge")
            else:
                print("Not authorized")
        except GObject.GError as error:
             print("Error checking authorization: %s" % error.message)
            
        print("Authorization check has been cancelled "
              "and the dialog should now be hidden.\n"
              "This process will exit in ten seconds.")
        GObject.timeout_add(10000, on_tensec_timeout, loop)


    def do_cancel(self ,cancellable):
        print("Timer has expired; cancelling authorization check")
        cancellable.cancel()
        return False


    def action_whitelist(self, notifyObj, two, three):

        print "Device added to whitelist."



        notifyObj.close()

    def action_once(self, notifyObj, two, three):

        print "Enabling device once."



        notifyObj.close()

    def action_toggle(self, button, something, dev):
        
        if not dev in self.devtree:
            print "Device "+dev+" not found in device list"
            return False
        try:
            if self.devtree[dev]['enabled'] == True:
                self.action_disable(dev)
                button.set_label("Enable device")
            else:
                self.action_enable(dev)
                button.set_label("Disable device")
                
        except RuntimeError:
            button.set_label("Error...")
            raise
        #else:
            #button.set_label("Error...")
        
        
        #print "Clicked button"



    def action_enable(self, dev):
        
        self.action_set(self.devtree[dev]['path']+'authorized', '1')
        self.devtree[dev]['enabled'] = True
        
    def action_disable(self, dev):
        
        self.action_set(self.devtree[dev]['path']+'authorized', '0')
        self.devtree[dev]['enabled'] = False
        
    def action_set(self, path, value):
        f = open(path, 'w')
        enabled=f.write(value)
        f.close

    def device_vendor_string(self, device):

        if device.get_property("ID_VENDOR_FROM_DATABASE"):
            return device.get_property("ID_VENDOR_FROM_DATABASE")
            
        elif device.get_property("ID_VENDOR_ENC"):
            return device.get_property("ID_VENDOR_ENC")
            
        else:
            return device.get_property("ID_VENDOR")


    def device_model_string(self, device):

        if device.get_property("ID_PRODUCT_FROM_DATABASE"):
            return device.get_property("ID_PRODUCT_FROM_DATABASE")
            
        elif device.get_property("ID_MODEL_ENC"):
            return device.get_property("ID_MODEL_ENC")
            
        else:
            return device.get_property("ID_MODEL")

    def on_change(self, device):
        
        if not device.get_property("DEVNUM"):
            return False

        devname = get_dev_path(device)
        
        if device_is_hub(device):
            # check if authorized_default has changed
            
            print "Checking authorized_default state"

        # check if device authorized state has changed
        print "Checking device state"
        

    def on_remove(self, device):
        
        if not device.get_property("DEVNUM"):
            return False

        devname = get_dev_path(device)

        if devname in self.notifications:
            del self.notifications[devname]
            
    def on_add(self, device):
        
        if not device.get_property("DEVNUM"):
            return False

        devname = get_dev_path(device)

        if devname not in self.notifications:
            text="%s\n%s" % ( self.device_vendor_string(device), self.device_model_string(device) )
            Notify.init('My Application Name')
            self.notifications[devname]=(device)
            self.notifications[devname] = Notify.Notification.new(
                'New USB device connected',
                text,
                'security-medium'
            )
        
        self.notifications[devname].add_action('whitelist', 'Whitelist ', self.action_whitelist, None, None)
        self.notifications[devname].add_action('once', 'Allow once ', self.action_once, None, None)
        
        self.notifications[devname].show()
        
        """
        print "subsystem", device.get_subsystem()
        print "devtype", device.get_devtype()
        print "name", device.get_name()
        print "number", device.get_number()
        print "sysfs_path:", device.get_sysfs_path()
        print "driver:", device.get_driver()
        print "action:", device.get_action()
        print "seqnum:", device.get_seqnum()
        print "device type:", device.get_device_type()
        print "device number:", device.get_device_number()
        print "device file:", device.get_device_file()
        print "device file symlinks:", ", ".join(device.get_device_file_symlinks())
        print "device keys:", ", ".join(device.get_property_keys())
        for device_key in device.get_property_keys():
            print "   device property %s: %s"  % (device_key, device.get_property(device_key))
        """

    # Dbus event handler
    def on_uevent (self, client, action, device):
        print ("action " + action + " on device " + device.get_sysfs_path())
        #if device.get_subsystem() == "usb":
        if action == "add":
            self.on_add(device)
        if action == "remove":
            self.on_remove(device)
        if action == "change":
            self.on_change(device)

    def rec_print(self, devtree, dev, lev):

        if lev > 0:
            
            print "Level: "+str(lev)+"; Device: "+dev
            print devtree[dev]
            print "\n\n\n"
            device=devtree[dev]['device']
            
            
            color=color_to_string(self.style.lookup_color('info_fg_color')[1])
            #color="gray"
            
            label_text = "<span foreground='%s'><i>%s</i></span>, <b>%s</b>" % ( #\nPath: %s
                color,
                self.device_vendor_string(device), 
                self.device_model_string(device), 
                #device.get_sysfs_path()#.rsplit('/', 1)[0] + '/' 
                )
            print label_text+devtree[dev]['path']
            #print device.get_sysfs_path().rsplit('/', 1)[0] + '/' 
            #print get_dev_path(device)
            #print dev
            #label=device_vendor_string(device)+", "+device_model_string(device)
            #label="wololo"
            label_text=label_text.replace('\x20', ' ')

            if devtree[dev]['hub'] == False:
                
                box_vert = Gtk.Box(spacing=5, orientation=Gtk.Orientation.VERTICAL)
                self.container_box.pack_start(box_vert, False, False, 0)
                box_vert.show()
                
                box = Gtk.Box(spacing=5, orientation=Gtk.Orientation.HORIZONTAL)
                box_vert.pack_start(box, False, False, 0)
                
                box2 = Gtk.Box(spacing=5, orientation=Gtk.Orientation.HORIZONTAL)
                box_vert.pack_start(box2, False, False, 0)
                
                
                box_vert.set_margin_left(( 25*(lev-1) )+25)
                
                box.show()
                box2.show()
                
                
                label = Gtk.Label()
                label.set_markup(label_text.decode('string-escape'))
                
                always = Gtk.CheckButton("Enable always")

                button = Gtk.Button("")
                button.connect("button-release-event", self.action_toggle, dev)
                
                if devtree[dev]['enabled'] == True:
                    button.set_label("Disable device")
                    label.set_sensitive(True)
                    always.set_sensitive(True)
                else:
                    button.set_label("Enable device")
                    label.set_sensitive(False)
                    always.set_sensitive(False)
                
                box.pack_start(label, False, False, 0)
                label.show()
                
                box2.pack_start(button, False, False, 0)
                button.show()
                
                
                box2.pack_start(always, False, False, 0)
                always.show()

            else:
                
                button = Gtk.CheckButton()
                #button.set_halign(Gtk.Align.START)
                button.set_margin_left(25*(lev-1))
                #button.halign(Gtk.GTK_ALIGN_START)
                self.container_box.pack_start(button, False, False, 0)
                button.show()
                #disable
                #button.set_sensitive(False)
                
                label = Gtk.Label()
                label.set_markup(label_text.decode('string-escape'))
                #label.set_justify(Gtk.Justification.LEFT)
                button.add(label)
                label.show()
        
        
        for dp in self.devtree[dev]['children']:
            self.rec_print(self.devtree, dp, lev+1)

    def sort_devices(self):

        for device in self.devices:
            if device.get_driver() != "hub":
                continue

            #device
            dev = device.get_sysfs_path().rsplit('/', 2)[1] + '/'
            #parent
            par = device.get_sysfs_path().rsplit('/', 3)[1] + '/'
            if par in self.devtree:

                if dev not in self.devtree[par]['children']:
                    self.devtree[par]['children'].append(dev)
                
                if dev in self.devtree:
                    self.devtree[dev]['has_par']=True
                else:
                    self.devtree[dev]={'name': dev, 'has_par': True, 'children':[], 'hub':True}
                
            else:
                self.devtree[par]={'name': par, 'has_par': False, 'children': [dev], 'hub':True}

                if dev in self.devtree:
                    self.devtree[dev]['has_par']=True
                else:
                    self.devtree[dev]={'name': dev, 'has_par': True,'children':[], 'hub':True}

        for device in self.devices:
            
            
            if device.get_driver() != "hub":
                continue
            
            dev = device.get_sysfs_path().rsplit('/', 2)[1] + '/'
            self.devtree[dev]['device']=device
            #self.devtree[dev]['ok']=True

        for device in self.devices:
            if device.get_driver() == "hub":
                continue
                
            
            devpath=device.get_sysfs_path()
            dev = devpath.rsplit('/', 1)[1].rsplit(':', 1)[0] + '/'
            
            if dev not in self.devtree:
                self.devtree[dev]={'name': dev, 'has_par': True,'children':[], 'hub':False, 'device':device}
                par = devpath.rsplit('/', 2)[1] + '/'

                if dev not in self.devtree[par]['children']:
                    self.devtree[par]['children'].append(dev)

                #self.devtree[dev]['ok']=True

        for dev in self.devtree:
            if 'device' in self.devtree[dev]:
                #print self.devtree[dev]['device']
                if self.devtree[dev]['hub'] == True:
                    self.devtree[dev]['path']=self.devtree[dev]['device'].get_sysfs_path().rsplit('/', 1)[0] + '/'
                else:
                    self.devtree[dev]['path']=self.devtree[dev]['device'].get_sysfs_path().rsplit('/', 0)[0] + '/'
                print self.devtree[dev]['path']
                self.devtree[dev]['enabled']=self.device_enabled(self.devtree[dev]['path'])

                #print "good";

        #print self.devtree

        for dev in self.devtree:

            if self.devtree[dev]['has_par'] == True:
                continue
            self.rec_print(self.devtree, dev, 0)
                


def get_dev_path(device):

    devdriver = device.get_driver()
    devpath = device.get_sysfs_path()

    if devdriver != "hub":
        return devpath.rsplit('/', 1)[1].rsplit(':', 1)[0] + '/'
    if devdriver == "hub":
        return devpath.rsplit('/', 2)[1] + '/'

    return False

def device_is_hub(device):
    
    if device.get_driver() == "hub":
        return True
    else:
        return False

def color_to_string(gdkcolor):
    color = gdkcolor.to_string()
    rgb = color[4:len(color)-1].split(',')
    rgb2 = (int(num) for num in rgb)
    return '#'+"".join(map(chr, rgb2)).encode('hex')

def main():
    u=UsbGuard()
    
if __name__ == '__main__':
    main()
