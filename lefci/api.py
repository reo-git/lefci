from http import HTTPStatus
from flask_restful import Api, Resource, request

from lefci import app, model
from lefci.deploy import deploy

api = Api(app)
state = model.State()


def create_report(message, status=model.Status.OK):
    report = model.Report(message, status)
    report_with_source = model.ReportBySource(report, 'api')
    return report_with_source.encode()


def error_report(message):
    return create_report(message, model.Status.ERROR)


class Configs(Resource):

    def get(self, name=None):
        if name:
            return state.get_config(name).encode()
        else:
            return state.saved_configs

    def post(self):
        config_raw = request.get_json()['config']
        try:
            config = model.Config(**config_raw)
            state.save_config(config)
        except Exception as e:
            return error_report(str(e)), HTTPStatus.BAD_REQUEST.value

        return create_report('Current configuration saved'), HTTPStatus.OK.value

    def put(self, name):
        try:
            config = state.get_config(name)
        except Exception as e:
            return error_report(str(e)), HTTPStatus.NOT_FOUND.value
        data = request.get_json()
        deploy(config, data['server'])

    def delete(self, name):
        try:
            state.delete_config(name)
        except Exception as e:
            return error_report(str(e)), HTTPStatus.NOT_FOUND.value

        return create_report(f'Configuration {name} deleted'), HTTPStatus.OK.value


class Trees(Resource):

    def get(self, name, uuid=None):
        try:
            config = state.get_config(name)
        except Exception as e:
            return error_report(str(e)), HTTPStatus.NOT_FOUND.value

        if uuid:
            tree = config.find_tree(uuid)
            return tree.encode(), HTTPStatus.OK.value
        else:
            return [tree.encode() for tree in config.log_trees]

    def put(self, name, uuid):
        try:
            config = state.get_config(name)
        except Exception as e:
            return error_report(str(e)), HTTPStatus.NOT_FOUND.value

        node = config.find_tree(uuid)
        if node:
            data = request.get_json()
            node.update_config(**data)
            verify_reports = config.verify_node(node)
            return verify_reports.encode(), HTTPStatus.OK.value
        else:
            return error_report(f'No node with {uuid} found!'), HTTPStatus.NOT_FOUND.value

    def post(self, name, uuid=None):
        try:
            config = state.get_config(name)
        except Exception as e:
            return error_report(str(e)), HTTPStatus.NOT_FOUND.value

        parent = config.find_tree(uuid)
        child = model.LogTree(parent=parent, **request.get_json())
        if parent:
            parent.add_tree(child)
        else:
            config.add_tree(child)
        verify_reports = config.verify_node(child)
        state.save_config(config)
        return verify_reports.encode(), HTTPStatus.OK.value

    def delete(self, name, uuid):
        try:
            config = state.get_config(name)
        except Exception as e:
            return error_report(str(e)), HTTPStatus.NOT_FOUND.value

        tree = config.find_tree(uuid)
        if not tree:
            return error_report(f'No node with {uuid} found!'), HTTPStatus.NOT_FOUND.value

        parent = tree.parent
        if parent:
            parent.remove_tree(tree)
            state.save_config(config)
            return create_report(f'Removed tree {uuid} from {parent.id}'), HTTPStatus.OK.value
        else:
            config.remove_tree(tree)
            state.save_config(config)
            return create_report(f'Removed tree {uuid} from config'), HTTPStatus.OK.value


api.add_resource(Configs, '/v1/configs', '/v1/configs/<string:name>')
api.add_resource(Trees, '/v1/configs/<string:name>/trees', '/v1/configs/<string:name>/trees/<string:uuid>')

