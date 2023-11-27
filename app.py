from datetime import timedelta

from flask import Flask, render_template, request, url_for, redirect, session
from db import connect_server, execute_sql, LoginException

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
    table_names_formatted = [str(item)[2:-3] for item in table_names]
    for table_name in table_names_formatted:
        tmp_quer = f'SELECT * FROM {table_name}'
        table_contents[table_name] = execute_sql(dbconn, tmp_quer)

    return render_template('database.html', table_names=table_names_formatted, table_contents=table_contents)


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
    session.clear()
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('getdb'))


@app.route('/api/edit_table', methods=['POST'])
def edit_table():
    return "ABOBA" + request.form['value']


if __name__ == '__main__':
    app.run(debug=True)
