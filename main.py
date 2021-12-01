import kazoo.client
import kazoo.protocol.states
import pendulum
import qtawesome
from PySide2 import QtWidgets, QtGui, QtCore


def expandPath(path: str, node: QtGui.QStandardItem):
    print(f"Expanding path {path}...")
    children = zk.get_children(path) if path != "" else ["/"]
    for name in children:
        childNode = QtGui.QStandardItem(name)
        childPath = f"{path}/{name}".replace("//", "/")
        stat: kazoo.protocol.states.ZnodeStat
        value, stat = zk.get(childPath)
        createdAt = pendulum.from_timestamp(stat.ctime // 1000).isoformat(" ")[:-9]
        updatedAt = pendulum.from_timestamp(stat.mtime // 1000).isoformat(" ")[:-9]
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


def calcPathFromIndex(index: QtCore.QModelIndex):
    values = []
    while index.data() is not None:
        values.append(model.index(index.row(), 0, index.parent()).data())
        index = index.parent()
    return "/".join(reversed(["" if x == "/" else x for x in values])) or "/"


def expandLeaf(index: QtCore.QModelIndex):
    print(f"Expanding leaf {index.data()}...")
    path = calcPathFromIndex(index)
    node = model.itemFromIndex(index)
    not model.hasChildren(index) and expandPath(path, node)


def refreshLeaf(index: QtCore.QModelIndex):
    print(f"Refreshing leaf {index.data()} ...")
    path = calcPathFromIndex(index)
    stat: kazoo.protocol.states.ZnodeStat
    value, stat = zk.get(path)
    createdAt = pendulum.from_timestamp(stat.ctime // 1000).isoformat(" ")[:-6]
    updatedAt = pendulum.from_timestamp(stat.mtime // 1000).isoformat(" ")[:-6]
    infoLabel.setText("\n".join([x.strip() for x in f"""
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
    global zk
    zk = kazoo.client.KazooClient(serverCombo.currentText())
    zk.start()
    refreshTree()


zk = kazoo.client.KazooClient()
app = QtWidgets.QApplication()
window = QtWidgets.QMainWindow()
splitter = QtWidgets.QSplitter(window)
treeView = QtWidgets.QTreeView(splitter)
model = QtGui.QStandardItemModel(treeView)
treeView.setModel(model)
treeView.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
treeView.setAlternatingRowColors(True)
treeView.setSelectionBehavior(QtWidgets.QTreeView.SelectRows)
treeView.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
treeView.clicked.connect(refreshLeaf)
treeView.doubleClicked.connect(expandLeaf)
detailWidget = QtWidgets.QWidget(splitter)
detailLayout = QtWidgets.QVBoxLayout(detailWidget)
detailWidget.setLayout(detailLayout)
infoLabel = QtWidgets.QLabel("\n\n\n\n\n")
pathEdit = QtWidgets.QTextEdit("path.")
valueEdit = QtWidgets.QTextEdit("value.")
detailLayout.addWidget(infoLabel, 0)
detailLayout.addWidget(pathEdit, 1)
detailLayout.addWidget(valueEdit, 2)
splitter.addWidget(treeView)
splitter.addWidget(detailWidget)
splitter.setStretchFactor(0, 2)
splitter.setStretchFactor(1, 1)
window.setWindowTitle("Ice Spring Zookeeper Explorer")
window.setCentralWidget(splitter)
window.resize(1280, 720)
window.statusBar().showMessage("Ready.")
toolbar = window.addToolBar("Toolbar")
toolbar.setMovable(False)
serverCombo = QtWidgets.QComboBox()
serverCombo.setEditable(True)
serverCombo.addItem("127.0.0.1:2181")
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
