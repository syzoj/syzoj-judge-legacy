# -*- coding: utf-8 -*-
#!/usr/bin/python
import os
import time
import zipfile
import urllib
import urllib2
import json
import lorun
import codecs
from random import randint

_SYZOJ_URL = "http://localhost:5283"
_DOWNLOAD_TESTDATA_URL = _SYZOJ_URL + "/static/uploads"
_GET_TASK_URL = _SYZOJ_URL + "/api/waiting_judge"
_UPLOAD_TASK_URL = _SYZOJ_URL + "/api/update_judge"
_SESSION_ID = "233"
_BASE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))
_TESTDATA_DIR = os.path.join(_BASE_DIR, "testdata")

if not os.path.isdir(_TESTDATA_DIR):
    os.mkdir(_TESTDATA_DIR)


def compile_src(source, language, des):
    if language == "C++":
        source_file = des + "_tmp.cpp"
    elif language == "C":
        source_file = des + "_tmp.c"
    elif language == "Pascal":
        source_file = des + "_tmp.pas"
    exe_file = des

    with codecs.open(source_file, "w", "utf-8") as f:
        f.write(source)

    if os.path.isfile(des):
        os.remove(des)
    
    if language == "C++":
        os.system("g++ " + source_file + " -o " + exe_file + " -O2 -lm -DONLINE_JUDGE")
    elif language == "C":
        os.system("gcc " + source_file + " -o " + exe_file + " -O2 -lm -DONLINE_JUDGE")
    elif language == "Pascal":
        os.system("fpc " + source_file + " -O2")
        os.system("mv " + des + "_tmp " + des)
    os.remove(source_file)

    if os.path.isfile(des):
        return True
    else:
        return False


def format_ans(s):
    s = s.replace('\n', ' ').replace('\r', ' ')
    s += " "
    last = " "
    ret = ""
    for c in s:
        if c == " " and last == " ":
            continue
        ret += c
        last = c
    return ret


def check_ans(std_ans, out):
    with open(std_ans) as f:
        sa = f.read()
    with open(out) as f:
        ou = f.read()
    sa = format_ans(sa)
    ou = format_ans(ou)
    if sa == ou:
        return True
    else:
        return False


def get_judge_task():
    global _GET_TASK_URL, _SESSION_ID
    url = _GET_TASK_URL + "?" + urllib.urlencode({"session_id": _SESSION_ID})
    task = urllib2.urlopen(url).read()
    print task
    return json.loads(task)


def upload_judge_result(result, judge_id):
    global _UPLOAD_TASK_URL, _SESSION_ID
    url = _UPLOAD_TASK_URL + "/" + str(judge_id) + "?" + urllib.urlencode({"session_id": _SESSION_ID})
    data = urllib.urlencode({"result": json.dumps(result)})
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    return response.read()


def download_file(url, des):
    df = urllib2.urlopen(url)
    with open(des, "a") as f:
        while True:
            data = df.read(4096)
            if data:
                f.write(data)
            else:
                break
    df.close()


def unzip_as_testdata(testdata, des_dir):
    if not os.path.isdir(des_dir):
        os.mkdir(des_dir)

    zip_file = zipfile.ZipFile(testdata)

    for name in zip_file.namelist():
        with open(os.path.join(des_dir, name), "wb") as f:
            f.write(zip_file.read(name))
            f.close()

    zip_file.close()


def get_testdata_dir(testdata_name):
    global _TESTDATA_DIR, _DOWNLOAD_TESTDATA_URL
    testdata_dir = os.path.join(_TESTDATA_DIR, testdata_name)
    if os.path.isdir(testdata_dir):
        return testdata_dir

    tmp_zip_file = _TESTDATA_DIR + testdata_name + "_tmp.zip"
    download_file(_DOWNLOAD_TESTDATA_URL + "/" + testdata_name, tmp_zip_file)
    unzip_as_testdata(tmp_zip_file, testdata_dir)
    os.remove(tmp_zip_file)

    return testdata_dir


def shorter_read(file_name, max_len):
    with open(file_name) as f:
        s = f.read(max_len + 10)
        if len(s) > max_len:
            s = s[:max_len] + "..."
    return s


