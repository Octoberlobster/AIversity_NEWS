
import subprocess
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from queue import Queue
from threading import Thread

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
    force=True
)

# 您目前的腳本清單
scripts = [
        # "Crawler/craw.py",

        # "New_Summary/scripts/quick_run.py",
        # "Supabase_error_fix/news_notitle.py",

        # "Category_images/generate_categories_from_single_news.py",
        # "Analyze/Position_flag.py",
        # "Analyze/Who_talk.py",
        # "Analyze/Suicide_flag.py",
        # "Attribution/Attribution_gemini.py",
        # "Category_images/generate_picture_to_supabase/generate_from_supabase.py",
        # "Analyze/Pros_and_cons.py",
        # "Supabase_error_fix/who_talk_false.py",
        # "Analyze/Pro_Analyze.py",

        # "Relative/Relative_News.py",
        # "Supabase_error_fix/relative_false.py",
        # "Translate/Translate.py",
        # "Relative/Relative_Topics.py",

        # 10大新聞
        # "Toptennews/Toptennews.py"

        # 專題相關(每天執行)
        # "Topic/topic_get_title.py",
        # "Topic/Classfication.py",
        # "Topic/complete_news_grouper.py",
        # 'Topic/topic_group_update.py',
        # "Topic/topic_summary.py",
        # "Topic/Pro_Analyze_Topic.py",
        # "Topic/topic_5w1h_2.py",
        # "Topic/topic_report.py",
        # "Topic/translate_topic.py",

        # 專題相關(每週執行)
        # "Topic/complete_news_grouper.py",
        # "Topic/topic_summary.py",
        # "Topic/Pro_Analyze_Topic.py",
        # "Topic/topic_5w1h_2.py",
        # "Topic/topic_report.py",
        # "Topic/translate_topic.py",
]

def log_stream(stream, script_name, log_queue):
    """將輸出串流寫入日誌佇列"""
    for line in stream:
        log_queue.put((script_name, line.strip()))

def run_script(script, log_queue):
    """執行單一 Python 腳本"""
    try:
        logging.info(f"▶ 執行 {script} ...")
        
        process = subprocess.Popen(
            ["python", "-u", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        # 建立專門的執行緒來處理輸出
        log_thread = Thread(
            target=log_stream,
            args=(process.stdout, script, log_queue),
            daemon=True
        )
        log_thread.start()

        # 等待程序完成
        return_code = process.wait()
        log_thread.join()

        if return_code != 0:
            logging.error(f"❌ {script} 執行出錯 (return code {return_code})")
            return False
        else:
            logging.info(f"✅ {script} 執行完成")
            return True
            
    except Exception as e:
        logging.error(f"❌ {script} 執行時發生錯誤: {str(e)}")
        return False

def log_worker(log_queue):
    """處理日誌佇列的工作者"""
    while True:
        try:
            script_name, message = log_queue.get()
            if message == "STOP":
                break
            logging.info(f"[{script_name}] {message}")
            log_queue.task_done()
        except Exception:
            continue

def run_scripts_parallel(max_workers=None):
    """平行執行所有指定的 Python 腳本"""
    if max_workers is None:
        # 使用 CPU 核心數量作為預設值
        max_workers = max(1, multiprocessing.cpu_count())
    
    logging.info(f"開始平行執行腳本，最大同時執行數: {max_workers}")
    
    # 建立日誌佇列和日誌處理執行緒
    log_queue = Queue()
    log_thread = Thread(target=log_worker, args=(log_queue,), daemon=True)
    log_thread.start()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任務
        future_to_script = {
            executor.submit(run_script, script, log_queue): script 
            for script in scripts
        }
        
        # 等待所有任務完成
        for future in as_completed(future_to_script):
            script = future_to_script[future]
            try:
                success = future.result()
                if not success:
                    logging.error(f"❌ {script} 執行失敗")
            except Exception as e:
                logging.error(f"❌ {script} 執行時發生錯誤: {str(e)}")
    
    # 停止日誌處理執行緒
    log_queue.put(("", "STOP"))
    log_thread.join()
    
    logging.info("所有腳本執行完成")

if __name__ == "__main__":
    run_scripts_parallel(max_workers=4)