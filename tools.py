#encoding=utf8
import os
import sys
import xlwt
import json
import shutil
import heapq
import xlwt
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
        val, val_type = Tools.type_check(res[0][-1])
        if val_type != "float":
            return res
        res_new = []
        for items in res:
            if val_type == "float":
                items[-1] = str(int(float(items[-1])))
            res_new.append(items)
        return res_new

    @staticmethod
    def type_check(arg):
        val_type = "str"
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
    def group_compute(groupby_dic, func_list):
        if isinstance(func_list, list) and len(func_list) > 0 and  func_list[0] in Tools.FUNCTION:
            pass
        else:
            print("error:group function error!!!")
            exit()
        func = func_list[0]
        res_dic = {}
        if func in ["none", "distinct"]:
            if func == "none":
                res_dic = groupby_dic
            elif func == "distinct":
                res_dic = {k:list(set(v))[:3] for k, v in groupby_dic.items()}
        if func in ["count", "sum", "mean", "std"]:
            if func == "count":
                res_dic = {k:len(v) for k, v in groupby_dic.items()}
            elif func == "sum":
                res_dic = {k:sum(list(map(float, v))) for k, v in groupby_dic.items()}
            elif func == "mean":
                res_dic = {k:np.mean(list(map(float, v))) for k, v in groupby_dic.items()}
            elif func == "std":
                res_dic = {k:np.std(list(map(float, v)), ddof=1) for k, v in groupby_dic.items()}
        if func in ["top"]:
            if func == "top":
                if len(func_list) != 3:
                    print("error:group function top args num != 2!!!")
                    exit()
                n = int(func_list[2])
                for k, v in groupby_dic.items():
                    fv = list(map(float, v))
                    items = heapq.nlargest(n, fv)
                    res_dic.update({k:items})
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
    def dict_matrixfy(groupby_dic, horizon=True):
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
    def join(dic_pre, dic_post):
        keys_pre = set(dic_pre.keys())
        keys_post = set(dic_post.keys())
        cross = keys_pre & keys_post
        diff_pre = keys_pre - cross
        diff_post = keys_post - cross
        res = []
        pre_len, post_len = -1, -1
        for key in cross:
            item_pre  = key.split("\t") + dic_pre[key]
            item_post = key.split("\t") + dic_post[key]
            if pre_len == -1:
                pre_len, post_len = len(item_pre), len(item_post)
            item_list = item_pre + item_post
            res.append(item_list)
        for key in diff_pre:
            item_list = item_pre[key] + ['none']*post_len
            res.append(item_list)
        for key in diff_post:
            item_list = ['none']*pre_len + item_post[key]
            res.append(item_list)
        return res

    @staticmethod
    def print(arg, print_flag=False):
        #print_flag = True
        if print_flag:
            print(arg)
        else:
            pass
    
    @staticmethod
    def clean_dir(dir_path):
        #clean input dir
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.mkdir(dir_path)

    @staticmethod
    def clean_file(file_path):
        #clean output excel
        if os.path.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def clean_files():
        Tools.clean_dir(Tools.OUTPUT_DIR)
        Tools.clean_file(Tools.OUTPUT_EXCEL)

    @staticmethod
    def write_excel(in_dir, out_file, sep="\t"):
        wb = xlwt.Workbook()
        file_list = []
        for root, dirs, files in os.walk(in_dir):
            for f in files:
                file_list.append(f)
        if len(file_list) == 0:
            print("no output files, exit")
            return
        file_list = sorted(file_list)

        for f in file_list:
            ws = wb.add_sheet(f)
            full_path = in_dir + f
            with open(full_path) as fin:
                line_count = -1
                for line in fin:
                    line_count += 1
                    res = line.split(sep)
                    count = -1
                    for item in res:
                        count += 1
                        ws.write(line_count, count, item)
        wb.save(out_file)
                        
    @staticmethod
    def write_file(items_list, out_file, sep="\t"):
        if os.path.exists(out_file):
            os.remove(out_file)
        with open(out_file, "a") as f:
            #write data to file
            for items in items_list:
                line = Tools.GLOBAL_SEP.join(items) + "\n"
                f.write(line)

    @staticmethod
    def format_data(items_list=[], outfile="", print_type="print"):
        if print_type == "print":
            for items in items_list:
                print(Tools.GLOBAL_SEP.join(map(str, items)))
        elif print_type == "file":
            out_file = Tools.OUTPUT_DIR + outfile
            Tools.write_file(items_list, out_file)
        else:
            Tools.write_excel(Tools.OUTPUT_DIR, Tools.OUTPUT_EXCEL)
            

