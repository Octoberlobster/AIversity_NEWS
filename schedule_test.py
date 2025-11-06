import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
    force=True
)

scripts = [
    # "test5_play_taiwan.py", 
    # "test5_play_usa.py",
    # "./New_Summary/scripts/quick_run.py",

    # "test5_play_taiwan_2.py", 
    # "test5_play_usa_2.py",

    # "test5_play_indo.py", 
    # "test5_play_japan.py",
    # "./New_Summary/scripts/quick_run.py",

    # "test5_play_indo_2.py", 
    # "test5_play_japan_2.py",

    "./demo/data_to_supabase/generate_categories_from_single_news.py",
    "Position_flag.py",
    "pros_and_cons.py",

    "Who_talk.py",
    "supabase_error_fix/who_talk_false.py",
    "Pro_Analyze.py",
    "./demo/data_to_supabase/generate_picture_to_supabase/generate_from_supabase.py",
    "Translate.py",

    "./Relative_News.py",
    "./supabase_error_fix/relative_false.py"
    "./Relative_Topics.py",

    # 專題相關
    # "topic/Classfication.py",
    # "topic/topic_summary.py",
    # "topic/complete_news_grouper.py",
    # "topic/Pro_Analyze_Topic.py",
    # "topic/topic_5w1h_2.py",
    # "topic/topic_report.py",
    # "topic/translate_topic.py",
]

def run_scripts():
    """執行所有指定的 Python 腳本"""
    for script in scripts:
        logging.info(f"▶ 執行 {script} ...")

        process = subprocess.Popen(
            ["python", "-u", script],  # Add -u flag to force unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"  # Use replace instead of ignore for better handling
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
