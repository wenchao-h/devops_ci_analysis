# -*- coding: utf-8 -*-
import argparse
import csv
import datetime
import os
import sys
from functools import reduce
import math

from utils import mysql_process_client, get_fields_chinese, autolabel, autolabel_color
import matplotlib.pyplot as plt
import pandas as pd

from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
import matplotlib

fm = font_manager.FontManager()
fm.addfont("chinese.msyh.ttf")
font_manager.fontManager.ttflist.extend(fm.ttflist)
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'

# plt.rc('font', size=5.79)          # controls default text sizes
# plt.rc('axes', titlesize=10)     # fontsize of the axes title
# plt.rc('axes', labelsize=5.79)    # fontsize of the x and y labels
# plt.rc('xtick', labelsize=5.79)    # fontsize of the tick labels
# plt.rc('ytick', labelsize=5.79)    # fontsize of the tick labels
# plt.rc('legend', fontsize=10)    # legend fontsize
# plt.rc('figure', titlesize=5.79)  # fontsize of the figure title


DIMENSION = [
    "pipeline",
    "project",
    ]
GROUPBY = [
    "month",
    "week"
]


def get_project_build_success(cursor, time_sql, output, project, groupby, encode, title, filename, xlabel, need_csv):
    plt.rc('font', size=5.79)          # controls default text sizes
    plt.rc('axes', titlesize=10)     # fontsize of the axes title
    plt.rc('axes', labelsize=8)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=5.79)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=5.79)    # fontsize of the tick labels
    plt.rc('legend', fontsize=10)    # legend fontsize
    plt.rc('figure', titlesize=5.79)  # fontsize of the figure title
    csvfile = os.path.join(output, "2-%s.csv"%filename)
    month_headers = get_fields_chinese(["MONTH", "PROJECT_ID", "BUILD_SUCCESS", "BUILD_TOTAL", "BUILD_SUCCESS_RATE"])
    week_headers = get_fields_chinese(["WEEK", "PROJECT_ID", "BUILD_SUCCESS", "BUILD_TOTAL", "BUILD_SUCCESS_RATE"])
    headers = ""

    where_sql = [" PROJECT_ID='%s' "%project]
    if time_sql:
        where_sql += time_sql
    sql = ""
    if groupby == "month":
        headers = month_headers
        sql += "select DATE_FORMAT(END_TIME, '%Y-%m') as MONTH, sum(case when STATUS=0 then 1 else 0 end ) as BUILD_SUCCESS,  count(STATUS) as BUILD_TOTAL from T_PIPELINE_BUILD_HISTORY {WHERE} group by MONTH"
    elif groupby == "week":
        headers = week_headers
        sql += "select YEAR(END_TIME) as YEAR, WEEK(END_TIME) as WEEK, sum(case when STATUS=0 then 1 else 0 end ) as BUILD_SUCCESS, count(STATUS) as BUILD_TOTAL from T_PIPELINE_BUILD_HISTORY {WHERE} group by WEEK order by YEAR asc, WEEK asc  "
    sql = sql.format(WHERE=" WHERE " + " AND ".join(where_sql))
    print("SQL: %s"%sql)
    cursor.execute(sql)
    result = cursor.fetchall()
    rows = []
    if groupby == "month":
        rows = [(*row, format(row[1]/row[2]*100, ".1f")) for row in result] # [(2022-01, 3, 4, 75.0)]
    elif groupby == "week":
        rows = [("{year}-{week:02d}".format(year=row[0], week=row[1]), row[2], row[3], format(row[2]/row[3]*100, ".1f")) for row in result]
    if need_csv:
        with open(csvfile, "w", newline="", encoding=encode) as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    
    xticks = [row[0] for row in rows]
    total_rows = [row[2] for row in rows ]
    rate_rows = [float(row[3]) for row in rows ]

    x = list(range(1,len(xticks)+1))
    width = 0.35
    fig, ax1 = plt.subplots(figsize=[6.4, 5.2])

    color1 = 'tab:blue'
    color2 = 'tab:red'
    max_y = max(total_rows)
    ax1.set_ylim(0, max_y + math.ceil(max_y/10))
    p1 = ax1.bar(x, total_rows, width, color=color1)
    autolabel_color(ax1, p1, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    plt.xticks(x, xticks, rotation=45)
    ax2 = ax1.twinx()
    ax2.plot(x, rate_rows, color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)

    ax1.set_title(title)
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel("????????????", color=color1)
    ax2.set_ylabel("???????????????(%)", color=color2)

    png_path = os.path.join(output, "3-%s.png"%filename)
    plt.savefig(png_path, dpi=300)

def get_build_summary(start=None, end=None, dim=None, project=None, top=None, groupby=None, output=None, encode=None, need_csv=None):

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
    if not os.path.exists(output):
        os.mkdir(output)
    if dim == "project":
        if project is not None:
            if groupby == "month":
                # ??????????????????ID?????????????????????????????????

                get_project_build_success(cursor, time_sql, output, project, groupby, encode, "%s????????????????????????"%project, "%s-project-build-summay-monthly"%project, "??????", need_csv)
                pass
            elif groupby == "week":
                # ??????????????????ID?????????????????????????????????

                get_project_build_success(cursor, time_sql, output, project, groupby, encode, "%s????????????????????????"%project, "%s-project-build-summary-weekly"%project, "???", need_csv)
                pass
            else:
                print("groupby?????????month??????week.")
                sys.exit(1)
            pass
        elif project is None:
            if groupby == "month":
                plt.rc('font', size=5.79)          # controls default text sizes
                plt.rc('axes', titlesize=10)     # fontsize of the axes title
                plt.rc('axes', labelsize=8)    # fontsize of the x and y labels
                plt.rc('xtick', labelsize=5.79)    # fontsize of the tick labels
                plt.rc('ytick', labelsize=5.79)    # fontsize of the tick labels
                plt.rc('legend', fontsize=10)    # legend fontsize
                plt.rc('figure', titlesize=5.79)  # fontsize of the figure title
                sql = "SELECT DATE_FORMAT(END_TIME, '%Y-%m') as MONTH,  SUM(CASE WHEN STATUS=0 THEN 1 ELSE 0 END ) AS BUILD_SUCCESS, COUNT(STATUS) AS BUILD_TOTAL FROM T_PIPELINE_BUILD_HISTORY  {WHERE}  GROUP BY MONTH "
                if time_sql:
                    sql = sql.format(WHERE= " WHERE " + "AND".join(time_sql))
                print("SQL: %s"%sql)
                headers = get_fields_chinese(["MONTH", "BUILD_SUCCESS", "BUILD_TOTAL", "BUILD_SUCCESS_RATE"])
                cursor.execute(sql)
                result = cursor.fetchall()
                rows = list(result)
                rows = [(*row, format(row[1]/row[2]*100, ".1f")) for row in rows]
                csvfile = os.path.join(output, "3-bkci-build-summary-monthly.csv")
                if need_csv:
                    with open(csvfile, "w", newline="", encoding=encode) as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(rows)
                
                xticks = [row[0] for row in rows]
                total_rows = [row[2] for row in rows ]
                rate_rows = [float(row[3]) for row in rows ]

                x = list(range(1,len(xticks)+1))
                width = 0.35
                fig, ax1 = plt.subplots(figsize=[6.4, 5.2])
                max_y = max(total_rows)
                ax1.set_ylim(0, max_y + math.ceil(max_y/10))
                color1 = 'tab:blue'
                color2 = 'tab:red'
                p1 = ax1.bar(x, total_rows, width, color=color1)
                autolabel_color(ax1, p1, color=color1)
                ax1.tick_params(axis='y', labelcolor=color1)
                plt.xticks(x, xticks, rotation=45)
                ax2 = ax1.twinx()
                ax2.plot(x, rate_rows, color=color2)
                ax2.tick_params(axis='y', labelcolor=color2)

                ax1.set_title("?????????????????????????????????")
                ax1.set_xlabel("??????")
                ax1.set_ylabel("????????????", color=color1)
                ax2.set_ylabel("???????????????(%)", color=color2)

                png_path = os.path.join(output, "3-bkci-build-summary-monthly.png")
                plt.savefig(png_path, dpi=300)
                pass
            elif groupby == "week":
                plt.rc('font', size=5.79)          # controls default text sizes
                plt.rc('axes', titlesize=10)     # fontsize of the axes title
                plt.rc('axes', labelsize=8)    # fontsize of the x and y labels
                plt.rc('xtick', labelsize=5.79)    # fontsize of the tick labels
                plt.rc('ytick', labelsize=5.79)    # fontsize of the tick labels
                plt.rc('legend', fontsize=10)    # legend fontsize
                plt.rc('figure', titlesize=5.79)  # fontsize of the figure title
                sql = "select YEAR(END_TIME) as YEAR, WEEK(END_TIME) as WEEK, sum(case when STATUS=0 then 1 else 0 end ) as BUILD_SUCCESS, count(STATUS) as BUILD_TOTAL from T_PIPELINE_BUILD_HISTORY {WHERE} group by WEEK order by YEAR asc, WEEK asc  "
                if time_sql:
                    sql = sql.format(WHERE= " WHERE " + "AND".join(time_sql))
                print("SQL: %s"%sql)
                headers = get_fields_chinese(["WEEK", "BUILD_SUCCESS", "BUILD_TOTAL", "BUILD_SUCCESS_RATE"])
                cursor.execute(sql)
                result = cursor.fetchall()
                rows = [("{year}-{week:02d}".format(year=row[0], week=row[1]), row[2], row[3], format(row[2]/row[3]*100, ".1f")) for row in result]
                rows.sort(key=lambda row: row[0])
                print("rows: %s"%rows)
                csvfile = os.path.join(output, "3-bkci-build-summary-weekly.csv")
                if need_csv:
                    with open(csvfile, "w", newline="", encoding=encode) as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(rows)

                xticks = [row[0] for row in rows]
                total_rows = [row[2] for row in rows ]
                print("total_rows: %s"%total_rows)
                rate_rows = [float(row[3]) for row in rows ]

                x = list(range(1,len(xticks)+1))
                width = 0.35
                fig, ax1 = plt.subplots(figsize=[6.4, 5.2])
                max_y = max(total_rows)
                ax1.set_ylim(0, max_y + math.ceil(max_y/10))
                color1 = 'tab:blue'
                color2 = 'tab:red'
                p1 = ax1.bar(x, total_rows, width, color=color1)
                autolabel_color(ax1, p1, color=color1)
                ax1.tick_params(axis='y', labelcolor=color1)
                plt.xticks(x, xticks, rotation=45)
                ax2 = ax1.twinx()
                ax2.plot(x, rate_rows, color=color2)
                ax2.tick_params(axis='y', labelcolor=color2)

                ax1.set_title("?????????????????????????????????")
                ax1.set_xlabel("???")
                ax1.set_ylabel("????????????", color=color1)
                ax2.set_ylabel("???????????????(%)", color=color2)

                png_path = os.path.join(output, "3-bkci-build-summary-weekly.png")
                plt.savefig(png_path, dpi=300)
                pass
            else:
                # ????????????????????????????????????????????????????????????????????????????????????

                sql = "SELECT PROJECT_ID, SUM(CASE WHEN STATUS=0 THEN 1 ELSE 0 END ) AS BUILD_SUCCESS, COUNT(STATUS) AS BUILD_TOTAL FROM T_PIPELINE_BUILD_HISTORY  {WHERE}  GROUP BY PROJECT_ID ORDER BY BUILD_TOTAL DESC "
                if time_sql:
                    sql = sql.format(WHERE= " WHERE " + "AND".join(time_sql))
                print("SQL: %s"%sql)
                cursor.execute(sql)
                result = cursor.fetchall()

                rows = [(*row, format(row[1]/row[2]*100, '.1f')) for row in result]
                build_total = reduce(lambda x, y: x + y, map(lambda row: row[2], rows))
                success_total = reduce(lambda x, y: x + y, map(lambda row: row[1], rows))
                last_row = [("??????", success_total, build_total, format(success_total/build_total*100, ".1f"))]
                rows.extend(last_row)
                headers = get_fields_chinese(["PROJECT_ID", "BUILD_SUCCESS", "BUILD_TOTAL", "BUILD_SUCCESS_RATE"])
                csvfile = os.path.join(output, "5-bkci-build-summary-of-projects.csv")
                if need_csv:
                    with open(csvfile, "w", newline="", encoding=encode) as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(rows)

                # draw a table
                df = pd.DataFrame(rows, columns=headers)
                fig, ax =plt.subplots()
                ax.axis('tight')
                ax.axis('off')
                table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center", bbox=[0, 0, 1,1])
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                table.auto_set_column_width(col=list(range(len(df.columns))))
                for (row, col), cell in table.get_celld().items():
                    if (row == 0):
                        cell.set_text_props(fontproperties=FontProperties(weight='bold'))
                ax.set_title("???????????????????????????")
                pngfile = os.path.join(output, '5-bkci-build-summary-of-projects.png')
                plt.savefig(pngfile, dpi=300)
    elif dim == "pipeline":
        if project:
            projects = project.split(",")
            proj = projects[0]
            if top:
                headers = get_fields_chinese(["PIPELINE_NAME", "BUILD_SUCCESS", "BUILD_FAILED", "BUILD_TOTAL", "BUILD_SUCCESS_RATE", "BULD_FAILED_RATE"])
                # sql = "select T_PIPELINE_INFO.PIPELINE_NAME as PIPELINE_NAME,  sum(case when STATUS=0 then 1 else 0 end ) as BUILD_SUCCESS, count(STATUS) as BUILD_TOTAL from T_PIPELINE_BUILD_HISTORY LEFT JOIN T_PIPELINE_INFO ON T_PIPELINE_BUILD_HISTORY.PIPELINE_ID=T_PIPELINE_INFO.PIPELINE_ID {WHERE} GROUP BY PIPELINE_NAME ORDER BY BUILD_TOTAL DESC LIMIT %d "%top
                sql = "select T_PIPELINE_INFO.PIPELINE_NAME as PIPELINE_NAME,  sum(case when STATUS=0 then 1 else 0 end ) as BUILD_SUCCESS,  sum(case when STATUS=1 then 1 else 0 end ) as BUILD_FAILED,  count(STATUS) as BUILD_TOTAL from T_PIPELINE_BUILD_HISTORY LEFT JOIN T_PIPELINE_INFO ON T_PIPELINE_BUILD_HISTORY.PIPELINE_ID=T_PIPELINE_INFO.PIPELINE_ID {WHERE} GROUP BY PIPELINE_NAME ORDER BY BUILD_TOTAL DESC"
                where_sql = " WHERE T_PIPELINE_BUILD_HISTORY.PROJECT_ID = '%s' "%proj
                if time_sql:
                    where_sql += " AND " + " AND ".join(time_sql)
                sql = sql.format(WHERE=where_sql)
                print("SQL: %s"%sql)
                cursor.execute(sql)
                result = cursor.fetchall()

                rows = [(*row, format(row[1]/row[3]*100, '.1f'), format(row[2]/row[3]*100, ".1f")) for row in result]

                # ????????????top x
                build_top_rows = sorted(rows, key=lambda row: row[3], reverse=True)[:top]
                selected_rows = [(row[0], row[1], row[3], row[4]) for row in build_top_rows]
                headers = get_fields_chinese(["PIPELINE_NAME", "BUILD_SUCCESS", "BUILD_TOTAL", "BUILD_SUCCESS_RATE"])
                csvfile = os.path.join(output, "5-%s-project-pipeline-build-count-top%s.csv"%(proj, top))
                if need_csv:
                    with open(csvfile, "w", newline="", encoding=encode) as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(selected_rows)
                # draw a table
                df = pd.DataFrame(selected_rows, columns=headers)
                # fig, ax =plt.subplots(figsize=[6.4, 5.2])
                fig, ax = plt.subplots()
                # ax.axis('tight')
                ax.axis('off')
                table = ax.table(cellText=df.values,colLabels=df.columns,cellLoc="center", loc="center")
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                table.auto_set_column_width(col=list(range(len(df.columns))))
                for (row, col), cell in table.get_celld().items():
                    if (row == 0):
                        cell.set_text_props(fontproperties=FontProperties(weight='bold'))
                ax.set_title("%s???????????????????????????top%s"%(proj, top))
                pngfile = os.path.join(output, "5-%s-project-pipeline-build-count-top%s.png"%(proj, top))
                plt.savefig(pngfile, dpi=300)

                # ???????????????top x
                failed_top_rows = sorted(rows, key=lambda row: float(row[5]), reverse=True)[:top]
                selected_rows = [(row[0], row[2], row[3], row[5]) for row in failed_top_rows]
                headers = get_fields_chinese(["PIPELINE_NAME", "BUILD_FAILED", "BUILD_TOTAL", "BULD_FAILED_RATE"])
                csvfile = os.path.join(output, "6-%s-project-build-failed-rate-top%s.csv"%(proj, top))
                if need_csv:
                    with open(csvfile, "w", newline="", encoding=encode) as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(selected_rows)
                # draw a table
                df = pd.DataFrame(selected_rows, columns=headers)
                # fig, ax =plt.subplots(figsize=[6.4, 5.2])
                fig, ax = plt.subplots()
                # ax.axis('tight')
                ax.axis('off')
                table = ax.table(cellText=df.values,colLabels=df.columns,cellLoc="center", loc="center")
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                table.auto_set_column_width(col=list(range(len(df.columns))))
                for (row, col), cell in table.get_celld().items():
                    if (row == 0):
                        cell.set_text_props(fontproperties=FontProperties(weight='bold'))
                ax.set_title("%s??????????????????????????????top%s"%(proj, top))
                pngfile = os.path.join(output, "6-%s-project-build-failed-rate-top%s.png"%(proj, top))
                plt.savefig(pngfile, dpi=300)
                

            else:
                print("?????????top??????")
                sys.exit(1)
        else:
            print("project????????????????????????????????????ID, ??????????????????ID???????????????????????????ID")
            sys.exit(1)

    cursor.close()
    client.close()
    print("?????????????????????????????????: %s"%output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="???????????????????????????????????????/????????????????????????????????????????????????????????????????????????????????????")
    parser.add_argument("-s","--start", help="????????????, ?????????%%Y-%%m-%%d, ???2022-03-29")
    parser.add_argument("-e","--end", help="????????????????????????%%Y-%%m-%%d, ???2022-03-29")
    parser.add_argument("-d","--dim", help="?????????project/pipline, ????????????/???????????????????????????????????????", choices=DIMENSION, default="project")
    parser.add_argument("-p","--project", help="??????ID???????????????ID???????????????????????????????????????????????????????????????????????????????????????", default=None)
    parser.add_argument("-t","--top", help="???????????????x????????????", default=10, type=int)
    parser.add_argument("-g","--groupby", help="?????????????????????????????????????????????week/month??????????????????", default=None)
    parser.add_argument("-o","--output", help="???????????????????????????, ???????????????????????????output??????", default="output")
    parser.add_argument("-E","--encode", help="??????????????????????????????utf-8/gb18030????????????gb18030", choices=["utf-8", "gb18030"], default="gb18030")
    parser.add_argument("-x", "--csv", help="????????????csv", action="store_true")
    args = parser.parse_args()
    if args.start:
        try:
            datetime.datetime.strptime(args.start, "%Y-%m-%d")
        except Exception as e:
            print("start?????????????????????????????????????????????%%Y-%%m-%%d, ???2022-03-29???%s"%e)
    if args.end:
        try:
            datetime.datetime.strptime(args.end, "%Y-%m-%d")
        except Exception as e:
            print("end?????????????????????????????????????????????%%Y-%%m-%%d, ???2022-03-29???%s"%e)
    get_build_summary(start=args.start, end=args.end, dim=args.dim, project=args.project, top=args.top, groupby=args.groupby, output=args.output, encode=args.encode, need_csv=args.csv)
