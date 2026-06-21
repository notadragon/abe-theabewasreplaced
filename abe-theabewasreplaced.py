#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import os
import pathlib
import urwid
import pathlib


title = "The Abe Was Replaced <";

if urwid.display.web.is_web_request():
    Screen = urwid.display.web.Screen
    loop_cls = urwid.SelectEventLoop
else:
    event_loops: dict[str, type[urwid.EventLoop] | None] = {
        "none": None,
        "select": urwid.SelectEventLoop,
        "asyncio": urwid.AsyncioEventLoop,
    }
    if hasattr(urwid, "TornadoEventLoop"):
        event_loops["tornado"] = urwid.TornadoEventLoop
    if hasattr(urwid, "GLibEventLoop"):
        event_loops["glib"] = urwid.GLibEventLoop
    if hasattr(urwid, "TwistedEventLoop"):
        event_loops["twisted"] = urwid.TwistedEventLoop
    if hasattr(urwid, "TrioEventLoop"):
        event_loops["trio"] = urwid.TrioEventLoop
    if hasattr(urwid, "ZMQEventLoop"):
        event_loops["zmq"] = urwid.ZMQEventLoop

    parser = argparse.ArgumentParser(description="Input test")
    parser.add_argument(
        "argc",
        help="Positional arguments ('r' for raw display)",
        metavar="<arguments>",
        nargs="*",
        default=(),
    )
    group = parser.add_argument_group("Advanced Options")
    group.add_argument(
        "--event-loop",
        choices=event_loops,
        default="none",
        help="Event loop to use ('none' = use the default)",
    )
    group.add_argument("--debug-log", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if not hasattr(urwid.display, "curses") or "r" in args.argc:
        Screen = urwid.display.raw.Screen
    else:
        Screen = urwid.display.curses.Screen

    loop_cls = event_loops[args.event_loop]

    if args.debug_log:
        logging.basicConfig(
            level=logging.DEBUG,
            filename="debug.log",
            format=(
                "%(levelname)1.1s %(asctime)s | %(threadName)s | %(name)s \n"
                "\t%(message)s\n"
                "-------------------------------------------------------------------------------"
            ),
            datefmt="%d-%b-%Y %H:%M:%S",
            force=True,
        )

        logging.captureWarnings(True)

def hello_message(loop, args):
    text = urwid.Text("", align="center")
    fill = urwid.Filler(text, "middle")

    def update_message(loop, msg):
        if msg[1] == 0:
            text.set_text("<")
        elif msg[1] > 0:
            text.set_text(msg[0][:msg[1]] + " <")
        else:
            text.set_text("")

        timeout = 0.1
        if msg[1] == len(msg[0]):
            timeout = 1
            nextdir = -1
        else:
            nextdir = msg[2]
            
        if msg[1] >= -2:
            loop.set_alarm_in(timeout, update_message, (msg[0], msg[1] + nextdir, nextdir) )

    loop.set_alarm_in(0, update_message, ("Hello",0,1))
    loop.set_alarm_in(3, update_message, ("Nice to meet you :)",0,1))
    loop.set_alarm_in(9, update_message, ("Get to work now!!!!".upper(),0,1))
    

    loop.widget = fill

def opening_title(loop, args):
    left = urwid.Text("")
    text = urwid.Text("")
    right = urwid.Text("")
    bordered = urwid.LineBox(text)
    columns = urwid.Columns( (left, bordered, right) )
    fill = urwid.Filler(columns, "middle")


    # update the text of our title
    def title_update(loop, count):
        text.set_text(title[:count] + " <")
        if count < len(title)-2:
            loop.set_alarm_in(0.1, title_update, count+1)
        else:
            loop.set_alarm_in(2.5, title_update2, count)
            
    def title_update2(loop, count):
        if count > 0:
            text.set_text(title[:count] + " <")
        elif count == 0:
            text.set_text("<")
        else:
            text.set_text("")
            
        if count > -2:
            loop.set_alarm_in(0.1, title_update2, count-1)
        else:
            loop.set_alarm_in(1, hello_message, None)
            
    loop.set_alarm_in(0.1, title_update, 1)
    loop.widget = fill

# --------------------------------------------------------------------------------------------------
class LineWalker(urwid.ListWalker):
    """ListWalker-compatible class for lazily reading file contents."""

    def __init__(self, name: str) -> None:
        # do not overcomplicate example
        self.file = open(name, encoding="utf-8")  # noqa: SIM115  # pylint: disable=consider-using-with
        self.lines = []
        self.focus = 0

    def get_focus(self):
        return self._get_at_pos(self.focus)

    def set_focus(self, focus) -> None:
        self.focus = focus
        self._modified()

    def get_next(self, position: int) -> tuple[urwid.Edit, int] | tuple[None, None]:
        return self._get_at_pos(position + 1)

    def get_prev(self, position: int) -> tuple[urwid.Edit, int] | tuple[None, None]:
        return self._get_at_pos(position - 1)

    def read_next_line(self) -> str:
        """Read another line from the file."""

        next_line = self.file.readline()

        if not next_line or next_line[-1:] != "\n":
            # no newline on last line of file
            self.file = None
        else:
            # trim newline characters
            next_line = next_line[:-1]

        edit = urwid.Edit("", next_line, allow_tab=True)
        edit.edit_pos = 0
        edit.original_text = next_line
        self.lines.append(edit)

        return next_line

    def _get_at_pos(self, pos: int) -> tuple[urwid.Edit, int] | tuple[None, None]:
        """Return a widget for the line number passed."""

        if pos < 0:
            # line 0 is the start of the file, no more above
            return None, None

        if len(self.lines) > pos:
            # we have that line so return it
            return self.lines[pos], pos

        if self.file is None:
            # file is closed, so there are no more lines
            return None, None

        assert pos == len(self.lines), "out of order request?"  # noqa: S101  # "assert" is OK in examples

        self.read_next_line()

        return self.lines[-1], pos

    def split_focus(self) -> None:
        """Divide the focus edit widget at the cursor location."""

        focus = self.lines[self.focus]
        pos = focus.edit_pos
        edit = urwid.Edit("", focus.edit_text[pos:], allow_tab=True)
        edit.original_text = ""
        focus.set_edit_text(focus.edit_text[:pos])
        edit.edit_pos = 0
        self.lines.insert(self.focus + 1, edit)

    def combine_focus_with_prev(self) -> None:
        """Combine the focus edit widget with the one above."""

        above, _ = self.get_prev(self.focus)
        if above is None:
            # already at the top
            return

        focus = self.lines[self.focus]
        above.set_edit_pos(len(above.edit_text))
        above.set_edit_text(above.edit_text + focus.edit_text)
        del self.lines[self.focus]
        self.focus -= 1

    def combine_focus_with_next(self) -> None:
        """Combine the focus edit widget with the one below."""

        below, _ = self.get_next(self.focus)
        if below is None:
            # already at bottom
            return

        focus = self.lines[self.focus]
        focus.set_edit_text(focus.edit_text + below.edit_text)
        del self.lines[self.focus + 1]

class EditDisplay(urwid.Frame):

    palette: typing.ClassVar[list[tuple[str, str, str, ...]]] = [
        ("body", "default", "default"),
        ("foot", "dark cyan", "dark blue", "bold"),
        ("key", "light cyan", "dark blue", "underline"),
    ]

    footer_text = (
        "foot",
        [
            "Text Editor    ",
            ("key", "F5"),
            " save  ",
            ("key", "F8"),
            " done",
        ],
    )

    def __init__(self, loop, name: str) -> None:
        self.loop = loop
        self.save_name = name
        self.walker = LineWalker(name)
        self.listbox = urwid.ListBox(self.walker)
        self.footer = urwid.AttrMap(urwid.Text(self.footer_text), "foot")
        super().__init__(urwid.AttrMap(self.listbox, "body"), footer=self.footer)

    def keypress(self, size, k):
        """Last resort for keypresses."""

        if k == "f5":
            self.save_file()
        elif k == "f8":
            self.save_file()
            main_menu(self.loop,None)
        elif k == "delete":
            # delete at end of line
            self.walker.combine_focus_with_next()
        elif k == "backspace":
            # backspace at beginning of line
            self.walker.combine_focus_with_prev()
        elif k == "enter":
            # start new line
            self.walker.split_focus()
            # move the cursor to the new line and reset pref_col
            self.loop.process_input(["down", "home"])
        elif k == "right":
            w, pos = self.walker.get_focus()
            w, pos = self.walker.get_next(pos)
            if w:
                self.listbox.set_focus(pos, "above")
                self.loop.process_input(["home"])
        elif k == "left":
            w, pos = self.walker.get_focus()
            w, pos = self.walker.get_prev(pos)
            if w:
                self.listbox.set_focus(pos, "below")
                self.loop.process_input(["end"])
        else:
            return super().keypress(size, k)

    def save_file(self) -> None:
        """Write the file out to disk."""

        lines = []
        walk = self.walker
        for edit in walk.lines:
            # collect the text already stored in edit widgets
            lines.append(edit.edit_text)

        # then the rest
        while walk.file is not None:
            lines.append(walk.read_next_line())

        # write back to disk
        with open(self.save_name, "w", encoding="utf-8") as outfile:
            prefix = ""
            for line in lines:
                outfile.write(prefix + line)
                prefix = "\n"


def edit_program(loop):
    editor = EditDisplay(loop, "abewasreplaced.program")
    loop.widget = editor

# --------------------------------------------------------------------------------------------------

def run_program(loop):
    pass

# --------------------------------------------------------------------------------------------------

def buy_upgrades(loop):
    pass

# --------------------------------------------------------------------------------------------------

class FileListIterator(urwid.ListWalker):
    def __init__(self, text):
        self.position = 0
        self.lines = text.split("\n")

    def _get_line(self, index):
        # Load from cache if already read
        if index < len(self.lines):
            return self.lines[index]
        return None

    def get_focus(self):
        line = self._get_line(self.position)
        if line is None:
            return None, None
        return urwid.Text(line), self.position

    def set_focus(self, position):
        self.position = position

    def get_next(self, position):
        line = self._get_line(position + 1)
        if line is None:
            return None, None
        return urwid.Text(line), position + 1

    def get_prev(self, position):
        if position <= 0:
            return None, None
        line = self._get_line(position - 1)
        return urwid.Text(line), position - 1

class HelpListBox(urwid.ListBox):
    def __init__(self, walker, helpdone):
        self.helpdone = helpdone
        super().__init__(walker)

    def keypress(self, size, key):
        if key == 'enter':
            self.helpdone()
        return super().keypress(size, key)

def show_help(loop):
    help_text = """
This is the help text for our game.

We hope you enjoy playing it.
"""
    
    walker = FileListIterator(help_text)
    listbox = HelpListBox(walker, lambda : main_menu(loop,None))
    bordered = urwid.LineBox(listbox)

    loop.widget = bordered

def exit_program(loop):
    raise urwid.ExitMainLoop

def menu(loop, title, choices_):
    body = [urwid.Text(title), urwid.Divider()]
    for c in choices_:
        button = urwid.Button(c[0])
        urwid.connect_signal(button, "click", item_chosen, user_args=(loop, c[0], c[1]))
        body.append(urwid.AttrMap(button, None, focus_map="reversed"))
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


def item_chosen(loop, label, cb, button):
    #print(f"LOOP:{loop} LABEL:{label} CB:{cb}")
    cb(loop)
    
main_menu_options = [
    ("Edit Program", edit_program),
    ("Buy Upgrades", buy_upgrades),
    ("Help", show_help),
    ("Exit", exit_program),
    ]

def main_menu(loop, args):
    main = urwid.Padding(menu(loop, "Make your choice", main_menu_options), left=2, right=2)
    top = urwid.Overlay(
        main,
        urwid.SolidFill("\N{MEDIUM SHADE}"),
        align=urwid.CENTER,
        width=(urwid.RELATIVE, 60),
        valign=urwid.MIDDLE,
        height=(urwid.RELATIVE, 60),
        min_width=20,
        min_height=9,
    )
    loop.widget = main

    
def main():
    urwid.display.web.set_preferences(title)
    if urwid.display.web.handle_short_request():
        return
    
    screen = Screen()
    columns = urwid.Columns( () )
    fill = urwid.Filler(columns, "middle")

    def input_filter(keys, raw):
        if "q" in keys or "Q" in keys:
            raise urwid.ExitMainLoop

        return keys

    loop = urwid.MainLoop(
        fill,
        [
        ],
        screen,
        input_filter=input_filter,
        event_loop=loop_cls() if loop_cls is not None else None,
    )

    #loop.set_alarm_in(0, opening_title, None)
    #loop.set_alarm_in(0, hello_message, None)
    loop.set_alarm_in(0, main_menu, None)


    try:
        old = screen.tty_signal_keys("undefined", "undefined", "undefined", "undefined", "undefined")
        loop.run()
    finally:
        if old:
            screen.tty_signal_keys(*old)        


if __name__ == '__main__':
    main()
    
    
