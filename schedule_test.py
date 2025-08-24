import schedule
import subprocess
import time

scripts = ["test4.py", 
           "clean_data.py",
           # "supabase_upload.py", 
           "/code/畢專test/New_Summary/scripts/quick_run.py",
           "/code/畢專test/demo/data_to_supabase/generate_categories_from_single_news.py",
           "/code/畢專test/demo/data_to_supabase/generate_picture_to_supabase/generate_from_supabase.py",
           "Relative_News.py"]

for script in scripts:
    print(f"執行 {script} ...")
    result = subprocess.run(
        ['python', script],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    if result.returncode != 0:
        print(f"{script} 執行出錯：\n{result.stderr}")
        break
    else:
        print(result.stdout)