#coding :utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2018 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
该文件主要是负责一些对于code名称的处理
"""


def QA_util_code_tostr(code):
    """
    将所有沪深股票从数字转化到6位的代码

    因为有时候在csv等转换的时候,诸如 000001的股票会变成office强制转化成数字1

    """
    return '00000{}'.format(str(code)[0:6])[-6:]


def QA_util_code_tolist(code, auto_fill=True):
    """转换code==> list

    Arguments:
        code {[type]} -- [description]

    Keyword Arguments:
        auto_fill {bool} -- 是否自动补全(一般是用于股票/指数/etf等6位数,期货不适用) (default: {True})

    Returns:
        [list] -- [description]
    """

    if isinstance(code, str):
        if auto_fill:
            return [QA_util_code_tostr(code)]
        else:
            return [code]

    elif isinstance(code, list):
        if auto_fill:
            return [QA_util_code_tostr(item) for item in code]
        else:
            return [item for item in code]
