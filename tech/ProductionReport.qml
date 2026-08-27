import QtQuick                                                          // core QML types
import QtQuick.Controls                                                  // Page, Button, Label, Dialog
import QtQuick.Layouts                                                    // RowLayout, ColumnLayout
import QtQuick.Window                                                      // Window.width/height for scaleFactor


Page {                                                                        // production totals / part-wise report screen

    // Same 1280x720 design baseline as Main.qml, driven off the actual
    // window size so this page scales to whatever screen it's shown on.
    readonly property real scaleFactor: Math.min(Window.width / 1280, Window.height / 720)  // uniform UI scale

    ListModel {
        id: partsModel                                                          // backing data for the part-wise table below
    }

    function refreshPartsTable() {
        partsModel.clear()                                                       // rebuild the table from scratch each time

        for (var i = 1; i <= 4; i++) {                                            // one row per part number
            partsModel.append({
                part: "Part " + i,                                                 // row label
                total: productionModel.getTotal(i),                                 // this part's total count
                ok: productionModel.getOK(i),                                        // this part's OK count
                ng: productionModel.getNG(i)                                          // this part's NG count
            })
        }
    }

    Component.onCompleted: refreshPartsTable()                                       // populate the table on first load

    Connections {
        target: productionModel                                                       // listen for count changes from Python

        function onDataChanged() {
            refreshPartsTable()                                                        // re-pull the table whenever data changes
        }
    }

    Rectangle {

        anchors.fill: parent                                                            // fill the whole page
        color: "#f2f2f2"                                                                  // light grey page background


        ColumnLayout {

            anchors.fill: parent                                                          // stretch to fill the Rectangle
            anchors.margins: 20 * scaleFactor                                               // scaled padding
            spacing: 15 * scaleFactor                                                        // scaled gap between rows
            RowLayout{
                Layout.fillWidth: true                                                        // stretch to the layout's full width
                spacing:10 * scaleFactor                                                        // scaled gap between buttons
                Button{
                    text:"Back"
                    Layout.preferredWidth: 150 * scaleFactor                                      // scaled width
                    Layout.preferredHeight: Math.max(50 * scaleFactor, 44)                          // scaled height, min touch target 44px
                    onClicked:{
                        stackView.pop()                                                              // return to the home screen
                    }
                }
                Button{
                    text:"Reset"
                    Layout.preferredWidth: 150 * scaleFactor                                          // scaled width
                    Layout.preferredHeight: Math.max(50 * scaleFactor, 44)                              // scaled height, min touch target 44px
                    onClicked:{
                        resetConfirmDialog.open()                                                        // ask for confirmation before wiping data
                    }
                }
            }

            Label {
                text: "Production Report"

                color: "black"
                font.pixelSize: 28 * scaleFactor                                                          // scaled title size
                font.bold: true
            }

            Dialog {
                id: resetConfirmDialog                                                                     // opened by the Reset button above

                title: "Reset All Data"
                modal: true                                                                                 // block interaction with the rest of the UI
                standardButtons: Dialog.Yes | Dialog.No                                                       // built-in Yes/No buttons
                anchors.centerIn: Overlay.overlay                                                              // center over the whole window

                Label {
                    text: "This will permanently delete all production counts and log history. Continue?"
                    color: "black"
                    wrapMode: Text.WordWrap                                                                     // wrap long confirmation text
                }

                onAccepted: {
                    productionModel.resetData()                                                                  // wipe all counts/baselines/logs
                    logModel.clear()                                                                              // wipe the QML-side recent-results list too
                }
            }




            // Summary

            RowLayout {


                Layout.fillWidth:true                                                                              // stretch to the layout's full width

                spacing:20 * scaleFactor                                                                             // scaled gap between summary tiles



                Rectangle {

                    Layout.fillWidth:true                                                                             // share width evenly with the other tiles
                    Layout.preferredHeight:100 * scaleFactor                                                            // scaled tile height

                    radius:10                                                                                            // rounded corners
                    color:"white"


                    Column {

                        anchors.centerIn:parent                                                                           // center the label/value pair


                        Label {
                            text:"TOTAL PARTS"
                        }


                        Label {

                            text:productionModel.totalParts                                                                 // overall total across all parts

                            font.pixelSize:32 * scaleFactor                                                                   // large value display
                            font.bold:true

                        }

                    }

                }



                Rectangle {

                    Layout.fillWidth:true                                                                                     // share width evenly with the other tiles
                    Layout.preferredHeight:100 * scaleFactor                                                                    // scaled tile height

                    radius:10                                                                                                    // rounded corners
                    color:"white"


                    Column {

                        anchors.centerIn:parent                                                                                   // center the label/value pair


                        Label {
                            text:"OK"
                        }


                        Label {

                            text:productionModel.totalOK                                                                            // overall OK count across all parts

                            color:"green"

                            font.pixelSize:32 * scaleFactor                                                                            // large value display
                            font.bold:true

                        }

                    }

                }





                Rectangle {

                    Layout.fillWidth:true                                                                                              // share width evenly with the other tiles
                    Layout.preferredHeight:100 * scaleFactor                                                                             // scaled tile height

                    radius:10                                                                                                             // rounded corners
                    color:"white"


                    Column {

                        anchors.centerIn:parent                                                                                            // center the label/value pair


                        Label {
                            text:"NG"
                        }


                        Label {

                            text:productionModel.totalNG                                                                                     // overall NG count across all parts

                            color:"red"

                            font.pixelSize:32 * scaleFactor                                                                                     // large value display
                            font.bold:true

                        }

                    }

                }








            }





            Label {

                text:"Part Wise Details"

                font.pixelSize:22 * scaleFactor                                                                                                   // scaled heading size
                font.bold:true

            }





            // Table Header


            Rectangle {

                Layout.preferredHeight:45 * scaleFactor                                                                                             // scaled header row height

                Layout.fillWidth:true                                                                                                                // stretch to the layout's full width

                color:"#dddddd"                                                                                                                        // grey header background



                RowLayout {


                    anchors.fill:parent                                                                                                                 // fill the header Rectangle
                    anchors.leftMargin:15 * scaleFactor                                                                                                    // scaled inner padding
                    anchors.rightMargin:15 * scaleFactor                                                                                                    // scaled inner padding


                    Label {
                        text:"PART NAME"
                        Layout.preferredWidth:200 * scaleFactor                                                                                              // aligns with the delegate's part column
                        font.bold:true
                        font.pixelSize:16 * scaleFactor                                                                                                        // scaled font size
                    }


                    Label {
                        text:"TOTAL"
                        Layout.preferredWidth:100 * scaleFactor                                                                                                 // aligns with the delegate's total column
                        font.bold:true
                        font.pixelSize:16 * scaleFactor                                                                                                          // scaled font size
                    }


                    Label {
                        text:"OK"
                        Layout.preferredWidth:100 * scaleFactor                                                                                                   // aligns with the delegate's OK column
                        font.bold:true
                        font.pixelSize:16 * scaleFactor                                                                                                            // scaled font size
                    }


                    Label {
                        text:"NG"
                        Layout.preferredWidth:100 * scaleFactor                                                                                                     // aligns with the delegate's NG column
                        font.bold:true
                        font.pixelSize:16 * scaleFactor                                                                                                              // scaled font size
                    }

                }

            }





            // Table Data


            ListView {

                Layout.fillWidth:true                                                                                                                                 // stretch to the layout's full width

                Layout.fillHeight:true                                                                                                                                  // take remaining vertical space


                model:partsModel                                                                                                                                          // backing data built by refreshPartsTable()



                delegate:Rectangle {


                    width:ListView.view.width                                                                                                                              // match the list's width

                    height:50 * scaleFactor                                                                                                                                  // scaled row height


                    color:"white"

                    border.color:"#cccccc"                                                                                                                                     // thin row separator



                    RowLayout {


                        anchors.fill:parent                                                                                                                                       // fill the delegate Rectangle
                        anchors.leftMargin:15 * scaleFactor                                                                                                                         // scaled inner padding
                        anchors.rightMargin:15 * scaleFactor                                                                                                                         // scaled inner padding



                        Label {

                            text:model.part                                                                                                                                            // this row's part label

                            Layout.preferredWidth:200 * scaleFactor                                                                                                                       // aligns with the header's part column

                            font.pixelSize:16 * scaleFactor                                                                                                                                 // scaled font size

                        }



                        Label {

                            text:model.total                                                                                                                                                 // this row's total count

                            Layout.preferredWidth:100 * scaleFactor                                                                                                                             // aligns with the header's total column

                            font.pixelSize:16 * scaleFactor                                                                                                                                       // scaled font size

                        }



                        Label {

                            text:model.ok                                                                                                                                                          // this row's OK count

                            color:"green"

                            Layout.preferredWidth:100 * scaleFactor                                                                                                                                   // aligns with the header's OK column

                            font.pixelSize:16 * scaleFactor                                                                                                                                             // scaled font size

                        }



                        Label {

                            text:model.ng                                                                                                                                                                // this row's NG count

                            color:"red"

                            Layout.preferredWidth:100 * scaleFactor                                                                                                                                         // aligns with the header's NG column

                            font.pixelSize:16 * scaleFactor                                                                                                                                                   // scaled font size

                        }


                    }

                }


            }


        }

    }

}