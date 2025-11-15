__author__  = 'Vu Van Viet'
__email__   = 'vuvanviet2k3@gmail.com'
__date__    = 'HUST/2025'

#------------------------------------------------
import math
import openpyxl
import utils, solver
import __print__
# __print__.icon()



class DATA:
    def __init__(self, input):
        wb = openpyxl.load_workbook(input, data_only=True)
        self.Asetting = utils.ReadInput2Setting(work_book=wb, sheet_name='SETTING')
        self.Abus = utils.ReadInput2Sheet(work_book=wb, sheet_name='BUS')
        self.Aline = utils.ReadInput2Sheet(work_book=wb, sheet_name='LINE')
        self.Asource = utils.ReadInput2Sheet(work_book=wb, sheet_name='SOURCE')
        self.Atrf2 = utils.ReadInput2Sheet(work_book=wb, sheet_name='TRF2')
        self.Atrf3 = utils.ReadInput2Sheet(work_book=wb, sheet_name='TRF3')
        self.Ashunt = utils.ReadInput2Sheet(work_book=wb, sheet_name='SHUNT')
        self.data()

    def data(self):
        """
        self.AlgoPF          : [PF, nmax, eps]
        self.Sbase
        self.Bus             : Bus ID      
        self.BrnC0           : {brnID:[frombus, tobus]}
        self.BrnC1           : {bus: [brnID]}
        trf2 : ID > 100000
        """
        # SETTING
        unit = self.Asetting['GE_PowerUnit'][0]
        if unit.upper() not in {'MVA','KVA'}:
            title = f'POWER UNIT not in MVA, KVA'
            utils.warning(title)
            return False
        #
        if unit.upper() == 'MVA':
            self.sbase = self.Asetting['GE_Sbase'][0] * 1e6
        else:
            self.sbase = self.Asetting['GE_Sbase'][0] * 1e3
        self.AlgoPF = self.Asetting['PF']

        # BUS
        self.busAll = {}
        memo = 1
        for key, v in self.Abus.items():
            unit = v['MEMO']
            if unit:
                if unit.upper() not in {'MVA', 'KVA'}:
                    title = f'MEMO SHEET BUS not in MVA, KVA'
                    utils.warning(title)
                    return False
                #
                if unit.upper() == 'MVA':
                    memo = memo * 1e6
                elif unit.upper() == 'KVA':
                    memo = memo * 1e3
            #
            v1 = v['PLOAD'] if v['PLOAD'] else 0
            v2 = v['QLOAD'] if v['QLOAD'] else 0
            v1pu = v1 * memo / self.sbase
            v2pu = v2 * memo / self.sbase
            self.busAll[key] = [v1pu, v2pu]

        # SOURCE
        self.slackAll = {}
        self.pvAll = {}
        memo = 1
        for key, v in self.Asource.items():
            unit = v['MEMO']
            if unit:
                if unit.upper() not in {'MVA', 'KVA'}:
                    title = f'MEMO SHEET SOURCE not in MVA, KVA'
                    utils.warning(title)
                    return False
                #
                if unit.upper() == 'MVA':
                    memo = memo * 1e6
                else:
                    memo = memo * 1e3
            #
            if v['CODE'] == 3:
                v1 = v['BUS_ID']
                v2 = v['vGen [pu]']
                v3 = v['aGen [deg]'] *math.pi / 180
                self.slackAll[v1] = [v2, v3]
            elif v['CODE'] == 2:
                v1 = v['BUS_ID']
                v2 = v['vGen [pu]']
                v3 = v['Pgen'] * memo / self.sbase
                self.pvAll[v1] = [v2, v3]

        # LINE
        self.brnC0 = {}
        self.brnC1 = {}
        self.lineAll = {}
        for k, v in self.Aline.items():
            b1, b2 = v['BUS_ID1'], v['BUS_ID2']
            self.brnC0[k] = [b1, b2]
            self.brnC1.setdefault(b1, []).append(k)
            self.brnC1.setdefault(b2, []).append(k)
            #
            l = v['LENGTH [km]']
            kv = v['kV']
            r = v['R [Ohm/km]'] * l * self.sbase / (kv * 1e3)**2
            x = v['X [Ohm/km]'] * l * self.sbase / (kv * 1e3)**2
            b = v['B [microS/km]'] * l * (kv * 1e3)**2 / self.sbase / 1e6
            self.lineAll[k] = [complex(r, x), complex(0, b)]

        # TRF2
        # Neu co trf2 thi trf2ID se trung voi lineID
        # ->  New trf2ID = trf2ID + len(lineID)
        kline = len(self.lineAll.keys())
        self.x2All = {}
        memo1, memo2 = 1, 1
        for k, v in self.Atrf2.items():
            b1, b2 = v['BUS_ID1'], v['BUS_ID2']
            self.brnC0[k + kline] = [b1, b2]
            self.brnC1.setdefault(b1, []).append(k + kline)
            self.brnC1.setdefault(b2, []).append(k + kline)
            #
            unit = v['MEMO']
            if unit:
                p1, p2 = unit.split(',')
                p1, p2 = p1.strip(), p2.strip()
                if p1.upper() not in {'MVA', 'KVA'}:
                    title = 'MEMO S(VA) SHEET TRF2 not in MVA, KVA'
                    utils.warning(title)
                    return False
                elif p1.upper() == 'MVA':
                    memo1 = memo1 * 1e6
                elif p1.upper() == 'KVA':
                    memo1 = memo1 * 1e3
                #
                if p2.upper() not in {'MW', 'KW'}:
                    title = 'MEMO P(W) SHEET TRF2 not in MW, KW'
                    utils.warning(title)
                    return False
                elif p2.upper() == 'MW':
                    memo2 = memo2 * 1e6
                elif p2.upper() == 'KW':
                    memo2 = memo2 * 1e3

            sn = v['Sn'] * memo1
            r = v['pk'] * memo2 * self.sbase / sn**2
            x = v['uk [%]'] * self.sbase / sn / 1e2
            g = v['P0'] * memo2 / self.sbase
            b = v['i0 [%]'] * sn / self.sbase / 1e2
            #
            kv1, kv2 = v['kV1'], v['kV2']
            if kv1 > kv2:
                self.x2All[k + kline] = [b1, complex(r, x), complex(g, -b)]
            else:
                self.x2All[k + kline] = [b2, complex(r, x), complex(g, -b)]

        # TRF3

        # SHUNT
        self.shuntAll = {}
        memo = 1
        for k, v in self.Ashunt.items():
            v1 = v['BUS_ID']
            unit = v['MEMO']
            if unit:
                if unit.upper() not in {'MVAR', 'KVAR'}:
                    title = 'MEMO VAR SHEET SHUNT not in MVAR, KVAR'
                    utils.warning(title)
                    return False
                elif unit.upper() == 'MVAR':
                    memo = memo * 1e6
                elif unit.upper() == 'KVAR':
                    memo = memo * 1e3

            g = v['deltaP'] * memo / self.sbase
            b = v['Qshunt'] * memo / self.sbase
            self.shuntAll[v1] = complex(g, b)


