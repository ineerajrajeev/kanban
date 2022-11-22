from api import *

def format_report(template, data={}):
    with open(template) as file:
        template = Template(file.read())
        return template.render(data)

@app.route('/', methods=['GET'])
def index():
    res = requests.get('http://localhost:5000/api/home')
    if res.status_code == 200:
        return render_template('index.html', data=res.json())
    return jsonify({'message': res.json()['message']}), 500

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/register', json=data)
        if res.status_code == 200:
            return redirect('/')
        return jsonify({'message': res.json()['message']}), 500
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/login', json=data)
        if res.status_code == 200:
            session['kanban'] = res.json()
            return redirect('/dashboard')
        return redirect('/')

@app.route('/logout', methods=['GET'])
def logout_page():
    session.pop('kanban', None)
    return redirect('/')

@app.route('/dashboard', methods=['GET'])
@token_required
def dashboard_page(current_user):
    res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
    data = res.json()['task']
    if res.status_code == 200:
        if data != "":
            for i in range(len(data)):
                tasks = requests.get('http://localhost:5000/api/listasks/'+str(data[i]['list_id']), headers={'x-access-tokens': session['kanban']['token']})
                data[i]['task_data'] = tasks.json()
        else:
            data = -1
    return render_template('dashboard.html', tasks=data)

