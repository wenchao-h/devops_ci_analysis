import pymysql
import json
import datetime
from dateutil.relativedelta  import * 

FIELDS_MAP = {
    "DAY": "日期",
    "MONTH": "月份",
    "WEEK": "周",
    "YEAR": "年份",
    "TRIGGER": "流水线触发方式",
    "BUILD_CNT": "构建次数",
    "PIPELINE_CREATED_CNT": "流水线新建数",
    "BUILD_SUCCESS": "成功构建次数",
    "BUILD_FAILED": "构建失败次数",
    "BUILD_SUCCESS_RATE": "构建成功率",
    "BULD_FAILED_RATE": "构建失败率",
    "BUILD_TOTAL": "构建总次数",
    "ATOM_CODE": "插件代码",
    "ATOM_NAME": "插件名称",
    "ATOM_USED": "插件使用数",
    "PIPELINE_NAME": "流水线名称",
    "PIPELINE_ID": "流水线ID",
    "PROJECT_ID": "项目ID",
    "BUILD_NUM": "构建次数",
    "BUILD_NO": "构建号",
    "FINISH_COUNT": "完成次数",
    "RUNNING_COUNT": "运行次数",
    "QUEUE_COUNT": "排队次数",
    "LATEST_BUILD_ID": "最近构建ID",
    "LATEST_TASK_ID": "最近任务ID",
    "LATEST_START_USER": "最近构建启动者",
    "LATEST_START_TIME": "最近构建启动时间",
    "LATEST_END_TIME": "最近构建结束时间",
    "LATEST_TASK_COUNT": "最近任务计数",
    "LATEST_TASK_NAME": "最近任务名称",
    "LATEST_STATUS": "最近构建状态",
    "BUILD_NUM_ALIAS": "自定义构建号",
    "NOT_USE_DAYS": "未使用天数",
}

def get_fields_chinese(fields=[], fields_map=FIELDS_MAP):
    """
    fileds: ["T_PIPELINE_INFO.PIPELINE_NAME", "T_PIPELINE_BUILD_SUMMARY.PIPELINE_ID"]
    return: ["流水线名称", "流水线ID"]
    """
    fields_chinese = []
    for field in fields:
        field_key = field.split(".")[-1]
        fields_chinese.append(fields_map[field_key])
    return fields_chinese

def get_config():
    with open("config.json", "r") as f:
        config = json.loads(f.read())
    return config

def mysql_project_client():
    config = get_config()
    client = pymysql.connect(
        host=config["host"],
        user=config["user"],
        port=config["port"],
        password=config["password"],
        db="devops_ci_project",
        charset='utf8'
    )
    return client

def mysql_process_client():
    config = get_config()
    client = pymysql.connect(
        host=config["host"],
        user=config["user"],
        port=config["port"],
        password=config["password"],
        db="devops_ci_process",
        charset='utf8'
    )
    return client

def mysql_store_client():
    config = get_config()
    client = pymysql.connect(
        host=config["host"],
        user=config["user"],
        port=config["port"],
        password=config["password"],
        db="devops_ci_store",
        charset='utf8'
    )
    return client

def autolabel(ax, rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        if height == 0:
            continue
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, rect.get_y() + height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom') 

def autolabel_color(ax, rects, color):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, rect.get_y() + height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', color=color)                   
    

def get_week_list(start, end):
    """
    start: %Y-%m-%d, 2022-01-01
    end: %Y-%m-%d, 2022-03-01
    return: ["2022-01", "2022-02",  ..., "2022-09"]
    """
    start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
    end_date= datetime.datetime.strptime(end, "%Y-%m-%d")
    incre_date = start_date
    week_list = []
    while incre_date <= end_date:
        week_list.append(incre_date.strftime("%Y-%W"))
        incre_date += datetime.timedelta(days=1)
    week_list = list(set(week_list))
    week_list.sort()
    print("week_list: %s"%week_list)
    return week_list

def get_month_list(start, end):
    """
    start: %Y-%m-%d, 2022-01-01
    end: %Y-%m-%d, 2022-03-01
    return: ["2022-01", "2022-02", "2022-03"]
    """
    start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
    end_date= datetime.datetime.strptime(end, "%Y-%m-%d")
    incre_date = start_date
    month_list = []
    while incre_date <= end_date:
        month_list.append(incre_date.strftime("%Y-%m"))
        incre_date += relativedelta(months=+1)
    month_list = list(set(month_list))
    month_list.sort()
    print("month_list: %s"%month_list)
    return month_list
