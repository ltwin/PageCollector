"""
Author: lt
Date: 2019-07-23
Desc: 自定义数据库异常
"""


class ModelException(Exception):
    """
    自定义异常
    """

    def __init__(self, message='Error occurred in database operation!'):
        self.value = str(message)
        Exception.__init__(self, self.value)

    def __str__(self):
        return self.value


class IdException(ModelException):
    """
    不合法的ObjectId异常
    """

    def __init__(self, message='Illegal input ObjectId!'):
        self.value = str(message)
        Exception.__init__(self, self.value)

    def __str__(self):
        return self.value


class OverdueOperationException(ModelException):
    """
    操作过期数据异常
    """

    def __init__(self, message='Operate the overdue data!'):
        self.value = str(message)
        ModelException.__init__(self, self.value)

    def __str__(self):
        return self.value


class OperateNotExistsDataException(ModelException):
    """
    操作不存在的数据异常
    """

    def __init__(self, message='The operated data not exist!'):
        self.value = str(message)
        ModelException.__init__(self, self.value)

    def __str__(self):
        return self.value


class FindException(ModelException):
    """
    查询数据异常
    """

    def __init__(self, message='Find data from database failed!'):
        self.value = str(message)
        ModelException.__init__(self, self.value)

    def __str__(self):
        return self.value


class InsertException(ModelException):
    """
    插入数据异常
    """

    def __init__(self, message='Insert data to database failed!'):
        self.value = str(message)
        ModelException.__init__(self, self.value)

    def __str__(self):
        return self.value


class UpdateException(ModelException):
    """
    更新数据库异常
    """

    def __init__(self, message='Update data from database failed!'):
        self.value = str(message)
        ModelException.__init__(self, self.value)

    def __str__(self):
        return self.value


class DeleteException(ModelException):
    """
    删除数据库异常
    """

    def __init__(self, message='Delete data from database failed!'):
        self.value = str(message)
        ModelException.__init__(self, self.value)

    def __str__(self):
        return self.value
