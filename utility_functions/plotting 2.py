# plotting.py
import matplotlib.pyplot as plt

def plot_time_line(jobs, title, font_size=12, figsize=(6, 3)):
    """
    Plot a timeline of jobs with their start and end times.

    Parameters:
    jobs : dict
        A dictionary where keys are job IDs and values are lists containing start and end times of the jobs.
    title : str
        The title of the plot.
    font_size : int, optional
        The font size for plot labels and title (default is 12).
    figsize : tuple, optional
        The size of the figure for the plot (default is (6, 3)).

    Example:
    jobs = {'Job1': [1, 4], 'Job2': [2, 6], 'Job3': [5, 9]}
    plot_time_line(jobs, 'Job Timeline')
    """
    # Extract job IDs, start times, and end times
    job_ids = list(jobs.keys())
    start_times = [jobs[job][0] for job in job_ids]
    end_times = [jobs[job][1] for job in job_ids]

    # Calculate durations
    durations = [end - start for start, end in zip(start_times, end_times)]

    # Plot
    plt.figure(figsize=figsize)
    plt.barh(job_ids, durations, left=start_times, color='blue')
    plt.xlabel('Time', fontsize=font_size)
    plt.ylabel('Job ID', fontsize=font_size)
    plt.title(title, fontsize=font_size)
    plt.xticks(fontsize=font_size)
    plt.yticks(fontsize=font_size)
    plt.grid(True)

    # Show the plot
    plt.show()