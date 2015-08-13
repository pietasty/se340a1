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

    def set_io_sys(self, io_sys):
        """Set the io subsystem."""
        self.io_sys = io_sys

    def add_process(self, process):
        """Add and start the process."""
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

    def dispatch_next_process(self):
        """Dispatch the process at the top of the stack."""
        # Starts the first two processes on the stack
        if len(self.run_stack) > 1:
            self.run_stack[-1].event.set()
            self.run_stack[-2].event.set()
        if len(self.run_stack) > 0:
            self.run_stack[-1].event.set()
    
    # I am disappointed with this function
    def to_top(self, process):
        """Move the process to the top of the stack."""
        # remove the process from the stack
        removed_index = self.run_stack.index(process)
        removed_process = process
        self.run_stack.remove(process)
        # Move the process to a temp window (top of the wait window)
        # I feel bad doing this but this is why I did it
        # If I move the this process to the top of the runnable stack, and there are 8 process running, it will either override the the 8th process window or the program will crash as there is no room on the runnable stack to place this. We have to move this process to a temp window because if we don't, the text "How many loops" can disappear for a interactive process.
        # But by putting the process on the top of the wait stack, an error will never occur as the max process is 8, so if we have 8 interactive processes waiting, we will be unable to move a runnable process to the top and also we have to start one of the interactive process, reducing the wait stack to 7, allowing us to use that position for the temp window.
        removed_process.state = State.waiting
        self.io_sys.move_process(process,7)
        # Check to see process in middle of the stack
        if len(self.run_stack) - removed_index > 0:
            # If was in middle, reshuffle the stack
            for x in range(removed_index,len(self.run_stack)):
                self.io_sys.move_process(self.run_stack[x],x)
        # Add the process back onto the stack
        self.run_stack.append(removed_process)
        removed_process.state = State.runnable
        self.io_sys.move_process(removed_process,len(self.run_stack)-1)
        
        # Cheap way out to get 2 processes running
        for r_p in self.run_stack:
            r_p.event.clear()
        self.dispatch_next_process()


    def pause_system(self):
        """Pause the currently running process.
        As long as the dispatcher doesn't dispatch another process this
        effectively pauses the system.
        """
        # Stop all the processes!!!
        for r_p in self.run_stack:
            r_p.event.clear()

    def resume_system(self):
        """Resume running the system."""
        # Tell the top 2 processes to start
        self.dispatch_next_process()

    def wait_until_finished(self):
        """Hang around until all runnable processes are finished."""
        # Make the thread wait till all over threads are finished
        self.event.clear()
        self.event.wait()


    def proc_finished(self, process):
        """Receive notification that "proc" has finished.
        Only called from running processes.
        """
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

    def proc_waiting(self, process):
        """Receive notification that process is waiting for input."""
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

    def process_with_id(self, id):
        """Return the process with the id."""
        # Finds the process in the run or the wait stack
        process = ''
        for p in self.run_stack:
            if p.id == id:
                process = p
        for p in self.wait_stack:
            if p.id == id:
                process = p
        return process

    def process_kill(self, process):
        '''Gets called when a process is killed'''
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
        # Kill the process
        process.event.set()
        process.state = State.killed
