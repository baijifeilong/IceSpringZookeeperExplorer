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
    treeView.header().setDefaultSectionSize(200)
    treeView.header().stretchLastSection()
    treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
    treeView.expandAll()
    detailLabel.setText("Ready.")


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
    detailLabel.setText("\n".join([x.strip() for x in f"""
    Path: {path}
    Value: {value.decode()}
    Created At: {createdAt}
    Updated At: {updatedAt}
    czxid: {stat.czxid}
    mzxid: {stat.mzxid}
    pzxid: {stat.pzxid}
    version: {stat.version}
    cversion: {stat.cversion}
    aversion: {stat.aversion}
    ephemeralOwner: {stat.ephemeralOwner}
    dataLength: {stat.dataLength}
    numChildren: {stat.numChildren}
    """.strip().splitlines()]))


zk = kazoo.client.KazooClient()
zk.start()
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
detailLabel = QtWidgets.QLabel("Ready.")
detailLayout.addWidget(detailLabel)
splitter.addWidget(treeView)
splitter.addWidget(detailWidget)
window.setWindowTitle("Zookeeper Explorer")
window.setCentralWidget(splitter)
window.resize(1280, 720)
window.statusBar().showMessage("Ready.")
toolbar = window.addToolBar("Toolbar")
toolbar.setMovable(False)
action = QtWidgets.QAction(qtawesome.icon("fa.refresh"), "Refresh", toolbar)
action.triggered.connect(refreshTree)
toolbar.addAction(action)
window.show()
font = app.font()
font.setPointSize(12)
app.setFont(font)
refreshTree()
app.exec_()
