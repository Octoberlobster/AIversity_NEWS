import schedule
import subprocess
import time

scripts = ["cr_with_supabase2.py",  "clean_daa.py", "SE_test2.py", "Cluster.py", "GenerateNews.py", "GenerateRoles.py", "event_progress.py", "similarity.py", "Predict_Future.py"]

for script in scripts:
    print(f"執行 {script} ...")
    result = subprocess.run(['python3', script])
    if result.returncode != 0:
        print(f"{script} 執行出錯，停止後續執行。")
        break