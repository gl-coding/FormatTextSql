#encoding=utf8
import os
import sys
import xlwt
import json
import shutil

from tools import Tools

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
        self.group_func = []
        self.count_type = ""
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
        #clean input dir
        if os.path.exists(Tools.OUTPUT_DIR):
            shutil.rmtree(Tools.OUTPUT_DIR)
        os.mkdir(Tools.OUTPUT_DIR)

        #clean output excel
        if os.path.exists(Tools.OUTPUT_EXCEL):
            os.remove(Tools.OUTPUT_EXCEL)

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
                
    def select(self, func):
        if ":" in func and len(func.split(":")) == 2:
            func, count_type = func.split(":")
            self.count_type = count_type
        funcname, args = func.split("(")
        args = args.strip(")")
        args = args.split(",")
        #arg[0] -> count col name
        self.val_idx = args[0]
        self.val_idx = self.head_idx(self.val_idx)
        #arg[1:] -> others
        self.group_func = [funcname] + args[1:]
                
    def where(self, condition):
        if len(condition) > 1:
            print("error: where condition > 1")
            exit()
        cons = [item.strip() for item in condition[0].split("and")]
        for con in cons:
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
                groupby_dic[key] = [float(val)]
            else:
                groupby_dic[key].append(float(val))
        #print groupby_dic
        #res = [(k+"\t"+str(v)).split("\t") for k, v in groupby_dic.items()]
        res = Tools.group_compute(groupby_dic, self.group_func)
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

    def run_sql(self, sql_str):
        res = []
        
        arg_dic = Tools.parse_sql(sql_str)
        print(arg_dic)
        self.in_file = Tools.error_check(arg_dic.get("from", Tools.ERR_NO_INPUT))
        self.load_data()
        #print(self.global_list)
        arg_dic.pop("from")

        self.out_file = Tools.error_check(arg_dic.get("into", Tools.ERR_NO_OUTPUT))
        arg_dic.pop("into")

        self.view_style = Tools.error_check(arg_dic.get("view", Tools.ERR_NO_VIEW))
        self.set_print_type(self.view_style)
        arg_dic.pop("view")

        self.select(Tools.error_check(arg_dic.get("select", Tools.ERR_NO_FUNC)))

        #self.val_idx = Tools.error_check(arg_dic.get("value", Tools.ERR_NO_VALUE))
        #arg_dic.pop("value")
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
        if self.count_type == "int":
            self.final_res = Tools.type_trans(self.final_res)
        if self.print_type == "print":
            for items in self.final_res:
                print("\t".join(map(str, items)))
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
                        #if line_count == -1:
                        #    continue
                        res = line.split("\t")
                        count = -1
                        for item in res:
                            count += 1
                            item, val_type = Tools.type_convert(item)
                            ws.write(line_count, count, item)

            wb.save(Tools.OUTPUT_EXCEL)
                    
if __name__ == "__main__":
    sql = Sql()
    #write one sql res to a file in out_dir

    #sql.run_sql("from data.log.head select count(count) groupby logtime into res.logtime view print")
    #sql.run_sql("from data.log select count(count) where ctype != video groupby logtime into res.logtime.nov view print")
    #sql.run_sql("from data.log select sum(count) where ctype != video groupby logtime into res.logtime.nov view print")
    #sql.run_sql("from data.log.head select avg(count) where ctype != video groupby logtime into res.logtime.nov view print")
    #sql.run_sql("from data.log.head select top(count, 3) where ctype != video groupby logtime into res.logtime.nov view print")
    sql.run_sql("from data.log.head select top(count, 3):int where ctype != video groupby logtime into res.logtime.nov view print")
    #sql.run_sql("from data.log select 0 where ctype == video groupby logtime into res.logtime.v view file value count")

    #sql.run_sql("from data.log select 0 where logtime=:filt_some groupby cate, logtime into res.cate view file value count")
    #sql.run_sql("from data.log select 0 where logtime=:filt_some groupby ctype, logtime into res.ctype view file value count")

    #sql.run_sql("from data.log select 0 where ctype != video and logtime=:filt_some groupby cate, logtime into res.cate.nov view file value count")
    #sql.run_sql("from data.log select 0 where ctype != video and logtime=:filt_some groupby ctype, logtime into res.ctype.nov view file value count")

    #sql.run_sql("from data.log select 0 where ctype != video and logtime=>merge_val groupby cate, logtime into res.cate.nov.int view file value count")
    #sql.run_sql("from data.log select 0 where ctype != video and logtime=>merge_val groupby ctype, logtime into res.ctype.nov.int view file value count")
    
    #write files in output to excel 
    sql.set_print_type("excel")
    sql.format_data()
    

