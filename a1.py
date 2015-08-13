#!/usr/bin/env python3
# A1 for COMPSCI340/SOFTENG370 2015
# Prepared by Robert Sheehan
# Modified by Yubo Wu

import dispatcher
import iosys
import process
import curses
import curses.panel
import re
from time import sleep

def menu(menu_string):
    """Present menu information, receive key from user and process.

    The format of each command must be like: "(q)uit"
    The letter expected as input is "q" in this case and the
    function name is "quit".
    Each function name must be unique.
    Functions return True iff the menu interaction has finished.
    Commands are separated by commas.
    """
    finished = False
    while not finished:
        command_list = re.split(", *", menu_string)
        command_dictionary = {}
        for command in command_list:
            letter = command[1]
            function = letter + command[3:]
            command_dictionary[letter] = function
        menu_window.addstr(0, 0, menu_string+":", curses.A_REVERSE)
        refresh_menu()

        key = ""
        while key not in command_dictionary:
            key = menu_window.getkey().lower()
        finished = globals()[command_dictionary[key]]() # call the command, exit this menu if True


def refresh_menu():
    """Refresh the menu and put the cursor there."""
    menu_window.clrtoeol()
    menu_panel.top()  # put the menu at the top of the panel stack
    curses.panel.update_panels()
    curses.doupdate()

def new():
    """Get info from user to create a new process."""
    menu("(i)nteractive, (b)ackground, (c)ancel")
    return False

def get_process_from_user(request):
    """Return the process corresponding to the number entered by the user."""
    menu_window.addstr(0, 0, request)
    refresh_menu()
    number = int(menu_window.getstr())
    return the_dispatcher.process_with_id(number)

def focus():
    """Get focus process number from the user
    and then hang around until the user has entered
    data to that process.
    """
    process = get_process_from_user("Enter the number of the input process:")
    process.panel.top() # the top panel has the cursor
    curses.panel.update_panels()
    curses.doupdate()
    input = process.panel.window().getstr()
    # only get here after the user has pressed return
    # put the data in the buffer of the process and wake it up
    # ...
    io_system.fill_buffer(process,input)
    return False

def top():
    """Move a runnable process to the top of the stack."""
    process = get_process_from_user("Enter the number of the process to move:")
    # ...
    the_dispatcher.to_top(process)
    return False

def kill():
    """Kill the process at the top of the stack."""
    process = get_process_from_user("Enter the number of the process to kill:")
    # ...
    the_dispatcher.process_kill(process)
    return False

def halt():
    """Halt the system for 5 seconds.
    This is so that can see the current state of the system
    without things changing.
    """
    the_dispatcher.pause_system()
    sleep(5)
    the_dispatcher.resume_system()
    return False

def pause():
    """Pause input for 5 seconds.
    This is so that when you watch the system when receiving
    input from a file you can allow the system to run for a time
    without new commands arriving.
    """
    sleep(5)

def wait():
    """Wait until all runnable processes have finished."""
    the_dispatcher.wait_until_finished()
    return True

def interactive():
    """Create an interactive process."""
    new_process = process.Process(io_system, the_dispatcher, process.Type.interactive)
    the_dispatcher.add_process(new_process)
    return True

def background():
    """Create a background process."""
    new_process = process.Process(io_system, the_dispatcher, process.Type.background)
    the_dispatcher.add_process(new_process)
    return True

def cancel():
    """Cancel the current menu level."""
    return True

def quit():
    # the_dispatcher.shut_down()
    return True

def main(stdscr):
    global menu_window, menu_panel, io_system, the_dispatcher

    curses.echo()
    panels = []
    menu_window = curses.newwin(2, (iosys.WINDOW_WIDTH + 2) * 2 + 3)
    menu_panel = curses.panel.new_panel(menu_window)
    menu_window.addstr(1, 0, "Stack of runnable processes")
    menu_window.addstr(1, iosys.WINDOW_WIDTH + 3, "Set of waiting processes")
    the_dispatcher = dispatcher.Dispatcher()
    io_system = iosys.IO_Sys(the_dispatcher, panels) # setup the windows
    the_dispatcher.set_io_sys(io_system)
    menu("(n)ew, (f)ocus, (t)op, (k)ill, (h)alt, (p)ause, (w)ait, (q)uit")

curses.wrapper(main)
print("the end")