def run(exe_file, std_in, std_out, time_limit, memory_limit, file_io, file_io_input_name, file_io_output_name):
    result_str = (
        'Accepted',
        'Presentation Error',
        'Time Limit Exceed',
        'Memory Limit Exceed',
        'Wrong Answer',
        'Runtime Error',
        'Output Limit Exceed',
        'Compile Error',
        'System Error'
    )
    
    user_out = "user_tmp.out"
    std_in_f = open(std_in)
    user_out_f = open(user_out, 'w')

    if file_io:
        os.system("cp " + std_in + " " + file_io_input_name);
        std_in_f = open("/dev/null")
    run_cfg = {
        'args': ['./' + exe_file],
        'fd_in': std_in_f.fileno(),
        'fd_out': user_out_f.fileno(),
        'timelimit': time_limit,
        'memorylimit': memory_limit * 1024,
    }

    res = lorun.run(run_cfg)
    std_in_f.close()
    user_out_f.close()

    if file_io:
        os.remove(user_out)
        user_out = file_io_output_name
    result = {}
    result['status'] = result_str[res['result']]
    if res['result'] == 0:
        if not os.path.isfile(user_out):
            result['status'] = 'Wrong Answer' 
        elif not check_ans(std_out, user_out):
            print "zz"
            result['status'] = 'Wrong Answer'
    if not 'timeused' in res:
        result['time_used'] = 0
    else:
        result["time_used"] = res["timeused"]
    if not 'memoryused' in res:
        result['memory_used'] = 0
    else:
        result["memory_used"] = res["memoryused"]

    result["input"] = shorter_read(std_in, 120)
    result["answer"] = shorter_read(std_out, 120)
    
    if os.path.isfile(user_out):
        result["user_out"] = shorter_read(user_out, 120)
        os.remove(user_out)
    else:
        result["user_out"] = ""
    
    if file_io:
        os.system("rm -r " + file_io_input_name) 
    return result


def judge(source, language, time_limit, memory_limit, testdata, file_io, file_io_input_name, file_io_output_name):
    result = {"status": "Judging", "score": 0, "total_time": 0, "max_memory": 0, "case_num": 0}

    testdata_dir = get_testdata_dir(testdata)
    exe_file = "tmp_exe"

    if not compile_src(source, language, exe_file):
        result["status"] = "Compile Error"
        return result

    with open(os.path.join(testdata_dir, "data_rule.txt")) as f:
        data_rule = f.read()
    lines = data_rule.split('\n')
    for i in range(0, len(lines)):
        lines[i] = lines[i].replace('\r', '').replace('\n', '')
    dt_no = lines[0].split()
    std_in = lines[1]
    std_out = lines[2]

    for i, no in enumerate(dt_no):
        std_in_file = os.path.join(testdata_dir, std_in.replace("#", str(no)))
        std_out_file = os.path.join(testdata_dir, std_out.replace("#", str(no)))

        res = run(exe_file, std_in_file, std_out_file, time_limit, memory_limit, file_io, file_io_input_name, file_io_output_name)

        result[i] = res
        result["case_num"] += 1
        result["total_time"] += res["time_used"]
        if res["memory_used"] > result["max_memory"]:
            result["max_memory"] = res["memory_used"]

        if res["status"] == "Accepted":
            result["score"] += 1.0 / len(dt_no) * 100
        elif result["status"] == "Judging":
            result["status"] = res["status"]
    result["score"] = int(result["score"] + 0.1)
    if result["status"] == "Judging":
        result["status"] = "Accepted"
    os.remove(exe_file)
    return result


def main():
    while True:
        time.sleep(1)
        task = get_judge_task()
        if not task["have_task"]:
            continue

        try:
            result = judge(task["code"], task["language"], task["time_limit"], task["memory_limit"], task["testdata"], task["file_io"], task["file_io_input_name"], task["file_io_output_name"])
        except Exception as e:
            result = {"status": "System Error", "score": 0, "total_time": 0, "max_memory": 0, "case_num": 0}
            print e

        upload_judge_result(result, task["judge_id"])


def test_connect_to_server():
    task = get_judge_task()
    testdata_dir = get_testdata_dir(task["testdata"])
    print task
    print testdata_dir
    print upload_judge_result({"status": "System Error", "score": 0, "total_time": 0, "max_memory": 0, "case_num": 0},
                              task["judge_id"])


if __name__ == '__main__':
    # test_connect_to_server()
    # main()
    while True:
        try:
            main()
        except Exception as e:
            print e
            pass
