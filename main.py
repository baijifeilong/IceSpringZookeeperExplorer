import kazoo.client
import kazoo.protocol.states
import pendulum
from PySide2 import QtWidgets, QtGui, QtCore

zk = kazoo.client.KazooClient()
zk.start()
zk.delete("/1", recursive=True)
zk.delete("/2", recursive=True)
zk.ensure_path("/Animals/Elephant")
zk.ensure_path("/Animals/Dolphin")
zk.ensure_path("/Animals/Monkey")
zk.ensure_path("/Animals/Monkey/BetaMonkey")
zk.ensure_path("/Animals/Monkey/GammaMonkey")
zk.ensure_path("/Animals/Monkey/AlphaMonkey")
zk.ensure_path("/Fruits/Watermelon")
zk.ensure_path("/Fruits/Banana")
zk.ensure_path("/Fruits/Orange")
zk.ensure_path("/Fruits/Apple")
zk.ensure_path("/Vegetables/Broccoli")
zk.ensure_path("/Vegetables/Tomato")
zk.ensure_path("/Vegetables/Potato")
zk.ensure_path("/Vegetables/Union")
zk.ensure_path("/Vegetables/Cucumber")
zk.set("/Animals/Dolphin", b"This is a dolphin")
zk.set("/Vegetables/Potato", b"This is a potato")

print(zk.get_children("/Fruits"))
print(zk.get("/Fruits"))


def refreshNode(zooNode: str, treeNode: QtGui.QStandardItem):
    for childZooNode in zk.get_children(zooNode):
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
        refreshNode(absoluteNode, childTreeNode)


def refresh():
    model.clear()
    model.setHorizontalHeaderLabels(["Path", "Created", "Updated", "Value"])
    refreshNode("/", model)
    treeView.setAlternatingRowColors(True)
    treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
    treeView.header().setDefaultSectionSize(200)
    treeView.header().stretchLastSection()
    treeView.setSelectionBehavior(QtWidgets.QTreeView.SelectRows)
    treeView.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
    treeView.expandAll()


app = QtWidgets.QApplication()
window = QtWidgets.QMainWindow()
splitter = QtWidgets.QSplitter(window)
treeView = QtWidgets.QTreeView(splitter)
model = QtGui.QStandardItemModel(treeView)
treeView.setModel(model)
treeView.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
treeView.expandAll()
detailWidget = QtWidgets.QWidget(splitter)
detailLayout = QtWidgets.QVBoxLayout(detailWidget)
detailWidget.setLayout(detailLayout)
detailLayout.addWidget(QtWidgets.QLabel("Ready."))
splitter.addWidget(treeView)
splitter.addWidget(detailWidget)
window.setWindowTitle("Zookeeper Explorer")
window.setCentralWidget(splitter)
window.resize(1280, 720)
window.statusBar().showMessage("Ready.")
toolbar = window.addToolBar("Toolbar")
toolbar.setMovable(False)
action = QtWidgets.QAction("Refresh", toolbar)
action.triggered.connect(refresh)
toolbar.addAction(action)
window.show()
font = app.font()
font.setPointSize(12)
app.setFont(font)
refresh()
app.exec_()
