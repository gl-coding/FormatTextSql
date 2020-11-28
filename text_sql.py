import os
import sys

class Sql:

    def __init__(self, filename):
        self.head_list = []
        self.head_flag = False
        self.global_list = []
        self.filename = filename
        self.final_res = []
        self.load_data()

    def format_check(self):
        pass

    def set_head(self, head_str=""):
        if not head_str:
            self.head_list = [i for i in range(10)]
        else:
            self.head_list = head_str.split("\t")
            self.head_falg = True

    def set_val_idx(self, val_idx):
        self.val_idx = val_idx

    def get_val_idx(self):
        return self.val_idx

    def load_data(self):
        with open(self.filename) as f:
            for line in f:
                splits = line.strip().split("\t")
                self.global_list.append(splits)

    def groupby(self, seg_list):
        groupby_dic = {}
        print "aaaaaaaaaaaa"
        val_idx  = self.get_val_idx()
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

    #eg. select 1 groupby 2 3 sortby 2
    def parse_sql(self, sql):
        print sql
        sql = sql + " "
        res = []
        keywords = ["select", "groupby", "sortby"]
        for key in keywords:
            idx = sql.find(key)
            if idx == -1:
                keywords.remove(key)
                continue
            res.append(idx)
        res.append(-1)
        print res
        interval = [[res[i], res[i+1]] for i in range(len(res)-1)]
        print keywords
        print interval
        res_dic = zip(keywords, interval)
        print res_dic
        arg_dic = []
        for k, v in res_dic:
            key = k
            val = sql[v[0]:v[1]]
            val = val.replace(key, "").strip()
            val = [int(i) for i in val.split(" ") if i != ""]
            arg_dic.append((key, val))
        print arg_dic
        return arg_dic

    def run_sql(self, sql_str):
        res = []
        arg_dic = self.parse_sql(sql_str)
        for k, v in arg_dic:
            print k
            if k == "select":
                if len(v) > 1:
                    return -1
                self.set_val_idx(v[0])
            if k == "groupby":
                res = self.groupby(v)
            if k == "sortby":
                res = self.sortby(v)
        self.final_res = res
        self.format_data()
    
    def format_data(self):
        for items in self.final_res:
            print "\t".join(items)
        
if __name__ == "__main__":
    filename = sys.argv[1]
    sql = Sql(filename)
    #sql_str = "select 0 groupby 1 sortby 1"
    sql_str = "select 0 groupby 1"
    sql.run_sql(sql_str)
    
