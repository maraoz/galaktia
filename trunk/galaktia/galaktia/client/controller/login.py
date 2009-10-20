 #!/usr/bin/python
# -*- coding: utf-8 -*-

import os

import pyglet
from pyglet.gl import glViewport, glMatrixMode, glLoadIdentity, glOrtho
import pyglet.gl as gl

from galaktia.client.controller.widget import TextWidget, PasswordField


CLIENT_VERSION = "0.2"

class LoginViewport(pyglet.graphics.Batch):

    def __init__(self):
        super(LoginViewport, self).__init__()
        self.background = pyglet.graphics.OrderedGroup(0)
        self.foreground = pyglet.graphics.OrderedGroup(1)


class LoginHandler():

    def __init__(self, window):
        self.viewport = LoginViewport()
        self.window = window
        self.welcomeLabel = pyglet.text.Label(u'¡Welcome to Galaktia!',
                font_name='Arial', font_size=36, bold=True,
                x=self.window.width//2, y=self.window.height//1.5,
                anchor_x='center', anchor_y='center')
        self.usernameLabel = pyglet.text.Label(u'Username',
                font_name='Arial', font_size=12, bold=True,
                x=self.window.width//4, y=self.window.height//4,
                anchor_x='center', anchor_y='center')
        self.passwordLabel = pyglet.text.Label(u'Password',
                font_name='Arial', font_size=12, bold=True,
                x=self.window.width//4, y=self.window.height//5,
                anchor_x='center', anchor_y='center')
        self.stateLabel = pyglet.text.Label(u'',
                font_name='Arial', font_size=12, bold=True,
                x=self.window.width//2, y=self.window.height//7,
                anchor_x='center', anchor_y='center',
                color=(255, 0, 0, 255) )

        self.widgets = [
            TextWidget('', self.window.width//4 + 50, self.window.height//4 - 10, self.window.width//2, self.viewport),
            PasswordField('', self.window.width//4 + 50, self.window.height//5 - 10, self.window.width//2, self.viewport)
        ]
        for w in self.widgets:
            w.caret.visible = False
        self.text_cursor = self.window.get_system_mouse_cursor('text') 
        self.focus = None
        self.set_focus(self.widgets[0])

        self.old_version = False

    def on_mouse_motion(self, x, y, dx, dy):
        for widget in self.widgets:
            if widget.hit_test(x, y):
                self.window.set_mouse_cursor(self.text_cursor)
                break
        else:
            self.window.set_mouse_cursor(None)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.focus:
            for widget in self.widgets:
                if widget.hit_test(x, y):
                    self.set_focus(widget)
                    break
        if self.focus:
            self.focus.caret.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.focus:
            self.focus.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
    def on_mouse_release(self, x, y, buttons, modifiers):
        pass

    def on_text(self, text):
        if self.focus:
            if text != '\r':
                self.focus.caret.on_text(text)

    def on_text_motion(self, motion):
        if self.focus:
            self.focus.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        if self.focus:
            self.focus.caret.on_text_motion_select(motion)

    def set_focus(self, focus):
        if self.focus:
            self.focus.caret.visible = False
            self.focus.caret.mark = self.focus.caret.position = 0

        self.focus = focus
        if self.focus:
            self.focus.caret.visible = True
            self.focus.caret.mark = 0
            self.focus.caret.position = len(self.focus.document.text)

    def on_draw(self):
        self.window.clear()
        self.viewport.draw()
        self.welcomeLabel.draw()
        self.usernameLabel.draw()
        self.passwordLabel.draw()
        self.stateLabel.draw()

    def on_close(self):
        self.window.exit()
        exit()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.window.dispatch_event('on_close')
        elif symbol in (pyglet.window.key.ENTER, pyglet.window.key.NUM_ENTER):
            self.ingresar()
            return True
        elif symbol == pyglet.window.key.TAB and self.focus:
            this = self.widgets.index(self.focus)
            self.set_focus(self.widgets[1-this])
    def on_key_release(self,symbol,modifiers):
        pass

    def on_resize(self,width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(gl.GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(gl.GL_MODELVIEW)

    def on_user_joined(self, username):
        pass

    def on_user_rejected(self):
        self.stateLabel.text = u'Oops. ¡That name is already taken!'
    def on_check_protocol_version(self, session_id, version, url):
        if version != CLIENT_VERSION:
            self.stateLabel.text = ("Client version is too old. You need %s." + \
            " Download it from %s" ) % (version, url)
            self.old_version = True
            self.set_focus(None) 

    def ingresar(self):
        username = self.widgets[0].text()
        password = self.widgets[1].text()
        
        self.window.request_user_join(username, password)

    def on_connection_refused(self):
        self.stateLabel.text = u'No server listening!'

