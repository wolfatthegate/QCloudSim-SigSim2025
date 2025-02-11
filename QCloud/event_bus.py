class EventBus:
    """
    A lightweight event bus for managing event-based communication.
    """
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        """
        Subscribe to a specific event type with a callback.

        Parameters:
        - event_type (str): The type of event to subscribe to.
        - callback (callable): A function to be called when the event is published.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        """
        Publish an event to all subscribers.

        Parameters:
        - event_type (str): The type of event to publish.
        - data (dict): Event-related data to pass to subscribers.
        """
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)
