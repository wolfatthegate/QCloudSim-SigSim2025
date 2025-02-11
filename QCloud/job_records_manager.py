# job_records_manager.py

class JobRecordsManager:
    def __init__(self, event_bus):
        """
        Initialize the JobRecordsManager with an EventBus instance.
        """
        self.event_bus = event_bus
        self.job_records = {}

    def log_job_event(self, job_id, event_type, timestamp):
        """
        Logs a job event with a timestamp.

        Parameters:
        - job_id: The ID of the job.
        - event_type: The type of event (e.g., 'arrival', 'start', 'finish', 'devc_start', 'devc_finish').
        - timestamp: The timestamp of the event.
        """
        if job_id not in self.job_records:
            self.job_records[job_id] = {}
        
        # Append the timestamp if the event_type already exists
        if event_type in self.job_records[job_id]:
            if isinstance(self.job_records[job_id][event_type], list):
                self.job_records[job_id][event_type].append(timestamp)
            else:
                self.job_records[job_id][event_type] = [self.job_records[job_id][event_type], timestamp]
        else:
            self.job_records[job_id][event_type] = timestamp

    def get_job_records(self):
        """
        Returns all job records.
        """
        return self.job_records
