__author__  = "Vu Van Viet"
__email__   = "vuvanviet2k3@gmail.com"
__github__  = "https://github.com/vuviet2k3"
__version__ = "1.0.0"
__address__ = "OAEM Lab"
__history__ = {
    "3/10/26" : "First Version (1.0.0)" 
}

import os, sys
import time, cmath, math
import pandas as pd
import numpy as np
import argparse
PY_PATH   = os.path.dirname(__file__)
DATA_PATH = os.path.join(PY_PATH, "data")
PARSER_INPUT = argparse.ArgumentParser()
PARSER_INPUT.usage = "Power Load Flow"
PARSER_INPUT.add_argument('-fi', help='(str) Input file.xlsx', default="test_2.xlsx", type=str)
AGVRS = PARSER_INPUT.parse_known_args()[0]


def S2v5(t):
    return round(t, 5)

class GetData:
    global AGVRS
    def __init__(self):
        self.data = os.path.join(DATA_PATH, AGVRS.fi)

        print(10*'=' +' SET DATA ' + 10*'=')
        self.get_Settings()
        self.get_Bus()
        self.get_Source()
        self.get_Brn()
        self.get_Trf2()
        # self.get_Trf3()
        self.get_Shunt()


    def get_Settings(self):
        print('SETTING:')
        settingLst = pd.read_excel(self.data, sheet_name='SETTING', header=1)

        sUnit = settingLst.loc[settingLst['##GENERAL'] == 'GE_PowerUnit'].iloc[0, 1]
        self.sBase = settingLst.loc[settingLst['##GENERAL'] == 'GE_Sbase'].iloc[0, 1]
        
        self.typePF = settingLst.loc[settingLst['##GENERAL'] == 'PF'].iloc[0, 1]
        self.nMax = settingLst.loc[settingLst['##GENERAL'] == 'PF'].iloc[0, 2]
        self.Epsilon = settingLst.loc[settingLst['##GENERAL'] == 'PF'].iloc[0, 3]

        print('\tSBASE\tUNIT\tPF\tNMAX\tEPS')
        print(f'\t{self.sBase}\t{sUnit}\t{self.typePF}\t{self.nMax}\t{self.Epsilon}')

        if sUnit.upper() == 'KVA':
            self.sBase = self.sBase /1e3
        elif sUnit.upper() == 'MVA':
            pass
        else:
            raise ValueError(f'Khong ton tai kieu UNIT: {sUnit}')

    def get_Bus(self):
        BusLst = pd.read_excel(self.data, sheet_name='BUS', header=1)
        flagOn = BusLst[BusLst['FLAG'] == 1]
        self.LoadLst = []

        if not list(flagOn):
            return ValueError('Khong tim thay data BUS')

        self.Bus = flagOn['ID'].to_list()
        kV = flagOn['kV'].to_list()
        #
        print('SET BUS:')
        print('\tBUS\tkV')
        for (bus, v) in zip(self.Bus, kV):
            print(f'\t{bus}\t{v}')

        flagLoad = flagOn[flagOn['PLOAD'].notna()]
        id = flagLoad['ID'].tolist()
        pload = flagLoad['PLOAD'].to_numpy() / self.sBase
        qload = flagLoad['QLOAD'].to_numpy() / self.sBase
        #
        typeLoad = flagOn['MEMO'].to_list()[0]
        if typeLoad.upper() == 'KVA':
            pload = pload / 1e3
            qload = qload / 1e3
        else:
            pass 
        #
        self.LoadLst = [(int(l), float(p), float(q)) for (l, p, q) in zip(id, pload, qload)]
        print('SET LOAD:')
        print('\tBUS\tPLOAD\tQLOAD\tUNIT')
        for load in self.LoadLst:
            print(f'\t{load[0]}\t{load[1]}\t{load[2]}\tp.u')

    def get_Source(self):
        sourceLst = pd.read_excel(self.data, sheet_name='SOURCE', header=1)
        flagOn = sourceLst[sourceLst['FLAG'] == 1]
        self.SlackLst = []
        self.PVLst = []

        flagSource = flagOn[flagOn['CODE'] == 3]
        if not list(flagSource.index):
            raise ValueError('Khong tim thay data BUS SWING')
        
        id = flagSource['ID'].tolist()
        vgen = flagSource['vGen [pu]']
        agen = flagSource['aGen [deg]']
        self.SlackLst = [(s, v, a * math.pi / 180) for (s, v, a) in zip(id, vgen, agen)]
        #
        print('SET SLACK:')
        print('\tBUS\tVGEN\tAGEN\tUNIT')
        for src in self.SlackLst:
            print(f'\t{src[0]}\t{src[1]}\t{src[2]}\tp.u')

        flagPV = flagOn[flagOn['CODE'] == 2]
        id = flagPV['ID'].tolist()
        vgen = flagPV['vGen [pu]']
        pgen = flagPV['Pgen'].to_numpy()
        if flagOn['MEMO'].tolist()[0].upper() == "KVA":
            pgen = pgen / 1e3
        self.PVLst = [(pv, v, p) for (pv, v, p) in zip(id, vgen, pgen)]
        #
        print('SET PV:')
        print('\tBUS\tVGEN\tPGEN\tUNIT')
        for pv in self.PVLst:
            print(f'\t{pv[0]}\t{pv[1]}\t{pv[2]}\tp.u')

    def get_Brn(self):
        BrnLst = pd.read_excel(self.data, sheet_name='LINE', header=1)
        flagOn = BrnLst[BrnLst['FLAG'] == 1]
        self.BrnLst = []

        if not list(flagOn.index):
            return ValueError('Khong tim thay data BRANCH')

        fbus = flagOn['BUS_ID1'].tolist()
        tbus = flagOn['BUS_ID2'].tolist()
        kv = flagOn['kV'].to_numpy()
        length = flagOn['LENGTH [km]'].to_numpy()
        r = flagOn['R [Ohm/km]'].to_numpy()
        x = flagOn['X [Ohm/km]'].to_numpy()
        b = flagOn['B [microS/km]'].to_numpy()
        rate = flagOn['RATEA [A]'].to_numpy()

        zBase = kv**2 / self.sBase
        IBase = self.sBase * 1e3 / math.sqrt(3) / kv
        r_pu = r * length / zBase
        x_pu = x * length / zBase
        b_pu = b * length * 1e-6 * zBase
        rate_pu = rate / IBase

        self.BrnLst = [(f, t, r, x, b, rate) for (f, t, r, x, b, rate) in 
                        zip(fbus, tbus, r_pu, x_pu, b_pu, rate_pu)] 

        #
        print('SET BRANCH:')
        print('\tFBUS\tTBUS\tR\tX\tB\tRATE\tUNIT')
        for brn in self.BrnLst:
            print(f'\t{brn[0]}\t{brn[1]}\t{S2v5(brn[2])}\t{S2v5(brn[3])}\t{S2v5(brn[4])}\t{S2v5(brn[5])}\tp.u')

    def get_Trf2(self):
        Trf2Lst = pd.read_excel(self.data, sheet_name='TRF2', header=1)
        flagOn = Trf2Lst[Trf2Lst['FLAG'] == 1]
        self.Trf2Lst = []

        if not list(flagOn.index):
            return False
        
        fbus = flagOn['BUS_ID1'].tolist()
        tbus = flagOn['BUS_ID2'].tolist()
        kv1 = flagOn['kV1'].to_numpy()
        kv2 = flagOn['kV2'].to_numpy()
        Sdm = flagOn['Sn'].to_numpy()
        uk = flagOn['uk [%]'].to_numpy()    # dien ap ngan mach
        pk = flagOn['pk'].to_numpy()        # ton that ngan mach
        p0 = flagOn['P0'].to_numpy()        # ton that ko tai
        i0 = flagOn['i0 [%]'].to_numpy()    # dong dien ko tai
        #
        typeTrf2 = flagOn['MEMO'].tolist()[0]
        type = typeTrf2.upper().split(',')
        typeS, typePk = type[0], type[1]

        if typeS == 'KVA':
            Sdm = Sdm / 1e3
        #
        if typePk == 'MVA':
            pk = pk * 1e3
        
        r_pu = pk * 1e-3 * self.sBase / Sdm**2
        x_pu = uk * self.sBase / Sdm / 1e2
        g_pu = p0 * 1e-3 / self.sBase
        b_pu = i0 * Sdm / self.sBase / 1e2
            
        self.Trf2Lst = [ (int(f), int(t), r, x, b, g) for (f, t, r, x, b, g)
                        in zip(fbus, tbus, r_pu, x_pu, b_pu, g_pu)]
        
        print('SET TRF2:')
        print('\tFBUS\tTBUS\tR\tX\tB\tG\tUNIT')
        for trf2 in self.Trf2Lst:
            print(f'\t{trf2[0]}\t{trf2[1]}\t{trf2[2]}\t{trf2[3]}\t{trf2[4]}\t{trf2[5]}\tp.u')


    def get_Shunt(self):
        ShuntLst = pd.read_excel(self.data, sheet_name='SHUNT', header=1)
        flagOn = ShuntLst[ShuntLst['FLAG'] == 1]
        self.ShuntLst = []
        if not list(flagOn.index):
            return False
        #
        else:
            id = flagOn['BUS_ID'].tolist()
            kv = flagOn['kV'].to_numpy()
            qshunt = flagOn['Qshunt'].to_numpy()
            typeShunt = flagOn['MEMO'].to_list()[0]

            if typeShunt.upper() == 'KVAR':
                qshunt = qshunt / self.sBase / 1e3
            else:
                qshunt = qshunt/self.sBase

            self.ShuntLst = [(s, q) for (s, q) in zip(id, qshunt)]

            print('SET SHUNT:')
            print('\tBUS\tKV\tUNIT')
            for shunt in self.ShuntLst:
                print(f'\t{shunt[0]}\t{shunt[1]}\tp.u')