class PF(DATA):
    def __init__(self, input):
        super().__init__(input)



    def runPSM(self, nMax, Eps):
        return solver.PSM(
                    abus = self.busAll,
                    aslack = self.slackAll,
                    brnC0 = self.brnC0,
                    brnC1 = self.brnC1,
                    aline = self.lineAll,
                    atrf2 = self.x2All,
                    ashunt = self.shuntAll,
                    nMax = nMax,
                    Eps = Eps
                )
    #
    def runNR(self, nMax, Eps):
        return solver.NR(
                    abus = self.busAll,
                    aslack = self.slackAll,
                    apv = self.pvAll,
                    brnC0 = self.brnC0,
                    brnC1 = self.brnC1,
                    aline = self.lineAll,
                    atrf2 = self.x2All,
                    ashunt = self.shuntAll,
                    nMax = nMax,
                    Eps = Eps
                )

    def Run(self):
        typePF = self.AlgoPF[0]
        nMax = self.AlgoPF[1]
        Esp = self.AlgoPF[2]
        if typePF.upper() not in {'PSM', 'NR'}:
            title = 'POWER FLOW METHOR not in {PSM, NR}'
            utils.warning(title)
            return False
        elif typePF.upper() == 'PSM':
            self.runPSM(nMax, Esp)
        elif typePF.upper() == 'NR':
            self.runNR(nMax, Esp)





if __name__=='__main__':
    input = r"D:\OAEM Lab\CodePy\Power Flow\data\test_2.xlsx"
    # datap = DATA(input)
    pf = PF(input).Run()

