import json
import os
import re

from collections import namedtuple
from os.path import isfile, join
from uuid import uuid4
from enum import IntEnum


class Status(IntEnum):
    OK = 1
    UNKNOWN = 2
    WARNING = 3
    ERROR = 4


Message = namedtuple('Message', ['message', 'status'])


class ApiConfig:
    allowed_fields = ['message', 'host', 'program']
    filter_hit_span_class = 'filter_hit'
    report_level = Status.UNKNOWN


class State:

    def __init__(self):
        self.DEFAULT_CONFIG_PATH = 'configs'
        self.configs_cache = {}
        if not os.path.exists(self.DEFAULT_CONFIG_PATH):
            os.mkdir(self.DEFAULT_CONFIG_PATH)

        self.saved_configs = [f for f in os.listdir(self.DEFAULT_CONFIG_PATH) if isfile(join(self.DEFAULT_CONFIG_PATH, f))]

    def delete_config(self, config_name):
        filepath = join(self.DEFAULT_CONFIG_PATH, config_name)
        os.remove(filepath)
        self.saved_configs.remove(config_name)
        self.configs_cache.pop(config_name)
        return True

    def get_config(self, config_name):
        if config_name not in self.configs_cache:
            self.configs_cache[config_name] = self.load_config(config_name)
        return self.configs_cache[config_name]

    def save_config(self, config):
        filepath = join(self.DEFAULT_CONFIG_PATH, config.name)
        with open(filepath, 'w') as file:
            file.write(config.to_json())
        if config.name not in self.saved_configs:
            self.saved_configs.append(config.name)
        if config.name not in self.configs_cache:
            self.configs_cache[config.name] = config
        return True

    def load_config(self, config_name):
        filepath = join(self.DEFAULT_CONFIG_PATH, config_name)
        with open(filepath, 'r') as file:
            config_data = json.load(file)

        return Config(**config_data)


class Config:

    def __init__(self, **kwargs):
        self.name = str(uuid4())
        self.log_trees = []
        self.server = []

        if kwargs:
            for key, value in kwargs.items():
                if key == 'log_trees':
                    self.log_trees = [LogTree(**child) for child in value]
                elif key in self.__dict__:
                    self.__dict__[key] = value

    def add_tree(self, tree, position=None):
        if position is None or not (0 <= position < self.log_trees.__len__()):
            self.log_trees.append(tree)
        else:
            self.log_trees.insert(position, tree)

    def remove_tree(self, tree):
        self.log_trees.remove(tree)

    def verify_node(self, node):
        reports = ReportBySource()
        # verify if node configuration is OK
        report = node.get_verify_report()
        reports.add(report, node.title)
        if report.get_highest_status_code() == Status.ERROR:
            return reports

        reports += self.get_filter_report(node, node.filters)
        reports += self.get_example_report(node, node.example)

        return reports

    def get_filter_report(self, node, filters):
        """
        Tests the filters match with the example of all siblings and goes threw the sub-tree and test if the given
        filters are matching on the examples of the nodes. Goes deeper if they hit, and stops at nodes which don't hit.
        :param node: node and it's subtree, whose example should be tested
        :type node: LogTree
        :param filters: filters to test
        :type filters: list(Filter)
        :return: report of all test from siblings and in the sub-tree
        :rtype: Report
        """
        reports = ReportBySource()
        for sibling in self._get_siblings(node):
            sibling_report = sibling.get_example_miss_report(filters)
            reports.add(sibling_report, sibling.title)

        reports += self.get_filter_match_report_of_children(node, filters)

        return reports

    def get_filter_match_report_of_children(self, node, filters):
        """
        Goes threw a sub-tree and test if the given filters are matching on the examples of the nodes. Goes deeper if
        they hit, and stops at nodes which don't hit.
        :param node: node and it's subtree, whose example should be tested
        :type node: LogTree
        :param filters: filters to test
        :type filters: list(Filter)
        :return: report of all test from nodes in the sub-tree
        :rtype: Report
        """
        reports = ReportBySource()
        for child in node.children:
            child_report = child.get_example_match_report(filters)
            reports.add(child_report, child.title)

            # if the filter hits, do the same for the child
            if child_report.get_highest_status_code() == Status.OK:
                reports += self.get_filter_match_report_of_children(child, filters)

        return reports

    def get_example_report(self, node, example):
        """
        Goes the tree upwards and test if the ancestors filters match on the given example. Also test if the filters of
        the siblings and the siblings of the ancestors miss on the given example.
        :param node: node and it ancestor, whose filters should be tested
        :type node: LogTree
        :param example: example to test
        :return: report of all test from siblings and parent
        :rtype: Report
        """
        reports = ReportBySource()
        siblings = self._get_siblings(node)
        for sibling in siblings:
            sibling_report = sibling.get_filter_miss_report(example)
            reports.add(sibling_report, sibling.title)

        if node.parent:
            reports.add(node.parent.get_filter_match_report(example), node.parent.title)
            reports += self.get_example_report(node.parent, example)
        return reports

    def _get_siblings(self, node):
        if node.parent:
            siblings = [child for child in node.parent.children if child is not node]
        else:
            siblings = [child for child in self.log_trees if child is not node]
        return siblings

    def find_tree(self, uuid):
        """
        Search all LogTrees in the current config and returns the sub-tree if found.
        :param uuid: str
        :return: LogTree
        """
        for tree in self.log_trees:
            result = tree.search_for_descendant(uuid)
            if result:
                return result

    def encode(self):
        var_dict = self.__dict__.copy()
        trees = []
        for tree in var_dict.pop('log_trees'):
            trees.append(tree.encode())
        var_dict['log_trees'] = trees
        return var_dict

    def to_json(self):
        return json.dumps(self.encode(), indent=4)


