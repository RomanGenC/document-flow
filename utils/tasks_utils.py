import simplejson


def run_task(
    task,
    task_args=None,
    task_kwargs=None,
    queue=None,
    task_id=None,
    time_limit=None,
):
    task_args = task_args or []
    task_kwargs = task_kwargs or {}
    queue = queue or 'celery'
    try:
        simplejson.dumps(task_args)
        simplejson.dumps(task_kwargs)
    except simplejson.errors.JSONDecodeError:
        raise TypeError('Only simple types task arguments permitted')

    task.apply_async(
        args=[],
        kwargs=task_kwargs,
        queue=queue,
        task_id=task_id,
        time_limit=time_limit,
    )