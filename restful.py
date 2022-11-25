from werkzeug.utils import secure_filename

from imports import *
from model import *


class test(Resource):

    def get(self):
        return make_response(jsonify({'message': 'Hello World'}), 200)


api.add_resource(test, '/api/home')


# Register new user
class register(Resource):

    def post(self):
        args = request.json
        user_data_username = userdetails.query.filter_by(uname=args['username']).first()
        user_data_email = userdetails.query.filter_by(email=args['email']).first()
        if user_data_username or user_data_email:
            return make_response(jsonify({'message': 'User already exists'}), 400)
        new_user = userdetails(
            public_id=str(uuid4()),
            uname=args['username'],
            password=generate_password_hash(args['password'], method='sha256'),
            email=args['email'],
            name=args['name'],
            surname=args['surname']
        )
        db.session.add(new_user)
        db.session.commit()
        return make_response(jsonify({'message': 'New user created'}), 201)


api.add_resource(register, '/api/register')


# Get authentication token
class api_login(Resource):

    def post(self):
        auth = request.get_json(force=True)
        if not auth or not auth.get('username') or not auth.get('password'):
            return make_response(jsonify({'message': 'Could not verify'}), 401)
        User_data = userdetails.query.filter_by(uname=auth.get('username')).first()
        if not User_data:
            return make_response(jsonify({'message': 'User does not exist'}), 404)
        if check_password_hash(User_data.password, auth.get('password')):
            token = jwt.encode({'public_id': User_data.public_id,
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                               app.config['SECRET_KEY'], algorithm='HS256')
            return make_response(jsonify({'token': token, 'user': User_data.serialize()}), 200)
        return make_response(jsonify({'message': 'Invalid credentials'}), 401)


api.add_resource(api_login, '/api/login')


# User details
class getuser(Resource):
    method_decorators = {'get': [token_required_api], 'post': [token_required_api]}

    # Get user details
    def get(self, current_user):
        user_data = userdetails.query.filter_by(public_id=current_user.public_id).first()
        if not user_data:
            return make_response(jsonify({'message': 'User does not exist'}), 404)
        return make_response(jsonify({'user': user_data.serialize()}), 200)

    # Update user details
    def post(self, current_user):
        args = request.json
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
        return make_response(jsonify({'message': 'User details updated'}), 200)


api.add_resource(getuser, '/api/user')


# cards
class tasks(Resource):
    method_decorators = {'get': [token_required_api], 'post': [token_required_api]}

    # Get all cards
    def get(self, current_user):
        task_data = cards.query.filter_by(user_id=current_user.public_id).all()
        if not task_data:
            return make_response(jsonify({'tasks': ''}), 404)
        data = [task.serialize() for task in task_data]
        for i in data:
            late = datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d") >= datetime.datetime.strptime(
                i['date'], "%Y-%m-%d")
            i['color'] = 'danger' if late else 'primary'
        return make_response(jsonify({'tasks': data}), 200)

    # Add new card
    def post(self, current_user):
        args = request.json
        new_list = cards(user_id=current_user.public_id,
                         date=args['deadline'],
                         description=args['description'], title=args['title'])
        db.session.add(new_list)
        db.session.commit()
        return make_response(jsonify({'message': "New card created"}), 200)


api.add_resource(tasks, '/api/listasks')


# API for cards and lists within
class task(Resource):
    method_decorators = {'get': [token_required_api], 'patch': [token_required_api], 'delete': [token_required_api]}

    # Get cards
    def get(self, current_user, task_id):
        task_data = cards.query.filter_by(user_id=current_user.public_id, list_id=task_id).first()
        task_list = listitems.query.filter_by(user_id=current_user.public_id, list_id=task_id).all()
        if not task_data:
            return make_response(jsonify({'message': 'Task not found'}), 404)
        ans = {'task': task_data.serialize(),
               'task_data': [task.serialize() for task in task_list],
               'task_count': len(task_list)
               }
        return make_response(jsonify(ans), 200)

    # Update cards
    def patch(self, current_user, task_id):
        task_data = cards.query.filter_by(user_id=current_user.public_id, list_id=task_id).first()
        args = request.json
        task_data.title = args['title']
        task_data.description = args['description']
        task_data.date = args['deadline']
        db.session.commit()
        return make_response(jsonify({'message': 'Task updated'}), 200)

    # Delete cards
    def delete(self, current_user, task_id):
        cards_list = cards.query.filter_by(user_id=current_user.public_id, list_id=task_id).first()
        if not cards_list:
            return make_response(jsonify({'message': 'Task not found'}), 404)
        shared_tasks = sharedlist.query.filter_by(user_id=current_user.public_id, list_id=task_id).all()
        for task in shared_tasks:
            db.session.delete(task)
        tasks = listitems.query.filter_by(user_id=current_user.public_id, list_id=task_id).all()
        for task in tasks:
            db.session.delete(task)
        db.session.delete(cards_list)
        db.session.commit()
        return make_response(jsonify({'message': 'Task deleted'}), 200)


api.add_resource(task, '/api/listasks/<int:task_id>')


# API for adding task
class addtask(Resource):
    method_decorators = {'post': [token_required_api]}

    # Add new task
    def post(self, current_user, list_id):
        args = request.json
        new_task = listitems(list_id=list_id, description=args['description'], task=args['task'],
                         deadline=args['deadline'], progress=args['progress'], user_id=current_user.public_id)
        db.session.add(new_task)
        db.session.commit()
        return make_response(jsonify({'message': 'New task created!'}), 200)


api.add_resource(addtask, '/api/listasks/<int:list_id>/add')

