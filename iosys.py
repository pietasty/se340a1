# A1 for COMPSCI340/SOFTENG370 2015
# Prepared by Robert Sheehan
# Modified by Yubo Wu, ywu591, 6412428

# You are not allowed to use any sleep calls.

from process import State
import curses
import curses.panel

WINDOW_HEIGHT = 4
WINDOW_WIDTH = 40

# Only one of these is created and is sent to each process.
# The processes always print and get input via this.

class IO_Sys():
    """The IO subsystem."""

    def __init__(self, the_dispatcher, panels):
        """Construct an io system.
        the_dispatcher - the dispatcher
        panels - the curses panels for the program
        """
        self.the_dispatcher = the_dispatcher
        self.panels = panels
        self.process_buffers = dict()    # each process can have an input buffer
        self.runnable_window_boxes = []  # the boxes for the runnable process windows
        self.waiting_windows_boxes = []  # the boxes for waiting process windows
        y = 2
        for i in range(self.the_dispatcher.MAX_PROCESSES):
            self.runnable_window_boxes.append(Process_Window_Box(y, 0, self.panels))
            y += WINDOW_HEIGHT + 2
        y = 2
        for i in range(self.the_dispatcher.MAX_PROCESSES):
            self.waiting_windows_boxes.append(Process_Window_Box(y, WINDOW_WIDTH + 2 + 1, self.panels))
            y += WINDOW_HEIGHT + 2
        self.process_window_box = dict()        # the window box, just for the name
        self.refresh_screen()

    def allocate_window_to_process(self, process, tos):
        """Create a new process window for the process.

        All processes get created at the top of the runnable stack.
        process - the new process
        tos     - the current index of the top of the stack
        """
        window = curses.newwin(WINDOW_HEIGHT, WINDOW_WIDTH)
        window.scrollok(True)
        panel = curses.panel.new_panel(window)
        self.panels.append(panel)
        process.panel = panel
        self.move_process(process, tos)

    def remove_window_from_process(self, process):
        """Remove the process from this window."""
        self.process_window_box.pop(process).set_name("")
        panel = process.panel
        panel.window().erase()
        self.panels.remove(panel)
        self.refresh_screen()

    def refresh_screen(self):
        """Refresh the screen contents."""
        curses.panel.update_panels()
        curses.doupdate()

    def move_process(self, process, position):
        """Change the process' window position.
        process     - the process identifier
        position    - the position in the corresponding window list
        """
        if process.state == State.runnable:
            window_box = self.runnable_window_boxes[position]
        else: # must be waiting
            window_box = self.waiting_windows_boxes[position]
        old_window_box = self.process_window_box.pop(process, None)
        if old_window_box:
            old_window_box.set_name("")
        self.process_window_box[process] = window_box
        window_box.set_name(str(process.id))
        new_location = window_box.get_contents_location()
        panel = process.panel
        panel.move(*new_location) # move the process panel to the new location
        self.refresh_screen()

    def write(self, process, data):
        """Writes 'data' to the window associated with 'process'."""
        window = process.panel.window()
        window.addstr(data)
        self.refresh_screen()

    def fill_buffer(self, process, data):
        """Fill the process buffer with data."""

        process.lock.acquire()

        # Assign process the input data
        self.process_buffers[process] = data
        # Make the process runnable
        process.event.set()
        process.state = State.runnable
        # Stops the other processes in the stack
        for p in self.the_dispatcher.run_stack:
            p.event.clear()
        # Allows first one to run
        if len(self.the_dispatcher.run_stack) != 0:
            self.the_dispatcher.run_stack[-1].event.set()
        # Append process onto runnable stack and remove from waiting stack
        self.the_dispatcher.run_stack.append(process)
        self.the_dispatcher.wait_stack.remove(process)
        self.move_process(process,len(self.the_dispatcher.run_stack)-1)
        
        process.lock.release()

    def read(self, process):
        """Gets input from the window associated with 'process'."""
        # Change the state of the process to waiting
        process.state = State.waiting
        # Finds the first free slot in the waiting processes stack to place the process to
        locations = []
        for w_p in self.the_dispatcher.wait_stack: 
            locations.append(self.process_window_box[w_p].get_contents_location())
        location = 0
        for window in self.waiting_windows_boxes:
            if window.get_contents_location() not in locations:
                break
            else :
                location += 1
        # moves the process to the waiting stack visiually 
        self.move_process(process,location)
        # method remove from run_stack onto wait_stack
        self.the_dispatcher.proc_waiting(process)
        # waits for user input
        process.event.clear()
        process.event.wait()
        # default of -1 is given as the thread needs to be awaken before killed
        return self.process_buffers.pop(process,-1)

# =======================================================================================================================

class Process_Window_Box():
    """Holds the window border information for a process."""

    def __init__(self, y, x, panels):
        """Construct a process window."""
        self.y = y
        self.x = x
        self.box_around_window = curses.newwin(WINDOW_HEIGHT + 2, WINDOW_WIDTH + 2, y, x)
        panel = curses.panel.new_panel(self.box_around_window)
        panels.append(panel)
        self.set_name("")

    def set_name(self, name):
        """Set the process name."""
        self.box_around_window.box()
        self.box_around_window.addstr(0, 2, " Process: ")
        self.box_around_window.addstr(0, 12, name + " ")
        # self.box_around_window.refresh()

    def get_contents_location(self):
        """Return the (y, x) location of the contents of this window box."""
        return (self.y+1, self.x+1)
