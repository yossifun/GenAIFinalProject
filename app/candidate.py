class Candidate:
    def __init__(self, name: str, phone: str):
        self.name = name
        self.phone = phone

    @property
    def name(self):
        return self._name
    
    @property
    def phone(self):
        return self._phone