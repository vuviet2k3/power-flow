__author__  = 'Vu Van Viet'
__email__   = 'vuvanviet2k3@gmail.com'
__date__    = 'HUST/2025'

#---------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox


def warning(title):
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("ERROR", title)

def returnObject(val: str):
    if type(val) == str:
        val = val.strip()
        re_val = val.replace('.', '', 1)
        #
        if re_val.isdigit():
            if '.' in val:
                return float(val)
            else:
                return int(val)
        else:
            return val
    #
    return val


def ReadInput2Setting(work_book=None, sheet_name='SETTING'):
    if work_book is None:
        title = 'WORKBOOK NOT LOADED YET'
        warning(title)
        return None

    sheet = work_book[sheet_name]
    setting = {}
    #
    for i in range(1, 10000):
        v1 = sheet.cell(i, 1).value
        if v1 is None:
            v2 = sheet.cell(i+1, 1).value
            if v2 is None:
                break
        else:
            if v1.startswith('##'):
                continue
            else:
                for j in range(2, 1000):
                    v2 = sheet.cell(i, j).value
                    if v2:
                        setting.setdefault(str(v1), []).append(returnObject(v2))
                    else:
                        break
    #
    if not setting:
        title = f'NO DATA FOUND SHEET {sheet_name}'
    else:
        return setting

def ReadInput2Sheet(work_book=None, sheet_name=None):
    if work_book is None:
        title = 'WORKBOOK NOT LOADED YET'
        warning(title)
        return None
    #
    if sheet_name is None:
        title = 'SHEET NOT LOADED YET'
        warning(title)
        return None

    try:
        sheet = work_book[sheet_name]
    except:
        title = f'SHEET NAME {sheet_name} DOES NOT EXIST.'
        warning(title)
        return None

    res = {}

    # Raw - bat dau doc data tu hang
    for i in range(1, 10000):
        if i == 9999:
            title = f'NO KEY DATA "##" FOUND SHEET NAME: {sheet_name}'
            warning(title)
            return None
        #
        if sheet.cell(i, 1).value.startswith('##'):
            Raw = i
            break

    # Doc data
    res = {}
    for i in range(Raw+1, 10000):
        if i == 9999:
            title = f'NO DATA FOUND IN SHEET NAME: {sheet_name}'
            warning(title)
            return None
        #
        res1 = {}
        v1 = sheet.cell(i+1, 1).value
        if v1:
            for j in range(2, 10000):
                v2 = sheet.cell(Raw+1, j).value
                if v2:
                    v3 = sheet.cell(i+1, j).value
                    res1[v2] = returnObject(v3)
                else:
                    break
            res[returnObject(v1)] = res1
        else:
            break
    #
    return res




# def WriteOutput2Sheet(work_book=None, sheet_name=None):



