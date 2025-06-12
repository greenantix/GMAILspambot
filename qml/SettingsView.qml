import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ScrollView {
    id: settingsView
    
    Column {
        width: settingsView.width
        spacing: 20
        
        // Header
        Text {
            text: "⚙️ Settings"
            font.pixelSize: 28
            font.bold: true
            color: "white"
        }
        
        Text {
            text: "Configure Gmail Spam Bot and LM Studio integration"
            font.pixelSize: 14
            color: Material.color(Material.Grey, Material.Shade400)
        }
        
        // LM Studio Configuration
        Rectangle {
            width: parent.width
            height: 250
            color: Material.color(Material.Grey, Material.Shade900)
            radius: 8
            border.color: Material.color(Material.Grey, Material.Shade700)
            border.width: 1
            
            Column {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                
                Row {
                    width: parent.width
                    
                    Text {
                        text: "🧠 LM Studio Configuration"
                        font.pixelSize: 16
                        font.bold: true
                        color: "white"
                    }
                    
                    Item { width: parent.width - x }
                    
                    Rectangle {
                        width: 80
                        height: 25
                        radius: 12
                        color: lmStudioManager.isConnected ? Material.color(Material.Green, Material.Shade800) : Material.color(Material.Red, Material.Shade800)
                        
                        Text {
                            text: lmStudioManager.isConnected ? "Online" : "Offline"
                            color: "white"
                            font.pixelSize: 10
                            anchors.centerIn: parent
                        }
                    }
                }
                
                GridLayout {
                    width: parent.width
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    
                    Text {
                        text: "Server Endpoint:"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    TextField {
                        Layout.fillWidth: true
                        text: settingsManager.lmStudioEndpoint
                        placeholderText: "http://localhost:1234"
                        onTextChanged: settingsManager.lmStudioEndpoint = text
                    }
                    
                    Text {
                        text: "Active Model:"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    ComboBox {
                        Layout.fillWidth: true
                        model: lmStudioManager.availableModels
                        currentIndex: lmStudioManager.currentModelIndex
                        onCurrentIndexChanged: lmStudioManager.switchModel(currentIndex)
                    }
                    
                    Text {
                        text: "Temperature:"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    Row {
                        spacing: 10
                        
                        Slider {
                            from: 0.0
                            to: 1.0
                            value: settingsManager.temperature
                            onValueChanged: settingsManager.temperature = value
                        }
                        
                        Text {
                            text: settingsManager.temperature.toFixed(2)
                            color: "white"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
                
                Button {
                    text: "🧠 Run Analysis"
                    Material.background: Material.Teal
                    enabled: lmStudioManager.isConnected
                    onClicked: lmStudioManager.runAnalysis()
                }
            }
        }
        
        // Gmail Configuration
        Rectangle {
            width: parent.width
            height: 200
            color: Material.color(Material.Grey, Material.Shade900)
            radius: 8
            border.color: Material.color(Material.Grey, Material.Shade700)
            border.width: 1
            
            Column {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                
                Text {
                    text: "📧 Gmail Configuration"
                    font.pixelSize: 16
                    font.bold: true
                    color: "white"
                }
                
                GridLayout {
                    width: parent.width
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    
                    Text {
                        text: "Batch Size:"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    SpinBox {
                        from: 10
                        to: 1000
                        value: settingsManager.batchSize
                        onValueChanged: settingsManager.batchSize = value
                    }
                    
                    Text {
                        text: "Request Delay (ms):"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    SpinBox {
                        from: 0
                        to: 5000
                        value: settingsManager.requestDelay
                        onValueChanged: settingsManager.requestDelay = value
                    }
                    
                    Text {
                        text: "Server-side Filtering:"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    Switch {
                        checked: settingsManager.useServerSideFiltering
                        onToggled: settingsManager.useServerSideFiltering = checked
                    }
                }
            }
        }
        
        // Cleanup Configuration
        Rectangle {
            width: parent.width
            height: 180
            color: Material.color(Material.Grey, Material.Shade900)
            radius: 8
            border.color: Material.color(Material.Grey, Material.Shade700)
            border.width: 1
            
            Column {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                
                Text {
                    text: "🧹 Email Cleanup Configuration"
                    font.pixelSize: 16
                    font.bold: true
                    color: "white"
                }
                
                GridLayout {
                    width: parent.width
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    
                    Text {
                        text: "JUNK Retention (days):"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    SpinBox {
                        from: 1
                        to: 365
                        value: settingsManager.junkRetentionDays
                        onValueChanged: settingsManager.junkRetentionDays = value
                    }
                    
                    Text {
                        text: "Newsletter Retention (days):"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    SpinBox {
                        from: 1
                        to: 365
                        value: settingsManager.newsletterRetentionDays
                        onValueChanged: settingsManager.newsletterRetentionDays = value
                    }
                }
            }
        }
        
        // Action Buttons
        Row {
            spacing: 15
            
            Button {
                text: "💾 Save Settings"
                Material.background: Material.Blue
                onClicked: settingsManager.saveSettings()
            }
            
            Button {
                text: "📤 Export Settings"
                Material.background: Material.Purple
                onClicked: settingsManager.exportSettings()
            }
            
            Button {
                text: "📥 Import Settings"
                Material.background: Material.Orange
                onClicked: settingsManager.importSettings()
            }
            
            Button {
                text: "🔄 Reset to Defaults"
                Material.background: Material.Red
                onClicked: settingsManager.resetToDefaults()
            }
        }
    }
}