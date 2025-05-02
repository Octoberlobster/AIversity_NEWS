import schedule
import subprocess
import time

# 定義任務：呼叫不同的 Python 檔案
def run_a():
    subprocess.Popen(["python", "cr_with_supabase2.py"])
    time.sleep(120)  # 等待 1 秒，確保 a.py 完成
    subprocess.Popen(["python", "clean_daa.py"])
    time.sleep(900)  # 等待 900 秒，確保 a.py 完成
    subprocess.Popen(["python", "SE_test2.py"])

# 設定排程
# schedule.every(60).minutes.do(run_a)   # 每1分鐘跑一次 b.py
schedule.every(1).hours.do(run_a) # 每1小時跑一次 run_a

# # 持續執行
while True:
    schedule.run_pending()
    time.sleep(1)

# run_a()