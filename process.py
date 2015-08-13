# A1 for COMPSCI340/SOFTENG370 2015
# Prepared by Robert Sheehan
# Modified by Yubo Wu

# You are not allowed to use any extra sleep calls.

import threading
import _thread
from random import randint
from time import sleep
from enum import Enum

Type = Enum("Type", "background interactive")
State = Enum("State", "runnable waiting killed")

class Process(threading.Thread):
    """A process."""

    next_id = 1

    def __init__(self, iosys, dispatcher, type):
        """Construct a process.
        iosys - the io subsystem so the process can do IO
        dispatcher - so that the process can notify the dispatcher when it has finished
        """
        threading.Thread.__init__(self)
        self.id = Process.next_id
        Process.next_id += 1
        self.iosys = iosys
        self.dispatcher = dispatcher
        self.type = type
        self.panel = None
        self.daemon = True
        # You will need a process state variable - self.state
        # which should only be modified by the dispatcher and io system.
        # the state can be used to determine which list - runnable or waiting the process
        # appears in.
        self.state = State.runnable
        self.event = threading.Event()
        self.event.set()

    def run(self):
        """Start the process running."""
        # Give the process a window
        self.iosys.allocate_window_to_process(self,len(self.dispatcher.run_stack)-1)
        if self.type == Type.background:
            self.run_background()
        elif self.type == Type.interactive:
            self.run_interactive()
        self.dispatcher.proc_finished(self)

    def run_interactive(self):
        """Run as an interactive process."""
        # Something like the following but you will have to think about
        # pausing and resuming the process.
        
        loops = self.ask_user()
        while loops > 0:
            for i in range(loops):
                self.main_process_body()
            self.iosys.write(self, "\n")
            loops = self.ask_user()

    def run_background(self):
        """Run as a background process."""
        loops = randint(10, 160)
        for i in range(loops):
            self.main_process_body()

    def ask_user(self):
        """Ask the user for number of loops."""
        self.iosys.write(self, "How many loops? ")
        input = self.iosys.read(self)
        if self.state == State.killed:
            _thread.exit()
        return int(input)

    def main_process_body(self):
        # Something like the following but you will have to think about
        # pausing and resuming the process.

        # check to see if supposed to terminate
        if self.state == State.killed:
            _thread.exit()
        self.event.wait()
        self.iosys.write(self, "*")
        sleep(0.1)

