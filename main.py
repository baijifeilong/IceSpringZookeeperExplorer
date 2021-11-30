import kazoo.client
import kazoo.protocol.states
import pendulum
import qtawesome
from PySide2 import QtWidgets, QtGui, QtCore


def processNode(zooNode: str, treeNode: QtGui.QStandardItem):
    children = zk.get_children(zooNode) if zooNode != "" else ["/"]
    for childZooNode in children:
        childTreeNode = QtGui.QStandardItem(childZooNode)
        absoluteNode = f"{zooNode}/{childZooNode}"
        stat: kazoo.protocol.states.ZnodeStat
        value, stat = zk.get(absoluteNode)
        createdAt = pendulum.from_timestamp(stat.ctime // 1000).isoformat(" ")[:-9]
        updatedAt = pendulum.from_timestamp(stat.mtime // 1000).isoformat(" ")[:-9]
        treeNode.appendRow([
            childTreeNode,
            QtGui.QStandardItem(createdAt),
            QtGui.QStandardItem(updatedAt),
            QtGui.QStandardItem(value.decode()),
        ])
        processNode(absoluteNode, childTreeNode)


def refreshTree():
    print("refreshing...")
    model.clear()
    model.setHorizontalHeaderLabels(["Path", "Created", "Updated", "Value"])
    processNode("", model)
    treeView.header().setDefaultSectionSize(220)
    treeView.header().stretchLastSection()
    treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
    treeView.expandAll()
    refreshLeaf(model.index(0, 0))


def refreshLeaf(index: QtCore.QModelIndex):
    values = []
    while index.data() is not None:
        values.append(model.index(index.row(), 0, index.parent()).data())
        index = index.parent()
    path = "/".join(reversed(["" if x == "/" else x for x in values])) or "/"
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


def popDialog():
    dialog = QtWidgets.QInputDialog(parent=window)
    dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
    dialog.setWindowTitle("Connect to Zookeeper server")
    dialog.setLabelText("Please input <host:port>")
    dialog.setTextValue("127.0.0.1:2181")
    dialog.resize(500, 0)
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return
    global zk
    zk = kazoo.client.KazooClient(dialog.textValue())
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
detailWidget = QtWidgets.QWidget(splitter)
detailLayout = QtWidgets.QVBoxLayout(detailWidget)
detailWidget.setLayout(detailLayout)
infoLabel = QtWidgets.QLabel("\n\n\n\n\n")
pathEdit = QtWidgets.QTextEdit("path.")
valueEdit = QtWidgets.QTextEdit("value.")
detailLayout.addWidget(infoLabel)
detailLayout.addWidget(pathEdit)
detailLayout.addWidget(valueEdit)
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
action = QtWidgets.QAction(qtawesome.icon("mdi.connection"), "Connect", toolbar)
action.triggered.connect(popDialog)
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
