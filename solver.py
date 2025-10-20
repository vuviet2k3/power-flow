__author__ = 'Vu Van Viet'
__email__ = 'vuvanviet2k3@gmail.com'
__address__ = 'OAEM Lab'
__version__ = '1.0.0'

#-------------------------------------------------

import tkinter as tk
from tkinter import messagebox


# warning
def warning(title):
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("ERROR", title)


class PSM:
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
        YEU CAU : thong so he don vi TUONG DOI - p.u
        abus    : {busID: [pLoad, qLoad]}
        aslack  : {busID: [vGen, aGen]}
        apv     : {busID: [vGen, pGen]}
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
        #
        self.aline = aline
        self.atrf2 = atrf2
        self.ashunt = ashunt
        self.nMax = nMax
        self.Eps = Eps

        self.solve()


    #  check source
    def check_source(self, gen):
        visited = set()
        visitID = set()



    # check loop
    def check_loop(self, slack):
        """
        CHECK LOOP: THUAT TOAN DFS ket hop de quy
        return True -> LOOP
        return False -> NO LOOP
        """
        visited = set()
        visitID = set()
        #
        def dfs(node, parent):
            visited.add(node)
            for line in self.brnC1[node]:
                if line in visitID:
                    continue
                visitID.add(line)
                bus1, bus2 = self.brnC0[line]
                bus = bus1 if bus1 != node else bus2
                if bus in visited and bus != parent:
                    return True
                if dfs(bus, node):
                    return True
            return False

        return dfs(slack, None)

    # mapping
    def mapping(self, slack):
        mapping = set()
        visited = set()

        def dfs(bus):
            mapping.add(bus)
            for line in self.brnC1[bus]:
                if line not in visited:
                    visited.add(line)
                    v1, v2 = self.brnC0[line]
                    v = v1 if v1 != bus else v2
                    dfs(v)

        dfs(slack)
        return mapping

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

    def backward_sweep(self, ubus, sbus, slack, re_mapping):
        """
        Tinh dong cong suat nguoc - backward sweep

        :return -> sbrn1
        """
        sbrn1 = {}
        sbrn2 = {}
        visited = set()

        def dfs(lineID, visited):
            fromline = int()
            toline = list()
            for line in lineID:
                if line not in visited:
                    fromline = line
                else:
                    toline.append(line)
            return fromline, toline

        for bus in re_mapping:
            if bus == slack:
                break
            lineID = self.brnC1[bus]
            fromline, toline = dfs(lineID, visited)
            sbrn2[fromline] = sbus[bus]
            for line in toline:
                sbrn2[fromline] += sbrn1[line]
            sbrn1[fromline] = sbrn2[fromline] +abs(sbrn2[fromline])**2 / abs(ubus[bus])**2 * self.aline[fromline][0]
            visited.add(fromline)

        return sbrn1


    def forward_sweep(self, ubus, sbrn1, mapping):
        """
        Tinh dien ap thuan - forward sweep

        :return -> ubus
        """
        ubusN=  ubus.copy()
        visited = set()
        #
        for bus in mapping:
            lineID = self.brnC1[bus]
            for line in lineID:
                if line not in visited:
                    v = self.brnC0[line]
                    b1, b2 = v[0], v[1]
                    b = b1 if b1 != bus else b2
                    ubusN[b] = ubusN[bus] - sbrn1[line].conjugate() * self.aline[line][0] / ubusN[bus].conjugate()
                    visited.add(line)

        return ubusN

    def epsilon(self, ubus, ubusN):
        for k, v in ubus.items():
            real1, imag1 = ubus[k].real, ubus[k].imag
            real2, imag2 = ubusN[k].real, ubusN[k].imag
            eps = max(abs(real1 - real2), abs(imag1 - imag2))
            if eps > self.Eps:
                return False
        return True


    def solve(self):
        for k, v in self.aslack.items():
            slack = k
            param = v

        # check_source

        # check_loop
        if self.check_loop(slack=slack):
            title = 'LOOP DETECTED IN THE NETWORK. PLEASE USE A DIFFERENT METHOD.'
            warning(title)
            return None

        # mapping for grid
        mapping = list(self.mapping(slack=slack))
        re_mapping = mapping[::-1]

        # in
        ubus = {}
        for k, v in self.abus.items():
            ubus[k] = complex(1, 0)

        # solver
        for iter in range(1, self.nMax+1):
            if iter == self.nMax:
                title = 'KHONG HOI TU'
                warning(title)
                return None

            sbus = self.power_shunt(ubus)
            sbrn1 = self.backward_sweep(ubus, sbus, slack, re_mapping)
            ubusN = self.forward_sweep(ubus, sbrn1, mapping)

            if self.epsilon(ubus, ubusN):
                return ubusN
            else:
                print(ubusN)
                ubus = ubusN.copy()
                iter += 1


class NR:
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
        YEU CAU : thong so he don vi TUONG DOI - p.u
        abus    : {busID: [pLoad, qLoad]}
        aslack  : {busID: [vGen, aGen]}
        apv     : {busID: [vGen, pGen]}
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
        #
        self.aline = aline
        self.atrf2 = atrf2
        self.ashunt = ashunt
        self.nMax = nMax
        self.Eps = Eps

        self.solve()

    def Ybus(self):
        bus = list(self.brnC1.keys())
        n = len(self.brnC0.keys())
        visited = set()

        Ybus = [[0]*n]*n
        for k, v in self.brnC1.items():
            i = bus.index(k)
            for line in v:
                # line
                if line < n:
                    v1 = self.aline[line]
                    Ybus[i][i] += 1/v1[0] + v1[1]/2

                    if line not in visited:
                        v2 = self.brnC0[line]
                        node = v2[0] if v2[0] != bus else v2[1]
                        j = bus.index(node)
                        Ybus[i][j] = -1/v1[0]
                        Ybus[j][i] = Ybus[i][j]
                        visited.add(line)
                # trf2
                elif line > n:
                    v1 = self.atrf2[line]
                    Ybus[i][i] += 1/v1[1]
                    if v1[0] == bus:
                        Ybus[i][i] += v1[2]

                    if line not in visited:
                        v2 = self.brnC1[line]
                        node = v2[0] if v2[0] != bus else v2[1]
                        j = bus.index(node)
                        Ybus[i][j] = -1/v[1]
                        Ybus[j][i] = Ybus[i][j]
                        visited.add(line)










    def solve(self):
        self.Ybus()



if __name__=='__main__':
    brnC0 = {1: [1, 2], 2: [2, 3], 3: [3, 4], 4: [4, 5], 5: [3, 6], 6: [6, 7], 7: [6, 8], 8: [4, 8], 9: [8, 9]}
    brnC1 = {1: [1], 2: [1, 2], 3: [2, 5, 3], 4: [3, 8, 4], 5: [4], 6: [5, 6], 7: [6], 8: [8, 9], 9: [9]}
    print(brnC0.values())
#
#     nr = NR(brnC0=brnC0, brnC1=brnC1)
