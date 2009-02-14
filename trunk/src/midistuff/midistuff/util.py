class IdDict(dict):
    def __init__(self, *args, **kwargs):
        super(IdDict, self).__init__(*args, **kwargs)
        self.last_id= 0
    def __getitem__(self, key):
        if not key in self:
            self.last_id+= 1
            self[key]= self.last_id
        return dict.__getitem__(self, key)


