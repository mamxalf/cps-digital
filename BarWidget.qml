import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// Shows what rt400d is sending to the cooler display; any click opens the
// settings panel. All state lives in the daemon; this widget only polls and
// sends `rt400ctl set`.
BarWidget {
  id: root
  moduleName: "io.github.mamxalf.pccooler-rt400"

  readonly property string ctl: Quickshell.env("HOME") + "/.local/bin/rt400ctl"

  property string source: "cpu"
  property string unit: "c"
  property int fixed: 0
  property string active: "cpu"
  property string kind: "temp"
  property var rotateSources: ["cpu", "load"]
  property int rotateSeconds: 5
  property bool alert: false
  property int alertThreshold: 85
  property bool alerting: false
  property var shown: null
  property string error: ""

  // The display shows temperatures (convertible to F), percentages, or a raw
  // number; the daemon says which via `kind`.
  readonly property string label: error !== "" || shown === null
    ? "--"
    : kind === "temp"
      ? Math.round(unit === "f" ? shown * 1.8 + 32 : shown) + "°" + unit.toUpperCase()
      : kind === "percent"
        ? Math.round(shown) + "%"
        : String(Math.round(shown))

  function apply(text) {
    try {
      var s = JSON.parse(text)
      source = s.source
      unit = s.unit
      fixed = s.fixed
      active = s.active || s.source
      kind = s.kind || "temp"
      rotateSources = s.rotate_sources
      rotateSeconds = s.rotate_seconds
      alert = s.alert
      alertThreshold = s.alert_threshold
      alerting = s.alerting
      shown = s.shown
      error = s.ok ? (s.error || "") : (s.error || "error")
    } catch (e) {
      shown = null
      error = "rt400d not running"
    }
  }

  function run(args) {
    setProc.command = [ctl].concat(args)
    setProc.running = true
  }

  function setSource(value) { run(["set", "--source", value]) }
  function setUnit(value) { run(["set", "--unit", value]) }
  function setFixed(value) { run(["set", "--fixed", String(value)]) }
  function setRotateSources(list) { run(["set", "--rotate-sources", list.join(",")]) }
  function setRotateSeconds(value) { run(["set", "--rotate-seconds", String(value)]) }
  function setAlert(on) { run(["set", "--alert", on ? "on" : "off"]) }
  function setAlertThreshold(value) { run(["set", "--alert-threshold", String(value)]) }

  // ---- Settings popup. Bar.findPanelWidget requires open/close/opened on
  //      the bar-widget root, so they are forwarded to the loaded panel.
  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false
  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false

  function open() { if (panelLoader.item) panelLoader.item.open() }
  function close() { if (panelLoader.item) panelLoader.item.close() }
  function togglePanel() { if (panelLoader.item) panelLoader.item.toggle() }
  function closeForPopoutSwitch() { if (panelLoader.item) panelLoader.item.closeForPopoutSwitch() }

  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
  }

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  IpcHandler {
    target: "io.github.mamxalf.pccooler-rt400"

    function open(): void { root.open() }
    function close(): void { root.close() }
    function toggle(): void { root.togglePanel() }
  }

  Process {
    id: statusProc
    command: [root.ctl, "status"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.apply(text)
    }
    onExited: function(code) { if (code !== 0) root.apply("") }
  }

  Process {
    id: setProc
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.apply(text)
    }
  }

  Timer {
    interval: 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: if (!statusProc.running) statusProc.running = true
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "󰈐 " + root.label
    hasVisualContent: true
    tooltipText: "RT400 display: "
      + (root.source === "rotate" ? "ROTATE (" + root.active.toUpperCase() + ")" : root.active.toUpperCase())
      + (root.alerting ? " - OVER LIMIT" : "")
      + (root.error !== "" ? " (" + root.error + ")" : "")

    onPressed: function(b) { root.togglePanel() }
  }
}
