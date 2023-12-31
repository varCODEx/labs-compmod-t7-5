import numpy as np
import numpy.random as npr


class Object:
    def __init__(self, event_manager, name=None):
        self.event_manager: EventManager = event_manager
        self.input = None
        self.output = None
        self.blocked: bool = False
        self.name = name

    def __repr__(self):
        if self.name is not None:
            return f"{self.name}"
        else:
            return f"{self.__class__.__name__}"


class Event:
    def __init__(self, time, action, name=None):
        self.time = time
        self.action = action
        self.name = name

    def __repr__(self):
        if self.name is not None:
            return f"Event(time={self.time:.2f}, action={self.name})"
        else:
            return f"Event(time={self.time:.2f}, action={self.action})"


class EventManager:
    def __init__(self):
        self.events = []
        self.current_time = 0
        self.log = []

    def add_event(self, time_offset, event, name=None):
        self.events.append(Event(self.current_time + time_offset, event, name=name))

    def get_next_event(self):
        next_event = min(self.events, key=lambda e: e.time)
        self.events.remove(next_event)
        self.current_time = next_event.time
        return next_event

    def record_rejection(self):
        self.log.append({'time': self.current_time, 'type': 'rejection'})

    def record_customer_exit(self):
        self.log.append({'time': self.current_time, 'type': 'customer_exit'})


class Exit(Object):
    def __init__(self, event_manager: EventManager):
        super().__init__(event_manager)

    def accept(self):
        self.event_manager.record_customer_exit()


class Line(Object):
    def __init__(self, event_manager: EventManager, name=None):
        super().__init__(event_manager, name=name)
        self.input = None
        self.output = None

    def block(self):
        self.blocked = True

    def unblock(self):
        self.blocked = False
        self.input.output_unblocked_reaction()

    def output_unblocked_reaction(self):
        self.unblock()

    def output_blocked_reaction(self):
        self.block()

    def move(self):
        if not self.blocked:
            self.event_manager.add_event(0, self.output.accept)
        else:
            self.event_manager.record_rejection()


class K(Object):
    def __init__(self, event_manager, mu: float = None, t: float = None, name=None):
        super().__init__(event_manager, name=name)
        self.mu: float = mu
        self.t: float = t
        self.input: Line
        self.output: Line
        self.holding: bool = False

    def accept(self):  # accept from previous line
        if self.mu is not None:
            time_offset = npr.exponential(1 / self.mu)
        else:
            time_offset = self.t
        self.event_manager.add_event(time_offset, self.finish, name=f"server {self.name} finished")
        self.blocked = True
        self.input.output_blocked_reaction()

    def finish(self):  # finish processing
        if not self.output.blocked:
            self.release()
        else:
            self.holding = True

    def release(self):  # release to next line
        self.output.move()
        self.blocked = False
        self.input.output_unblocked_reaction()

    def output_unblocked_reaction(self):
        if self.holding:
            self.holding = False
            self.release()


class Q(Object):
    def __init__(self, event_manager, capacity: int, name=None):
        super().__init__(event_manager, name=name)
        self.capacity: int = capacity
        self.q = []
        self.input: Line
        self.output: K
        self.blocked = False  # full

    def accept(self):
        if self.output.blocked:
            if self.blocked:
                self.event_manager.record_rejection()
            else:
                self.event_manager.add_event(0, self.store, name=f"{self.name} +1")
                self.event_manager.log.append({'time': self.event_manager.current_time, 'type': 'queue add'})
        else:
            self.event_manager.add_event(0, self.output.accept)

    def store(self):
        self.q.append(self.event_manager.current_time)
        self.event_manager.log.append({'time': self.event_manager.current_time, 'type': 'queue length',
                                       'length': len(self.q)})
        if len(self.q) >= self.capacity:
            self.blocked = True

    def release(self):
        if len(self.q) > 0:
            serve_time = self.q.pop(0)
            self.event_manager.log.append({'time': self.event_manager.current_time, 'type': 'queue remove',
                                           'wait_time': self.event_manager.current_time - serve_time})
            self.event_manager.log.append({'time': self.event_manager.current_time, 'type': 'queue length',
                                           'length': len(self.q)})
            if len(self.q) < self.capacity:
                self.blocked = False
                self.event_manager.add_event(0, self.unblock_action, name=f"{self.name} -1")
            self.output.accept()

    def output_unblocked_reaction(self):
        self.release()

    def unblock_action(self):
        self.input.unblock()

    def output_blocked_reaction(self):
        pass
