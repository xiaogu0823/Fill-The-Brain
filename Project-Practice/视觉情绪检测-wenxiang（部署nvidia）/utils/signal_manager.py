class SignalManager:
    """Track signal-slot bindings so windows can disconnect cleanly."""

    def __init__(self):
        self._connections = []

    def connect(self, signal, slot):
        try:
            signal.disconnect(slot)
        except Exception:
            pass
        signal.connect(slot)
        self._connections.append((signal, slot))

    def disconnect_all(self):
        while self._connections:
            signal, slot = self._connections.pop()
            try:
                signal.disconnect(slot)
            except Exception:
                pass
