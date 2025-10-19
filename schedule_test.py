import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

scripts = [
    "test5_play.py", 
    "./New_Summary/scripts/quick_run.py",
    "Who_talk.py",
    "Position_flag.py",
    "Pro_Analyze.py",
    "./demo/data_to_supabase/generate_categories_from_single_news.py",
    "./Relative_News.py",
    "./Relative_Topics.py",
    "./demo/data_to_supabase/generate_picture_to_supabase/generate_from_supabase.py",
    "Translate.py"
]

def run_scripts():
    """執行所有指定的 Python 腳本"""
    for script in scripts:
        logging.info(f"▶ 執行 {script} ...")

        process = subprocess.Popen(
            ["python", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        for line in process.stdout:
            logging.info(f"[{script}] {line.strip()}")

        process.wait()

        if process.returncode != 0:
            logging.error(f"❌ {script} 執行出錯 (return code {process.returncode})")
            break
        else:
            logging.info(f"✅ {script} 執行完成")

if __name__ == "__main__":
    run_scripts()
