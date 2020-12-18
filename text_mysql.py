import pymysql
from tools import Tools

class MysqlOpt:
    def __init__(self, filename):
        #source
        self.filename  = filename
        self.dbname    = "text_format_tmp"
        self.tablename = filename.replace(".", "_")
        #sql
        self.create_tb = ""
        self.create_db = ""
        self.insert_sql= ""
        self.drop_tsql = ""
        #db
        self.cursor = None
        self.db     = None

    def db_connect(self):
        self.db = pymysql.connect(host='localhost', port=3306, user='root', passwd='123456') 
        self.cursor = self.db.cursor()
        self.cursor.execute(self.create_db)
        self.db.select_db(self.dbname)
        
    def db_drop(self):
        self.db_execute(self.drop_sql)
        
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

        self.drop_sql = "drop table if exists {};".format(self.tablename)

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
        self.db_close()

    def query(self, sql):
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
        except:
            print ("Error: unable to fetch data")

if __name__ == "__main__":
    sql = MysqlOpt("data.log.head")
    sql.build_data()
    sql.db_close()
    
