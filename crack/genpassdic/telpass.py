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
def cat_str(code,head,tail):
    for num in gen_num(7):
        s = head + code + num + tail
        yield s

def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="""构建电话号码的字典 
    典型用法：
        --last 2315
        --oper cmcc
    """,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--code', type=str, required=True, help="区号")
    parser.add_argument('--head', type=str, required=False, help="传一个前缀")
    parser.add_argument('--tail', type=str, required=False, help="传一个后缀")
    args = parser.parse_args()

    # 将 last 附加到每个项目后面
    code = args.code
    head = args.head
    tail = args.tail
    if head == None:
        head = ""
    if tail == None:
        tail = ""
    gen = cat_str(code,head,tail)

    # 输出结果
    for phonestr in gen:
        print(phonestr)


# 使用示例
if __name__ == "__main__":
    main()
