import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15

Rectangle {
    id: statsCard
    
    property string title: ""
    property string value: ""
    property string icon: ""
    property color accentColor: Material.Blue
    
    height: 80
    color: Material.color(Material.Grey, Material.Shade900)
    radius: 8
    border.color: Material.color(Material.Grey, Material.Shade700)
    border.width: 1
    
    Row {
        anchors.left: parent.left
        anchors.leftMargin: 15
        anchors.verticalCenter: parent.verticalCenter
        spacing: 12
        
        Rectangle {
            width: 40
            height: 40
            radius: 20
            color: Qt.rgba(statsCard.accentColor.r, statsCard.accentColor.g, statsCard.accentColor.b, 0.2)
            
            Text {
                text: icon
                font.pixelSize: 18
                anchors.centerIn: parent
            }
        }
        
        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            
            Text {
                text: title
                color: Material.color(Material.Grey, Material.Shade400)
                font.pixelSize: 11
                font.bold: true
            }
            
            Text {
                text: value
                color: "white"
                font.pixelSize: 16
                font.bold: true
            }
        }
    }
}