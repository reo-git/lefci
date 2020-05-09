import pytest
from lefci.model import Config, LogTree, Status, Report, ReportBySource


def create_filter(pattern, field='message'):
    return {'field': field, 'pattern': pattern}


def create_example(message=None, host=None, program=None):
    example = dict()
    if message:
        example['message'] = message
    if host:
        example['host'] = host
    if program:
        example['program'] = program

    return example


@pytest.fixture
def config_with_one_child():
    root_config = {
        'filters': [create_filter(pattern='abc', field='host')],
        'example': create_example(host='abc')
    }
    child1_config = {
        'filters': [create_filter(pattern='1', field='host')],
        'example': create_example(host='abc 1')
    }
    root = LogTree(**root_config)
    child = LogTree(**child1_config)
    root.add_tree(child)
    config = Config()
    config.log_trees.append(root)
    return {'config': config, 'nodes': {'root': root, 'child1': child}}


def test_only_one_node_verify_ok():
    node_config = {
        'filters': [
            create_filter(pattern='a', field='host'),
            create_filter(pattern='b', field='host'),
            create_filter(pattern='something', field='program'),
            create_filter(pattern='Hello', field='message'),
        ],
        'example': create_example(message='Hello World', host='abc', program='something')
     }
    node = LogTree(**node_config)
    config = Config()
    config.add_tree(node)
    report = config.verify_node(node).get_report_with_source(node.id)
    assert report.get_highest_status_code() == Status.OK
    assert len(report) == 4


def test_only_one_node_verify_not_ok():
    node_config = {
        'filters': [
            create_filter(pattern='a', field='host'),
            create_filter(pattern='b', field='host'),
            create_filter(pattern='something', field='program'),
            create_filter(pattern='Wrong pattern', field='message'),
        ],
        'example': create_example(message='Hello World', host='abc', program='something')
     }
    node = LogTree(**node_config)
    config = Config()
    config.add_tree(node)
    report = config.verify_node(node).get_report_with_source(node.id)
    assert len(report) == 5
    assert len(report.get_messages_with_status_code(Status.WARNING)) == 1
    assert report.get_highest_status_code() == Status.ERROR


def test_node_with_siblings_verify_ok(config_with_one_child):
    child2_config = {
        'filters': [create_filter('2', 'host')],
        'example': create_example(host='abc 2')
    }
    child3_config = {
        'filters': [create_filter('3', 'host')],
        'example': create_example(host='abc 3')
    }
    config = config_with_one_child['config']
    nodes = config_with_one_child['nodes']
    child2 = LogTree(**child2_config)
    child3 = LogTree(**child3_config)
    nodes['root'].add_tree(child2)
    nodes['root'].add_tree(child3)

    reports = config.verify_node(child2)
    report_root = reports.get_report_with_source(nodes['root'].id)
    report_child1 = reports.get_report_with_source(nodes['child1'].id)
    report_child2 = reports.get_report_with_source(child2.id)
    report_child3 = reports.get_report_with_source(child3.id)
    assert len(reports) == 4
    assert len(report_root) == 1
    assert report_root.get_highest_status_code() == Status.OK
    assert len(report_child1) == 2
    assert report_child1.get_highest_status_code() == Status.OK
    assert len(report_child2) == 1
    assert report_child2.get_highest_status_code() == Status.OK
    assert len(report_child3) == 2
    assert report_child2.get_highest_status_code() == Status.OK


def test_node_with_siblings_verify_not_ok(config_with_one_child):
    child2_config = {
        'filters': [create_filter('Hello', 'message')],
        'example': create_example(message='Hello World')
    }
    child3_config = {
        'filters': [create_filter('a', 'host')],
        'example': create_example(host='a')
    }
    config = config_with_one_child['config']
    nodes = config_with_one_child['nodes']
    child1 = nodes['child1']
    child2 = LogTree(**child2_config)
    child3 = LogTree(**child3_config)
    nodes['root'].add_tree(child2)
    nodes['root'].add_tree(child3)

    reports = config.verify_node(child1)
    report_child2 = reports.get_report_with_source(child2.id)
    report_child3 = reports.get_report_with_source(child3.id)

    assert len(report_child2) == 2
    assert report_child2.get_highest_status_code() == Status.UNKNOWN
    assert len(report_child3) == 2
    assert report_child3.get_highest_status_code() == Status.WARNING


