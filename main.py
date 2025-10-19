from google.cloud import run_v2

# Pub/Sub background function
def trigger_run_job(event, context):
    client = run_v2.JobsClient()
    job_name = client.job_path("airy-sled-471803-b7", "asia-east1", "my-job")
    request = run_v2.RunJobRequest(name=job_name)
    client.run_job(request=request)
    print("✅ Cloud Run Job triggered:", job_name)
