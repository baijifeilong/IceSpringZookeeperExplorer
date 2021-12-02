import json
import pathlib
import urllib.parse

import kazoo.client
import kazoo.protocol.states
import pendulum
import qtawesome
from PySide2 import QtWidgets, QtGui, QtCore


def expandPath(path: str, node: QtGui.QStandardItem):
    print(f"Expanding path {path}...")
    children = zk.get_children(path) if path != "" else ["/"]
    for name in sorted(children):
        childPath = f"{path}/{name}".replace("//", "/")
        stat: kazoo.protocol.states.ZnodeStat
        value, stat = zk.get(childPath)
        createdAt = pendulum.from_timestamp(stat.ctime // 1000).isoformat(" ")[:-9]
        updatedAt = pendulum.from_timestamp(stat.mtime // 1000).isoformat(" ")[:-9]
        unquotedName = urllib.parse.unquote(name)
        title = unquotedName if stat.numChildren == 0 else f"{unquotedName} [{stat.numChildren}]"
        childNode = QtGui.QStandardItem(title)
        childNode.setData(childPath, QtCore.Qt.UserRole)
        node.appendRow([
            childNode,
            QtGui.QStandardItem(createdAt),
            QtGui.QStandardItem(updatedAt),
            QtGui.QStandardItem(value.decode()),
        ])
        name == "/" and expandPath(childPath, childNode)
    path == "" and treeView.expand(model.index(0, 0))


def refreshTree():
    print("Refreshing tree...")
    model.clear()
    model.setHorizontalHeaderLabels(["Path", "Created", "Updated", "Value"])
    expandPath("", model)
    treeView.header().setDefaultSectionSize(220)
    treeView.header().stretchLastSection()
    treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
    refreshLeaf(model.index(0, 0))


def expandLeaf(index: QtCore.QModelIndex):
    print(f"Expanding leaf {index.data()}...")
    index = model.index(index.row(), 0, index.parent())
    path = model.itemFromIndex(index).data(QtCore.Qt.UserRole)
    node = model.itemFromIndex(index)
    not model.hasChildren(index) and expandPath(path, node)


def refreshLeaf(index: QtCore.QModelIndex):
    print(f"Refreshing leaf {index.data()} ...")
    index = model.index(index.row(), 0, index.parent())
    path = model.itemFromIndex(index).data(QtCore.Qt.UserRole)
    stat: kazoo.protocol.states.ZnodeStat
    value, stat = zk.get(path)
    createdAt = pendulum.from_timestamp(stat.ctime // 1000).isoformat(" ")[:-6]
    updatedAt = pendulum.from_timestamp(stat.mtime // 1000).isoformat(" ")[:-6]
    infoEdit.setText("\n".join([x.strip() for x in f"""
    ctime: {createdAt}
    mtime: {updatedAt}
    czxid: {stat.czxid} mzxid: {stat.mzxid}
    pzxid: {stat.pzxid} version: {stat.version} 
    cversion: {stat.cversion} aversion: {stat.aversion}
    ephemeralOwner: {stat.ephemeralOwner}
    """.strip().splitlines()]))
    pathEdit.setProperty("raw", path)
    refreshPath()
    valueEdit.setProperty("raw", value.decode())
    refreshValue()


def doConnect():
    global zk, servers
    server = serverCombo.currentText()
    server = server if ":" in server else f"{server}:2181"
    zk = kazoo.client.KazooClient(server)
    zk.start()
    server not in servers and serverCombo.insertItem(0, server)
    servers = list(dict.fromkeys([server] + servers))
    configPath.write_text("\n".join(servers))
    refreshTree()


def convertText(raw: str, type: str) -> str:
    if type == "URL":
        text = urllib.parse.unquote(raw)
        parts = text.split("?")
        prefix = parts[0]
        jd = dict(urllib.parse.parse_qsl(parts[-1]))
        query = "\n".join(f"    {k} = {v}" for k, v in jd.items())
        return "\n".join((prefix, query)).strip()
    if type == "JSON":
        return json.dumps(json.loads(raw), ensure_ascii=False, indent=4)
    return raw


def convertTextOrIllegal(raw: str, type: str) -> str:
    try:
        return convertText(raw, type)
    except json.decoder.JSONDecodeError:
        return "<ILLEGAL JSON>"


def detectType(text: str) -> str:
    if text.startswith("{") or text.startswith("["):
        return "JSON"
    if "?" in urllib.parse.unquote(text):
        return "URL"
    return "Raw"


def refreshPath():
    raw = pathEdit.property("raw") or ""
    type = pathRadioGroup.checkedButton().text()
    type = detectType(raw) if type == "Auto" else type
    text = convertTextOrIllegal(raw, type)
    pathEdit.setText(text)


def refreshValue():
    raw = valueEdit.property("raw") or ""
    type = valueRadioGroup.checkedButton().text()
    type = detectType(raw) if type == "Auto" else type
    text = convertTextOrIllegal(raw, type)
    valueEdit.setText(text or "<EMPTY>")


zk = kazoo.client.KazooClient()
app = QtWidgets.QApplication()
app.setWindowIcon(qtawesome.icon("mdi.elephant"))
font = app.font()
font.setPointSize(12)
app.setFont(font)

window = QtWidgets.QMainWindow()
mainSplitter = QtWidgets.QSplitter(window)
window.setWindowTitle("Ice Spring Zookeeper Explorer")
window.setCentralWidget(mainSplitter)
window.statusBar().showMessage("Ready.")
window.resize(1280, 720)
window.show()

treeView = QtWidgets.QTreeView(mainSplitter)
detailSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, mainSplitter)
mainSplitter.addWidget(treeView)
mainSplitter.addWidget(detailSplitter)
mainSplitter.setStretchFactor(0, 2)
mainSplitter.setStretchFactor(1, 1)

model = QtGui.QStandardItemModel(treeView)
treeView.setModel(model)
treeView.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
treeView.setAlternatingRowColors(True)
treeView.setSelectionBehavior(QtWidgets.QTreeView.SelectRows)
treeView.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
treeView.clicked.connect(refreshLeaf)
treeView.doubleClicked.connect(expandLeaf)

infoEdit = QtWidgets.QTextEdit("\n\n\n\n\n")
pathWidget = QtWidgets.QWidget(detailSplitter)
valueWidget = QtWidgets.QWidget(detailSplitter)
detailSplitter.addWidget(infoEdit)
detailSplitter.addWidget(pathWidget)
detailSplitter.addWidget(valueWidget)
detailSplitter.setStretchFactor(1, 1)
detailSplitter.setStretchFactor(2, 2)

pathLayout = QtWidgets.QVBoxLayout(pathWidget)
pathLayout.setMargin(0)
pathLayout.setSpacing(0)
pathWidget.setLayout(pathLayout)
pathEdit = QtWidgets.QTextEdit("path.")
pathRadioLayout = QtWidgets.QHBoxLayout(pathWidget)
pathLayout.addWidget(pathEdit)
pathLayout.addLayout(pathRadioLayout)
pathAutoRadio = QtWidgets.QRadioButton("Auto", pathWidget)
pathAutoRadio.setChecked(True)
pathRawRadio = QtWidgets.QRadioButton("Raw", pathWidget)
pathUrlRadio = QtWidgets.QRadioButton("URL", pathWidget)
pathRadioGroup = QtWidgets.QButtonGroup(pathLayout)
pathRadioGroup.buttonClicked.connect(refreshPath)
for radio in pathAutoRadio, pathRawRadio, pathUrlRadio:
    pathRadioLayout.addWidget(radio)
    pathRadioGroup.addButton(radio)
pathRadioLayout.addStretch()

valueLayout = QtWidgets.QVBoxLayout(valueWidget)
valueLayout.setMargin(0)
valueLayout.setSpacing(0)
valueWidget.setLayout(valueLayout)
valueEdit = QtWidgets.QTextEdit("value.")
valueRadioLayout = QtWidgets.QHBoxLayout(valueWidget)
valueLayout.addWidget(valueEdit)
valueLayout.addLayout(valueRadioLayout)
valueAutoRadio = QtWidgets.QRadioButton("Auto", valueWidget)
valueAutoRadio.setChecked(True)
valueRawRadio = QtWidgets.QRadioButton("Raw", valueWidget)
valueJsonRadio = QtWidgets.QRadioButton("JSON", valueWidget)
valueRadioGroup = QtWidgets.QButtonGroup(valueLayout)
valueRadioGroup.buttonClicked.connect(refreshValue)
for radio in valueAutoRadio, valueRawRadio, valueJsonRadio:
    valueRadioLayout.addWidget(radio)
    valueRadioGroup.addButton(radio)
valueRadioLayout.addStretch()

toolbar = window.addToolBar("Toolbar")
toolbar.setMovable(False)
serverCombo = QtWidgets.QComboBox()
connectAction = QtWidgets.QAction(qtawesome.icon("mdi.connection"), "Connect", toolbar)
connectAction.triggered.connect(doConnect)
refreshAction = QtWidgets.QAction(qtawesome.icon("fa.refresh"), "Refresh", toolbar)
refreshAction.triggered.connect(refreshTree)
toolbar.addWidget(serverCombo)
toolbar.addAction(connectAction)
toolbar.addAction(refreshAction)

configPath = pathlib.Path("servers.txt")
configPath.touch(exist_ok=True)
servers = [x.strip() for x in configPath.read_text().splitlines() if x.strip()] or ["127.0.0.1:2181"]
serverCombo.setEditable(True)
[serverCombo.addItem(server) for server in servers]

app.exec_()
