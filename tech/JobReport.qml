import QtQuick                                                    // core QML types (Item, Rectangle, ListView, ...)
import QtQuick.Controls                                            // Page, Button, Label, TextField
import QtQuick.Layouts                                              // ColumnLayout, RowLayout

Page {                                                               // root page, pushed onto the StackView

    Rectangle {
        anchors.fill: parent                                         // fill the whole page
        color: "#f2f2f2"                                              // light grey page background

        ColumnLayout {

            anchors.fill: parent                                      // stretch to fill the Rectangle
            anchors.margins: 20                                        // padding around the whole layout
            spacing: 15                                                 // vertical gap between rows

            // Top bar
            RowLayout {
                Layout.fillWidth: true                                  // stretch to the layout's full width

                Button {
                    text: "Back"

                    onClicked: {
                        stackView.pop()                                  // return to the previous page
                    }
                }

                Label {
                    text: "Job Report"
                    font.pixelSize: 28                                    // large page title
                    font.bold: true
                    Layout.fillWidth: true                                 // push following items to the right
                }
            }

            // Search area
            Rectangle {
                Layout.fillWidth: true
                height: 70                                                 // fixed bar height

                color: "white"
                radius: 8                                                   // rounded corners

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 15                                     // inner padding
                    spacing: 15                                              // gap between fields

                    Label {
                        text: "From Date"
                    }

                    TextField {
                        id: fromDate                                         // referenced by the SEARCH button below
                        placeholderText: "dd-MM-yyyy"
                        Layout.preferredWidth: 150
                    }

                    Label {
                        text: "To Date"
                    }

                    TextField {
                        id: toDate                                            // referenced by the SEARCH button below
                        placeholderText: "dd-MM-yyyy"
                        Layout.preferredWidth: 150
                    }

                    Button {
                        text: "SEARCH"

                        onClicked: {
                            jobReportModel.filterDate(
                                fromDate.text,                                  // typed "from" date string
                                toDate.text                                     // typed "to" date string
                            )
                        }
                    }
                }
            }

            // Table header
            Rectangle {
                Layout.fillWidth: true
                height: 50                                                     // fixed header row height

                color: "#d5d5d5"                                               // grey header background

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10

                    Label {
                        text: "JOB"
                        Layout.preferredWidth: 100                              // aligns with the delegate's job column
                        font.bold: true
                    }

                    Label {
                        text: "PART NAME"
                        Layout.preferredWidth: 200                              // aligns with the delegate's part column
                        font.bold: true
                    }

                    Label {
                        text: "RESULT"
                        Layout.preferredWidth: 100                              // aligns with the delegate's result column
                        font.bold: true
                    }

                    Label {
                        text: "OK"
                        Layout.preferredWidth: 80                               // aligns with the delegate's OK column
                        font.bold: true
                    }

                    Label {
                        text: "NG"
                        Layout.preferredWidth: 80                               // aligns with the delegate's NG column
                        font.bold: true
                    }

                    Label {
                        text: "TIME"
                        Layout.preferredWidth: 150                              // aligns with the delegate's time column
                        font.bold: true
                    }

                    Label {
                        text: "DATE"
                        Layout.fillWidth: true                                  // takes remaining width
                        font.bold: true
                    }
                }
            }

            // Job data
            ListView {
                id: jobList                                                     // referenced by delegate's width binding

                Layout.fillWidth: true
                Layout.fillHeight: true                                          // takes all remaining vertical space

                clip: true                                                        // hide delegate overflow at the edges

                model: jobReportModel                                             // backing data for the rows below

                delegate: Rectangle {

                    width: jobList.width                                          // match the list's width
                    height: 50                                                     // fixed row height

                    color: index % 2 === 0 ? "white" : "#f8f8f8"                    // alternating row stripes

                    border.color: "#dddddd"                                         // thin row separator

                    RowLayout {

                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10

                        Label {
                            text: model.job                                          // this row's job identifier
                            Layout.preferredWidth: 100
                        }

                        Label {
                            text: model.part                                         // this row's part name
                            Layout.preferredWidth: 200
                        }

                        Label {
                            text: model.result                                       // this row's OK/NG result text

                            color: model.result === "OK"
                                   ? "green"                                          // OK shown in green
                                   : "red"                                            // NG shown in red

                            font.bold: true

                            Layout.preferredWidth: 100
                        }

                        Label {
                            text: model.result === "OK" ? "1" : "0"                    // 1 if this row was an OK
                            Layout.preferredWidth: 80
                        }

                        Label {
                            text: model.result === "NG" ? "1" : "0"                    // 1 if this row was an NG
                            Layout.preferredWidth: 80
                        }

                        Label {
                            text: model.time                                           // this row's timestamp
                            Layout.preferredWidth: 150
                        }

                        Label {
                            text: model.date                                           // this row's date
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
