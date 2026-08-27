import QtQuick                                                          // core QML types
import QtQuick.Controls                                                  // Page, Button, Label
import QtQuick.Layouts                                                    // RowLayout, ColumnLayout
import QtQuick.Window                                                      // Window.width/height for scaleFactor
import "contents"                                                            // local Logs.qml component

Page {                                                                        // Part 4 inspection screen

    // Same 1280x720 design baseline as Main.qml, driven off the actual
    // window size so this page scales to whatever screen it's shown on.
    readonly property real scaleFactor: Math.min(Window.width / 1280, Window.height / 720)  // uniform UI scale

    property string currentDate: Qt.formatDate(new Date(), "dd-MM-yyyy")       // today's date, refreshed by the Timer
    property string currentTime: Qt.formatTime(new Date(), "hh:mm:ss")          // clock time, refreshed by the Timer

    property int okCount: 0                                                      // part 4 OK count since last reset
    property int ngCount: 0                                                       // part 4 NG count since last reset
    property int totalCount: 0                                                     // part 4 total count since last reset

    function refreshCounts() {
        okCount = productionModel.getOKSinceReset(4)                               // pull latest OK count from the model
        ngCount = productionModel.getNGSinceReset(4)                                // pull latest NG count from the model
        totalCount = productionModel.getTotalSinceReset(4)                           // pull latest total count from the model
    }

    Component.onCompleted: {
        backend.selectScheme(4)                                                       // switch the camera to part 4 on entry
        refreshCounts()                                                                // populate counters immediately
    }

    Connections {
        target: productionModel                                                        // listen for count changes from Python

        function onDataChanged() {
            refreshCounts()                                                             // re-pull counters whenever data changes
        }
    }
    Rectangle {
        anchors.fill: parent                                                            // fill the whole page
        color: "#D3D3D3"                                                                  // grey page background

        RowLayout{
            id: top_layer                                                                 // referenced by several anchors below
            spacing: 10 * scaleFactor                                                       // scaled gap

            Image {
                source: "images/Ensteinlogo.png"                                             // company logo
                Layout.preferredWidth: 140 * scaleFactor                                       // scaled width
                Layout.preferredHeight: 140 * scaleFactor                                       // scaled height
                fillMode: Image.PreserveAspectFit                                                // scale without distorting
                smooth: true                                                                      // smooth scaling
                mipmap: true                                                                       // better quality when shrunk
                sourceSize.width: 280 * scaleFactor                                                  // decode at 2x display size
                sourceSize.height: 280 * scaleFactor                                                  // decode at 2x display size
            }
        }

        Button {
            text: "BACK"
            width: 150 * scaleFactor                                                                   // scaled width
            height: Math.max(50 * scaleFactor, 44)                                                       // scaled height, min touch target 44px
            anchors.top: top_layer.bottom                                                                 // sit just below the logo row
            anchors.left: parent.left
            anchors.topMargin: 10 * scaleFactor                                                            // scaled margin
            anchors.leftMargin: 10 * scaleFactor                                                            // scaled margin
            onClicked: {
                if (gpiocontroller)                                                                          // guard in case GPIO wasn't wired up
                    gpiocontroller.conveyor_off()                                                              // stop the conveyor before leaving

                stackView.pop()                                                                                // return to the home screen
            }
        }

        Label {
            text: "PART 4"
            font.pixelSize: 28 * scaleFactor                                                                     // scaled title size
            font.bold: true
            color: "#003366"
            anchors.verticalCenter: top_layer.verticalCenter                                                       // align with the logo row
            anchors.horizontalCenter: parent.horizontalCenter                                                       // center horizontally
        }
        Image {
            id: logoImage                                                                                           // referenced by the date/time Column below
            source: "images/logo2.jpeg"                                                                              // secondary/customer logo
            anchors.top: parent.top                                                                                    // pin to top-right corner
            anchors.right: parent.right
            anchors.topMargin: 10 * scaleFactor                                                                        // scaled margin
            anchors.rightMargin: 10 * scaleFactor                                                                       // scaled margin
            width: 90 * scaleFactor                                                                                     // scaled width
            height: 60 * scaleFactor                                                                                    // scaled height
            fillMode: Image.PreserveAspectFit                                                                            // scale without distorting
            smooth: true                                                                                                  // smooth scaling
            mipmap: true                                                                                                   // better quality when shrunk
            sourceSize.width: 180 * scaleFactor                                                                             // decode at 2x display size
            sourceSize.height: 120 * scaleFactor                                                                            // decode at 2x display size
        }

        Column {
            anchors.top: logoImage.top                                                                                       // align with the secondary logo
            anchors.right: logoImage.left                                                                                     // sit to its left
            anchors.rightMargin: 15 * scaleFactor                                                                               // scaled gap
            spacing: 2 * scaleFactor                                                                                             // scaled gap between date/time

            Text {
                text: currentDate                                                                                                 // live date display
                font.pixelSize: 14 * scaleFactor                                                                                    // scaled font size
                color: "black"
            }

            Text {
                text: currentTime                                                                                                  // live clock display
                font.pixelSize: 16 * scaleFactor                                                                                     // scaled font size
                font.bold: true
                color: "green"
            }
        }

        Timer {
            interval: 1000                                                                                                          // tick once per second
            running: true                                                                                                            // start immediately
            repeat: true                                                                                                              // keep ticking

            onTriggered: {
                var now = new Date()                                                                                                   // current wall-clock time
                currentDate = Qt.formatDate(now, "dd-MM-yyyy")                                                                          // refresh displayed date
                currentTime = Qt.formatTime(now, "hh:mm:ss")                                                                             // refresh displayed time
            }
        }

        ColumnLayout {
            anchors.top: top_layer.bottom                                                                                                // below the logo row
            anchors.left: parent.left                                                                                                     // fill the remaining page area
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.topMargin: 0 * scaleFactor                                                                                              // no extra gap below the logo row
            anchors.leftMargin: 15 * scaleFactor                                                                                             // scaled margin
            anchors.rightMargin: 15 * scaleFactor                                                                                            // scaled margin
            anchors.bottomMargin: 15 * scaleFactor                                                                                            // scaled margin
            spacing: 15 * scaleFactor                                                                                                          // scaled gap between rows

            RowLayout {
                Layout.alignment: Qt.AlignHCenter                                                                                                // center the control buttons
                spacing: 10 * scaleFactor                                                                                                          // scaled gap between buttons

                Button { text: "START"; Layout.preferredWidth: 150 * scaleFactor;Layout.preferredHeight: Math.max(50 * scaleFactor, 44)  // sized/scaled START button
                enabled: backend.schemeReady                                                                                                     // disabled until the scheme switch settles
                onClicked: {
                    if (gpiocontroller)                                                                                                            // guard in case GPIO wasn't wired up
                        gpiocontroller.conveyor_on()                                                                                                // start the conveyor
                    }}
                Button { text: "STOP"; Layout.preferredWidth: 150 * scaleFactor;Layout.preferredHeight: Math.max(50 * scaleFactor, 44);  // sized/scaled STOP button
                    onClicked: {
                        if (gpiocontroller)                                                                                                             // guard in case GPIO wasn't wired up
                            gpiocontroller.conveyor_off()                                                                                                 // stop the conveyor

                        stackView.pop()                                                                                                                    // return to the home screen
                    } }
                Button { text: "RESET"; Layout.preferredWidth: 150 * scaleFactor;Layout.preferredHeight: Math.max(50 * scaleFactor, 44)  // sized/scaled RESET button
                    onClicked: {
                        productionModel.resetPart(4)                                                                                                        // capture a new baseline for part 4
                    }
                }
               // Button { text: "SWITCH"; Layout.preferredWidth: 150 * scaleFactor;Layout.preferredHeight: Math.max(50 * scaleFactor, 44) }
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter                                                                                                            // center the count tiles
                spacing: 15 * scaleFactor                                                                                                                      // scaled gap between tiles

                Rectangle {
                    Layout.preferredWidth: 140 * scaleFactor                                                                                                     // scaled tile width
                    Layout.preferredHeight: 70 * scaleFactor                                                                                                      // scaled tile height
                    color: "#27AE60"                                                                                                                                // green = OK tile
                    radius: 8

                    Column {
                        anchors.centerIn: parent
                        Label { text: "OK"; color: "white"; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }               // tile heading
                        Label { text: okCount ; color: "white"; font.pixelSize: 24 * scaleFactor; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }  // OK count value
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 140 * scaleFactor                                                                                                        // scaled tile width
                    Layout.preferredHeight: 70 * scaleFactor                                                                                                         // scaled tile height
                    color: "#E74C3C"                                                                                                                                    // red = NG tile
                    radius: 8

                    Column {
                        anchors.centerIn: parent
                        Label { text: "NG"; color: "white"; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }               // tile heading
                        Label { text: ngCount ; color: "white"; font.pixelSize: 24 * scaleFactor; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }  // NG count value
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 140 * scaleFactor                                                                                                          // scaled tile width
                    Layout.preferredHeight: 70 * scaleFactor                                                                                                           // scaled tile height
                    color: "#3498DB"                                                                                                                                     // blue = total tile
                    radius: 8

                    Column {
                        anchors.centerIn: parent
                        Label { text: "TOTAL"; color: "white"; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }             // tile heading
                        Label { text: totalCount ; color: "white"; font.pixelSize: 24 * scaleFactor; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }  // total count value
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true                                                                                                                                   // fill remaining width
                Layout.fillHeight: true                                                                                                                                    // fill remaining height
                spacing: 15 * scaleFactor                                                                                                                                    // scaled gap

                // Common Logs
                Logs {
                    Layout.fillWidth: true                                                                                                                                    // recent-results list, shared component
                    Layout.fillHeight: true
                }

                // Last Result
                Rectangle {
                    Layout.preferredWidth: 220 * scaleFactor                                                                                                                    // scaled card width
                    Layout.preferredHeight: 220 * scaleFactor                                                                                                                    // scaled card height

                    color: "white"
                    radius: 8
                    border.color: "#CCCCCC"

                    Column {
                        anchors.centerIn: parent
                        spacing: 15 * scaleFactor                                                                                                                                  // scaled gap between rows

                        Label {
                            text: "LAST RESULT"
                            font.pixelSize: 18 * scaleFactor                                                                                                                        // scaled heading size
                            font.bold: true
                        }

                        Label {
                            text: logModel ? logModel.latestStatus : "-"                                                                                                             // most recent OK/NG, or "-" if none
                            color: logModel && logModel.latestStatus === "OK" ? "green" : "red"                                                                                       // green for OK, red otherwise
                            font.pixelSize: 32 * scaleFactor                                                                                                                             // large status text
                            font.bold: true
                        }

                        Label {
                            text: logModel ? logModel.latestTime : "-"                                                                                                                  // timestamp of the latest result
                            color: "#666666"
                            font.pixelSize: 14 * scaleFactor                                                                                                                              // scaled font size
                        }
                    }
                }
            }
        }
    }
}
