import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import "components" as Components

ScrollView {
    id: dashboard
    
    Column {
        width: dashboard.width
        spacing: 20
        
        // Header
        Text {
            text: "📊 Dashboard"
            font.pixelSize: 28
            font.bold: true
            color: "white"
        }
        
        Text {
            text: "Monitor your email organization and system performance"
            font.pixelSize: 14
            color: Material.color(Material.Grey, Material.Shade400)
        }
        
        // Stats Grid
        GridLayout {
            width: parent.width
            columns: 4
            rowSpacing: 15
            columnSpacing: 15
            
            // Gmail Connection Status
            Components.StatsCard {
                Layout.fillWidth: true
                title: "Gmail Connection"
                value: gmailCleaner.isConnected ? "Connected" : "Disconnected"
                icon: "📧"
                accentColor: gmailCleaner.isConnected ? Material.Green : Material.Red
            }
            
            // Unread Emails
            Components.StatsCard {
                Layout.fillWidth: true
                title: "Unread Emails"
                value: gmailCleaner.unreadCount.toLocaleString()
                icon: "📬"
                accentColor: Material.Orange
            }
            
            // LM Studio Model
            Components.StatsCard {
                Layout.fillWidth: true
                title: "Active Model"
                value: lmStudioManager.currentModel || "None"
                icon: "🧠"
                accentColor: Material.Teal
            }
            
            // Processing Accuracy
            Components.StatsCard {
                Layout.fillWidth: true
                title: "Accuracy"
                value: (gmailCleaner.accuracyRate * 100).toFixed(1) + "%"
                icon: "🎯"
                accentColor: Material.Blue
            }
        }
        
        // Quick Actions
        Text {
            text: "⚡ Quick Actions"
            font.pixelSize: 20
            font.bold: true
            color: "white"
            topPadding: 20
        }
        
        Flow {
            width: parent.width
            spacing: 15
            
            Button {
                text: "🚀 Start Processing"
                Material.background: Material.Blue
                onClicked: emailRunner.startBulkProcessing()
            }
            
            Button {
                text: "🧠 Run LM Analysis"
                Material.background: Material.Teal
                onClicked: lmStudioManager.runAnalysis()
            }
            
            Button {
                text: "📤 Export Email List"
                Material.background: Material.Purple
                onClicked: emailRunner.exportEmailList()
            }
            
            Button {
                text: "🧹 Cleanup Old Emails"
                Material.background: Material.Orange
                onClicked: emailRunner.startCleanup()
            }
        }
        
        // Recent Activity
        Text {
            text: "📋 Recent Activity"
            font.pixelSize: 20
            font.bold: true
            color: "white"
            topPadding: 20
        }
        
        Rectangle {
            width: parent.width
            height: 300
            color: Material.color(Material.Grey, Material.Shade900)
            radius: 8
            border.color: Material.color(Material.Grey, Material.Shade700)
            border.width: 1
            
            ListView {
                id: activityList
                anchors.fill: parent
                anchors.margins: 15
                model: auditManager.recentActivity
                
                delegate: Rectangle {
                    width: activityList.width
                    height: 50
                    color: "transparent"
                    
                    Row {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 15
                        
                        Text {
                            text: model.icon || "📧"
                            font.pixelSize: 16
                        }
                        
                        Column {
                            Text {
                                text: model.description || "No description"
                                color: "white"
                                font.pixelSize: 12
                            }
                            
                            Text {
                                text: model.timestamp || ""
                                color: Material.color(Material.Grey, Material.Shade400)
                                font.pixelSize: 10
                            }
                        }
                    }
                }
                
                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                }
            }
        }
    }
}