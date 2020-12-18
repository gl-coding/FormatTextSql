import pymysql
from tools import Tools

class MysqlOpt:
    def __init__(self, filename):
        #source
        self.filename  = filename
        self.dbname    = "text_format_tmp"
        self.tablename = filename.replace(".", "_").replace("/", "_")
        #sql
        self.create_tb = ""
        self.create_db = ""
        self.insert_sql= ""
        self.drop_tb_sql = ""
        #db
        self.cursor = None
        self.db     = None
        #outfile
        self.outfile = ""
        #init action
        self.build_data()
        Tools.clean_files()

    def db_connect(self):
        self.db = pymysql.connect(host='localhost', port=3306, user='root', passwd='123456') 
        self.cursor = self.db.cursor()
        
    def db_drop(self):
        self.db_execute(self.create_db)
        self.db.select_db(self.dbname)
        self.db_execute(self.drop_tb_sql)
        
    def db_create(self):
        self.db_execute(self.create_tb)

    def db_close(self):
        self.cursor.close()

    def db_execute(self, sql):
        #try:
            print(sql)
            self.cursor.execute(sql)
            self.db.commit()
        #except:
        #    print(sql, "error!!!")
        #    self.db.rollback()
    
    def seg_mapping(self, string):
        if string == "int":
            return "int(20)"
        if string == "str":
            return "varchar(100)"
        if string == "float":
            return "float"
        return "error"

    def gen_sql(self):
        line_list = []
        with open(self.filename) as f:
            count = 0
            for line in f:
                line_list.append(line)
                count += 1
                if count == 2:
                    break

        head_list = [item.strip() for item in line_list[0].split("\t")]
        type_list = [self.seg_mapping(Tools.type_check(item)[1]) for item in line_list[1].split("\t")]
        print(head_list)
        print(type_list)

        data_list = zip(head_list, type_list)
        kernel = ", ".join([k + " " + v for k, v in data_list])
        self.create_tb = "create table {} ({}) ENGINE=InnoDB DEFAULT CHARSET=utf8;".format(self.tablename, kernel)

        self.create_db  = "create database if not exists {};".format(self.dbname)

        self.drop_tb_sql = "drop table if exists {};".format(self.tablename)

        segment = ",".join(head_list)
        self.insert_sql = "insert into {} ({}) values(values_seg);".format(self.tablename, segment)

    def db_insert(self):
        with open(self.filename) as f:
            count = 0
            for line in f:
                count += 1
                if count == 1:
                    continue
                values  = ",".join(["'" + item.strip() + "'" for item in line.split("\t")])
                exe_sql = self.insert_sql.replace("values_seg", values)
                self.db_execute(exe_sql)

    def build_data(self):
        self.gen_sql()
        self.db_connect()
        self.db_drop()
        self.db_create()
        self.db_insert()

    def query(self, sql):
        splits = sql.split(";")
        if len(splits) == 2:
            sql, self.outfile = [item.strip() for item in sql.split(";")]
        else:
            self.outfile = ""

        sql = sql.replace(self.filename, self.tablename) + ";"
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        res = []
        for items in results:
            item = [it for it in map(str, items)]
            res.append(item)

        if self.outfile == "":
            Tools.format_data(res, print_type="print")
        else:
            Tools.format_data(res, self.outfile, print_type="file")
        self.db_close()

if __name__ == "__main__":
    sql = MysqlOpt("data.log.head")
    sql.query("select * from data.log.head;test")
    Tools.format_data(print_type="excel")
    


