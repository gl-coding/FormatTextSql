#encoding=utf8
import os
import sys
import xlwt
import json
import shutil
import heapq
import numpy as np

class Tools:
    GLOBAL_SEP    = "\t"

    ERR_NO_INPUT  = -1
    ERR_NO_OUTPUT = -2
    ERR_NO_VIEW   = -3
    ERR_NO_VALUE  = -4
    ERR_NO_FUNC   = -5

    KEYWORDS  = ["from", "into", "view", "select", "where", "groupby", "sortby", "value"]
    EXE_ORDER = ["where", "groupby", "sortby"]
    FUNCTION  = ["none", "distinct", "count", "sum", "mean", "std", "top"]
    EXCEPT    = ["select"]

    OUTPUT_DIR   = "output/"
    OUTPUT_EXCEL = "output.xls"
    
    TRANSFORM = __import__("tools_transform")
    
    @staticmethod
    def type_trans(res):
        if len(res) == 0 or len(res[0]) == 0:
            return
        val, val_type = Tools.type_convert(res[0][-1])
        if val_type != "float":
            return res
        res_new = []
        for items in res:
            if val_type == "float":
                items[-1] = str(int(float(items[-1])))
            res_new.append(items)
        return res_new

    @staticmethod
    def type_convert(arg):
        val_type = ""
        res = arg
        try:
            res = int(arg)
        except Exception:
            pass
        else:
            val_type = "int"

        try:
            res = float(arg)
        except Exception:
            pass
        else:
            #res = int(res)
            val_type = "float"

        return res, val_type
    
    @staticmethod
    def error_check(errno):
        error_map = {
                Tools.ERR_NO_INPUT :  "no input file",
                Tools.ERR_NO_OUTPUT : "no output file",
                Tools.ERR_NO_VIEW :   "no view style",
                Tools.ERR_NO_VALUE:   "no value idx",
                Tools.ERR_NO_FUNC:    "no group func"
                }
        if isinstance(errno, int) and errno < 0:
            err_msg = error_map.get(errno, "")
            print("error:", err_msg)
            exit(1)
        elif isinstance(errno, list) and len(errno) == 1:
            return errno[0]
        else:
            print("error: unknown")

    @staticmethod
    def order_pick(arg_dic):
        res = []
        for item in Tools.EXE_ORDER:
            if item in arg_dic:
                res.append((item, arg_dic[item]))
        return res
    
    @staticmethod
    def list_find(data_list, arg):
        res = -1
        try:
            res = data_list.index(arg)
        except:
            res = -1
        return res

    @staticmethod
    def filter(data_list, head_list, con):
        res = []
        if "!=" in con:
            col, con_arg = [item.strip() for item in con.split("!=")]
            idx = Tools.list_find(head_list, col)
            for items in data_list:
                if items[idx] != con_arg:
                    res.append(items)
        if "=>" in con:
            #transform
            col, func_name = [item.strip() for item in con.split(":")]
            idx = Tools.list_find(head_list, col)
            func = getattr(Tools.TRANSFORM, func_name)
            for items in data_list:
                items[idx] = func(items[idx])
                res.append(items)
        if "=:" in con:
            #filter
            col, func_name = [item.strip() for item in con.split(":")]
            idx = Tools.list_find(head_list, col)
            func = getattr(Tools.TRANSFORM, func_name)
            for items in data_list:
                filt_res = func(items[idx])
                if filt_res:
                    res.append(items)
        return res

    @staticmethod
    def parse_sql(sql):
        #print sql
        sql = sql + " "
        res = []
        keywords = Tools.KEYWORDS
        key_left = []
        for key in keywords:
            idx = sql.find(key)
            if idx != -1:
                key_left.append(key)
                res.append(idx)
        #res.append(-1)
        Tools.print(res)
        key_left = list(zip(key_left, res))
        key_left.sort(key=lambda x:x[1])
        keys = [k for k, v in key_left] + [-1]
        res  = [v for k, v in key_left] + [-1]
        interval = [[res[i], res[i+1]] for i in range(len(res)-1)]
        res_dic = dict(zip(keys, interval))
        Tools.print(res_dic)
        arg_dic = {}
        for k, v in res_dic.items():
            key = k
            val = sql[v[0]:v[1]]
            val = val.replace(key, "").strip()
            if key in Tools.EXCEPT:
                val = [val.strip()]
            else:
                val = [str(i.strip()) for i in val.split(",") if i != ""]
            arg_dic[key] = val
        #print(arg_dic)
        return arg_dic

    @staticmethod
    def matrixfy(groupby_dic, horizon=True):
        res = []
        for k, v in groupby_dic.items():
            if isinstance(v, list):
                if horizon:
                    res.append(k.split(Tools.GLOBAL_SEP) + v)
                else:
                    for item in v:
                        res.append((k + Tools.GLOBAL_SEP + str(item)).split(Tools.GLOBAL_SEP))
            else:
                res.append((k + Tools.GLOBAL_SEP + str(v)).split(Tools.GLOBAL_SEP))
        return res

    @staticmethod
    def group_compute(groupby_dic, func_list):
        if isinstance(func_list, list) and len(func_list) > 0 and  func_list[0] in Tools.FUNCTION:
            pass
        else:
            print("error:group function error!!!")
            exit()
        func = func_list[0]
        res_dic = {}
        if func == "none":
            res_dic = groupby_dic
        elif func == "distinct":
            res_dic = {k:list(set(v)) for k, v in groupby_dic.items()}
        elif func == "count":
            res_dic = {k:len(v) for k, v in groupby_dic.items()}
        elif func == "sum":
            res_dic = {k:sum(v) for k, v in groupby_dic.items()}
        elif func == "mean":
            res_dic = {k:np.mean(v) for k, v in groupby_dic.items()}
        elif func == "std":
            res_dic = {k:np.std(v, ddof=1) for k, v in groupby_dic.items()}
        elif func == "top":
            if len(func_list) != 2:
                print("error:group function top args num != 2!!!")
                exit()
            n = int(func_list[1])
            for k, v in groupby_dic.items():
                items = heapq.nlargest(n, v)
                res_dic.update({k:items})
            pass
        else:
            print("error:group function match none!!!")
        return res_dic

    @staticmethod
    def group_merge(groupby_list):
        if len(groupby_list) == 1:
            return groupby_list[0]
        keys = groupby_list[0].keys()
        res  = {}
        for key in keys:
            res[key] = []
            for kv in groupby_list:
                res[key].append(kv.get(key, ""))
        return res
    
    @staticmethod
    def print(arg, print_flag=False):
        #print_flag = True
        if print_flag:
            print(arg)
        else:
            pass