# API for deleting card
class deletetasklist(Resource):
    method_decorators = {'delete': [token_required_api]}

    def delete(self, current_user, id):
        task_data = listitems.query.filter_by(user_id=current_user.public_id, list_id=id).all()
        if not task_data:
            return make_response(jsonify({'message': 'Task not found'}), 404)
        for i in task_data:
            db.session.delete(i)
        db.session.commit()
        return make_response(jsonify({'message': 'Task deleted'}), 200)


api.add_resource(deletetasklist, '/api/listasks/<int:id>/delete')


# Mark task as completed
class completed(Resource):
    method_decorators = {'post': [token_required_api]}

    def post(self, current_user, id):
        task_data = listitems.query.filter_by(user_id=current_user.public_id, id=id).first()
        if not task_data:
            return make_response(jsonify({'message': 'Task not found'}), 405)
        task_data.progress = 100
        db.session.commit()
        return make_response(jsonify({'message': 'Task completed'}), 200)


api.add_resource(completed, '/api/task/<int:id>/completed')


# Delete task from list
class deletetask(Resource):
    method_decorators = {'post': [token_required_api]}

    def post(self, current_user, task_id):
        task_data = listitems.query.filter_by(user_id=current_user.public_id, id=task_id).first()
        if not task_data:
            return make_response(jsonify({'message': 'Task not found'}), 404)
        db.session.delete(task_data)
        db.session.commit()
        return make_response(jsonify({'message': 'Task deleted'}), 200)


api.add_resource(deletetask, '/api/task/<int:task_id>/delete')


# Update task
class updatetask(Resource):
    method_decorators = {'post': [token_required_api]}

    def post(self, current_user, task_id):
        task_data = listitems.query.filter_by(user_id=current_user.public_id, id=task_id).first()
        args = request.json
        task_data.progress = args['progress']
        db.session.commit()
        pl = progresslog(task_id=task_id, progress=args['progress'], user_id=current_user.public_id, date=datetime.datetime.now())
        db.session.add(pl)
        db.session.commit()
        return make_response(jsonify({'message': 'Task updated'}), 200)


api.add_resource(updatetask, '/api/task/<task_id>/updateprogress')


# API For shared task
class sharedtask(Resource):
    method_decorators = {'post': [token_required_api]}

    # Share task
    def post(self, current_user, task_id):
        user_details = userdetails.query.filter_by(uname=request.get_json(force=True)['username']).first()
        if not user_details:
            return make_response(jsonify({'message': 'User not found'}), 404)
        new_share = sharedlist(user_id=user_details.public_id, list_id=task_id, owner_id=current_user.public_id)
        db.session.add(new_share)
        db.session.commit()
        return make_response(jsonify({'message': 'Task shared'}), 200)


api.add_resource(sharedtask, '/api/task/<task_id>/share')


class sharedtasks(Resource):
    method_decorators = {'get': [token_required_api]}

    # Get shared tasks
    def get(self, current_user):
        shared_data = sharedlist.query.filter_by(user_id=current_user.public_id).all()
        if not shared_data:
            return make_response(jsonify({'message': 'No shared tasks'}), 200)
        else:
            ans = [task.serialize() for task in shared_data]
            if len(ans) > 0:
                for i in ans:
                    late = datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d") >=\
                           datetime.datetime.strptime(i['deadline'], "%Y-%m-%d")
                    if late : i['color'] = 'danger'
                    elif i['progress'] == 100 : i['color'] = 'success'
                    else : i['color'] = 'default'
            else:
                ans = -1
            return make_response(jsonify(ans), 200)


api.add_resource(sharedtasks, '/api/sharedtasks')


# get shared task details
class sharedtaskdetails(Resource):
    method_decorators = {'get': [token_required_api]}

    # Get shared task details
    def get(self, current_user):
        shared_data = sharedlist.query.filter_by(user_id=current_user.public_id).all()
        shared_data = [i.serialize() for i in shared_data]
        for i in shared_data:
            i['list'] = cards.query.filter_by(list_id=i['list_id']).first().serialize()
            i['list']['tasks'] = [j.serialize() for j in listitems.query.filter_by(list_id=i['list_id']).all()]
            i['owner_id'] = userdetails.query.filter_by(public_id=i['owner_id']).first().serialize()
            i['user_id'] = userdetails.query.filter_by(public_id=i['user_id']).first().serialize()
        return make_response(jsonify(shared_data), 200)


api.add_resource(sharedtaskdetails, '/api/tasksdata')


# API for moving task from card to another
class movetask(Resource):
    method_decorators = {'post': [token_required_api]}

    def post(self, current_user, task_id):
        args = request.json
        task_data = listitems.query.filter_by(user_id=current_user.public_id, task_id=task_id).first()
        if not task_data:
            return make_response(jsonify({'message': 'Task not found'}), 404)
        task_data.list_id = args['list_id']
        db.session.commit()
        return make_response(jsonify({'message': 'Task moved'}), 200)


api.add_resource(movetask, '/api/task/<task_id>/movetask')


# API for deleting shared task
class deletesharedtask(Resource):
    method_decorators = {'post': [token_required_api]}

    def post(self, current_user, task_id):
        shared_data = sharedlist.query.filter_by(user_id=current_user.public_id, id=task_id).first()
        if not shared_data:
            return make_response(jsonify({'message': 'Task not found'}), 404)
        db.session.delete(shared_data)
        db.session.commit()
        return make_response(jsonify({'message': 'Task deleted'}), 200)


api.add_resource(deletesharedtask, '/api/sharedtask/delete/<task_id>')

