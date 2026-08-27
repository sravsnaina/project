import QtQuick                                                        // core QML types
import QtQuick.Controls                                                // ApplicationWindow, Button, Menu, Dialog, ...
import QtQuick.Layouts                                                  // (used by pushed pages, not directly here)
import QtQuick.Window                                                    // Window.FullScreen / Window.Windowed enums


ApplicationWindow {                                                       // top-level window, loaded as the app's root
    id: window                                                            // referenced by the fullscreen shortcuts below
    visible: true                                                          // show the window on startup
    visibility: Window.FullScreen                                          // start in kiosk fullscreen
    width: 1280                                                            // design baseline width
    height: 720                                                            // design baseline height
    title: "Home"

    // Design baseline is 1280x720. Every hardcoded size/font/margin in
    // this file and the pushed pages is multiplied by this factor, so
    // the whole UI scales to whatever screen it lands on (7" panel,
    // dev monitor, etc.) instead of overflowing or getting cropped.
    readonly property real scaleFactor: Math.min(width / 1280, height / 720)  // uniform UI scale for this window's size

    // Default text color for every Label/Control in the app.
    // Without this, unstyled Labels inherit a light/white color
    // that's invisible on the white cards used throughout the UI.
    palette.text: "black"                                                    // default text color app-wide
    palette.windowText: "black"                                              // default window-text color app-wide

    // Kiosk: starts in real OS-level fullscreen (covers the Pi taskbar),
    // so the client only ever sees the app, never the desktop.
    // F11 toggles back to a normal window - Escape drops out of
    // fullscreen the same way - this is the operator/admin escape hatch,
    // not something shown to the client.
    Shortcut {
        sequence: "F11"                                                       // key combo that toggles fullscreen
        onActivated: window.visibility = (window.visibility === Window.FullScreen)
            ? Window.Windowed                                                  // currently fullscreen -> go windowed
            : Window.FullScreen                                                // currently windowed -> go fullscreen
    }

    Shortcut {
        sequence: "Escape"                                                     // key that always exits fullscreen
        onActivated: {
            if (window.visibility === Window.FullScreen)
                window.visibility = Window.Windowed                             // drop to a normal window
        }
    }

    StackView {
        id: stackView                                                          // referenced by push()/pop() on every page
        anchors.fill: parent                                                    // fill the whole window
        initialItem: homePage                                                    // start on the home screen
    }

    Component {
        id: homePage                                                            // the Home button's target/initial page

        Rectangle {
            anchors.fill: parent                                                  // fill the StackView
            color: "#F5F5F5"                                                       // light grey home background

            Label {
                text: "ENSTEIN ROBOTS & AUTOMATIONS PVT. LTD."
                font.pixelSize: 28 * scaleFactor                                    // scaled font size
                font.bold: true
                color: "red"
                anchors.right: parent.right                                          // pin to bottom-right corner
                anchors.bottom: parent.bottom
                anchors.rightMargin: 20 * scaleFactor                                 // scaled margin
                anchors.bottomMargin: 20 * scaleFactor                                // scaled margin
            }

            Image {
source: "images/Ensteinlogo.png"                                                       // company logo asset
width: 250 * scaleFactor                                                                // scaled display width
height: 250 * scaleFactor                                                               // scaled display height
fillMode: Image.PreserveAspectFit                                                        // scale without distorting
smooth: true                                                                              // smooth scaling
sourceSize.width: 250 * scaleFactor                                                        // decode at display size (perf)
sourceSize.height: 250 * scaleFactor                                                       // decode at display size (perf)
anchors.horizontalCenter: buttonColumn.horizontalCenter                                     // center over the part buttons
anchors.bottom: part1Button.top                                                             // sit just above Part 1 button
anchors.bottomMargin: 10 * scaleFactor                                                       // scaled gap above the button
            }
            Column {
                id: buttonColumn                                                        // referenced by the logo's centering above
                anchors.centerIn: parent                                                 // center the button stack on screen
                spacing: 20 * scaleFactor                                                 // scaled gap between buttons

                Button {
                    id: part1Button                                                        // referenced by the logo's anchor above
                    text: "Part 1"
                    width: 220 * scaleFactor                                                // scaled button width
                    height: 55 * scaleFactor                                                 // scaled button height
                    onClicked: stackView.push("Part1.qml")                                   // navigate to the Part 1 page
                }

                Button {
                    text: "Part 2"
                    width: 220 * scaleFactor                                                  // scaled button width
                    height: 55 * scaleFactor                                                   // scaled button height
                    onClicked: stackView.push("Part2.qml")                                      // navigate to the Part 2 page
                }

                Button {
                    text: "Part 3"
                    width: 220 * scaleFactor                                                     // scaled button width
                    height: 55 * scaleFactor                                                      // scaled button height
                    onClicked: stackView.push("Part3.qml")                                         // navigate to the Part 3 page
                }

                Button {
                    text: "Part 4"
                    width: 220 * scaleFactor                                                        // scaled button width
                    height: 55 * scaleFactor                                                         // scaled button height
                    onClicked: stackView.push("Part4.qml")                                            // navigate to the Part 4 page
                }
            }

            Button {
                text: "Report"
                width: 220 * scaleFactor                                                               // scaled button width
                height: 55 * scaleFactor                                                                // scaled button height
                onClicked: stackView.push("ProductionReport.qml")                                        // navigate to the report page
                anchors.right: parent.right                                                               // pin to the right edge
                anchors.rightMargin: 40 * scaleFactor                                                       // scaled margin
                anchors.verticalCenter: parent.verticalCenter                                                // vertically centered
            }

            Button {
                id: powerButton                                                                             // referenced by its own background/contentItem below
                text: "⏻"                                                                                    // power symbol
                width: 45 * scaleFactor                                                                       // scaled button width
                height: 45 * scaleFactor                                                                       // scaled button height
                font.pixelSize: 24 * scaleFactor                                                                // scaled icon size
                anchors.top: parent.top                                                                          // pin to top-right corner
                anchors.right: parent.right
                anchors.topMargin: 20 * scaleFactor                                                               // scaled margin
                anchors.rightMargin: 20 * scaleFactor                                                              // scaled margin
                onClicked: powerMenu.open()                                                                         // show the shutdown/reboot menu

                background: Rectangle {
                    radius: width / 2                                                                                // circular button
                    color: powerButton.pressed ? "#D0D0D0" : "#E8E8E8"                                                // pressed vs idle shade
                    border.color: "#B0B0B0"
                }

                contentItem: Text {
                    text: powerButton.text                                                                            // mirrors the button's label
                    font: powerButton.font
                    color: "black"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                // Explicit white/black colors below - the app's palette.text
                // override (set at window level) doesn't reach into Menu's
                // own popup, which otherwise falls back to a dark system
                // theme and renders text unreadably dark-on-dark.
                Menu {
                    id: powerMenu                                                                                       // opened by the power button above
                    y: parent.height                                                                                     // drop down just below the button
                    x: parent.width - width                                                                              // right-align under the button

                    background: Rectangle {
                        implicitWidth: 160 * scaleFactor                                                                   // scaled menu width
                        color: "white"
                        border.color: "#B0B0B0"
                        radius: 4 * scaleFactor                                                                             // scaled corner radius
                    }

                    MenuItem {
                        text: "Shutdown"
                        contentItem: Text {
                            text: parent.text                                                                               // mirrors the menu item's label
                            font: parent.font
                            color: "black"
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: parent.highlighted ? "#E0E0E0" : "transparent"                                            // hover/highlight shade
                        }
                        onTriggered: {
                            powerConfirmDialog.pendingAction = "shutdown"                                                     // remember which action to confirm
                            powerConfirmDialog.open()                                                                          // show the Yes/No confirmation
                        }
                    }

                    MenuItem {
                        text: "Reboot"
                        contentItem: Text {
                            text: parent.text                                                                                  // mirrors the menu item's label
                            font: parent.font
                            color: "black"
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: parent.highlighted ? "#E0E0E0" : "transparent"                                               // hover/highlight shade
                        }
                        onTriggered: {
                            powerConfirmDialog.pendingAction = "reboot"                                                          // remember which action to confirm
                            powerConfirmDialog.open()                                                                             // show the Yes/No confirmation
                        }
                    }

                    // Restart button hidden for now - relaunching this
                    // frozen build crashes (PyInstaller onefile self-
                    // extraction race, still being tracked down).
                    // backend.restartApp() is still there for when it's
                    // fixed.
                    /*
                    MenuItem {
                        text: "Restart"
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            color: "black"
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: parent.highlighted ? "#E0E0E0" : "transparent"
                        }
                        onTriggered: {
                            powerConfirmDialog.pendingAction = "restart"
                            powerConfirmDialog.open()
                        }
                    }
                    */
                }
            }

            Dialog {
                id: powerConfirmDialog                                                                                        // opened from the Shutdown/Reboot menu items
                modal: true                                                                                                    // block interaction with the rest of the UI
                x: (parent.width - width) / 2                                                                                  // horizontally centered
                y: (parent.height - height) / 2                                                                                 // vertically centered
                title: "Confirm"
                standardButtons: Dialog.No | Dialog.Yes                                                                          // built-in Yes/No buttons

                // Same fix as powerMenu above - Popup-derived items don't
                // pick up the window's palette.text override, so without
                // this the title/label/Yes-No text render dark-on-dark.
                palette.window: "white"                                                                                          // dialog background
                palette.text: "white"                                                                                            // (see note above on Popup palette quirk)
                palette.windowText: "black"                                                                                       // title/body text color
                palette.buttonText: "white"                                                                                       // Yes/No button text color

                background: Rectangle {
                    color: "white"
                    radius: 6 * scaleFactor                                                                                        // scaled corner radius
                    border.color: "#B0B0B0"
                }

                // Set right before open() by the Shutdown/Reboot
                // buttons above - which action Yes will actually run.
                property string pendingAction: ""                                                                                   // "shutdown" or "reboot"

                Label {
                    color: "black"
                    text: {
                        if (powerConfirmDialog.pendingAction === "shutdown")
                            return "Shut down the system?"                                                                            // message for the shutdown action
                        if (powerConfirmDialog.pendingAction === "reboot")
                            return "Reboot the system?"                                                                                // message for the reboot action
                        return ""                                                                                                       // no pending action - no message
                    }
                }

                onAccepted: {
                    if (pendingAction === "shutdown")
                        backend.shutdownSystem()                                                                                         // run the confirmed shutdown
                    else if (pendingAction === "reboot")
                        backend.rebootSystem()                                                                                            // run the confirmed reboot
                }
            }
        }
    }
}
