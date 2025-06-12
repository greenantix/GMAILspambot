import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ScrollView {
    id: backlogView
    
    Column {
        width: backlogView.width
        spacing: 20
        
        // Header
        Row {
            width: parent.width
            
            Column {
                Text {
                    text: "📧 Backlog Processing"
                    font.pixelSize: 28
                    font.bold: true
                    color: "white"
                }
                
                Text {
                    text: "Process large volumes of emails with smart model selection"
                    font.pixelSize: 14
                    color: Material.color(Material.Grey, Material.Shade400)
                }
            }
            
            Item { Layout.fillWidth: true }
            
            // Processing controls
            Row {
                spacing: 10
                anchors.verticalCenter: parent.verticalCenter
                
                Button {
                    text: emailRunner.isProcessing ? "⏸️ Pause" : "▶️ Start"
                    Material.background: emailRunner.isProcessing ? Material.Orange : Material.Green
                    onClicked: emailRunner.isProcessing ? emailRunner.pause() : emailRunner.start()
                }
                
                Button {
                    text: "⏹️ Stop"
                    Material.background: Material.Red
                    enabled: emailRunner.isProcessing
                    onClicked: emailRunner.stop()
                }
            }
        }
        
        // Processing Configuration
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
                    text: "⚙️ Processing Configuration"
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
                        value: 100
                        onValueChanged: emailRunner.batchSize = value
                    }
                    
                    Text {
                        text: "Model Strategy:"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    ComboBox {
                        model: ["Auto Select", "Fast (Phi-3)", "Standard (Llama-8B)", "Large Context (100k)"]
                        currentIndex: 0
                        onCurrentTextChanged: lmStudioManager.setStrategy(currentText)
                    }
                    
                    Text {
                        text: "Email Query:"
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    TextField {
                        Layout.fillWidth: true
                        text: "is:unread"
                        placeholderText: "Gmail search query"
                        onTextChanged: emailRunner.query = text
                    }
                }
            }
        }
        
        // Progress Display
        Rectangle {
            width: parent.width
            height: 150
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
                        text: "📊 Progress"
                        font.pixelSize: 16
                        font.bold: true
                        color: "white"
                    }
                    
                    Item { width: parent.width - x }
                    
                    Text {
                        text: emailRunner.processedCount + " / " + emailRunner.totalCount
                        color: Material.color(Material.Grey, Material.Shade300)
                        font.pixelSize: 12
                    }
                }
                
                ProgressBar {
                    width: parent.width
                    value: emailRunner.totalCount > 0 ? emailRunner.processedCount / emailRunner.totalCount : 0
                    Material.accent: Material.Teal
                }
                
                Row {
                    width: parent.width
                    
                    Text {
                        text: "Current Model: " + (lmStudioManager.currentModel || "None")
                        color: Material.color(Material.Grey, Material.Shade400)
                        font.pixelSize: 11
                    }
                    
                    Item { width: parent.width - x }
                    
                    Text {
                        text: "ETA: " + emailRunner.estimatedTimeRemaining
                        color: Material.color(Material.Grey, Material.Shade400)
                        font.pixelSize: 11
                    }
                }
            }
        }
        
        // Live Log Output
        Rectangle {
            width: parent.width
            height: 300
            color: Material.color(Material.Grey, Material.Shade900)
            radius: 8
            border.color: Material.color(Material.Grey, Material.Shade700)
            border.width: 1
            
            Column {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10
                
                Text {
                    text: "📝 Live Processing Log"
                    font.pixelSize: 14
                    font.bold: true
                    color: "white"
                }
                
                ScrollView {
                    width: parent.width
                    height: parent.height - 40
                    
                    TextArea {
                        text: emailRunner.liveLog
                        readOnly: true
                        color: Material.color(Material.Grey, Material.Shade300)
                        font.family: "monospace"
                        font.pixelSize: 10
                        wrapMode: TextArea.Wrap
                        
                        background: Rectangle {
                            color: "transparent"
                        }
                    }
                }
            }
        }
    }
}