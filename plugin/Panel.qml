import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// Settings popup for the RT400 display: what number the cooler shows (CPU,
// GPU, hottest of both, or a fixed value) and its unit. State lives in
// rt400d; BarWidget.qml owns it and this panel only reads and requests.
Panel {
  id: root
  moduleName: "local.pccooler-rt400"
  ipcTarget: "local.pccooler-rt400"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  readonly property var barIdentity: hostWidget || root

  readonly property color contentForeground: bar ? bar.foreground : Commons.Color.foreground
  readonly property string contentFontFamily: bar ? bar.fontFamily : Style.font.family

  readonly property string source: hostWidget ? hostWidget.source : "cpu"
  readonly property string unit: hostWidget ? hostWidget.unit : "c"
  readonly property int fixed: hostWidget ? hostWidget.fixed : 0
  readonly property string label: hostWidget ? hostWidget.label : "--"
  readonly property string error: hostWidget ? hostWidget.error : ""

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.barIdentity
    bar: root.bar
    open: root.opened
    centerOnBar: false
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(300))
    contentHeight: panel.fittedContentHeight(content.implicitHeight)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      Column {
        id: content
        width: parent.width
        spacing: Style.space(10)

        Text {
          textFormat: Text.PlainText
          width: parent.width
          horizontalAlignment: Text.AlignHCenter
          text: root.label
          color: root.contentForeground
          font.family: root.contentFontFamily
          font.pixelSize: Style.font.body * 2.4
          font.bold: true
        }

        Text {
          textFormat: Text.PlainText
          width: parent.width
          horizontalAlignment: Text.AlignHCenter
          visible: root.error !== ""
          text: root.error
          wrapMode: Text.WordWrap
          color: Qt.darker(root.contentForeground, 1.5)
          font.family: root.contentFontFamily
          font.pixelSize: Style.font.caption
        }

        PanelSeparator { width: parent.width; foreground: root.contentForeground }

        PanelSectionHeader {
          width: parent.width
          text: "SOURCE"
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
        }

        ButtonGroup {
          options: [
            { value: "cpu", label: "CPU" },
            { value: "gpu", label: "GPU" },
            { value: "max", label: "MAX" },
            { value: "fixed", label: "FIXED" }
          ]
          value: root.source
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
          onChanged: function(v) { if (root.hostWidget) root.hostWidget.setSource(v) }
        }

        PanelSectionHeader {
          width: parent.width
          text: "UNIT"
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
        }

        ButtonGroup {
          options: [
            { value: "c", label: "°C" },
            { value: "f", label: "°F" }
          ]
          value: root.unit
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
          onChanged: function(v) { if (root.hostWidget) root.hostWidget.setUnit(v) }
        }

        PanelSectionHeader {
          width: parent.width
          visible: root.source === "fixed"
          text: "FIXED VALUE  " + (fixedSlider.dragging ? Math.round(fixedSlider.liveValue) : root.fixed)
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
        }

        PanelSlider {
          id: fixedSlider
          visible: root.source === "fixed"
          width: parent.width
          height: Style.spacing.controlHeight
          bar: root.bar
          minimum: 0
          maximum: 199
          step: 1
          integer: true
          value: root.fixed
          onReleased: function(v) { if (root.hostWidget) root.hostWidget.setFixed(Math.round(v)) }
        }
      }
    }
  }
}
