def calculate_duration(tasklist, return_seconds=False):
    """
    task list comes as a list of task objects, we take the instance variable "duration",
    it's a string looking like "120530" -> "DDHHMN"
    """
    durations = [0, 0, 0]  # days, hours, minutes
    if type(tasklist) is not list:
        tasks = [tasklist]
    else:
        tasks = tasklist
    for t in tasks:
        durations[0] = durations[0] + int(t.duration[0:2])  # days
        durations[1] = durations[1] + int(t.duration[2:4])  # hours
        durations[2] = durations[2] + int(t.duration[4:6])  # minutes

    minutes, hours = durations[2] % 60, durations[2] // 60
    hours, days = durations[1] % 24 + hours, durations[1] // 24
    days = durations[0] + days

    if return_seconds:
        s_time = days * 8.64e4 + hours * 3.6e3 + minutes * 60
        return s_time

    return days, hours, minutes

def return_string_duration(seconds):
    """
    kind of the opposite of calculate duration, here we input seconds and output a string "DDHHMN"
    """
    minutes = int(seconds // 60) % 60
    hours = int(seconds // 3600) % 24
    days = int(seconds // 86400)
    l = [days, hours, minutes]
    for i in range(len(l)):
        l[i] = str(l[i])
        if len(l[i]) == 1:
            l[i] = "0" + l[i]
    return l[0], l[1], l[2]
def get_percentage(remaining_time, duration):
    p = 100 - ((remaining_time / duration) * 100)
    return p