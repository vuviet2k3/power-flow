__author__  = 'Vu Van Viet'
__email__   = 'vuvanviet2k3@gmail.com'
__date__    = 'HUST/2025'

"""
10/10/25: 
    Chua fix MBA 3 cuon day cho NR [idea: convert 3 nut -> 4 nut]
    Da test voi pss/e grid 3 bus: eps = 0
"""
#-------------------------------------------------

import tkinter as tk
from tkinter import messagebox
import numpy as np


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
                if brn in self.aline:
                    line = self.aline[brn]
                    s += line[1] / 2
                #
                if brn in self.atrf2:
                    x2 = self.atrf2[brn]
                    if k == x2[0]:
                        s += x2[2]
            #
            if k in self.ashunt:
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
        ubus[slack] = complex(param[0], param[1])

        # solve
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
                 apv=None,
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
        self.apv = apv
        self.brnC0 = brnC0
        self.brnC1 = brnC1
        #
        self.aline = aline
        self.atrf2 = atrf2
        self.ashunt = ashunt
        self.nMax = nMax
        self.Eps = Eps

        # self.solve()
        self.Ybus()

    def Ybus(self):
        bus = list(self.abus.keys())
        n = len(bus)
        bus_idx = {bus[i]: i for i in range(n)}
        Y = np.zeros((n, n), dtype=complex)

        for line, v in self.brnC0.items():
            b1, b2 = v[0], v[1]
            i, j = bus_idx[b1], bus_idx[b2]
            # line
            if line in self.aline:
                z, b = self.aline[line]
                y = 1 / z

                Y[i, i] += y + b/2
                Y[j, j] += y + b/2
                Y[i, j] -= y
                Y[j, i] -= y
            # trf2
            if line in self.atrf2:
                b_ref, z, shunt = self.atrf2[line]
                y = 1 / z

                Y[i, i] += y
                Y[j, j] += y
                Y[i, j] -= y
                Y[j, i] -= y
                if b_ref == b1:
                    Y[i, i] += shunt
                elif b_ref == b2:
                    Y[j, j] += shunt
            # shunt
            if b1 in self.ashunt:
                v = self.ashunt[b1]
                Y[i, i] += v
            elif b2 in self.ashunt:
                v = self.ashunt[b2]
                Y[j, j] += v

        print(Y)
        return Y

    def Jacobi(self, ubus, abus, Ybus, slackID, pvID):
        bus = list(self.abus.keys())
        n = len(bus)
        bus_idx = {bus[i]:i for i in range(n)}
        J1 = np.zeros((n, n), dtype=float)
        J2 = np.zeros((n, n), dtype=float)
        J3 = np.zeros((n, n), dtype=float)
        J4 = np.zeros((n, n), dtype=float)

        # J1
        for line, v in self.brnC0.items():
            b1, b2 = v[0], v[1]
            i, j = bus_idx[b1], bus_idx[b2]
            u1, u2 = abs(ubus[i]), abs(ubus[j])
            a1, a2 = abus[i], abus[j]
            sl, genr = int(), list()
            sl = slackID[0]
            genr.append(sl)
            for pv in pvID:
                genr.append(bus_idx[pv])

            Yij, aij = abs(Ybus[i, j]), np.angle(Ybus[i, j])
            Yii, aii = abs(Ybus[i, i]), np.angle(Ybus[i, i])
            Yjj, ajj = abs(Ybus[j, j]), np.angle(Ybus[j, j])

            # J1
            J1[i, i] += u1 * u2 * Yij * np.sin(aij - a1 + a2)
            J1[j ,j] += u2 * u1 * Yij * np.sin(aij - a2 + a1)
            J1[i, j] = -u1 * u2 * Yij * np.sin(aij - a1 + a2)
            J1[j, i] = -u2 * u1 * Yij * np.sin(aij - a2 + a1)

            # J2
            if J2[i ,i] == 0:
                J2[i ,i] = 2 * u1 * Yii * np.cos(aii)
            if J2[j ,j] == 0:
                J2[j, j] = 2 * u2 * Yjj * np.cos(ajj)
            J2[i, i] += u2 * Yij * np.cos(aij - a1 + a2)
            J2[j, j] += u1 * Yij * np.cos(aij - a2 + a1)
            J2[i, j] = u2 * Yij * np.cos(aij - a1 + a2)
            J2[j, i] = u1 * Yij * np.cos(aij - a2 + a1)

            # J3
            J3[i, i] += u1 * u2 * Yij * np.cos(aij - a1 + a2)
            J3[j ,j] += u2 * u1 * Yij * np.cos(aij - a2 + a1)
            J3[i, j] = -u1 * u2 * Yij * np.cos(aij - a1 + a2)
            J3[j, i] = -u2 * u1 * Yij * np.cos(aij - a2 + a1)

            # J4
            if J4[i ,i] == 0:
                J4[i ,i] = -2 * u1 * Yii * np.sin(aii)
            if J4[j ,j] == 0:
                J4[j, j] = -2 * u2 * Yjj * np.cos(ajj)
            J4[i, i] -= u2 * Yij * np.sin(aij - a1 + a2)
            J4[j, j] -= u1 * Yij * np.sin(aij - a2 + a1)
            J4[i, j] = -u2 * Yij * np.sin(aij - a1 + a2)
            J4[j, i] = -u1 * Yij * np.sin(aij - a2 + a1)

        J1 = np.delete(np.delete(J1, obj=sl, axis=0), obj=pv, axis=1) # xoa hang, cot
        J2 = np.delete(J2, obj=sl, axis=0)
        J3 =np.delete(np.delete(J3, obj=pv, axis=0), obj=pv, axis=1)
        J4 = np.delete(J4, obj=pv, axis=0)
        J = np.vstack((np.hstack((J1, J2)), np.hstack((J3, J4))))
        return J

    def power_bus(self, ubus, abus, Ybus, slackID, pvID):
        bus = list(ubus.keys())
        n = len(ubus)
        bus_idx = {bus[i]: i for i in range(n)}
        P = np.zeros(n, dtype=float)
        Q = np.zeros(n, dtype=float)
        sl, pv = int(), list()
        sl = slackID[0]
        pv.append(sl)
        for pv in pvID:
            pv.append(bus_idx[pv])

        for line, v in self.brnC0.items():
            b1, b2 = v[0], v[1]
            i, j = bus_idx[b1], bus_idx[b2]
            ui, uj = abs(ubus[i]), abs(ubus[j])
            ai, aj = abus[i], abus[j]
            Yij, aij = abs(Ybus[i, j]), np.angle(Ybus[i, j])

            P[i] += ui * uj * Yij * np.cos(aij - ai + aj)
            P[j] += uj * ui * Yij * np.cos(aij - aj + ai)
            Q[i] -= ui * uj * Yij * np.sin(aij - ai + aj)
            Q[j] -= uj * ui * Yij * np.sin(aij - aj + ai)

        P = np.delete(P, obj=pv)
        Q = np.delete(Q, obj=sl)
        S = np.vstack((P, Q))

        return S


    def solve(self):
        Ybus = self.Ybus()
        slackID = list(self.aslack.keys())
        pvID = list(self.apv.keys())


        # in






class GAMSPY:
    def __init__(self,
                 abus=None,
                 aslack=None,
                 apv=None,
                 brnC0=None,
                 brnC1=None,
                 aline=None,
                 atrf2=None,
                 ashunt=None,
                 solver='cplex'):
        self.abus = abus
        self.aslack = aslack
        self.apv = apv
        self.brnC0 = brnC0
        self.brnC1 = brnC1
        self.aline = aline
        self.atrf2 = atrf2
        self.ashunt = ashunt
        self.solver = solver

    # def define_Set(self):



# if __name__=='__main__':
#     brnC0 = {1: [1, 2], 2: [2, 3], 3: [3, 4], 4: [4, 5], 5: [3, 6], 6: [6, 7], 7: [6, 8], 8: [4, 8], 9: [8, 9]}
#     brnC1 = {1: [1], 2: [1, 2], 3: [2, 5, 3], 4: [3, 8, 4], 5: [4], 6: [5, 6], 7: [6], 8: [8, 9], 9: [9]}
#     print(brnC0.values())
#
#     nr = NR(brnC0=brnC0, brnC1=brnC1)

