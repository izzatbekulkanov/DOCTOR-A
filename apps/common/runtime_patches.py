from copy import copy


def apply_runtime_patches():
    """
    Apply small compatibility patches needed by the current runtime.

    Django 5.1 on Python 3.14 can hit an AttributeError in
    django.template.context.BaseContext.__copy__ when admin templates clone the
    render context. Replace that implementation with a version that copies the
    instance dictionary directly.
    """
    from django.template.context import BaseContext

    if getattr(BaseContext.__copy__, "_doctor_a_patched", False):
        return

    def _base_context_copy(self):
        duplicate = object.__new__(self.__class__)
        duplicate.__dict__ = self.__dict__.copy()
        duplicate.dicts = self.dicts[:]
        return duplicate

    _base_context_copy._doctor_a_patched = True
    BaseContext.__copy__ = _base_context_copy
