import json
from flask import request, current_app
from flask_security import roles_accepted
from flask_security.utils import encrypt_password
from server import forms

def get_users():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        result = str(running_context.User.query.all())
        return json.dumps(result)
    return __func()

def create_user(username):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        form = forms.NewUserForm(request.form)
        if form.validate():
            if not running_context.User.query.filter_by(email=username).first():
                un = username
                pw = encrypt_password(form.password.data)

                # Creates User
                u = running_context.user_datastore.create_user(email=un, password=pw)

                if form.role.data:
                    u.set_roles(form.role.data)

                has_admin = False
                for role in u.roles:
                    if role.name == 'admin':
                        has_admin = True
                if not has_admin:
                    u.set_roles(['admin'])

                running_context.db.session.commit()
                current_app.logger.info('User added: {0}'.format(
                    json.dumps({"name": username, "roles": [str(_role) for _role in u.roles]})))
                return json.dumps({"status": "user added " + str(u.id)})
            else:
                current_app.logger.warning('Could not create user {0}. user already exists'.format(username))
                return json.dumps({"status": "user exists"})
        else:
            current_app.logger.error('Could not add user {0}. Invalid form'.format(username))
            return json.dumps({"status": "invalid input"})
    return __func()

def read_user(username):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        user = running_context.user_datastore.get_user(username)
        if user:
            return json.dumps(user.display())
        else:
            current_app.logger.error('Could not display user {0}. User does not exist'.format(username))
            return json.dumps({"status": "could not display user"})
    return __func()

def update_user(username):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        user = running_context.user_datastore.get_user(username)
        if user:
            form = forms.EditUserForm(request.form)
            if form.validate():
                if form.password:
                    user.password = encrypt_password(form.password.data)
                    running_context.db.session.commit()
                if form.role.data:
                    user.set_roles(form.role.data)
            current_app.logger.info('Updated user {0}. Roles: {1}'.format(username, form.role.data))
            return json.dumps(user.display())
        else:
            current_app.logger.error('Could not edit user {0}. User does not exist'.format(username))
            return json.dumps({"status": "could not edit user"})
    return __func()

def delete_user(username):
    from server.flaskserver import running_context, current_user
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        user = running_context.user_datastore.get_user(username)
        if user:
            if user != current_user:
                running_context.user_datastore.delete_user(user)
                running_context.db.session.commit()
                current_app.logger.info('User {0} deleted'.format(username))
                return json.dumps({"status": "user removed"})
            else:
                current_app.logger.error('Could not delete user {0}. User is current user.'.format(username))
                return json.dumps({"status": "user could not be removed"})
        else:
            current_app.logger.error('Could not delete user {0}. Form invalid'.format(username))
            return json.dumps({"status": "user could not be removed"})
    return __func()
