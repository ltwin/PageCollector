"""
Ac自动机
"""

import os
import pickle
import codecs


class TrieNode:
    def __init__(self):
        self.success = dict()  # 转移表
        self.failure = None  # 错误表
        self.emits = set()  # 输出表


class AcAutomaton(object):

    def __init__(self, patterns, model_path=None):
        """
        :param patterns: 模式串列表
        :param model_path: AC自动机持久化位置
        """
        self._save_path = model_path
        self._patterns = patterns
        if self._save_path and os.path.exists(self._save_path):
            self._root = self.__load_corasick()
            if not self._root:
                self.refresh()
        else:
            self.refresh()

    def __insert_node(self):
        """
        Create Trie
        """
        for pattern in self._patterns:
            line = self._root
            for character in pattern:
                line = line.success.setdefault(character, TrieNode())
            line.emits.add(pattern)

    def __create_fail_path(self):
        """
        Create Fail Path
        """
        my_queue = list()
        for node in self._root.success.values():
            node.failure = self._root
            my_queue.append(node)
        while len(my_queue) > 0:
            gone_node = my_queue.pop(0)
            for k, v in gone_node.success.items():
                my_queue.append(v)
                parent_failure = gone_node.failure

                while parent_failure and k not in parent_failure.success.keys():
                    parent_failure = parent_failure.failure
                v.failure = parent_failure.success[k] if parent_failure else self._root
                if v.failure.emits:
                    v.emits = v.emits.union(v.failure.emits)

    def __save_corasick(self):
        with codecs.open(self._save_path, "wb") as f:
            pickle.dump(self._root, f)

    def __load_corasick(self):
        with codecs.open(self._save_path, "rb") as f:
            try:
                return pickle.load(f)
            except (EOFError, TypeError):
                return None

    def refresh(self):
        self._root = TrieNode()
        self.__insert_node()
        self.__create_fail_path()
        if self._save_path:
            self.__save_corasick()

    def search(self, context):
        search_result = list()
        search_node = self._root
        for char in context:
            while search_node and char not in search_node.success.keys():
                search_node = search_node.failure
            if not search_node:
                search_node = self._root
                continue
            search_node = search_node.success[char]
            if search_node.emits:
                search_result += search_node.emits
        return search_result


if __name__ == "__main__":
    data = ['he', 'she', 'his', 'hers']
    s = "ushers"
    ac = AcAutomaton(data, "model.pkl")
    print(ac.search(s))