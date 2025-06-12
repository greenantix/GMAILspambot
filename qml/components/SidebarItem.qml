import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15

Rectangle {
    id: sidebarItem
    
    property string text: ""
    property string icon: ""
    property bool isActive: false
    
    signal clicked()
    
    width: parent.width
    height: 50
    color: isActive ? Material.color(Material.Blue, Material.Shade700) : 
           mouseArea.containsMouse ? Material.color(Material.Grey, Material.Shade700) : "transparent"
    radius: 8
    
    Behavior on color {
        ColorAnimation { duration: 200 }
    }
    
    Row {
        anchors.left: parent.left
        anchors.leftMargin: 15
        anchors.verticalCenter: parent.verticalCenter
        spacing: 12
        
        Text {
            text: icon
            font.pixelSize: 16
            anchors.verticalCenter: parent.verticalCenter
        }
        
        Text {
            text: sidebarItem.text
            color: isActive ? "white" : Material.color(Material.Grey, Material.Shade300)
            font.pixelSize: 14
            font.bold: isActive
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        
        onClicked: sidebarItem.clicked()
    }
}