from imports import *
from model import *


class Api(Resource):
    # Testing the API
    @app.route('/api/home', methods=['GET'])
    def home():
        return jsonify({'message': 'Hello World'})

    # Registering a new user
    @app.route('/api/register', methods=['POST'])
    def register():
        args = request.get_json(force=True)
        user_data = userdetails.query.filter_by(uname=args['username']).first()
        if request.method == 'POST':
            if user_data:
                return jsonify({'message': 'User already exists'}), 401
            else:
                username = args['username']
                password = args['password']
                email = args['email']
                name = args['name']
                surname = args['surname']
                hashed_password = generate_password_hash(password, method='sha256')
                new_user = userdetails(name=name, surname=surname, uname=username, email=email, password=hashed_password,
                                          public_id=str(uuid.uuid4()))
                db.session.add(new_user)
                db.session.commit()
                return jsonify({'message': 'New user created!'})

    # Logging in a user
    @app.route('/api/login', methods=['POST'])
    def api_login():
        if request.method == 'POST':
            auth = request.get_json(force=True)
            if not auth or not auth.get('username') or not auth.get('password'):
                return jsonify({'message': 'Please enter credentials'}), 404
            User_data = userdetails.query.filter_by(uname=auth.get('username')).first()
            if not User_data:
                return jsonify({'message': 'User not found'}), 404
            if check_password_hash(User_data.password, auth.get('password')):
                token = jwt.encode({'public_id': User_data.public_id,
                                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                                   app.config['SECRET_KEY'], algorithm='HS256')
                return jsonify({'token': token, 'user': User_data.serialize()}), 200
            return jsonify({'message': 'Invalid credentials'}), 401

    # Getting user data and edit on profile page
    @app.route('/api/user', methods=['GET', 'POST'])
    @token_required_api
    def getuser(current_user):
        if request.method == 'GET':
            user_data = userdetails.query.filter_by(public_id=current_user.public_id).first()
            if not user_data:
                return jsonify({'message': 'User not found'}), 404
            return jsonify({'user': user_data.serialize()}), 200
        elif request.method=='POST':
            args = request.get_json(force=True)
            user_data = userdetails.query.filter_by(public_id=current_user.public_id).first()
            if not user_data:
                return jsonify({'message': 'User not found'}), 404
            user_data.name = args['name']
            user_data.surname = args['surname']
            user_data.uname = args['username']
            user_data.email = args['email']
            user_data.password = args['password']
            user_data.password = generate_password_hash(user_data.password, method='sha256')
            db.session.commit()
            return jsonify({'message': 'User updated'}), 200

    # Lists of tasks
    @app.route('/api/listasks', methods=['GET', 'POST'])
    @token_required_api
    def tasks(current_user):
        # Getting all lists
        if request.method == 'GET':
            task_data = listasks.query.filter_by(user_id=current_user.public_id).all()
            if not task_data:
                return jsonify({'task': ''}), 200
            data = [task.serialize() for task in task_data]
            for i in data:
                late = datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d") >= datetime.datetime.strptime(i['date'], "%Y-%m-%d")
                i['color'] = 'danger' if late else 'primary'
            return jsonify({'task': data}), 200
        # Adding a new list
        elif request.method == 'POST':
            args = request.get_json(force=True)
            new_list = listasks(user_id=current_user.public_id, date=args['deadline'], description=args['description'], title=args['title'])
            db.session.add(new_list)
            db.session.commit()
            return jsonify({'message': 'New task created!'}), 200

    # View and edit a specific task list
    @app.route('/api/listasks/<task_id>', methods=['GET', 'DELETE', 'PATCH'])
    @token_required_api
    def task(current_user, task_id):
        task_data = listasks.query.filter_by(list_id=task_id).first()
        task_list = tasks.query.filter_by(list_id=task_id).all()
        if not task_data:
            return jsonify({'message': 'None'}), 404
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                # Getting a specific list
                if request.method == 'GET':
                    if not task_data:
                        return jsonify({'message': "None"}), 404
                    ans = {'task': task_data.serialize(), 'task_data': [task.serialize() for task in task_list],
                           'task_count': len(task_list)}
                    return jsonify(ans), 200
                # Editing specific list
                elif request.method == 'PATCH':
                    args = request.get_json(force=True)
                    task_data.title = args['title']
                    task_data.description = args['description']
                    task_data.date = args['deadline']
                    db.session.commit()
                    return jsonify({'message': 'Task updated'}), 200
                # Delete list
                elif request.method == 'DELETE':
                    db.session.delete(task_data)
                    db.session.commit()
                    for i in task_list:
                        db.session.delete(i)
                        db.session.commit()
                    return jsonify({'message': 'Task deleted'}), 200

    # Add task to list
    @app.route('/api/listasks/<list_id>/add', methods=['POST'])
    @token_required_api
    def addtask(current_user, list_id):
        task_data = listasks.query.filter_by(list_id=list_id).first()
        if not task_data:
            return jsonify({'message': 'Task not found'}), 404
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                # Add new task to list given list_id
                if request.method == 'POST':
                    args = request.get_json(force=True)
                    new_task = tasks(list_id=list_id, description=args['description'], task=args['task'],
                                     deadline=args['deadline'], progress=args['progress'], user_id=current_user.public_id)
                    db.session.add(new_task)
                    db.session.commit()
                    return jsonify({'message': 'New task created!'}), 200
                    db.session.add(new_task)
                    db.session.commit()
                    return jsonify({'message': 'New task created!'}), 200

    @app.route('/api/listasks/<id>/delete', methods=['DELETE'])
    @token_required_api
    def deletetasklist(current_user, id):
        task_data = tasks.query.filter_by(task_id=id).first()
        if not task_data:
            return jsonify({'message': 'Task not found'}), 404
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                if request.method == 'DELETE':
                    db.session.delete(task_data)
                    db.session.commit()
                    return jsonify({'message': 'Task deleted'}), 200

    @app.route('/api/task/<id>/comlete', methods=['POST'])
    @token_required_api
    def comleted(current_user, id):
        task_data = tasks.query.filter_by(id=id).first()
        if not task_data:
            return jsonify({'message': 'Task not found'}), 405
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                if request.method == 'POST':
                    task_data.progress = 100
                    db.session.commit()
                    return jsonify({'message': 'Task completed'}), 200

    # Delete task from list
    @app.route('/api/task/<task_id>/delete', methods=['POST'])
    @token_required_api
    def deletetask(current_user, task_id):
        task_data = tasks.query.filter_by(id=task_id).first()
        if not task_data:
            return jsonify({'message': 'Task not found'}), 404
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                if request.method == 'POST':
                    db.session.delete(task_data)
                    db.session.commit()
                    return jsonify({'message': 'Task deleted'}), 200

    # Edit task from list
    @app.route('/api/task/<task_id>/updateprogress', methods=['POST'])
    @token_required_api
    def updatetask(current_user, task_id):
        task_data = tasks.query.filter_by(id=task_id).first()
        if not task_data:
            return jsonify({'message': 'Task not found'}), 404
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                if request.method == 'POST':
                    args = request.get_json(force=True)
                    task_data.progress = args['progress']
                    db.session.commit()
                    return jsonify({'message': 'Task updated'}), 200

    @app.route('/api/task/<task_id>/share', methods=['GET','POST'])
    @token_required_api
    def sharetask(current_user, task_id):
        task_data = listasks.query.filter_by(list_id=task_id).first()
        if not task_data:
            return jsonify({'message': 'Task not found'}), 406
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                if request.method == 'GET':
                    return jsonify({'message': task_data.serialize()}), 200
                elif request.method == 'POST':
                    user_details = userdetails.query.filter_by(uname=request.get_json(force=True)['username']).first()
                    if not user_details:
                        return jsonify({'message': 'User not found'}), 404
                    else:
                        new_share = sharedlist(user_id=user_details.public_id, list_id=task_id, owner_id=current_user.public_id)
                        db.session.add(new_share)
                        db.session.commit()
                        return jsonify({'message': 'Task shared'}), 200

    @app.route('/api/sharedtasks', methods=['GET'])
    @token_required_api
    def sharedtasks(current_user):
        shared_data = sharedlist.query.filter_by(user_id=current_user.public_id).all()
        if not shared_data:
            return jsonify({'message': 'No shared tasks'}), 200
        else:
            ans = [task.serialize() for task in shared_data]
            if len(ans) > 0:
                for i in ans:
                    late = datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d") >= datetime.datetime.strptime(i['deadline'], "%Y-%m-%d")
                    if late:
                        i['color'] = 'danger'
                    elif i['progress'] == 100:
                        i['color'] = 'success'
                    else:
                        i['color'] = 'default'
            else:
                ans = -1
            return jsonify(ans), 200

    @app.route('/api/tasksdata', methods=['GET'])
    @token_required_api
    def sharedtasksid(current_user):
        shared_data = sharedlist.query.filter_by(user_id=current_user.public_id).all()
        shared_data = [i.serialize() for i in shared_data]
        for i in shared_data:
            i['list'] = listasks.query.filter_by(list_id=i['list_id']).first().serialize()
            i['list']['tasks'] = [j.serialize() for j in tasks.query.filter_by(list_id=i['list_id']).all()]
            i['owner_id'] = userdetails.query.filter_by(public_id=i['owner_id']).first().serialize()
            i['user_id'] = userdetails.query.filter_by(public_id=i['user_id']).first().serialize()
        return jsonify(shared_data), 200

    @app.route('/api/task/<id>/movetask', methods=['POST'])
    @token_required_api
    def movetask(current_user, id):
        task_data = tasks.query.filter_by(id=id).first()
        if not task_data:
            return jsonify({'message': 'Task not found'}), 404
        else:
            if task_data.user_id != current_user.public_id:
                return jsonify({'message': 'Unauthorized access'}), 401
            else:
                if request.method == 'POST':
                    args = request.get_json(force=True)
                    task_data.list_id = args['moveto']
                    db.session.commit()
                    return jsonify({'message': 'Task moved'}), 200
