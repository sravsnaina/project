from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Property, Signal, Slot  # Qt list-model base classes


class LogModel(QAbstractListModel):                            # QML-facing list model of recent OK/NG results

    TimeRole = Qt.UserRole + 1                                  # custom role id for the "time" field
    EventRole = Qt.UserRole + 2                                 # custom role id for the "event" field
    StatusRole = Qt.UserRole + 3                                # custom role id for the "status" field

    latestChanged = Signal()                                    # emitted whenever latestStatus/latestTime change

    def __init__(self):
        super().__init__()                                      # initialize the QAbstractListModel base
        self.logs = []                                          # in-memory list of log-entry dicts, newest first

    def rowCount(self, parent=QModelIndex()):
        return len(self.logs)                                   # number of rows QML should render

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():                                 # guard against an out-of-range/invalid index
            return None                                          # nothing to return

        log = self.logs[index.row()]                             # the entry dict for this row

        if role == self.TimeRole:                                 # QML asked for the time role
            return log["time"]                                    # return that entry's timestamp

        if role == self.EventRole:                                 # QML asked for the event role
            return log["event"]                                    # return that entry's event/part label

        if role == self.StatusRole:                                # QML asked for the status role
            return log["status"]                                   # return that entry's OK/NG status

        return None                                                 # unrecognized role

    def roleNames(self):
        return {
            self.TimeRole: b"time",                                 # exposes log.time to QML delegates
            self.EventRole: b"event",                               # exposes log.event to QML delegates
            self.StatusRole: b"status"                              # exposes log.status to QML delegates
        }

    @Property(str, notify=latestChanged)
    def latestStatus(self):

        if not self.logs:                                          # no entries yet
            return "-"                                              # placeholder for the UI

        return self.logs[0]["status"]                               # status of the most recent entry

    @Property(str, notify=latestChanged)
    def latestTime(self):

        if not self.logs:                                           # no entries yet
            return "-"                                               # placeholder for the UI

        return self.logs[0]["time"]                                  # timestamp of the most recent entry

    def addLog(self, time, event, status):

        # Newest entry first
        self.beginInsertRows(
            QModelIndex(),                                          # no parent (flat list)
            0,                                                        # inserting at row 0
            0                                                         # ...through row 0 (single row)
        )

        self.logs.insert(0, {
            "time": time,                                             # new entry's timestamp
            "event": event,                                            # new entry's event/part label
            "status": status                                           # new entry's OK/NG status
        })

        self.endInsertRows()                                          # tell views the insert is complete

        # Keep only latest 5
        if len(self.logs) > 5:                                        # trim once the list grows past 5 entries

            self.beginRemoveRows(
                QModelIndex(),                                         # no parent (flat list)
                5,                                                      # first row being removed
                len(self.logs) - 1                                      # last row being removed
            )

            del self.logs[5:]                                          # drop everything past the newest 5

            self.endRemoveRows()                                       # tell views the removal is complete

        self.latestChanged.emit()                                      # notify bound latestStatus/latestTime

    @Slot()
    def clear(self):

        if not self.logs:                                              # nothing to clear
            return                                                      # no-op

        self.beginRemoveRows(
            QModelIndex(),                                              # no parent (flat list)
            0,                                                           # first row being removed
            len(self.logs) - 1                                          # last row being removed
        )

        self.logs = []                                                  # drop all entries

        self.endRemoveRows()                                            # tell views the removal is complete

        self.latestChanged.emit()                                       # notify bound latestStatus/latestTime
