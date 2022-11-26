from restful import *

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
            flash('You have successfully registered!', 'success')
            return redirect('/')
        flash(res.json()['message'], 'danger')
        return redirect('/')
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/login', json=data)
        if res.status_code == 200:
            session['kanban'] = res.json()
            flash('You have successfully logged in', 'success')
            return redirect('/dashboard')
        flash(res.json()['message'], 'danger')
        return redirect('/')

@app.route('/logout', methods=['GET'])
def logout_page():
    session.pop('kanban', None)
    return redirect('/')

@app.route('/dashboard', methods=['GET'])
@token_required
def dashboard_page(current_user):
    res = redis_client.get('cards_'+current_user.public_id)
    if res is None:
        res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
        redis_client.set('cards_'+current_user.public_id, json.dumps(res.json()))
        redis_client.expire('cards_'+current_user.public_id, timedelta(hours=12))
        data = res.json()['tasks']
    else:
        res = json.loads(res)
        data = res['tasks']
    if len (data) > 0:
        for i in range(len(data)):
            tasks = requests.get('http://localhost:5000/api/listasks/' + str(data[i]['list_id']),
                                    headers={'x-access-tokens': session['kanban']['token']})
            data[i]['listitems'] = tasks.json()
    else:
        data = -1
    return render_template('dashboard.html', tasks=data)

@app.route('/profile', methods=['GET','POST'])
@token_required
def profile_page(current_user):
    if request.method == 'GET':
        res = redis_client.get('user_'+current_user.public_id)
        if res is None:
            res = requests.get('http://localhost:5000/api/user', headers={'x-access-tokens': session['kanban']['token']})
            if res.status_code == 200:
                redis_client.set('user_'+current_user.public_id, json.dumps(res.json()))
                redis_client.expire('user_'+current_user.public_id, timedelta(hours=12))
                res = res.json()
            else:
                flash(res.json()['message'], 'danger')
                return redirect('/')
        else:
            res = json.loads(res)
        return render_template('profile.html', data=res['user'])
    elif request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/user', json=data,
                            headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            redis_client.delete('user_'+current_user.public_id)
            flash('You have successfully updated your profile!', 'success')
            return redirect('/profile')
        return jsonify({'message': res.status_code}), 500

@app.route('/tasks', methods=['GET', 'POST'])
@token_required
def tasks_page(current_user):
    if request.method == 'GET':
        cac = redis_client.get('cards_'+current_user.public_id)
        shared_list = requests.get('http://localhost:5000/api/tasksdata', headers={'x-access-tokens': session['kanban']['token']})
        if cac is None:
            res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
            redis_client.set('cards_'+current_user.public_id, json.dumps(res.json()))
            redis_client.expire('cards_'+current_user.public_id, timedelta(hours=12))
            data = res.json()['tasks']
        else:
            data = json.loads(cac)['tasks']
        return render_template('tasks.html', tasks=data, shared_list=shared_list.json())
    elif request.method == 'POST':
        data = request.form
        res = requests.post('http://localhost:5000/api/listasks', json=data,
                            headers={'x-access-tokens': session['kanban']['token']})
        if res.status_code == 200:
            redis_client.delete('cards_'+current_user.public_id)
            flash('You have successfully created a new card '+data['title'], 'success')
            return redirect('/tasks')
        return jsonify({'message': res.json()}), 500
    return render_template('tasks.html')

@app.route('/tasks/<id>', methods=['GET', 'POST'])
@token_required
def task_page(current_user, id):
    if request.method == 'GET':
        res = requests.get('http://localhost:5000/api/listasks/' + id, headers={'x-access-tokens': session['kanban']['token']})
        lists = redis_client.get('cards_'+current_user.public_id)
        if lists is None:
            lists = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
            if res.status_code == 200:
                redis_client.set('cards_'+current_user.public_id, json.dumps(lists.json()))
                redis_client.expire('cards_'+current_user.public_id, timedelta(hours=12))
                lists = res.json()
            else:
                flash(res.json()['message'], 'danger')
                data = -1
                return redirect('/dashboard')
        else:
            lists = json.loads(lists)
        if res.status_code == 200:
            data = res.json()
            return render_template('viewList.html', data=data['task'], tasks=data['task_data'], lists=lists)
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
            redis_client.delete('cards_'+current_user.public_id)
            flash('You have successfully updated the card '+data['title'], 'success')
            return redirect('/tasks/'+id)
        return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<page>/<id>/delete', methods=['POST'])
