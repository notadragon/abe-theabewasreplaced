#!/usr/bin/env python3

import os
import pathlib
import curses
import curses.textpad


# pygame setup

title = "The Abe Was Replaced <";

def createMenu():
    menu = cursesmenu.CursesMenu(title, "Select an option below")

    return menu

def show(stdscr, message):

    height, width = 5, len(message) + 4
    sh, sw = stdscr.getmaxyx()
    start_y, start_x = (sh // 2) - (height // 2), (sw // 2) - (width // 2)

    # 1. Create a new window (nlines, ncols, begin_y, begin_x)
    win = curses.newwin(height, width, start_y, start_x)

    # 2. Add a border to the window
    win.box()

    # 3. Add the message (relative coordinates to the window)
    win.addstr(2, 2, message)

    # 4. Refresh the window to display content
    win.refresh()

    # Wait for user input to close the "popup"
    win.getch()

    
    
    
def menu(stdscr, menuitems):
    stdscr.clear()
    stdscr.addstr(5,10,title)
    stdscr.refresh()

    curses.napms(100)

    stdscr.addstr(8,13,"Select an option:", curses.A_UNDERLINE)

    for n,i in enumerate(menuitems):
        stdscr.addstr(9 + 2*n + 1, 15, f"{n}: {i}")
    stdscr.refresh()

    while True:
        ch = stdscr.getkey()
        show(stdscr, ch)

        
def main(stdscr):
    stdscr.clear()
    
    for n in range(0,len(title)):
        stdscr.clear();
        stdscr.addstr(5, 10, title[0:n] + " <")
        stdscr.refresh()

        curses.napms(100)

    menu(stdscr, [
        "Run Program",
        "Edit Program",
        "Buy Upgrades",
        "Exit"
        ])
        


if __name__ == '__main__':
    curses.wrapper(main)
    
    
