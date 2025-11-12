#datetime.now test
from datetime import datetime
current_time = datetime.now().isoformat(sep=' ', timespec='minutes')
print("Current Date and Time:", current_time)