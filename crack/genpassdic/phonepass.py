#!/usr/bin/env python3
import argparse

def has_consecutive(s, min_consecutive):
    """
    检查字符串 s 中是否有 min_consecutive 个或以上连续相同的数字
    """
    if min_consecutive < 1:
        raise ValueError("min_consecutive 必须大于等于1")
    if len(s) < min_consecutive:
        return False  # 字符串太短，不可能有连续 n 个

    count = 1  # 当前连续相同字符的个数
    for i in range(1, len(s)):
        if s[i] == s[i-1]:
            count += 1
        else:
            count = 1  # 重置计数
        if count >= min_consecutive:
            return True
    return False

def gen_num(n):
    """
    生成 n 位数字的所有组合，从 000...0 到 999...9
    返回一个包含所有 n 位字符串的列表
    """
    min_consecutive = 4
    if n < 1:
        raise ValueError("位数必须大于等于1")
    for i in range(10**n):
        s = str(i).zfill(n)
        if not has_consecutive(s, min_consecutive):
            yield s

def get_prefixes(operator=None):
    """
    返回中国所有手机号段（截至2024年）
    包含三大运营商和虚拟运营商的号段
    """
    # 中国移动
    mobile_cmcc = [
        '134', '135', '136', '137', '138', '139',  # 2G/3G号段
        '144', '147', '148',  # 物联网号段
        '150', '151', '152', '157', '158', '159',  # 3G号段
        '172', '178', '182', '183', '184', '187', '188', '195', '197',  # 4G/5G号段
        '198'  # 4G号段
    ]
    # 中国联通
    mobile_cucc = [
        '130', '131', '132',  # 2G/3G号段
        '140', '145', '146',  # 物联网号段
        '155', '156',  # 3G号段
        '166', '167', '171', '175', '176', '185', '186', '196'  # 4G/5G号段
    ]
    # 中国电信
    mobile_ctcc = [
        '133', '141', '149',  # 2G/3G和物联网号段
        '153', '162', '170', '173', '174', '177', '180', '181', '189', '190', '191', '193', '199'  # 3G/4G/5G号段
    ]
    # 中国广电（新增）
    mobile_cbn = [
        '192'
    ]
    # 运营商映射字典
    operator_map = {
        'cmcc': mobile_cmcc,
        'cucc': mobile_cucc,
        'ctcc': mobile_ctcc,
        'cbn': mobile_cbn,
        'all': mobile_cmcc + mobile_cucc + mobile_ctcc + mobile_cbn
    }
    if operator is None or operator.lower() == 'all':
        all_prefixes = operator_map['all']
    elif operator.lower() in operator_map:
        all_prefixes = operator_map[operator.lower()]
    else:
        all_prefixes = operator_map['all']

    # 去重并排序
    all_prefixes = sorted(set(all_prefixes))
    return all_prefixes
def cat_str(head_list,middle_n,last_str):
    for head_item in head_list:
        for middle_num in gen_num(middle_n):
            yield head_item + middle_num + last_str

def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="""构建电话号码的字典 
    典型用法：
        --last 2315
        --oper cmcc
    """,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--last', type=str, required=True, help="你知道号码以什么结尾,none表示你不知道以什么结尾")
    parser.add_argument('--oper', type=str, required=False, help="运营商,全部all 移动cmcc 联通cucc 电信ctcc")
    parser.add_argument('--head', type=str, required=False, help="给手机号码传一个前缀")
    parser.add_argument('--tail', type=str, required=False, help="给手机号码传一个后缀")
    args = parser.parse_args()

    # 将 last 附加到每个项目后面
    oper = args.oper
    prefixes = get_prefixes(oper)
    head = args.head
    last = args.last
    tail = args.tail
    if head != None:
        head_list = [head + item for item in prefixes]
    else:
        head_list = prefixes
    if last == 'none':
        last_n = 0
        last = ""
    else:
        last_n = len(last)
    middle_n = 11-3-last_n
    if tail == None:
        last_str = last
    else:
        last_str = last + tail
    gen = cat_str(head_list,middle_n,last_str)

    # 输出结果
    for phonestr in gen:
        print(phonestr)


# 使用示例
if __name__ == "__main__":
    main()
