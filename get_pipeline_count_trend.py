# -*- coding: utf-8 -*-
import argparse
import csv
import datetime
import os 
from functools import reduce
import math

from utils import mysql_process_client, get_fields_chinese, autolabel, get_month_list, get_week_list

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

def get_pipeline_create_trend(start=None, end=None, groupby=None, project=None, output=None, encode=None, need_csv=None):
    if not os.path.exists(output):
        os.mkdir(output)
    start_time = None
    end_time = None
    if start:
        start_time = datetime.datetime.strptime(start, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
    if end:
        end_time = datetime.datetime.strptime(end, "%Y-%m-%d")
        end_time += datetime.timedelta(
                hours=23,
                minutes=59,
                seconds=59,
                milliseconds=999
            )
        end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
    time_sql = []
    if start_time:
        time_sql.append(" CREATE_TIME > '%s' "%start_time)
    if end_time:
        time_sql.append(" CREATE_TIME < '%s' "%end_time)
    client = mysql_process_client()
    cursor = client.cursor()
    
    total_sql = "SELECT COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO WHERE CREATE_TIME < '%s'"%start_time
    print(total_sql)
    cursor.execute(total_sql)
    total_result = cursor.fetchone()
    total = total_result[0]
    print(total)


    if project:
        total_sql = "SELECT COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO WHERE PROJECT_ID = '%s' AND CREATE_TIME < '%s'"%(project,start_time)
        print(total_sql)
        cursor.execute(total_sql)
        total_result = cursor.fetchone()
        total = total_result[0]
        print(total)
        sql_tpl = "SELECT YEAR(CREATE_TIME) AS YEAR, DATE_FORMAT(CREATE_TIME, '%Y-%m') AS MONTH, COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY MONTH ORDER BY MONTH"
        csvfile = os.path.join(output, "%s-project-pipeline-count-trend-monthly.csv"%project)
        title = "%s项目每月流水线数量变化"%project
        pngfile = "2-%s-project-pipeline-count-trend-monthly.png"%project
        xlabel = "月份"
        headers = get_fields_chinese(["YEAR", "MONTH", "PIPELINE_CREATED_CNT"])
            
        if groupby == "week":
            sql_tpl = "SELECT YEAR(CREATE_TIME) AS YEAR, WEEK(CREATE_TIME) as WEEK, COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY WEEK ORDER BY WEEK"
            csvfile = os.path.join(output, "%s项目每周流水线数量变化.csv"%project)
            title = "%s项目每周流水线数量变化"%project
            pngfile = "2-%s-project-pipeline-count-trend-weekly.png"%project
            xlabel = "周"
            headers = get_fields_chinese(["YEAR", "WEEK", "PIPELINE_CREATED_CNT"])

        where_sql = []
        where_sql += [" PROJECT_ID = '%s' "%project]
        if time_sql:
            where_sql += time_sql
        where = " WHERE " + " AND ".join(where_sql)
        sql = sql_tpl.format(WHERE=where)
        print("SQL: %s"%sql)
        cursor.execute(sql)
        result = cursor.fetchall()
        rows = list(result)
        if groupby == "week":
            rows = [(row[0], "{year}-{week:02d}".format(year=row[0], week=row[1]), row[2]) for row in rows]
            print("rows: %s"%rows)
            week_base = [row[1] for row in rows]
            print("week_base: %s"%week_base)
            week_list = get_week_list(start, datetime.datetime.today().strftime("%Y-%m-%d"))
            week_not_in_base = set(week_list) - set(week_base)
            for week in week_not_in_base:
                year = week.split("-")[0]
                rows.append((year, week, 0))
            rows.sort(key=lambda row: row[1])
            print("sorted_rows: %s"%rows)
        elif groupby == "month":
            month_list = get_month_list(start, datetime.datetime.today().strftime("%Y-%m-%d"))
            month_base = [row[1] for row in rows]
            month_not_in_base = set(month_list) - set(month_base)
            for month in month_not_in_base:
                year = month.split("-")
                rows.append((year, month, 0))
            rows.sort(key=lambda row: row[1])
            print("sorted_rows: %s"%rows)    
        # print(rows)
        base_rows = []
        for index, row in enumerate(rows):
            index_rows = [row[2] for row in rows[:index]]
            print("index_rows: %s"%index_rows)
            index_total = reduce(lambda x, y: x+y, index_rows, total)
            base_rows.append((row[0], row[1], index_total))
        print(base_rows)
        if need_csv:
            with open(csvfile, "w", newline="", encoding=encode) as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        
        labels = [row[1] for row in rows]
        base_y = [row[2] for row in base_rows]
        y = [row[2] for row in rows]

        
        fig, ax = plt.subplots(figsize=[6.4, 5.2])
        width = 0.35
        max_y = max(base_y) + max(y)
        print("max_y: %s"%max_y)
        ax.set_ylim(0, max_y + math.ceil(max_y/10))
        p1 = ax.bar(labels, base_y, width, label="存量流水线", color="tab:blue")
        p2 = ax.bar(labels, y, width, label="新增流水线", bottom=base_y, color="tab:orange")
        ax.set_ylabel("流水线数量/条")
        ax.set_xlabel(xlabel)
        ax.legend()
        plt.xticks(rotation=45)
        autolabel(ax, p1)
        autolabel(ax, p2)
        ax.set_title(title)

        # labels = [row[1] for row in rows]
        # y = [row[2] for row in rows]
        # x = list(range(len(labels)))
        # fig, ax = plt.subplots(figsize=[6.4, 5.2])
        # width = 0.35

        # p = ax.bar(labels, y, width, label=project)
        # autolabel(ax, p)

        # ax.set_xlabel(xlabel)
        # ax.set_ylabel("流水线数量/条")
        # ax.set_title(title)
        # ax.legend()
        # plt.xticks(x, labels, rotation=45)
        pngfile = os.path.join(output, pngfile)
        plt.savefig(pngfile, dpi=300)

    else:

        sql = "SELECT YEAR(CREATE_TIME) AS YEAR, DATE_FORMAT(CREATE_TIME, '%Y-%m') AS MONTH, COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY MONTH ORDER BY MONTH"
        csvfile = os.path.join(output, "2-bkci-pipeline-count-trend-monthly.csv")
        title = "蓝盾每月流水线数量变化"
        pngfile = "2-bkci-pipeline-count-trend-monthly.png"
        xlabel = "月份"
        headers = get_fields_chinese(["YEAR", "MONTH", "PIPELINE_CREATED_CNT"])

        if groupby == "week":
            sql = "SELECT YEAR(CREATE_TIME) AS YEAR, WEEK(CREATE_TIME) as WEEK,  COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY WEEK ORDER BY WEEK"
            csvfile = os.path.join(output, "2-bkci-pipeline-count-trend-weekly.csv")
            title = "蓝盾每周流水线数量变化"
            pngfile = '2-bkci-pipeline-count-trend-monthly.png'
            xlabel = "周"
            headers = get_fields_chinese(["YEAR", "WEEK", "PIPELINE_CREATED_CNT"])

        where_sql = ""
        if time_sql:
            where_sql += " WHERE " + " AND ".join(time_sql)
        sql = sql.format(WHERE=where_sql)
        print("SQL: %s"%sql)
        cursor.execute(sql)
        result = cursor.fetchall()
        rows = list(result)
        if groupby == "week":
            rows = [(row[0], "{year}-{week:02d}".format(year=row[0], week=row[1]), row[2]) for row in rows]
            week_base = [row[1] for row in rows]
            print("week_base: %s"%week_base)
            week_list = get_week_list(start, datetime.datetime.today().strftime("%Y-%m-%d"))
            week_not_in_base = set(week_list) - set(week_base)
            for week in week_not_in_base:
                year = week.split("-")[0]
                rows.append((year, week, 0))
            rows.sort(key=lambda row: row[1])
            print("sorted_rows: %s"%rows)
        elif groupby == "month":
            month_list = get_month_list(start, datetime.datetime.today().strftime("%Y-%m-%d"))
            month_base = [row[1] for row in rows]
            month_not_in_base = set(month_list) - set(month_base)
            for month in month_not_in_base:
                year = month.split("-")
                rows.append((year, month, 0))
            rows.sort(key=lambda row: row[1])
            print("sorted_rows: %s"%rows)

        base_rows = []
        for index, row in enumerate(rows):
            index_rows = [row[2] for row in rows[:index]]
            print("index_rows: %s"%index_rows)
            index_total = reduce(lambda x, y: x+y, index_rows, total)
            base_rows.append((row[0], row[1], index_total))
        # print(base_rows)
        if need_csv:
            with open(csvfile, "w", newline="", encoding=encode) as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        
        labels = [row[1] for row in rows]
        base_y = [row[2] for row in base_rows]
        print("base_y: %s"%base_y)
        y = [row[2] for row in rows]
        print("y: %s"%y)
        fig, ax = plt.subplots(figsize=[6.4, 5.2])
        max_y = max(base_y) + max(y)
        print("max_y: %s"%max_y)
        ax.set_ylim(0, max_y + math.ceil(max_y/10))
        width = 0.35
        p1 = ax.bar(labels, base_y, width, label="存量流水线", color="tab:blue")
        p2 = ax.bar(labels, y, width, label="新增流水线", bottom=base_y, color="tab:orange")

        ax.set_ylabel("流水线数量/条")
        ax.set_xlabel(xlabel)
        ax.legend()
        plt.xticks(rotation=45)
        autolabel(ax, p1)
        autolabel(ax, p2)
        ax.set_title(title)
        pngfile = os.path.join(output, pngfile)
        plt.savefig(pngfile, dpi=300)
    cursor.close()
    client.close()
    print("请查看输出结果文件: %s"%output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取指定时间范围内流水线的新建数")
    parser.add_argument("-s", "--start", help="开始时间, 格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-e", "--end", help="结束时间，格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-g", "--groupby", help="分组，每月/每周新增数", default="month")
    parser.add_argument("-p", "--project", help="项目ID，多个项目ID英文逗号分隔，不指定项目名称则默认统计所有项目的构建成功率", default=None)
    parser.add_argument("-o", "--output", help="输出文件路径目录，默认输出目录是当前路径下output", default="output")
    parser.add_argument("-E", "--encode", help="输出文件的编码方式，utf-8/gb18030，默认为gb18030", choices=["utf-8", "gb18030"], default="gb18030")
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
    get_pipeline_create_trend(start=args.start, end=args.end, groupby=args.groupby, project=args.project, output=args.output, encode=args.encode, need_csv=args.csv)
