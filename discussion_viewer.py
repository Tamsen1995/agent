import os
import time
import curses
from datetime import datetime
from networked_agent_manager import NetworkedAgentManager
from models import Memory, Agent
from sqlalchemy import desc

class DiscussionViewer:
    def __init__(self, agent_manager):
        self.agent_manager = agent_manager
        self.last_message_id = 0
        self.messages = []
        self.running = True

    def get_new_messages(self, discussion_id):
        with self.agent_manager.Session() as session:
            new_messages = (
                session.query(Memory, Agent)
                .join(Agent)
                .filter(Memory.type == 'discussion')
                .filter(Memory.id > self.last_message_id)
                .filter(Memory.agent_id == Agent.id)  # Ensure we only get messages from the speaking agent
                .order_by(Memory.timestamp.asc())
                .all()
            )

            if new_messages:
                self.last_message_id = new_messages[-1][0].id

            return new_messages

    def format_message(self, memory, agent):
        timestamp = memory.timestamp.strftime("%H:%M:%S")
        # Truncate the message if it's too long
        content = memory.content[:200] + "..." if len(memory.content) > 200 else memory.content
        return f"[{timestamp}] {agent.name}: {content}"

    def run_viewer(self, stdscr):
        # Set up colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        # Hide cursor
        curses.curs_set(0)

        # Initialize windows
        height, width = stdscr.getmaxyx()
        header_win = curses.newwin(3, width, 0, 0)
        messages_win = curses.newwin(height - 6, width, 3, 0)
        status_win = curses.newwin(3, width, height - 3, 0)

        # Enable scrolling for messages window
        messages_win.scrollok(True)

        while self.running:
            try:
                # Clear windows
                header_win.clear()
                status_win.clear()

                # Draw header
                header_win.attron(curses.color_pair(1))
                header_win.box()
                header_win.addstr(1, 2, "Live Discussion Viewer")
                header_win.addstr(1, width - 20, f"Press 'q' to quit")
                header_win.attroff(curses.color_pair(1))
                header_win.refresh()

                # Get new messages
                new_messages = self.get_new_messages("discussion_1")
                for memory, agent in new_messages:
                    self.messages.append((memory, agent))

                # Display messages
                messages_win.clear()
                max_messages = height - 8  # Reserve space for header and status
                start_idx = max(0, len(self.messages) - max_messages)
                
                for i, (memory, agent) in enumerate(self.messages[start_idx:], start=1):
                    formatted_msg = self.format_message(memory, agent)
                    try:
                        messages_win.attron(curses.color_pair(2))
                        messages_win.addstr(i, 2, formatted_msg[:width-4])
                        messages_win.attroff(curses.color_pair(2))
                    except curses.error:
                        pass  # Ignore if message doesn't fit

                messages_win.refresh()

                # Draw status bar
                status_win.attron(curses.color_pair(3))
                status_win.box()
                status_win.addstr(1, 2, f"Messages: {len(self.messages)}")
                status_win.addstr(1, width - 25, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                status_win.attroff(curses.color_pair(3))
                status_win.refresh()

                # Check for 'q' key press
                stdscr.nodelay(1)
                key = stdscr.getch()
                if key == ord('q'):
                    self.running = False
                    break

                time.sleep(1)  # Update every second

            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                # Log error and continue
                with open("viewer_error.log", "a") as f:
                    f.write(f"{datetime.now()}: {str(e)}\n")
                time.sleep(1)

def view_live_discussion(agent_manager):
    viewer = DiscussionViewer(agent_manager)
    curses.wrapper(viewer.run_viewer)
