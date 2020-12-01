#encoding=utf8
import os
import sys
import xlwt
import json
import shutil

class Tools:
    ERR_NO_INPUT  = -1
    ERR_NO_OUTPUT = -2
    ERR_NO_VIEW   = -3
    ERR_NO_VALUE  = -4

    KEYWORDS  = ["from", "into", "view", "select", "where", "groupby", "sortby", "value"]
    EXE_ORDER = ["where", "groupby", "sortby"]

    OUTPUT_DIR = "output/"
    
    TRANSFORM = __import__("tools_transform")

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
                Tools.ERR_NO_VALUE:   "no value idx"
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
    def print(arg, print_flag=False):
        #print_flag = True
        if print_flag:
            print(arg)
        else:
            pass

class Sql:

    def __init__(self):
        self.global_dict = []
        self.global_list = []

        self.head_list  = []
        self.in_file    = ""
        self.out_file   = ""
        self.view_style = ""
        self.final_res  = []
        self.val_idx    = 0
        self.print_type = "print"
        self.clean_dir()

    def head_idx(self, col):
        if isinstance(col, str):
            res = Tools.list_find(self.head_list, col)
        elif isinstance(col, list):
            res = []
            for c in col:
                res_tmp = Tools.list_find(self.head_list, c)
                if res_tmp == -1:
                    res = res_tmp
                    col = c
                    break
                res.append(res_tmp)
        if res == -1:
            print("error: find col(%s) fail, exit" % col)
            exit(1)
        return res

    def set_head(self, head_str=""):
        self.head_list = head_str.strip().split("\t")
        print("headlist:", self.head_list)

    def set_print_type(self, print_type="file"):
        self.print_type = print_type
    
    def clean_dir(self):
        if os.path.exists(Tools.OUTPUT_DIR):
            shutil.rmtree(Tools.OUTPUT_DIR)
        os.mkdir(Tools.OUTPUT_DIR)

    def load_data(self):
        self.global_list = []
        with open(self.in_file) as f:
            count = 0
            for line in f:
                count += 1
                if count == 1:
                    self.set_head(line)
                    continue
                splits = line.strip().split("\t")
                self.global_list.append(splits)
                
    def where(self, condition):
        if len(condition) > 1:
            print("error: where condition > 1")
            exit()
        cons = [item.strip() for item in condition[0].split("and")]
        for con in cons:
            print(con)
            self.global_list = Tools.filter(self.global_list, self.head_list, con)
            #print(self.global_list)

    def groupby(self, seg_list):
        groupby_dic = {}
        val_idx  = self.val_idx
        for items in self.global_list:
            key = []
            val = items[val_idx]
            for seg in seg_list:
                key.append(items[seg])
            key = "\t".join(key)
            #print key
            if key not in groupby_dic:
                groupby_dic[key] = float(val)
            else:
                groupby_dic[key] += float(val)
        #print groupby_dic
        res = [(k+"\t"+str(v)).split("\t") for k, v in groupby_dic.items()]
        #print res
        return res

    #by col in cur cols
    def sortby(self, seg_str):
        sortby_dic = []
        seg_list = seg_str.split("\t")
        seg_left = set(head_list) - set(seg_list)
        for items in self.global_list:
            val = items[val_idx]
            key = []
            for seg in seg_list:
                key.append(items[seg])
            key = "\t".join(key)
            val = []
            for seg in seg_left:
                val.append(items[seg])
            val = "\t".join(val)
            sortby_dic.append(key, val)
        res = sortby_dic.sort()
        res = [(k+"\t"+v).split("\t") for k, v in res]
        return res
    
    def simple_sort(self):
        self.final_res.sort()

    #eg. select 1 groupby 2 3 sortby 2
    def parse_sql(self, sql):
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
            val = [str(i.strip()) for i in val.split(",") if i != ""]
            arg_dic[key] = val
        #print(arg_dic)
        return arg_dic

    def run_sql(self, sql_str):
        res = []
        
        arg_dic = self.parse_sql(sql_str)
        self.in_file = Tools.error_check(arg_dic.get("from", Tools.ERR_NO_INPUT))
        self.load_data()
        #print(self.global_list)
        arg_dic.pop("from")

        self.out_file = Tools.error_check(arg_dic.get("into", Tools.ERR_NO_OUTPUT))
        arg_dic.pop("into")

        self.view_style = Tools.error_check(arg_dic.get("view", Tools.ERR_NO_VIEW))
        self.set_print_type(self.view_style)
        arg_dic.pop("view")

        self.val_idx = Tools.error_check(arg_dic.get("value", Tools.ERR_NO_VALUE))
        self.val_idx = self.head_idx(self.val_idx)
        arg_dic.pop("value")
        Tools.print(arg_dic)

        exe_order = Tools.order_pick(arg_dic)
        Tools.print(exe_order)
        for k, v in exe_order:
            #print k
            if k == "where":
                res = self.where(v)
            if k == "groupby":
                val = self.head_idx(v)
                res = self.groupby(val)
            if k == "sortby":
                res = self.sortby(v)

        self.final_res = res
        self.simple_sort()
        self.format_data()
    
    def format_data(self):
        if self.print_type == "print":
            for items in self.final_res:
                print("\t".join(items))
        elif self.print_type == "file":
            out_dir  = Tools.OUTPUT_DIR
            out_file = out_dir + self.out_file
            if os.path.exists(out_file):
                os.remove(out_file)
            with open(out_file, "a") as f:
                for items in self.final_res:
                    line = "\t".join(items) + "\n"
                    #print(line)
                    f.write(line)
        else:
            in_dir   = Tools.OUTPUT_DIR
            wb = xlwt.Workbook()
            file_list = []
            for root, dirs, files in os.walk(in_dir):
                for f in files:
                    file_list.append(f)
            file_list = sorted(file_list)

            for f in file_list:
                ws = wb.add_sheet(f)
                full_path = in_dir + f
                with open(full_path) as fin:
                    line_count = -1
                    for line in fin:
                        line_count += 1
                        #if line_count == -1:
                        #    continue
                        res = line.split("\t")
                        count = -1
                        for item in res:
                            count += 1
                            item, val_type = Tools.type_convert(item)
                            ws.write(line_count, count, item)

            excel_out = "res.xls"
            if os.path.exists(excel_out):
                os.remove(excel_out)
            wb.save(excel_out)
                    
if __name__ == "__main__":
    sql = Sql()
    #write one sql res to a file in out_dir

    sql.run_sql("from data.log select 0 groupby logtime into res.logtime view file value count")
    sql.run_sql("from data.log select 0 where ctype != video groupby logtime into res.logtime.nov view file value count")

    #sql.run_sql("from data.log select 0 where logtime=:filt_some groupby cate, logtime into res.cate view file value count")
    #sql.run_sql("from data.log select 0 where logtime=:filt_some groupby ctype, logtime into res.ctype view file value count")

    #sql.run_sql("from data.log select 0 where ctype != video and logtime=:filt_some groupby cate, logtime into res.cate.nov view file value count")
    #sql.run_sql("from data.log select 0 where ctype != video and logtime=:filt_some groupby ctype, logtime into res.ctype.nov view file value count")

    #sql.run_sql("from data.log select 0 where ctype != video and logtime=>merge_val groupby cate, logtime into res.cate.nov.int view file value count")
    #sql.run_sql("from data.log select 0 where ctype != video and logtime=>merge_val groupby ctype, logtime into res.ctype.nov.int view file value count")
    
    #write files in output to excel 
    sql.set_print_type("excel")
    sql.format_data()
    

