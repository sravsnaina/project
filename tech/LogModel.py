from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Property, Signal


class LogModel(QAbstractListModel):

    TimeRole = Qt.UserRole + 1
    EventRole = Qt.UserRole + 2
    StatusRole = Qt.UserRole + 3

    latestChanged = Signal()

    def __init__(self):
        super().__init__()
        self.logs = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.logs)

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return None

        log = self.logs[index.row()]

        if role == self.TimeRole:
            return log["time"]

        if role == self.EventRole:
            return log["event"]

        if role == self.StatusRole:
            return log["status"]

        return None

    def roleNames(self):
        return {
            self.TimeRole: b"time",
            self.EventRole: b"event",
            self.StatusRole: b"status"
        }

    @Property(str, notify=latestChanged)
    def latestStatus(self):

        if not self.logs:
            return "-"

        return self.logs[-1]["status"]

    @Property(str, notify=latestChanged)
    def latestTime(self):

        if not self.logs:
            return "-"

        return self.logs[-1]["time"]

    def addLog(self, time, event, status):

        # Add new result
        self.beginInsertRows(
            QModelIndex(),
            self.rowCount(),
            self.rowCount()
        )

        self.logs.append({
            "time": time,
            "event": event,
            "status": status
        })

        self.endInsertRows()

        # Keep only latest 5
        if len(self.logs) > 5:

            self.beginRemoveRows(
                QModelIndex(),
                0,
                len(self.logs) - 6
            )

            del self.logs[0:len(self.logs) - 5]

            self.endRemoveRows()

        self.latestChanged.emit()