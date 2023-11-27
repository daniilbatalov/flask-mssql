import pypyodbc as odbc
import datetime


class LoginException(Exception):
    def __init__(self, message, extra_info):
        super().__init__(message)
        self.extra_info = extra_info


def connect_server(ip: str, port: str, driver: str, db_name: str, uid: str, passwd: str) -> odbc.Connection:
    servername = ip + ',' + port
    conn_string = f"""
        DRIVER={{{driver}}};
        SERVER={servername};
        DATABASE={db_name};
        Trust_Connection=yes;
        UID={uid};
        PWD={passwd};
    """
    try:
        return odbc.connect(conn_string)
    except odbc.DatabaseError as ex:
        sqlstate = ex.args[0]
        if sqlstate == '28000':
            raise LoginException("Неверный пароль для пользователя ", {"login": uid,
                                                                      "time": datetime.datetime.now().strftime(
                                                                          "%d/%m/%Y, %H:%M:%S")})


def execute_sql(connection: odbc.Connection, query: str) -> list:
    cursor = connection.cursor()
    cursor.execute(query)
    listres = cursor.fetchall()
    cursor.close()
    return listres


# def auth_user(uid: str, pwd: str) -> odbc.Connection:


# DRIVER_NAME = 'SQL SERVER'
# IP = '127.0.0.1'
# PORT = '1433'
# DATABASE_NAME = 'hospital'
#
# db = connect_server(IP, PORT, DRIVER_NAME, DATABASE_NAME, 'root', 'root')
#
# res = execute_sql(db, 'SELECT * FROM Admin_patient_view')
#
# print(res)
#
# db.close()
