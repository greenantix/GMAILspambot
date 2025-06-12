import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import "components" as Components

ApplicationWindow {
    id: mainWindow
    width: 1200
    height: 800
    visible: true
    title: "Gmail Spam Bot - LM Studio Integration"
    
    // Dark Material theme
    Material.theme: Material.Dark
    Material.accent: Material.Teal
    Material.primary: Material.Blue
    
    // Properties
    property int currentViewIndex: 0
    property var viewNames: ["Dashboard", "Backlog", "Audit", "Settings"]
    
    // Main layout
    RowLayout {
        anchors.fill: parent
        spacing: 0
        
        // Sidebar
        Rectangle {
            Layout.preferredWidth: 250
            Layout.fillHeight: true
            color: Material.color(Material.Grey, Material.Shade900)
            
            Column {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10
                
                // Header
                Rectangle {
                    width: parent.width
                    height: 80
                    color: "transparent"
                    
                    Column {
                        anchors.centerIn: parent
                        spacing: 5
                        
                        Text {
                            text: "📧 Gmail Spam Bot"
                            font.pixelSize: 18
                            font.bold: true
                            color: Material.color(Material.Teal)
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        
                        Text {
                            text: "LM Studio Powered"
                            font.pixelSize: 12
                            color: Material.color(Material.Grey, Material.Shade400)
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }
                }
                
                // Navigation items
                Repeater {
                    model: mainWindow.viewNames
                    
                    Components.SidebarItem {
                        width: parent.width
                        text: modelData
                        icon: getIconForView(modelData)
                        isActive: index === mainWindow.currentViewIndex
                        onClicked: {
                            mainWindow.currentViewIndex = index
                            stackView.currentIndex = index
                        }
                    }
                }
                
                // Spacer
                Item {
                    width: parent.width
                    Layout.fillHeight: true
                }
                
                // LM Studio Status
                Rectangle {
                    width: parent.width
                    height: 60
                    color: Material.color(Material.Grey, Material.Shade800)
                    radius: 8
                    
                    Row {
                        anchors.centerIn: parent
                        spacing: 10
                        
                        Rectangle {
                            width: 12
                            height: 12
                            radius: 6
                            color: lmStudioManager.isConnected ? Material.color(Material.Green) : Material.color(Material.Red)
                        }
                        
                        Text {
                            text: lmStudioManager.isConnected ? "LM Studio Online" : "LM Studio Offline"
                            color: "white"
                            font.pixelSize: 12
                        }
                    }
                }
            }
        }
        
        // Main content area
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Material.color(Material.Grey, Material.Shade800)
            
            // Content stack
            StackLayout {
                id: stackView
                anchors.fill: parent
                anchors.margins: 20
                currentIndex: mainWindow.currentViewIndex
                
                // Dashboard
                Dashboard {
                    
                }
                
                // Backlog Processing
                BacklogView {
                    
                }
                
                // Audit Log
                AuditLog {
                    
                }
                
                // Settings
                SettingsView {
                    
                }
            }
        }
    }
    
    // Helper function to get icons
    function getIconForView(viewName) {
        switch(viewName) {
            case "Dashboard": return "📊"
            case "Backlog": return "📧"
            case "Audit": return "📋"
            case "Settings": return "⚙️"
            default: return "📄"
        }
    }
}