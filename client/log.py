'''
Gestion des logs
'''
import logging
import logging.handlers
import queue

# Define a custom QueueListener that intercepts logs before passing them to the handler.
class InterceptingQueueListener(logging.handlers.QueueListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.widget = kwargs['widget']

    def handle(self, record):
        # Modify the log record if needed.
        #record.msg = f"[Intercepted at Listener] {record.msg}"
        # Now pass the modified record to the handlers.
        #super().handle(record)
        self.widget.append_html_text(record.msg + "<br>")
        if self.widget.scroll_bar:
            self.widget.scroll_bar.scroll_position = self.widget.scroll_bar.scrollable_height
            self.widget.scroll_bar.has_moved_recently = True
            #self.widget.scroll_bar.update_position()
            #self.widget.scroll_bar.redraw_scrollbar()
            self.widget.scroll_bar.set_scroll_from_start_percentage(1.0)


class Logger:
    def __init__(self, widget):
        # Create a queue to hold log records.
        log_queue = queue.Queue()

        # Configure a handler that processes logs received from the queue.
        listener_handler = logging.StreamHandler()
        #formatter = logging.Formatter('MYLOGGER: %(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        listener_handler.setFormatter(formatter)

        # Set up the QueueListener.
        #self.listener = logging.handlers.QueueListener(log_queue, listener_handler)
        self.listener = InterceptingQueueListener(log_queue, listener_handler, widget=widget)
        self.listener.start()  # Start the listener

        # Configure the root logger to use QueueHandler, sending all logs to the queue.
        root_logger = logging.getLogger()
        queue_handler = logging.handlers.QueueHandler(log_queue)
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(queue_handler)

    def __del__(self):
        self.listener.stop()

# EOF
