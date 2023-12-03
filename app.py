from datetime import timedelta

from flask import Flask, render_template, request, url_for, redirect, session, jsonify
from db import connect_server, execute_sql, LoginException, fetch_sql

driver_name = 'SQL SERVER'
ip = '127.0.0.1'
port = '1433'
database_name = 'hospital'

app = Flask(__name__)

app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SECRET_KEY'] = 'super secret key'


@app.route('/database', methods=['GET', 'POST'])
def getdb():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    dbconn = connect_server(ip, port, driver_name, database_name, session.get('username'), session.get('pwd'))
    dbconn_sys = connect_server(ip, port, driver_name, database_name, 'root','root')

    query_role = """SELECT r.name AS RoleName
    FROM sys.database_principals u
    INNER JOIN sys.database_role_members m ON u.principal_id = m.member_principal_id
    INNER JOIN sys.database_principals r ON m.role_principal_id = r.principal_id
    WHERE u.name = USER_NAME()
    AND r.is_fixed_role = 0;"""
    user_roles = execute_sql(dbconn, query_role)
    role = user_roles[0][0].capitalize() + '%'
    query = """SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS
     WHERE TABLE_NAME LIKE '{0}'"""
    table_names = execute_sql(dbconn, query.format(role))
    table_contents = {}
    table_types = {}
    table_primary = {}
    table_names_formatted = [str(item)[2:-3] for item in table_names]
    for table_name in table_names_formatted:
        if table_name != 'Admin_audit_view':
            tmp_query = f"SELECT * FROM {table_name} WHERE deleted = 'False'"
        else:
            tmp_query = f"SELECT * FROM {table_name}"
        tmp_query_type = """SELECT DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{0}'"""
        tmp_query_primary = """SELECT 
            icu.COLUMN_NAME AS PK_Column
        FROM 
            INFORMATION_SCHEMA.VIEW_TABLE_USAGE ivu
        JOIN 
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE icu ON ivu.TABLE_NAME = icu.TABLE_NAME
        WHERE 
            ivu.VIEW_NAME ='{0}'"""
        tf = tmp_query_primary.format(table_name)
        table_contents[table_name] = execute_sql(dbconn, tmp_query)
        table_types[table_name] = execute_sql(dbconn, tmp_query_type.format(table_name))
        table_primary[table_name] = execute_sql(dbconn_sys, tf)
    dbconn_sys.close()
    return render_template('database.html', table_names=table_names_formatted, table_contents=table_contents,
                           table_types=table_types, table_primary=table_primary)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uid = request.form['username']
        pwd = request.form['password']
        try:
            dbconn = connect_server(ip, port, driver_name, database_name, uid, pwd)
            session['logged_in'] = True
            session['username'] = uid
            session['pwd'] = pwd
            dbconn.close()
            if not session.modified:
                session.modified = True
            return redirect(url_for('getdb'))
        except LoginException as ex:
            return ex.__str__() + ex.extra_info["login"] + ". Время попытки входа: " + ex.extra_info["time"]

    return render_template("auth.html")


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('getdb'))


@app.route('/process_data', methods=['POST'])
def process_data():
    if not session.get('logged_in'):
        result = {'message': 'Ошибка входа в БД'}
        return jsonify(result)
    data = request.get_json()  # Получение данных из запроса

    dbconn = connect_server(ip, port, driver_name, database_name, session.get('username'), session.get('pwd'))
    update_query = """UPDATE {0}
        SET {1} = {2}
        WHERE {3} = {4}
        """

    if data['colName'].lower() in ['approved', 'done', 'deleted', 'on_stay']:
        data['value'] = data['value'].capitalize()
        uq_formatted = update_query.format(data['table'], data['colName'], f"'{data['value']}'",
                                           data['idCol'], data['id'])
    elif 'time' in data['colName'].lower() or 'date' in data['colName'].lower():
        uq_formatted = update_query.format(data['table'], data['colName'], f"'{data['value']}'",
                                           data['idCol'], data['id'])
    else:
        uq_formatted = update_query.format(data['table'], data['colName'], data['value'],
                                           data['idCol'], data['id'])
    res = fetch_sql(dbconn, uq_formatted)
    if res == 'Ok':
        result = {'message': 'Данные успешно обработаны', 'data': data}
    else:
        result = {'message': 'Ошибка ', 'error': sorted(res)[0]}

    return jsonify(result)


@app.route('/insert_delete', methods=['POST'])
def insert_delete():
    if not session.get('logged_in'):
        result = {'message': 'Ошибка входа в БД'}
        return jsonify(result)
    dbconn = connect_server(ip, port, driver_name, database_name, session.get('username'), session.get('pwd'))

    data = request.get_json()
    if len(data['toDeleteIds']) > 0:
        deleted_ids = []
        del_query = """DELETE FROM {0} WHERE {1} = {2}"""
        for Id in data['toDeleteIds']:
            dq_formatted = del_query.format(data['tableName'], data['primaryColumnName'], Id)
            tmpRes = fetch_sql(dbconn, dq_formatted)
            if tmpRes != 'Ok':
                result = {'message': 'Ошибка удаления ', 'error': sorted(tmpRes)[0], 'ids': deleted_ids}
                return jsonify(result)
            else:
                deleted_ids.append(Id)
    if len(data['newRowsData']) > 0:
        ins_ids = []
        ins_query = """INSERT INTO {0} VALUES {1}"""
        result = ''
        for entry in data['newRowsData']:
            row = []
            for key, value in entry.items():
                if key != data['primaryColumnName']:
                    value = '1' if value.lower() == 'true' else '0' if value.lower() == 'false' else f"'{value}'" if not value.isdigit() else value
                    row.append(value)
            result += f"({', '.join(row)}), "

        result = result[:-2]
        ins_query_form = ins_query.format(data['tableName'], result)
        tmpRes = fetch_sql(dbconn, ins_query_form)
        if tmpRes != 'Ok':
            result = {'message': 'Ошибка ', 'error': sorted(tmpRes)[0]}
            return jsonify(result)

    return jsonify({'message': 'Данные успешно обработаны', 'data': data})


@app.route('/logout', methods=['POST'])
def sign_out():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