def test_node_with_descendants_verify_ok(config_with_one_child):
    child2_config = {
        'filters': [create_filter('abc 12', 'host')],
        'example': create_example(host='abc 12')
    }
    child3_config = {
        'filters': [create_filter('abc 123', 'host')],
        'example': create_example(host='abc 123')
    }
    config = config_with_one_child['config']
    nodes = config_with_one_child['nodes']
    root = nodes['root']
    child1 = nodes['child1']
    child2 = LogTree(**child2_config)
    child3 = LogTree(**child3_config)
    child1.add_tree(child2)
    child1.add_tree(child3)

    reports = config.verify_node(root)
    report_root = reports.get_report_with_source(root.id)
    report_child1 = reports.get_report_with_source(child1.id)
    report_child2 = reports.get_report_with_source(child2.id)
    report_child3 = reports.get_report_with_source(child3.id)

    assert len(reports) == 4
    assert len(report_root) == 1
    assert report_root.get_highest_status_code() == Status.OK
    assert len(report_child1) == 1
    assert report_child1.get_highest_status_code() == Status.OK
    assert len(report_child2) == 1
    assert report_child2.get_highest_status_code() == Status.OK
    assert len(report_child3) == 1
    assert report_child3.get_highest_status_code() == Status.OK


def test_node_with_descendants_verify_not_ok(config_with_one_child):
    child2_config = {
        'filters': [create_filter('World', 'message')],
        'example': create_example(message='Hello World')
    }
    child3_config = {
        'filters': [create_filter('ab', 'host')],
        'example': create_example(host='ab')
    }
    config = config_with_one_child['config']
    nodes = config_with_one_child['nodes']
    root = nodes['root']
    child1 = nodes['child1']
    child2 = LogTree(**child2_config)
    child3 = LogTree(**child3_config)
    child1.add_tree(child2)
    child1.add_tree(child3)

    reports = config.verify_node(root)
    report_child2 = reports.get_report_with_source(child2.id)
    report_child3 = reports.get_report_with_source(child3.id)

    assert len(reports) == 4
    assert len(report_child2) == 1
    assert report_child2.get_highest_status_code() == Status.UNKNOWN
    assert len(report_child3) == 1
    assert report_child3.get_highest_status_code() == Status.WARNING


def test_node_with_ancestors_verify_ok(config_with_one_child):
    child2_config = {
        'filters': [create_filter('abc 2', 'host')],
        'example': create_example(host='abc 2')
    }
    child2_1_config = {
        'filters': [create_filter('abc 23', 'host')],
        'example': create_example(host='abc 23')
    }
    config = config_with_one_child['config']
    nodes = config_with_one_child['nodes']
    root = nodes['root']
    child1 = nodes['child1']
    child2 = LogTree(**child2_config)
    child2_1 = LogTree(**child2_1_config)
    root.add_tree(child2)
    child2.add_tree(child2_1)

    reports = config.verify_node(child2_1)
    report_root = reports.get_report_with_source(root.id)
    report_child1 = reports.get_report_with_source(child1.id)
    report_child2 = reports.get_report_with_source(child2.id)
    report_child2_1 = reports.get_report_with_source(child2_1.id)

    assert len(reports) == 4
    assert len(report_root) == 1
    assert report_root.get_highest_status_code() == Status.OK
    assert len(report_child1) == 1
    assert report_child1.get_highest_status_code() == Status.OK
    assert len(report_child2) == 1
    assert report_child2.get_highest_status_code() == Status.OK
    assert len(report_child2_1) == 1
    assert report_child2_1.get_highest_status_code() == Status.OK


def test_node_with_ancestors_verify_not_ok(config_with_one_child):
    child2_config = {
        'filters': [create_filter('World', 'message')],
        'example': create_example(message='Hello World')
    }
    child3_config = {
        'filters': [create_filter('ab', 'host')],
        'example': create_example(host='ab')
    }
    child1_1_config = {
        'filters': [create_filter('abc 12', 'host')],
        'example': create_example(host='abc 12')
    }
    config = config_with_one_child['config']
    nodes = config_with_one_child['nodes']
    root = nodes['root']
    child1 = nodes['child1']
    child1_1 = LogTree(**child1_1_config)
    child2 = LogTree(**child2_config)
    child3 = LogTree(**child3_config)
    root.add_tree(child2)
    root.add_tree(child3)
    child1.add_tree(child1_1)

    reports = config.verify_node(child1_1)
    report_child2 = reports.get_report_with_source(child2.id)
    report_child3 = reports.get_report_with_source(child3.id)

    assert len(reports) == 5
    assert len(report_child2) == 1
    assert report_child2.get_highest_status_code() == Status.UNKNOWN
    assert len(report_child3) == 1
    assert report_child3.get_highest_status_code() == Status.WARNING