class LogTree:

    def __init__(self, parent=None, **kwargs):
        self.id = uuid4().__str__()
        self.title = 'root'
        self.description = ''
        self.children = []
        self.filters = []
        self.actions = []
        self.example = {}
        self.parent = parent

        if kwargs:
            self.update_config(**kwargs)

    def update_config(self, **update_dict):
        for key, value in update_dict.items():
            if key == 'children':
                self.children = [LogTree(parent=self, **child) for child in value]
            elif key == 'filters':
                self.filters = [Filter(filter['field'], filter['pattern']) for filter in value]
            elif key in self.__dict__:
                self.__dict__[key] = value

    def add_tree(self, tree, position=None):
        tree.parent = self
        if position is None or not (0 <= position < self.children.__len__()):
            self.children.append(tree)
        else:
            self.children.insert(position, tree)

    def remove_tree(self, tree):
        self.children.remove(tree)

    def search_for_descendant(self, uuid):
        if uuid == self.id:
            return self
        for child in self.children:
            result = child.search_for_descendant(uuid)
            if result:
                return result

    def get_verify_report(self):
        report = Report()
        if not self.example:
            report.add('No examples given', Status.WARNING)
        if not self.filters:
            report.add('No filters given', Status.WARNING)

        # check if own filters hit on own example
        if self.example and self.filters:
            filter_messages = Report()
            for filter in self.filters:
                filter_messages += filter.match_example(self.example)
            highest_status = filter_messages.get_highest_status_code()
            if highest_status == Status.WARNING:
                filter_messages.add("Own filter miss on own examples", Status.ERROR)
            elif highest_status == Status.UNKNOWN and not filter_messages.get_messages_with_status_code(Status.OK):
                filter_messages.add('No filter hit any example', Status.ERROR)
            report += filter_messages

        return report

    def get_example_match_report(self, filters):
        return self._get_match_report(filters, self.example)

    def get_example_miss_report(self, filters):
        return self._get_miss_report(filters, self.example)

    def get_filter_match_report(self, example):
        return self._get_match_report(self.filters, example)

    def get_filter_miss_report(self, example):
        return self._get_miss_report(self.filters, example)

    def _get_match_report(self, filters, example):
        messages = Report()
        for filter in filters:
            messages += filter.match_example(example)
        return messages

    def _get_miss_report(self, filters, example):
        messages = Report()
        for filter in filters:
            messages += filter.miss_example(example)
        return messages

    def encode(self):
        var_dict = self.__dict__.copy()
        var_dict.pop('parent')
        var_dict['children'] = [child.encode() for child in self.children]
        var_dict['filters'] = [filter.encode() for filter in self.filters]
        return var_dict

    def to_json(self):
        return json.dumps(self.encode(), indent=4)


class Filter:
    def __init__(self, field, pattern):
        self.field = field
        self.pattern = pattern

    def match_example(self, example):
        if self.field == 'unknown':
            return Report()
        status = Status.UNKNOWN
        message = f"No example given for filter '{self.pattern}'"
        if self.field in example:
            match = re.search(self.pattern, example[self.field])
            if match:
                status = Status.OK
                message = f"Filter '{self.pattern}' matched example '{example[self.field]}'"
            else:
                status = Status.WARNING
                message = f"Filter '{self.pattern}' didn't match example '{example[self.field]}'"
        return Report(message, status)

    def miss_example(self, example):
        if self.field == 'unknown':
            return Report()
        status = Status.UNKNOWN
        message = f"Filter '{self.pattern}' did not hit any example"
        if self.field in example:
            match = re.search(f'({self.pattern})', example[self.field])
            if match:
                status = Status.WARNING
                formatted_example = f'<span class={ApiConfig.filter_hit_span_class}>{example[self.field]}</span>'
                message = f"Filter '{self.pattern}' hit example '{formatted_example}'"
            else:
                status = Status.OK
                message = f"Filter '{self.pattern}' did not hit example '{example[self.field]}, everything is OK'"
        return Report(message, status)

    def encode(self):
        return {'field': self.field, 'pattern': self.pattern}


class ReportBySource:
    def __init__(self, report=None, source='_default'):
        self.registry = {}
        if report:
            self.add(report, source)

    def add(self, report, source='_default'):
        if source not in self.registry:
            self.registry[source] = report
        else:
            self.registry[source] += report

    def get_report_with_source(self, source_name):
        report = self.registry[source_name] if source_name in self.registry else None
        return report

    def extend(self, report_registry):
        for source in report_registry.registry:
            if source in self.registry:
                self.registry[source] += report_registry.registry[source]
            else:
                self.registry[source] = report_registry.registry[source]

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __len__(self):
        return self.registry.__len__()

    def encode(self):
        return [{'source': source, 'messages': report.encode()} for source, report in self.registry.items()]


class Report:

    def __init__(self, message=None, status=Status.OK):
        self.entries = []
        if message:
            self.add(message, status)

    def add(self, message, status=Status.OK):
        if status >= ApiConfig.report_level:
            entry = Message(message, status)
            self.entries.append(entry)

    def get_highest_status_code(self):
        status = 0
        for entry in self.entries:
            if entry.status.value > status:
                status = entry.status.value
        if status:
            return status

    def get_messages_with_status_code(self, status):
        report = Report()
        for entry in self.entries:
            if entry.status is status:
                report.add(*entry)
        return report

    def __iadd__(self, other):
        self.entries += other.entries
        return self

    def __len__(self):
        return self.entries.__len__()

    def encode(self):
        return [{'message': entry.message, 'status': entry.status.name} for entry in self.entries]
