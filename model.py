from imports import *

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'kanban' in dict(session).keys():
            token = session['kanban']['token']
        elif token is None:
            return make_response(jsonify({'message': 'Token is missing !!'}), 401)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = userdetails.query.filter_by(public_id=data['public_id']).first()
            return f(current_user, *args, **kwargs)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.InvalidSignatureError):
            return None
        except Exception as e:
            return make_response(jsonify({'message': e}), 401)
    return decorated


def token_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']
        if not token:
            return make_response(jsonify({'message': 'Token is missing!'}), 401)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = userdetails.query.filter_by(public_id=data['public_id']).first()
        except:
            return make_response(jsonify({'message': 'Token is invalid!'}), 401)
        return f(current_user, *args, **kwargs)
    return decorated


class userdetails(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    uname = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    public_id = db.Column(db.String(50), unique=True)

    def __init__(self, name, surname, uname, email, password, public_id):
        self.name = name
        self.surname = surname
        self.uname = uname
        self.email = email
        self.password = password
        self.public_id = public_id

    def __repr__(self):
        return '<User %r>' % self.uname

    def serialize(self):
        return {
            'name': self.name,
            'surname': self.surname,
            'uname': self.uname,
            'email': self.email,
            'password': self.password,
            'public_id': self.public_id
        }


class cards(db.Model):
    list_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('userdetails.id'), nullable=False)

    def __init__(self, title, description, date, user_id):
        self.title = title
        self.description = description
        self.date = date
        self.user_id = user_id

    def serialize(self):
        return {
            'list_id': self.list_id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'user_id': self.user_id
        }

    def __repr__(self):
        return '<Task %r>' % self.title


class listitems(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    task = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.String(50), nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('cards.list_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('userdetails.id'), nullable=False)

    def __init__(self, task, description, deadline, progress, list_id, user_id):
        self.task = task
        self.description = description
        self.deadline = deadline
        self.progress = progress
        self.list_id = list_id
        self.user_id = user_id

    def serialize(self):
        return {
            'id': self.id,
            'task': self.task,
            'description': self.description,
            'deadline': self.deadline,
            'progress': self.progress,
            'list_id': self.list_id,
            'user_id': self.user_id
        }

    def __repr__(self):
        return '<Task %r>' % self.task


class sharedlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('cards.list_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('userdetails.public_id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('userdetails.public_id'), nullable=False)

    def __init__(self, list_id, user_id, owner_id):
        self.list_id = list_id
        self.user_id = user_id
        self.owner_id = owner_id

    def __repr__(self):
        return '<Task %r>' % self.task

    def serialize(self):
        return {
            'id': self.id,
            'list_id': self.list_id,
            'user_id': self.user_id,
            'owner_id': self.owner_id
        }

class progresslog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('listitems.id'), nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('userdetails.id'), nullable=False)

    def __init__(self, task_id, progress, date, user_id):
        self.task_id = task_id
        self.progress = progress
        self.date = date
        self.user_id = user_id

    def __repr__(self):
        return '<Task %r>' % self.task

    def serialize(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'progress': self.progress,
            'date': self.date,
            'user_id': self.user_id
        }