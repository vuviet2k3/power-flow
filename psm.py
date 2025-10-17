__author__ = 'Vu Van Viet'
__email__ = 'vuvanviet2k3@gmail.com'
__address__ = 'OAEM Lab'
__version__ = '1.0.0'

#-------------------------------------------------

import tkinter as tk
from tkinter import messagebox
import numpy as np
import cmath, math

from matplotlib.pyplot import title


# warning
def warning(title):
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("ERROR", title)


# brnC0 = {1: [1, 2], 2: [2, 3], 3: [3, 4], 4: [4, 5], 5: [3, 6], 6: [6, 7], 7: [6, 8], 8: [4, 8], 9: [8, 9]}
# brnC1 = {1: [1], 2: [1, 2], 3: [2, 5, 3], 4: [3, 8, 4], 5: [4], 6: [5, 6, 7], 7: [6], 8: [7, 8, 9], 9: [9]}
#
# if check_loop(brnC0, brnC1, 1):
#     print('NO LOOP')
# else:
#     print('LOOP')
#
#
# #

class Run:
    def __init__(self,
                 abus=None,
                 aslack=None,
                 brnC0=None,
                 brnC1=None,
                 aline=None,
                 atrf2=None,
                 ashunt=None,
                 nMax=200,
                 Eps=1e-5):
        """
        Run Power Summation Method - PSM
        YEU CAU : YEU CAU thong so he don vi TUONG DOI - p.u
        abus    : {busID: [pLoad, qLoad]}
        aslack  : {busID: [vGen, aGen]}
        brnC0   : {brnID: [frombus, tobus]}
        brnC1   : {bus: [brnID]}
        trf2    : ID> 100000
        aline   : {lineID: [rLine + 1j*xLine, bLine]}
        atrf2   : {x2ID: [rX2 + 1j*xX2, gX2 - 1jbX2]}
        ashunt  : {shuntID: [gShunt + 1j*bShunt]}

        :return -> ubus, abus
        """
        self.abus = abus
        self.aslack = aslack
        self.brnC0 = brnC0
        self.brnC1 = brnC1
        self.childrent = {}
        for k, v in self.brnC0.items():
            self.childrent.setdefault(v[0], []).append(v[1])
            self.childrent.setdefault(v[1], []).append(v[0])
        #
        self.aline = aline
        self.atrf2 = atrf2
        self.ashunt = ashunt
        self.nMax = nMax
        self.Eps = Eps
        print(self.brnC0)
        print(self.brnC1)
        print(self.childrent)

        # self.run()

    # check loop
    def check_loop(self, slack):
        """
        CHECK LOOP: THUAT TOAN DFS ket hop de quy
        return True -> LOOP
        return False -> NO LOOP
        """
        visited = set()
        visitid = set()

        #
        def dfs(node, parent):
            visited.add(node)
            for line in self.brnC1[node]:
                if line in visitid:
                    continue
                visitid.add(line)
                bus1, bus2 = self.brnC0[line]
                bus = bus1 if bus1 != node else bus2
                if bus in visited and bus != parent:
                    return True
                if dfs(bus, node):
                    return True
            return False

        return dfs(slack, None)

    def power_shunt(self, ubus):
        """
        Tinh toan POWER BUS co xet thanh phan SHUNT
        ubus: {busID: volt}

        :return -> sbus
        """
        sbus = {}
        for k, v in self.abus.items():
            sbus[k] = complex(v[0], v[1])
            s = complex(0, 0)
            #
            for brn in self.brnC1[k]:
                if brn in self.aline.keys():
                    line = self.aline[brn]
                    s += line[1] / 2
                #
                if brn in self.atrf2.keys():
                    x2 = self.atrf2[brn]
                    if k == x2[0]:
                        s += x2[2]
            #
            if k in self.ashunt.keys():
                s += self.ashunt[k]
            sbus[k] += s.conjugate() * abs(ubus[k]) ** 2

        return sbus

    def backward_sweep(self, ubus, sbus, slack):
        """
        Tinh dong cong suat nguoc - backward sweep

        :return -> sbrn1
        """
        sbrn1 = {}
        sbrn2 = {}
        visitID = set()
        visited = 1
        while True:
            if len(visitID) == len(self.brnC1.keys()):
                break

            for k, v in self.brnC1.items():
                if k == slack:
                    continue
                if len(v) == visited:
                    v1 = []
                    v2 = []
                    for v3 in v:
                        if v3 not in visitID:
                            v1.append(v3)
                        else:
                            v2.append(v3)
                    if len(v1) > 1:
                        continue

                    line = v1[0]
                    visitID.add(line)
                    sbrn2[line] = sbus[k]
                    if v2:
                        for v4 in v2:
                            sbrn2[line] += sbrn1[v4]
                    sbrn1[line] = sbrn2[line] + abs(sbrn2[line])**2 / abs(ubus[k])**2 * self.aline[line][0]
            visited += 1
        return sbrn1






    def forward_sweep(self, ubus):
        """
        Tinh dien ap thuan - forward sweep

        :return -> ubus
        """

        return

    def run(self):
        for k, v in self.aslack.items():
            slack = k
            param = v
        if self.check_loop(slack):
            title = 'LOOP DETECTED IN THE NETWORK. PLEASE USE A DIFFERENT METHOD.'
            warning(title)
            return None, None
        ubus = {}
        for k, v in self.abus.items():
            ubus[k] = complex(1, 0)

        sbus = self.power_shunt(ubus=ubus)
        sbus1 = self.backward_sweep(ubus=ubus, sbus=sbus, slack=slack)
        print(sbus1)


# if __name__=='__main__':
#     brnC0 = {1: [1, 2], 2: [2, 3], 3: [3, 4], 4: [4, 5], 5: [3, 6], 6: [6, 7], 7: [6, 8], 8: [4, 8], 9: [8, 9]}
#     brnC1 = {1: [1], 2: [1, 2], 3: [2, 5, 3], 4: [3, 8, 4], 5: [4], 6: [5, 6], 7: [6], 8: [8, 9], 9: [9]}
#     slack = 1
#     aline =
#     psm = Run(brnC0=brnC0, brnC1=brnC1)
#     if psm.check_loop(slack):
#         print('LOOP')
#     else:
#         print('NO LOOP')