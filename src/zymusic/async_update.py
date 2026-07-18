def async_update(cls):
    _original_update = cls.update

    def _safe_update(self):
        if not self.page:
            return

        async def _do_update():
            _original_update(self)

        self.page.run_task(_do_update)

    cls.update = _safe_update
    return cls
