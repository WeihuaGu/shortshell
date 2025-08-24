#!/usr/bin/env python3
import argparse

def print_list(items):
    for item in items:
        print(item)
def gen_num(n):
    """
    生成 n 位数字的所有组合，从 000...0 到 999...9
    返回一个包含所有 n 位字符串的列表
    """
    if n < 1:
        raise ValueError("位数必须大于等于1")
    
    return [str(i).zfill(n) for i in range(10**n)]
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
def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="""构建电话号码的字典 
    典型用法：
        --last 2315
        --oper cmcc
    """,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--last', type=str, required=True, help="你知道号码以什么结尾")
    parser.add_argument('--oper', type=str, required=False, help="运营商,全部all 移动cmcc 联通cucc 电信ctcc")
    args = parser.parse_args()

    # 将 last 附加到每个项目后面
    oper = args.oper
    prefixes = get_prefixes(oper)
    last = args.last
    last_n = len(last)
    middle = gen_num(11-3-last_n)
    last_list = [item + last for item in middle]
    phone_list = [x+y for x in prefixes for y in last_list]

    # 输出结果
    print_list(phone_list)


# 使用示例
if __name__ == "__main__":
    main()
