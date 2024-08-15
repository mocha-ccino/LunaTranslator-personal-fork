import threading, gobject, queue
import sqlite3, json
from traceback import print_exc
from myutils.config import globalconfig, savehook_new_data
from myutils.utils import autosql


class basetext:
    autofindpids = True

    def gettextonce(self):
        return None

    def init(self): ...
    def end(self): ...

    def __init__(self):
        self.pids = []
        self.gameuid = None
        #

        self.textgetmethod = gobject.baseobject.textgetmethod

        self.ending = False
        self.sqlqueue = None
        self.init()

    def startsql(self, sqlfname_all):
        self.sqlqueueput(None)
        self.sqlqueue = queue.Queue()
        try:

            # self.sqlwrite=sqlite3.connect(self.sqlfname,check_same_thread = False, isolation_level=None)
            self.sqlwrite2 = autosql(
                sqlite3.connect(
                    sqlfname_all, check_same_thread=False, isolation_level=None
                )
            )
            # try:
            #     self.sqlwrite.execute('CREATE TABLE artificialtrans(id INTEGER PRIMARY KEY AUTOINCREMENT,source TEXT,machineTrans TEXT,userTrans TEXT);')
            # except:
            #     pass
            try:
                self.sqlwrite2.execute(
                    "CREATE TABLE artificialtrans(id INTEGER PRIMARY KEY AUTOINCREMENT,source TEXT,machineTrans TEXT,origin TEXT);"
                )
            except:
                pass
        except:
            print_exc()
        threading.Thread(target=self.sqlitethread).start()

    def dispatchtext(self, text):
        if self.ending or not self.isautorunning:
            return
        if isinstance(text, tuple):
            self.textgetmethod(*text)
        else:
            self.textgetmethod(text)

    def waitfortranslation(self, text):
        resultwaitor = queue.Queue()
        self.dispatchtext((text, True, resultwaitor.put, True))
        text, info = resultwaitor.get(), 0
        if info:
            gobject.baseobject.displayinfomessage(text, info)
        else:
            return text

    @property
    def isautorunning(self):
        return globalconfig["autorun"]

    ##################
    def endX(self):
        self.ending = True
        self.sqlqueueput(None)
        self.end()

    def sqlqueueput(self, xx):
        try:
            self.sqlqueue.put(xx)
        except:
            pass

    def sqlitethread(self):
        while not self.ending:
            task = self.sqlqueue.get()
            if not task:
                break
            try:
                if len(task) == 2:
                    src, origin = task
                    lensrc = len(src)
                    ret = self.sqlwrite2.execute(
                        "SELECT * FROM artificialtrans WHERE source = ?", (src,)
                    ).fetchone()
                    try:
                        savehook_new_data[self.gameuid]["statistic_wordcount"] += lensrc
                    except:
                        pass
                    if ret is None:
                        try:
                            self.sqlwrite2.execute(
                                "INSERT INTO artificialtrans VALUES(NULL,?,?,?);",
                                (src, json.dumps({}), origin),
                            )
                        except:
                            self.sqlwrite2.execute(
                                "INSERT INTO artificialtrans VALUES(NULL,?,?);",
                                (src, json.dumps({})),
                            )
                        try:
                            savehook_new_data[self.gameuid][
                                "statistic_wordcount_nodump"
                            ] += lensrc
                        except:
                            pass
                elif len(task) == 3:
                    src, clsname, trans = task
                    ret = self.sqlwrite2.execute(
                        "SELECT machineTrans FROM artificialtrans WHERE source = ?",
                        (src,),
                    ).fetchone()
                    ret = json.loads((ret[0]))
                    ret[clsname] = trans
                    ret = json.dumps(ret, ensure_ascii=False)
                    self.sqlwrite2.execute(
                        "UPDATE artificialtrans SET machineTrans = ? WHERE source = ?",
                        (ret, src),
                    )
            except:
                print_exc()

    def runonce(self):
        t = self.gettextonce()
        if t:
            self.textgetmethod(t, False)
