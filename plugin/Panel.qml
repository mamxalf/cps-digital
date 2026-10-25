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
  readonly property string active: hostWidget ? hostWidget.active : "cpu"
  readonly property var rotateSources: hostWidget ? hostWidget.rotateSources : []
  readonly property int rotateSeconds: hostWidget ? hostWidget.rotateSeconds : 5
  readonly property bool alert: hostWidget ? hostWidget.alert : false
  readonly property int alertThreshold: hostWidget ? hostWidget.alertThreshold : 85
  readonly property bool alerting: hostWidget ? hostWidget.alerting : false

  // Rotation lists offered as buttons; any other list set via rt400ctl shows
  // as no selection here.
  readonly property var rotationPresets: ({
    "cpu-load": ["cpu", "load"],
    "temps": ["cpu", "gpu", "nvme"],
    "all": ["cpu", "gpu", "nvme", "load", "ram"]
  })
  readonly property string rotationPreset: {
    for (var key in rotationPresets)
      if (JSON.stringify(rotationPresets[key]) === JSON.stringify(rotateSources)) return key
    return ""
  }
  readonly property var tempSources: ["cpu", "gpu", "max", "nvme"]
  readonly property var otherSources: ["load", "ram", "fixed", "rotate"]

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
          text: root.active.toUpperCase() + (root.alerting ? "  -  OVER LIMIT" : "")
          color: Qt.darker(root.contentForeground, 1.5)
          font.family: root.contentFontFamily
          font.pixelSize: Style.font.caption
          font.letterSpacing: 1
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
            { value: "nvme", label: "SSD" }
          ]
          value: root.tempSources.indexOf(root.source) >= 0 ? root.source : ""
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
          onChanged: function(v) { if (root.hostWidget) root.hostWidget.setSource(v) }
        }

        ButtonGroup {
          options: [
            { value: "load", label: "LOAD" },
            { value: "ram", label: "RAM" },
            { value: "fixed", label: "FIXED" },
            { value: "rotate", label: "ROTATE" }
          ]
          value: root.otherSources.indexOf(root.source) >= 0 ? root.source : ""
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
          onChanged: function(v) { if (root.hostWidget) root.hostWidget.setSource(v) }
        }

        PanelSectionHeader {
          width: parent.width
          visible: root.source === "rotate"
          text: "ROTATE BETWEEN"
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
        }

        ButtonGroup {
          visible: root.source === "rotate"
          options: [
            { value: "cpu-load", label: "CPU+LOAD" },
            { value: "temps", label: "TEMPS" },
            { value: "all", label: "ALL" }
          ]
          value: root.rotationPreset
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
          onChanged: function(v) { if (root.hostWidget) root.hostWidget.setRotateSources(root.rotationPresets[v]) }
        }

        PanelSectionHeader {
          width: parent.width
          visible: root.source === "rotate"
          text: "SWITCH EVERY"
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
        }

        ButtonGroup {
          visible: root.source === "rotate"
          options: [
            { value: "3", label: "3s" },
            { value: "5", label: "5s" },
            { value: "10", label: "10s" },
            { value: "30", label: "30s" }
          ]
          value: String(root.rotateSeconds)
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
          onChanged: function(v) { if (root.hostWidget) root.hostWidget.setRotateSeconds(parseInt(v)) }
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

        PanelSeparator { width: parent.width; foreground: root.contentForeground }

        PanelSectionHeader {
          width: parent.width
          text: "OVER-TEMPERATURE ALERT"
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
        }

        ButtonGroup {
          options: [
            { value: "off", label: "OFF" },
            { value: "on", label: "BLINK" }
          ]
          value: root.alert ? "on" : "off"
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
          onChanged: function(v) { if (root.hostWidget) root.hostWidget.setAlert(v === "on") }
        }

        PanelSectionHeader {
          width: parent.width
          visible: root.alert
          text: "ABOVE  " + (alertSlider.dragging ? Math.round(alertSlider.liveValue) : root.alertThreshold) + " °C"
          foreground: root.contentForeground
          fontFamily: root.contentFontFamily
        }

        PanelSlider {
          id: alertSlider
          visible: root.alert
          width: parent.width
          height: Style.spacing.controlHeight
          bar: root.bar
          minimum: 50
          maximum: 100
          step: 1
          integer: true
          value: root.alertThreshold
          onReleased: function(v) { if (root.hostWidget) root.hostWidget.setAlertThreshold(Math.round(v)) }
        }
      }
    }
  }
}
