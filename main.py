import pathlib

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
        title = name if stat.numChildren == 0 else f"{name} [{stat.numChildren}]"
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
    pathEdit.setText(path)
    valueEdit.setText(value.decode() or "<EMPTY>")


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


zk = kazoo.client.KazooClient()
app = QtWidgets.QApplication()
window = QtWidgets.QMainWindow()
mainSplitter = QtWidgets.QSplitter(window)
treeView = QtWidgets.QTreeView(mainSplitter)
model = QtGui.QStandardItemModel(treeView)
treeView.setModel(model)
treeView.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
treeView.setAlternatingRowColors(True)
treeView.setSelectionBehavior(QtWidgets.QTreeView.SelectRows)
treeView.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
treeView.clicked.connect(refreshLeaf)
treeView.doubleClicked.connect(expandLeaf)
infoEdit = QtWidgets.QTextEdit("\n\n\n\n\n")
pathEdit = QtWidgets.QTextEdit("path.")
valueEdit = QtWidgets.QTextEdit("value.")
detailSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, mainSplitter)
detailSplitter.addWidget(infoEdit)
detailSplitter.addWidget(pathEdit)
detailSplitter.addWidget(valueEdit)
detailSplitter.setStretchFactor(1, 1)
detailSplitter.setStretchFactor(2, 2)
mainSplitter.addWidget(treeView)
mainSplitter.addWidget(detailSplitter)
mainSplitter.setStretchFactor(0, 2)
mainSplitter.setStretchFactor(1, 1)
window.setWindowTitle("Ice Spring Zookeeper Explorer")
window.setCentralWidget(mainSplitter)
window.resize(1280, 720)
window.statusBar().showMessage("Ready.")
toolbar = window.addToolBar("Toolbar")
toolbar.setMovable(False)
configPath = pathlib.Path("servers.txt")
configPath.touch(exist_ok=True)
servers = [x.strip() for x in configPath.read_text().splitlines() if x.strip()] or ["127.0.0.1:2181"]
serverCombo = QtWidgets.QComboBox()
serverCombo.setEditable(True)
[serverCombo.addItem(server) for server in servers]
toolbar.addWidget(serverCombo)
action = QtWidgets.QAction(qtawesome.icon("mdi.connection"), "Connect", toolbar)
action.triggered.connect(doConnect)
toolbar.addAction(action)
action = QtWidgets.QAction(qtawesome.icon("fa.refresh"), "Refresh", toolbar)
action.triggered.connect(refreshTree)
toolbar.addAction(action)
window.show()
font = app.font()
font.setPointSize(12)
app.setFont(font)
app.setWindowIcon(qtawesome.icon("mdi.elephant"))
app.exec_()
