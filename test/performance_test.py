"""
Author: lt
Date: 2019-10-21
Description: 性能测试
"""
import sys
sys.path.append('./..')
import cProfile

from _spider import crawl_one_site


if __name__ == '__main__':
    url = 'http://www.crpharm.com'
    base_output_dir = 'output'
    max_depth = 1
    concurrent_limit = 64
    level = 2
    cProfile.run('crawl_one_site("{}", "{}", {}, {}, {})'.format(
        url, base_output_dir, max_depth, concurrent_limit, level), 'prof.out')
