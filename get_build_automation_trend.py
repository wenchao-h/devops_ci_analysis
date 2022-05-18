# -*- coding: utf-8 -*-
import argparse
import csv
import datetime
import os
import math

from utils import mysql_process_client, get_fields_chinese, autolabel

import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib

fm = font_manager.FontManager()
fm.addfont("chinese.msyh.ttf")
font_manager.fontManager.ttflist.extend(fm.ttflist)
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'

plt.rc('font', size=5.79)          # controls default text sizes
plt.rc('axes', titlesize=10)     # fontsize of the axes title
plt.rc('axes', labelsize=8)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=5.79)    # fontsize of the tick labels
plt.rc('ytick', labelsize=5.79)    # fontsize of the tick labels
plt.rc('legend', fontsize=10)    # legend fontsize
plt.rc('figure', titlesize=5.79)  # fontsize of the figure title

def get_build_automation_trend(start=None, end=None, project=None,  groupby=None, output=None, encode=None, need_csv=None):
    if start:
        start = datetime.datetime.strptime(start, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
    if end:
        end = datetime.datetime.strptime(end, "%Y-%m-%d")
        end += datetime.timedelta(
                hours=23,
                minutes=59,
                seconds=59,
                milliseconds=999
            )
        end = end.strftime("%Y-%m-%d %H:%M:%S")
    time_sql = []
    if start:
        time_sql.append(" END_TIME > '%s' "%start)
    if end:
        time_sql.append(" END_TIME < '%s' "%end)
    if start is None and end is None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_sql.append(" END_TIME < '%s' "%now)
    client = mysql_process_client()
    cursor = client.cursor()
    sql = "SELECT  YEAR(END_TIME) AS YEAR, DATE_FORMAT(END_TIME, '%Y-%m') AS MONTH, {TRIGGER}, COUNT(BUILD_ID) AS BUILD_CNT FROM T_PIPELINE_BUILD_DETAIL {WHERE} GROUP BY MONTH ORDER BY MONTH"
    if groupby == "week":
        sql = "SELECT  YEAR(END_TIME) AS YEAR, WEEK(END_TIME) as WEEK, {TRIGGER}, COUNT(BUILD_ID) AS BUILD_CNT FROM T_PIPELINE_BUILD_DETAIL {WHERE} GROUP BY WEEK"
    auto_where = [" `TRIGGER` in ('TIME_TRIGGER', 'PIPELINE', 'WEB_HOOK')  "] + time_sql
    manual_where = [" `TRIGGER` not in ('TIME_TRIGGER', 'PIPELINE', 'WEB_HOOK') "] + time_sql
    if project:
        auto_where = [" PROJECT_ID = '%s'"%project] + auto_where
    auto_sql = sql.format(TRIGGER="'AUTO'", WHERE=" WHERE " + " AND ".join(auto_where))
    manual_sql = sql.format(TRIGGER="'MANUAL'", WHERE=" WHERE " + " AND ".join(manual_where))
    print("auto_sql: %s"%auto_sql)
    print("manual_sql: %s"%manual_sql)
    cursor.execute(auto_sql)
    auto_result = cursor.fetchall()
    auto_list= list(auto_result)
    if groupby == "week":
        auto_list = [(row[0], "{year}-{week:02d}".format(year=row[0], week=row[1]), row[2], row[3]) for row in auto_list]
        auto_list.sort(key=lambda row: row[1])
    # auto_list = [(*item, item)]
    auto_x_y = dict([(item[1], item[3]) for item in auto_list ])
    cursor.execute(manual_sql)
    manual_result = cursor.fetchall()
    manual_list = list(manual_result)
    if groupby == "week":
        manual_list = [(row[0], "{year}-{week:02d}".format(year=row[0], week=row[1]), row[2], row[3]) for row in manual_list]
        manual_list.sort(key=lambda row: row[1])
    manual_x_y = dict([(item[1], item[3]) for item in manual_list ])


    labels = sorted(list(set(list(auto_x_y.keys()) + list(manual_x_y.keys()))))
    auto_rate = {}
    for label in labels:
        build_count = auto_x_y.get(label, 0) + manual_x_y.get(label, 0)
        auto_y = auto_x_y.get(label, 0)
        rate = format(auto_y/build_count*100, ".1f")
        auto_rate[label] = float(rate)
    print("labels: %s"%labels)
    auto_y = [auto_x_y.get(label, 0) for label in labels]
    print("auto y: %s"%auto_y)
    manual_y = [manual_x_y.get(label, 0) for label in labels]
    print("manual y: %s"%manual_y)
    cursor.close()
    client.close()
    if not os.path.exists(output):
        os.mkdir(output)
    
    if groupby == "month":
        headers = get_fields_chinese(["YEAR", "MONTH", "TRIGGER", "BUILD_CNT"])
        if project:
            csvfile = os.path.join(output, "4-%s-project-build-automation-monthly.csv"%project)
            pngfile = os.path.join(output, "4-%s-project-build-automation-monthly.png"%project)
            xlabel = "月份"
            title = "%s项目每月构建自动化趋势"%project
            
        else:
            csvfile = os.path.join(output, "4-bkci-build-automation-monthly.csv")
            pngfile = os.path.join(output, "4-bkci-build-automation-monthly.png")
            xlabel = "月份"
            title = "蓝盾每月构建自动化趋势"
    
    elif groupby == "week":
        headers = get_fields_chinese(["YEAR", "WEEK", "TRIGGER", "BUILD_CNT"])
        if project:
            csvfile = os.path.join(output, "4-%s-project-build-automation-weekly.csv"%project)
            pngfile = os.path.join(output, "4-%s-project-build-automation-weekly.png"%project)
            xlabel = "周"
            title = "%s项目每周构建自动化趋势"%project
        else:
            csvfile = os.path.join(output, "4-bkci-build-automation-weekly.csv")
            pngfile = os.path.join(output, "4-bkci-build-automation-weekly.png")
            xlabel = "周"
            title = "蓝盾每周构建自动化趋势"
    
    # if project:
    #     csvfile = os.path.join(output, "1-%s项目构建自动化趋势.csv"%project)
    if need_csv:
        with open(csvfile, "w", newline="", encoding=encode) as f:
            writer = csv.writer(f)
            # headers = get_fields_chinese(["YEAR", "MONTH", "TRIGGER", "BUILD_CNT"])
            writer.writerow(headers)
            writer.writerows(auto_list)
            writer.writerows(manual_list)
    fig, ax1 = plt.subplots(figsize=[6.4, 5.2])
    width = 0.35
    max_y = max(auto_y) + max(manual_y)
    ax1.set_ylim(0, max_y + math.ceil(max_y/10))
    p1 = ax1.bar(labels, auto_y, width, label="自动构建", color="tab:orange")
    p2 = ax1.bar(labels, manual_y, width, label="手动构建", bottom=auto_y, color="tab:blue")

    ax1.set_ylabel('构建次数')
    ax1.set_xlabel(xlabel)
    ax1.legend()
    plt.xticks(rotation=45)
    autolabel(ax1, p1)
    autolabel(ax1, p2)

    color = 'tab:red'
    ax2 = ax1.twinx()
    rate_rows = [auto_rate.get(label, 0) for label in labels]
    print("rate_rows: %s"%rate_rows)
    ax2.plot(labels, rate_rows, color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylabel("自动构建占比(%)", color=color)

    # if project:
    ax1.set_title(title)
    # else:
    #     ax1.set_title('蓝盾构建自动化趋势')

    # if project:
    #     pngfile = os.path.join(output, "4-%s项目构建自动化趋势.png"%project)
    # else:
    #     pngfile = os.path.join(output, "4-蓝盾构建自动化趋势.png")
    plt.savefig(pngfile, dpi=300)
    print("请查看输出文件目录：%s"%output)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取指定时间范围内的手动触发构建次数和自动触发构建次数，并按月分类")
    parser.add_argument("-s", "--start", help="开始时间, 格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-e", "--end", help="结束时间，格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-p", "--project", help="项目ID")
    parser.add_argument("-g", "--groupby", help="分组统计，按照周/月", default="month")
    parser.add_argument("-o", "--output", help="结果输出目录的路径, 默认为当前路径下的output目录", default="output")
    parser.add_argument("-E","--encode", help="输出文件的编码方式，utf-8/gb18030，默认为gb18030", choices=["utf-8", "gb18030"], default="gb18030")
    parser.add_argument("-x", "--csv", help="是否生成csv", action="store_true")

    args = parser.parse_args()
    if args.start:
        try:
            datetime.datetime.strptime(args.start, "%Y-%m-%d")
        except Exception as e:
            print("start参数格式解析失败，请确认格式为%%Y-%%m-%%d, 如2022-03-29，%s"%e)
    if args.end:
        try:
            datetime.datetime.strptime(args.end, "%Y-%m-%d")
        except Exception as e:
            print("end参数格式解析失败，请确认格式为%%Y-%%m-%%d, 如2022-03-29，%s"%e)
    get_build_automation_trend(start=args.start, end=args.end, project=args.project, groupby=args.groupby, output=args.output, encode=args.encode, need_csv=args.csv)

