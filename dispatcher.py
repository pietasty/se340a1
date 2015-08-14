# A1 for COMPSCI340/SOFTENG370 2015
# Prepared by Robert Sheehan
# Modified by Yubo Wu

# You are not allowed to use any sleep calls.

from threading import Lock, Event
from process import State

class Dispatcher():
    """The dispatcher."""

    MAX_PROCESSES = 8

    def __init__(self):
        """Construct the dispatcher."""
        self.run_stack = []
        self.wait_stack = []
        self.event = Event()
        self.event.set()
        self.lock = Lock()

    def set_io_sys(self, io_sys):
        """Set the io subsystem."""
        self.io_sys = io_sys

    def add_process(self, process):
        """Add and start the process."""

        #Lock
        self.lock.acquire()

        # Stops everything in the stack
        for p in self.run_stack:
            p.event.clear()
        # Starts the first process on the stack
        if len(self.run_stack) != 0:
            self.run_stack[-1].event.set()
        # Add new process on stack
        self.run_stack.append(process)
        # Start the process
        process.start()

        # Release lock
        self.lock.release()

    def dispatch_next_process(self):
        """Dispatch the process at the top of the stack."""
        # Starts the first two processes on the stack
        if len(self.run_stack) > 1:
            self.run_stack[-1].event.set()
            self.run_stack[-2].event.set()
        if len(self.run_stack) > 0:
            self.run_stack[-1].event.set()
    
    def to_top(self, process):
        """Move the process to the top of the stack."""

        #Lock
        process.lock.acquire()

        # remove the process from the stack
        removed_index = self.run_stack.index(process)
        removed_process = process
        self.run_stack.remove(process)
        # Move the process to a temp window (top of the runnable window)
        self.io_sys.move_process(process,7)
        # Check to see process in middle of the stack
        if len(self.run_stack) - removed_index > 0:
            # If was in middle, reshuffle the stack
            for x in range(removed_index,len(self.run_stack)):
                self.io_sys.move_process(self.run_stack[x],x)
        # Add the process back onto the stack
        self.run_stack.append(removed_process)
        self.io_sys.move_process(removed_process,len(self.run_stack)-1)
        
        # Cheap way out to get 2 processes running
        for r_p in self.run_stack:
            r_p.event.clear()
        self.dispatch_next_process()

        process.lock.release()


    def pause_system(self):
        """Pause the currently running process.
        As long as the dispatcher doesn't dispatch another process this
        effectively pauses the system.
        """

        self.lock.acquire()

        # Stop all the processes!!!
        for r_p in self.run_stack:
            r_p.event.clear()

    def resume_system(self):
        """Resume running the system."""
        # Tell the top 2 processes to start
        self.dispatch_next_process()

        self.lock.release()

    def wait_until_finished(self):
        """Hang around until all runnable processes are finished."""
        # Make the thread wait till all over threads are finished
        if self.run_stack != 0:
            self.event.clear()
            self.event.wait()


    def proc_finished(self, process):
        """Receive notification that "proc" has finished.
        Only called from running processes.
        """
        
        process.lock.acquire()

        # Remove the finished process from the stack
        removed_index = self.run_stack.index(process)
        self.run_stack.remove(process)
        self.dispatch_next_process()
        self.io_sys.remove_window_from_process(process)
        # If the process was the 2nd one from the top on the stack, reshuffle the stack
        if len(self.run_stack) - removed_index > 0:
            for x in range(removed_index,len(self.run_stack)):
                self.io_sys.move_process(self.run_stack[x],x)

       # This is a check what will awake the this thread, when the this thread is waiting for all the processes to finish
        if(len(self.run_stack)) == 0:
            self.event.set()

        process.lock.release()

    def proc_waiting(self, process):
        """Receive notification that process is waiting for input."""

        process.lock.acquire()

        # Removes the process from the runnable stack
        removed_index = self.run_stack.index(process)
        self.run_stack.remove(process)
        self.dispatch_next_process()
        # If the process was the 2nd one from the top on the stack, reshuffle the stack
        if len(self.run_stack) - removed_index > 0:
            for x in range(removed_index,len(self.run_stack)):
                self.io_sys.move_process(self.run_stack[x],x)
        process.event.clear()
        # Add process to the wait stack
        self.wait_stack.append(process)

        process.lock.release()

    def process_with_id(self, id):
        """Return the process with the id."""

        self.lock.acquire()

        # Finds the process in the run or the wait stack
        process = ''
        for p in self.run_stack:
            if p.id == id:
                process = p
        for p in self.wait_stack:
            if p.id == id:
                process = p

        self.lock.release()

        return process

    def process_kill(self, process):
        '''Gets called when a process is killed'''

        process.lock.acquire()

        # Check if process is a runnable one or waiting one
        if process.state == State.runnable:
            # Remove from runnable stack, and reshuffle run stack if process was in middle of the stack
            removed_index = self.run_stack.index(process)
            self.run_stack.remove(process)
            self.dispatch_next_process()
            self.io_sys.remove_window_from_process(process)
            if len(self.run_stack) - removed_index > 0:
                for x in range(removed_index,len(self.run_stack)):
                    self.io_sys.move_process(self.run_stack[x],x)
        else:
            # Remove from the wait stack, no reshuffling needs to be done
            self.wait_stack.remove(process)
            self.io_sys.remove_window_from_process(process)

        process.lock.release()

        # Kill the process
        process.event.set()
        process.state = State.killed
