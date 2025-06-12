import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ScrollView {
    id: auditView
    
    Column {
        width: auditView.width
        spacing: 20
        
        // Header
        Row {
            width: parent.width
            
            Column {
                Text {
                    text: "📋 Audit Log"
                    font.pixelSize: 28
                    font.bold: true
                    color: "white"
                }
                
                Text {
                    text: "View and restore email processing actions"
                    font.pixelSize: 14
                    color: Material.color(Material.Grey, Material.Shade400)
                }
            }
            
            Item { Layout.fillWidth: true }
            
            // Action buttons
            Row {
                spacing: 10
                anchors.verticalCenter: parent.verticalCenter
                
                Button {
                    text: "🔄 Refresh"
                    Material.background: Material.Blue
                    onClicked: auditManager.refresh()
                }
                
                Button {
                    text: "📤 Export CSV"
                    Material.background: Material.Purple
                    onClicked: auditManager.exportToCsv()
                }
                
                Button {
                    text: "↩️ Restore Selected"
                    Material.background: Material.Orange
                    enabled: auditTable.selectedCount > 0
                    onClicked: auditManager.restoreSelected()
                }
            }
        }
        
        // Filters
        Rectangle {
            width: parent.width
            height: 80
            color: Material.color(Material.Grey, Material.Shade900)
            radius: 8
            border.color: Material.color(Material.Grey, Material.Shade700)
            border.width: 1
            
            Row {
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 20
                
                Text {
                    text: "🔍 Filters:"
                    color: "white"
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Column {
                    spacing: 5
                    
                    Text {
                        text: "Date Range:"
                        color: Material.color(Material.Grey, Material.Shade300)
                        font.pixelSize: 10
                    }
                    
                    ComboBox {
                        model: ["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"]
                        currentIndex: 2
                        onCurrentTextChanged: auditManager.setDateFilter(currentText)
                    }
                }
                
                Column {
                    spacing: 5
                    
                    Text {
                        text: "Action Type:"
                        color: Material.color(Material.Grey, Material.Shade300)
                        font.pixelSize: 10
                    }
                    
                    ComboBox {
                        model: ["All Actions", "Categorized", "Archived", "Deleted", "Labeled"]
                        onCurrentTextChanged: auditManager.setActionFilter(currentText)
                    }
                }
                
                Column {
                    spacing: 5
                    
                    Text {
                        text: "Category:"
                        color: Material.color(Material.Grey, Material.Shade300)
                        font.pixelSize: 10
                    }
                    
                    ComboBox {
                        model: ["All Categories", "JUNK", "NEWSLETTERS", "PERSONAL", "SHOPPING", "BILLS"]
                        onCurrentTextChanged: auditManager.setCategoryFilter(currentText)
                    }
                }
            }
        }
        
        // Audit Table
        Rectangle {
            width: parent.width
            height: 500
            color: Material.color(Material.Grey, Material.Shade900)
            radius: 8
            border.color: Material.color(Material.Grey, Material.Shade700)
            border.width: 1
            
            Column {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10
                
                // Table Header
                Rectangle {
                    width: parent.width
                    height: 30
                    color: Material.color(Material.Grey, Material.Shade800)
                    radius: 4
                    
                    Row {
                        anchors.left: parent.left
                        anchors.leftMargin: 10
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 20
                        
                        CheckBox {
                            id: selectAllCheckbox
                            checked: auditTable.allSelected
                            onToggled: auditTable.selectAll(checked)
                        }
                        
                        Text { text: "Timestamp"; color: "white"; font.bold: true; width: 120 }
                        Text { text: "Email Subject"; color: "white"; font.bold: true; width: 200 }
                        Text { text: "Action"; color: "white"; font.bold: true; width: 100 }
                        Text { text: "Category"; color: "white"; font.bold: true; width: 100 }
                        Text { text: "Sender"; color: "white"; font.bold: true; width: 150 }
                    }
                }
                
                // Table Content
                ListView {
                    id: auditTable
                    width: parent.width
                    height: parent.height - 50
                    model: auditManager.filteredEntries
                    
                    property int selectedCount: 0
                    property bool allSelected: false
                    
                    function selectAll(checked) {
                        for (var i = 0; i < count; i++) {
                            itemAtIndex(i).selected = checked
                        }
                        updateSelectedCount()
                    }
                    
                    function updateSelectedCount() {
                        var count = 0
                        for (var i = 0; i < auditTable.count; i++) {
                            if (itemAtIndex(i).selected) count++
                        }
                        selectedCount = count
                        allSelected = (count === auditTable.count)
                    }
                    
                    delegate: Rectangle {
                        width: auditTable.width
                        height: 40
                        color: mouseArea.containsMouse ? Material.color(Material.Grey, Material.Shade800) : "transparent"
                        
                        property bool selected: false
                        
                        Row {
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 20
                            
                            CheckBox {
                                checked: parent.parent.selected
                                onToggled: {
                                    parent.parent.selected = checked
                                    auditTable.updateSelectedCount()
                                }
                            }
                            
                            Text {
                                text: model.timestamp || ""
                                color: Material.color(Material.Grey, Material.Shade300)
                                font.pixelSize: 10
                                width: 120
                                elide: Text.ElideRight
                            }
                            
                            Text {
                                text: model.subject || ""
                                color: "white"
                                font.pixelSize: 10
                                width: 200
                                elide: Text.ElideRight
                            }
                            
                            Rectangle {
                                width: 80
                                height: 20
                                radius: 10
                                color: getActionColor(model.action)
                                
                                Text {
                                    text: model.action || ""
                                    color: "white"
                                    font.pixelSize: 9
                                    anchors.centerIn: parent
                                }
                            }
                            
                            Text {
                                text: model.category || ""
                                color: Material.color(Material.Teal)
                                font.pixelSize: 10
                                font.bold: true
                                width: 100
                            }
                            
                            Text {
                                text: model.sender || ""
                                color: Material.color(Material.Grey, Material.Shade400)
                                font.pixelSize: 10
                                width: 150
                                elide: Text.ElideRight
                            }
                        }
                        
                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                        }
                    }
                    
                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }
                }
            }
        }
        
        // Status Bar
        Rectangle {
            width: parent.width
            height: 40
            color: Material.color(Material.Grey, Material.Shade800)
            radius: 8
            
            Row {
                anchors.left: parent.left
                anchors.leftMargin: 15
                anchors.verticalCenter: parent.verticalCenter
                spacing: 20
                
                Text {
                    text: "📊 Total Entries: " + auditManager.totalEntries
                    color: Material.color(Material.Grey, Material.Shade300)
                    font.pixelSize: 12
                }
                
                Text {
                    text: "✅ Selected: " + auditTable.selectedCount
                    color: Material.color(Material.Blue)
                    font.pixelSize: 12
                }
                
                Text {
                    text: "🔍 Filtered: " + auditManager.filteredEntries.length
                    color: Material.color(Material.Teal)
                    font.pixelSize: 12
                }
            }
        }
    }
    
    function getActionColor(action) {
        switch(action) {
            case "categorized": return Material.color(Material.Blue)
            case "archived": return Material.color(Material.Orange)
            case "deleted": return Material.color(Material.Red)
            case "labeled": return Material.color(Material.Green)
            default: return Material.color(Material.Grey)
        }
    }
}