@token_required
def delete_task_page(current_user, page, id):
    res = requests.post('http://localhost:5000/api/task/'+ id + '/delete', headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        redis_client.delete('cards_'+current_user.public_id)
        flash('Task deleted successfully')
        return redirect('/tasks/'+page)
    return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<id>/add', methods=['GET', 'POST'])
@token_required
def add_task_page(current_user, id):
    data = request.form
    res = requests.post('http://localhost:5000/api/listasks/' + id + '/add', json=data,
                        headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        flash('You have successfully created a new task '+data['task'], 'success')
        return redirect('/tasks/'+id)
    flash('Failed to create a new task '+data['title'], 'danger')
    return redirect('/tasks/'+id)

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
        if res.status_code == 200:
            flash('You have successfully shared the card with ' + data['username'], 'success')
            return redirect('/tasks/' + id)
        flash('You have failed to share the card with ' + data['username'], 'danger')
        return redirect('/tasks/'+id)

@app.route('/tasks/<id>/delete', methods=['POST'])
@token_required
def delete_list_page(current_user, id):
    res = requests.delete('http://localhost:5000/api/listasks/' + id, headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        redis_client.delete('cards_'+current_user.public_id)
        flash('You have successfully deleted the card', 'success')
        return redirect('/tasks')
    flash('Failed to delete the card', 'danger')
    return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<page>/<id>/completed', methods=['POST'])
@token_required
def completed_task(current_user, page, id):
    res = requests.post('http://localhost:5000/api/task/' + id + '/completed',
                        headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        flash('You have successfully completed the task', 'success')
        return redirect('/tasks/'+page)
    return jsonify({'message': res.status_code}), 500

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
        data = res.json()['tasks']
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
    res = redis_client.get('cards_'+current_user.public_id)
    if res is None:
        res = requests.get('http://localhost:5000/api/listasks',
        headers={'x-access-tokens': session['kanban']['token']})
        data = res.json()['tasks']
        redis_client.set('cards_'+current_user.public_id, json.dumps(data))
        redis_client.expire('cards_'+current_user.public_id, timedelta(hours=1))
    else:
        data = json.loads(res)['tasks']
    res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
    shared_list = requests.get('http://localhost:5000/api/tasksdata',
                               headers={'x-access-tokens': session['kanban']['token']})
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
    res = requests.post('http://localhost:5000/api/task/'+ page+'/updateprogress', json=data,
                         headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        return redirect('/tasks/'+page)
    return jsonify({'message': res.status_code}), 500

@app.route('/tasks/<page>/<id>/movetask', methods=['POST'])
@token_required
def move_task(current_user, page, id):
    data = request.form
    res = requests.post('http://localhost:5000/api/task/'+id+'/movetask', json=data,
                         headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        return redirect('/tasks/'+page)
    return redirect('/tasks/'+page)

@app.route('/sharedtasks/<id>/delete', methods=['POST'])
@token_required
def delete_shared_list_page(current_user, id):
    res = requests.post('http://localhost:5000/api/sharedtask/delete/' + id, headers={'x-access-tokens': session['kanban']['token']})
    if res.status_code == 200:
        flash('Task deleted successfully', 'success')
        return redirect('/tasks')
    return jsonify({'message': res.status_code}), 500


@app.route('/export/pdf')
@token_required
def pdf(current_user):
    res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
    shared_list = requests.get('http://localhost:5000/api/tasksdata', headers={'x-access-tokens': session['kanban']['token']})
    data = res.json()['tasks']
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
    data = res.json()['tasks']
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


def allowed_file(filename, ALLOWED_EXTENSIONS=['csv']):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/tasks/<task_id>/summary', methods=['GET'])
@token_required
def summary_card(current_user, task_id):
    res = requests.get('http://localhost:5000/api/listasks/' + task_id,
    headers={'x-access-tokens': session['kanban']['token']})
    data = res.json()
    labels = []
    values = []
    if res.status_code == 200:
        if data != "":
            for i in data['task_data']:
                labels.append(i['task'])
                values.append(int(i['progress']))
        return render_template('summary.html', tasks=data, labels=labels, values=values)
    return jsonify({'message': res.status_code}), 500


@app.route('/summary', methods=['GET'])
@token_required
def summary(current_user):
    output = []
    res = requests.get('http://localhost:5000/api/listasks', headers={'x-access-tokens': session['kanban']['token']})
    cards = res.json()['tasks']
    for i in cards:
        res = requests.get('http://localhost:5000/api/listasks/' + str(i['list_id']),
                           headers={'x-access-tokens': session['kanban']['token']})
        data = res.json()
        if res.status_code == 200:
            data['labels'] = [task['task'] for task in data['task_data']]
            data['progress'] = [task['progress'] for task in data['task_data']]
            output.append(data)
        else:
            return jsonify({'message': res.status_code}), 500
    return render_template('overall_summary.html', output=output)


@app.route('/tasks/<id>/import', methods=['GET', 'POST'])
@token_required
def import_from_csv(current_user, id):
    res = requests.get('http://localhost:5000/api/listasks/' + id,
                       headers={'x-access-tokens': session['kanban']['token']})
    data = res.json()
    if res.status_code == 200:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part', 'danger')
                return redirect('/tasks/'+id)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect('/tasks/'+id)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                for i in file:
                    data = i.decode('utf-8').split(',')
                    if len(data) != 5 and data[1] != '':
                        return redirect('/tasks/'+id)
                    try:
                        task = {
                            'task': data[1],
                            'description': data[2],
                            'progress': data[3].strip(),
                            'deadline': datetime.datetime.strptime(data[4].strip(), '%d-%m-%Y').strftime('%Y-%m-%d')
                        }
                        print(task)
                        res = requests.post('http://localhost:5000//api/listasks/'+id+'/add',
                                            json=task,
                                            headers={'x-access-tokens': session['kanban']['token']})
                        flash('Task imported successfully: '+data[1], 'success')
                    except:
                        break
                        return redirect('/tasks/'+id)
                flash('All tasks imported successfully', 'success')
                return redirect('/tasks/'+id)
            flash('Invalid file format', 'danger')
            return redirect('/tasks/'+id)
    flash('An error occured', 'danger')
    return redirect('/tasks/'+id)


db.create_all()
if __name__ == '__main__':
    app.run(debug=True)