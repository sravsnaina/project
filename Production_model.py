from PySide6.QtCore import QObject, Signal, Property, Slot        # Qt/QML integration primitives
from datetime import datetime                                     # log entry date/time stamps
import json                                                         # counts.json read/write
import os                                                            # check whether counts.json exists

from paths import app_dir                                            # resolves app directory (dev vs packaged)


class ProductionModel(QObject):                                      # holds per-part counts + full result log

    dataChanged = Signal()                                            # emitted whenever counts/logs change

    def __init__(self):
        super().__init__()                                            # initialize QObject (needed for Signals/Slots)

        self.fileName = str(app_dir() / "counts.json")                 # persisted counts/logs file, next to the app

        self.logs = []                                                  # full history of individual results

        self.parts = {
            "1": {"ok": 0, "ng": 0, "total": 0},                         # running counts for part 1
            "2": {"ok": 0, "ng": 0, "total": 0},                         # running counts for part 2
            "3": {"ok": 0, "ng": 0, "total": 0},                         # running counts for part 3
            "4": {"ok": 0, "ng": 0, "total": 0}                          # running counts for part 4
        }

        # Per-part baseline captured by the RESET button on each Part
        # page. Subtracted only from the "since reset" getters below -
        # the raw counts (and the report) are never affected by it.
        self.baselines = {
            "1": {"ok": 0, "ng": 0, "total": 0},                         # baseline snapshot for part 1
            "2": {"ok": 0, "ng": 0, "total": 0},                         # baseline snapshot for part 2
            "3": {"ok": 0, "ng": 0, "total": 0},                         # baseline snapshot for part 3
            "4": {"ok": 0, "ng": 0, "total": 0}                          # baseline snapshot for part 4
        }

        self.loadData()                                                  # populate parts/baselines/logs from disk

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------

    def loadData(self):

        if not os.path.exists(self.fileName):                            # first run - no counts.json yet
            print("counts.json not found. Creating new file.")
            self.saveData()                                                # write out the current (empty) defaults
            return

        try:
            with open(self.fileName, "r") as file:
                data = json.load(file)                                     # parse the persisted state

            # Load part counts
            if "parts" in data:                                            # older files may lack this key

                for part in self.parts:                                     # only trust the 4 known part keys

                    if part in data["parts"]:                                # skip parts missing from the file
                        self.parts[part]["ok"] = data["parts"][part].get("ok", 0)      # OK count, default 0
                        self.parts[part]["ng"] = data["parts"][part].get("ng", 0)      # NG count, default 0
                        self.parts[part]["total"] = data["parts"][part].get("total", 0)  # total count, default 0

            # Load per-part baselines
            if "baselines" in data:                                          # older files may lack this key

                for part in self.baselines:                                   # only trust the 4 known part keys

                    if part in data["baselines"]:                              # skip parts missing from the file
                        self.baselines[part]["ok"] = data["baselines"][part].get("ok", 0)     # baseline OK
                        self.baselines[part]["ng"] = data["baselines"][part].get("ng", 0)     # baseline NG
                        self.baselines[part]["total"] = data["baselines"][part].get("total", 0)  # baseline total

            # Load logs
            self.logs = data.get("logs", [])                                  # full result history, default empty

            print("Production data loaded successfully.")
            print(self.parts)

        except (json.JSONDecodeError, OSError) as error:                      # malformed JSON or unreadable file

            print("Error loading counts.json:", error)

    # --------------------------------------------------
    # SAVE DATA
    # --------------------------------------------------

    def saveData(self):

        data = {
            "parts": self.parts,                                              # current per-part counts
            "baselines": self.baselines,                                       # current per-part reset baselines
            "logs": self.logs                                                  # full result history
        }

        try:

            with open(self.fileName, "w") as file:
                json.dump(data, file, indent=4)                                 # pretty-printed for easy inspection

            print("Production data saved.")

        except OSError as error:                                                # e.g. disk full, permissions

            print("Error saving counts.json:", error)

    # --------------------------------------------------
    # ADD PRODUCTION RESULT
    # --------------------------------------------------

    @Slot(str, str)
    def addLog(self, part, status):

        part = str(part)                                                        # normalize to the dict key type
        status = status.upper()                                                  # normalize case (ok/Ok/OK -> OK)

        # Validate part
        if part not in self.parts:                                              # unknown part number

            print("Invalid part:", part)
            return

        # Validate result
        if status not in ("OK", "NG"):                                          # unrecognized status string

            print("Invalid status:", status)
            return

        now = datetime.now()                                                     # timestamp this result

        # Create log
        log = {
            "part": part,                                                        # which part this result is for
            "status": status,                                                     # OK or NG
            "date": now.strftime("%d-%m-%Y"),                                     # date the result was recorded
            "time": now.strftime("%H:%M:%S")                                      # time the result was recorded
        }

        self.logs.append(log)                                                     # append to the full history

        # Update counters
        if status == "OK":                                                        # good part

            self.parts[part]["ok"] += 1                                            # bump this part's OK count

        elif status == "NG":                                                      # bad part

            self.parts[part]["ng"] += 1                                            # bump this part's NG count

        self.parts[part]["total"] += 1                                            # bump this part's total count

        # Save immediately
        self.saveData()                                                            # persist to counts.json right away

        # Notify QML
        self.dataChanged.emit()                                                    # refresh bound UI properties

        print(
            f"Part {part} -> {status} | "
            f"OK: {self.parts[part]['ok']} | "
            f"NG: {self.parts[part]['ng']} | "
            f"Total: {self.parts[part]['total']}"
        )

    # --------------------------------------------------
    # GET PART OK
    # --------------------------------------------------

    @Slot(int, result=int)
    def getOK(self, part):

        part = str(part)                                                          # normalize to the dict key type

        if part not in self.parts:                                                # unknown part number
            return 0

        return self.parts[part]["ok"]                                             # this part's OK count

    # --------------------------------------------------
    # GET PART NG
    # --------------------------------------------------

    @Slot(int, result=int)
    def getNG(self, part):

        part = str(part)                                                          # normalize to the dict key type

        if part not in self.parts:                                                # unknown part number
            return 0

        return self.parts[part]["ng"]                                             # this part's NG count

    # --------------------------------------------------
    # GET PART TOTAL
    # --------------------------------------------------

    @Slot(int, result=int)
    def getTotal(self, part):

        part = str(part)                                                          # normalize to the dict key type

        if part not in self.parts:                                                # unknown part number
            return 0

        return self.parts[part]["total"]                                          # this part's total count

    # --------------------------------------------------
    # GET PART COUNTS SINCE LAST PART-LEVEL RESET
    # --------------------------------------------------

    @Slot(int, result=int)
    def getOKSinceReset(self, part):

        part = str(part)                                                          # normalize to the dict key type

        if part not in self.parts:                                                # unknown part number
            return 0

        return self.parts[part]["ok"] - self.baselines[part]["ok"]                # count accumulated since last reset

    @Slot(int, result=int)
    def getNGSinceReset(self, part):

        part = str(part)                                                          # normalize to the dict key type

        if part not in self.parts:                                                # unknown part number
            return 0

        return self.parts[part]["ng"] - self.baselines[part]["ng"]                # count accumulated since last reset

    @Slot(int, result=int)
    def getTotalSinceReset(self, part):

        part = str(part)                                                          # normalize to the dict key type

        if part not in self.parts:                                                # unknown part number
            return 0

        return self.parts[part]["total"] - self.baselines[part]["total"]          # count accumulated since last reset

    # --------------------------------------------------
    # RESET A SINGLE PART'S DISPLAYED COUNTER
    # --------------------------------------------------

    @Slot(int)
    def resetPart(self, part):

        part = str(part)                                                           # normalize to the dict key type

        if part not in self.parts:                                                 # unknown part number
            return

        self.baselines[part] = {
            "ok": self.parts[part]["ok"],                                           # snapshot current OK count
            "ng": self.parts[part]["ng"],                                           # snapshot current NG count
            "total": self.parts[part]["total"]                                      # snapshot current total count
        }

        self.saveData()                                                             # persist the new baseline

        self.dataChanged.emit()                                                     # refresh bound UI properties

        print(f"Part {part} counter reset (baseline captured).")

    # --------------------------------------------------
    # FILTER BY DATE
    # --------------------------------------------------

    @Slot(str, str)
    def filterDate(self, fromDate, toDate):

        # Reset counters
        for part in self.parts:                                                     # zero every part before recount

            self.parts[part]["ok"] = 0
            self.parts[part]["ng"] = 0
            self.parts[part]["total"] = 0

        # Recalculate from logs
        for log in self.logs:                                                       # replay full history

            logDate = log["date"]                                                    # this entry's date

            if fromDate <= logDate <= toDate:                                        # entry falls within the range

                part = log["part"]                                                    # part this entry belongs to
                status = log["status"]                                                # OK/NG of this entry

                if part not in self.parts:                                            # ignore unknown part numbers
                    continue

                if status == "OK":                                                    # good part

                    self.parts[part]["ok"] += 1                                        # bump filtered OK count

                elif status == "NG":                                                  # bad part

                    self.parts[part]["ng"] += 1                                        # bump filtered NG count

                self.parts[part]["total"] += 1                                         # bump filtered total count

        self.dataChanged.emit()                                                        # refresh bound UI properties

    # --------------------------------------------------
    # RESET ALL DATA
    # --------------------------------------------------

    @Slot()
    def resetData(self):

        for part in self.parts:                                                        # wipe every part's counts

            self.parts[part]["ok"] = 0
            self.parts[part]["ng"] = 0
            self.parts[part]["total"] = 0

            self.baselines[part]["ok"] = 0                                              # wipe baseline too
            self.baselines[part]["ng"] = 0
            self.baselines[part]["total"] = 0

        self.logs = []                                                                   # wipe full result history

        self.saveData()                                                                  # persist the cleared state

        self.dataChanged.emit()                                                          # refresh bound UI properties

        print("Production data reset.")

    # --------------------------------------------------
    # OVERALL OK
    # --------------------------------------------------

    def getTotalOK(self):

        total = 0                                                                         # running sum across parts

        for part in self.parts:

            total += self.parts[part]["ok"]                                               # add this part's OK count

        return total                                                                       # combined OK count

    # --------------------------------------------------
    # OVERALL NG
    # --------------------------------------------------

    def getTotalNG(self):

        total = 0                                                                          # running sum across parts

        for part in self.parts:

            total += self.parts[part]["ng"]                                                # add this part's NG count

        return total                                                                        # combined NG count

    # --------------------------------------------------
    # OVERALL TOTAL
    # --------------------------------------------------

    def getTotalParts(self):

        total = 0                                                                           # running sum across parts

        for part in self.parts:

            total += self.parts[part]["total"]                                              # add this part's total count

        return total                                                                         # combined total count

    # --------------------------------------------------
    # QML PROPERTIES
    # --------------------------------------------------

    totalOK = Property(
        int,
        getTotalOK,                                                                          # getter defined above
        notify=dataChanged                                                                    # refresh signal
    )

    totalNG = Property(
        int,
        getTotalNG,                                                                           # getter defined above
        notify=dataChanged                                                                     # refresh signal
    )

    totalParts = Property(
        int,
        getTotalParts,                                                                        # getter defined above
        notify=dataChanged                                                                      # refresh signal
    )
