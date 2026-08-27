import QtQuick
import QtQuick.Controls
import QtQuick.Layouts 1.0
import QtQuick.Window
Rectangle {
    // Same 1280x720 design baseline as Main.qml, driven off the actual
    // window size so this embedded panel scales along with its page.
    readonly property real scaleFactor: Math.min(Window.width / 1280, Window.height / 720)

    radius: 8
    color: "white"
    border.color: "#C0C0C0"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10 * scaleFactor
        spacing: 10 * scaleFactor

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "LOG / EVENTS"
                font.pixelSize: 20 * scaleFactor
                font.bold: true
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.preferredWidth: 110 * scaleFactor
                Layout.preferredHeight: 26 * scaleFactor
                radius: 6
                color: !backend.connected ? "#C0392B" : (backend.schemeReady ? "#27AE60" : "#E67E22")

                Label {
                    anchors.centerIn: parent
                    text: !backend.connected ? "NOT CONNECTED" : (backend.schemeReady ? "READY" : "SWITCHING...")
                    color: "white"
                    font.bold: true
                    font.pixelSize: 12 * scaleFactor
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42 * scaleFactor
            color: "#F5F5F5"
            border.color: "#D0D0D0"
            border.width: 1 * scaleFactor
            radius: 8

            RowLayout {
                anchors.fill: parent
                anchors.margins: 0 * scaleFactor
                spacing: 0 * scaleFactor

                Label {
                    text: "TIME"
                    Layout.preferredWidth: 120 * scaleFactor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.bold: true
                    color: "#333333"
                }

                Label {
                    text: "EVENT"
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.bold: true
                    color: "#333333"
                }

                Label {
                    text: "STATUS"
                    Layout.preferredWidth: 100 * scaleFactor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.bold: true
                    color: "#333333"
                }
            }
        }
        // Log List
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            clip: true
            model: logModel
            spacing: 0 * scaleFactor

            ScrollBar.vertical: ScrollBar {}

            delegate: Rectangle {
                width: ListView.view.width
                height: 44 * scaleFactor

                color: index % 2 ? "#FAFAFA" : "white"
                border.color: "#E5E5E5"
                border.width: 0.5 * scaleFactor

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 0 * scaleFactor
                    spacing: 0 * scaleFactor

                    Label {
                        text: time
                        Layout.preferredWidth: 120 * scaleFactor
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        color: "#222222"
                    }

                    Label {
                        text: event
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        color: "#222222"
                    }

                    Label {
                        text: status
                        Layout.preferredWidth: 100 * scaleFactor
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.bold: true
                        color: status === "OK" ? "green" : "red"
                    }
                }
            }
        }
    }
}