class RunPF(GetData):
    def __init__(self):
        super().__init__()
        # if self.typePF.upper() == 'NR':
        #     self.NR()
        self.Ybus()

    def Ybus(self):
        if not self.BrnLst:
            fBrn = []
        else:
            fBrn, tBrn, rBrn, xBrn, bBrn, rateBrn = zip(*self.BrnLst)
        #
        if not self.Trf2Lst:
            fTrf2 =[]
        else:
            fTrf2, tTrf2, rTrf2, xTrf2, gTrf2, bTrf2 = zip(*self.Trf2Lst)
        #
        if not self.ShuntLst:
            fShunt = []
        else:
            fShunt, qShunt = zip(*self.ShuntLst)

        n = len(self.Bus)
        self.Ybus = np.zeros((n, n), dtype=np.complex128)
        
        for busa in range(len(self.Ybus)):
            if fBrn:
                self.Ybus[busa, busa] += 1 / (rBrn[busa] + 1j * xBrn[busa]) + 1j * bBrn[busa] / 2
            else:
                continue
            #
            if fTrf2:
                if busa in fTrf2:
                    k = fTrf2.index(busa)
                    self.Ybus[busa, busa] += 1 / (rTrf2[k] + 1j * xTrf2[k]) + (gTrf2[k] + 1j * bTrf2[k]) 
            else:
                continue
        


def main():
    PF = RunPF()
if __name__=="__main__":
    main()