@app.route('/profile', methods=['GET','POST'])
@token_required
def profile_page(current_user):
    if request.method == 'GET':
        res = requests.get('http://localhost:5000/api/user', headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            return render_template('profile.html', data=res.json()['user'])
        return jsonify({'message': res.json()['message']}), 500
    elif request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/user', json=data,
                            headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            return redirect('/profile')
        return jsonify({'message': res.status_code}), 500

@app.route('/tasks', methods=['GET', 'POST'])
@token_required
def tasks_page(current_user):
    if request.method == 'GET':
        res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
        shared_list = requests.get('http://localhost:5000/api/tasksdata', headers={'x-access-tokens': session['kanban']['token']})
        return render_template('tasks.html', tasks=res.json()['task'], shared_list=shared_list.json())
    elif request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/listasks', json=data,
                            headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            return redirect('/tasks')
        return jsonify({'message': res.status_code}), 500
    return render_template('tasks.html')

@app.route('/tasks/<id>', methods=['GET', 'POST'])
@token_required
def task_page(current_user, id):
    if request.method == 'GET':
        res = requests.get('http://localhost:5000/api/listasks/' + id, headers={'x-access-tokens': session['kanban']['token']})
        lists = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            data = res.json()
            return render_template('viewList.html', data=data['task'], tasks=data['task_data'], lists=lists.json())
        return jsonify({'message': res.status_code}), 500
    return redirect('/dashboard')

@app.route('/tasks/<id>/edit', methods=['GET','POST'])
@token_required
def edit_task_page(current_user, id):
    if request.method == 'GET':
        res = requests.get('http://localhost:5000/api/listasks/' + id, headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            data = res.json()['task']
            return render_template('viewList.html', data=data)
        return jsonify({'message': res.status_code}), 500
    elif request.method == 'POST':
        data = request.form
        res = requests.patch('http://localhost:5000/api/listasks/' + id, json=data,
                            headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            return redirect('/tasks/'+id)
        return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<page>/<id>/delete', methods=['POST'])
@token_required
def delete_task_page(current_user, page, id):
    res = requests.post('http://localhost:5000/api/task/'+ id + '/delete', headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        return redirect('/tasks/'+page)
    return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<id>/add', methods=['GET', 'POST'])
@token_required
def add_task_page(current_user, id):
    if request.method == 'GET':
        res = requests.get('http://localhost:5000/api/listasks/' + id, headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            data = res.json()['task']
            return render_template('addTask.html', data=data)
        return jsonify({'message': res.status_code}), 500
    elif request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/listasks/' + id + '/add', json=data,
                            headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            return redirect('/tasks/'+id)
        return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<id>/share', methods=['GET', 'POST'])
@token_required
def share_task_page(current_user, id):
    if request.method == 'GET':
        res = requests.get('http://localhost:5000/api/listasks/' + id + '/share',
                           headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            data = res.json()['task']
            return render_template('tasks.html', data=data)
        return jsonify({'message': res.status_code}), 500
    elif request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/task/' + id + '/share', json=data,
                            headers={'x-access-tokens': session['kanban']['token']})
        return redirect('/tasks/'+id)

@app.route('/tasks/<id>/delete', methods=['POST'])
@token_required
def delete_list_page(current_user, id):
    res = requests.delete('http://localhost:5000/api/listasks/' + id, headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        return redirect('/tasks')
    return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<page>/<id>/completed', methods=['POST'])
@token_required
def completed_task(current_user, page, id):
    res = requests.post('http://localhost:5000/api/task/'+ id +'/comlete',
                        headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        return redirect('/tasks/'+page)
    return jsonify(res.status_code)

@app.route('/export', methods=['GET','POST'])
@token_required
def export_page(current_user):
    if request.method == "GET":
        return render_template('export.html')
    elif request.method == "POST":
        start_date = str(request.form.get('startdate'))
        end_date = str(request.form.get('enddate'))
        include = request.form.get('include')
        res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
        data = res.json()['task']
        op = []
        if res.status_code == 200:
            if data != "":
                for i in range(len(data)):
                    if datetime.datetime.strptime(start_date, '%Y-%m-%d') <= datetime.datetime.strptime(data[i]['date'], '%Y-%m-%d') <= datetime.datetime.strptime(end_date, '%Y-%m-%d'):
                        tasks = requests.get('http://localhost:5000/api/listasks/' + str(data[i]['list_id']),
                                             headers={'x-access-tokens': session['kanban']['token']})
                        data[i]['task_data'] = tasks.json()
                        op.append(data[i])
                    else:
                        continue
                if data == []:
                    data = -1
            else:
                data = -1
        if include == "on":
            shared_list = requests.get('http://localhost:5000/api/tasksdata', headers={'x-access-tokens': session['kanban']['token']})
            return render_template('report.html', tasks=op, shared_list=shared_list.json())
        return render_template('report.html', tasks=op, shared_list=-1)
    return jsonify({'message': "Error occured"}), 500

@app.route('/export/fullexport', methods=['GET'])
@token_required
def full_export(current_user):
    res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
    shared_list = requests.get('http://localhost:5000/api/tasksdata',
                               headers={'x-access-tokens': session['kanban']['token']})
    data = res.json()['task']
    if res.status_code == 200:
        if data != "":
            for i in range(len(data)):
                tasks = requests.get('http://localhost:5000/api/listasks/' + str(data[i]['list_id']),
                                     headers={'x-access-tokens': session['kanban']['token']})
                data[i]['task_data'] = tasks.json()
        else:
            data = -1
    return render_template('report.html', tasks=data, shared_list = shared_list.json())

@app.route('/tasks/<page>/<id>/updateprogress', methods=['POST'])
@token_required
def update_task(current_user, page, id):
    data = request.form
    res = requests.post('http://localhost:5000/api/task/' + id+'/updateprogress', json=data,
                         headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        return redirect('/tasks/'+page)
    return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<page>/<id>/movetask', methods=['POST'])
@token_required
def move_task(current_user, page, id):
    data = request.form
    res = requests.post('http://localhost:5000/api/task/' + id+'/movetask', json=data,
                         headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        return redirect('/tasks/'+page)
    return jsonify({'message': res.status_code}), 500

@app.route('/export/pdf')
@token_required
def pdf(current_user):
    res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
    shared_list = requests.get('http://localhost:5000/api/tasksdata', headers={'x-access-tokens': session['kanban']['token']})
    data = res.json()['task']
    if res.status_code == 200:
        if data != "":
            for i in range(len(data)):
                tasks = requests.get('http://localhost:5000/api/listasks/' + str(data[i]['list_id']),
                                     headers={'x-access-tokens': session['kanban']['token']})
                data[i]['task_data'] = tasks.json()
        else:
            data = -1
    rendered = render_template('report.html', tasks=data, shared_list = shared_list.json())
    pdf = pdfkit.from_string(rendered, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=output.pdf'
    return response

@app.route('/export/csv', methods=['GET'])
@token_required
def export_csv(current_user):
    res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
    data = res.json()['task']
    if res.status_code == 200:
        if data != "":
            for i in range(len(data)):
                tasks = requests.get('http://localhost:5000/api/listasks/' + str(data[i]['list_id']),
                                     headers={'x-access-tokens': session['kanban']['token']})
                data[i]['task_data'] = tasks.json()
        else:
            data = -1
    si = io.StringIO()
    cw = csv.writer(si)
    lis = []
    cw.writerow(['List Name', 'Task Name', 'Task Description', 'Task Progress', 'Task Date'])
    for i in range(len(data)):
        for j in range(len(data[i]['task_data']['task_data'])):
            cw.writerow([data[i]['title'], data[i]['task_data']['task_data'][j]['task'], data[i]['task_data']['task_data'][j]['description'], data[i]['task_data']['task_data'][j]['progress'], data[i]['task_data']['task_data'][j]['deadline']])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=kanban_report_{user}_{time}.csv".format(user=current_user.uname, time=datetime.datetime.utcnow())
    output.headers["Content-type"] = "text/csv"
    return output

db.create_all()
if __name__ == '__main__':
    app.run(debug=True)