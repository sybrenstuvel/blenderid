def short_description(description: str):
    """Decorator to set the action function description.

    Added so that the description and function itself can be kept close to
    each other, without violating PEP8.
    """

    def decorator(func):
        func.short_description = description
        return func

    return decorator
